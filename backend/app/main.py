import logging
import urllib.parse
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse, Response

from .infra.middleware import add_middleware
from .infra.exceptions import ServiceError, ExternalServiceError, ResourceNotFoundError, AuthenticationError
from .infra.metrics import HealthChecker, metrics_collector
from .dependencies import get_current_user_openid, get_optional_user_openid

logger = logging.getLogger(__name__)
from .infra.config import settings
from .infra.bootstrap import seed
from .repositories.memory import MemoryRepository
from .repositories.tcb import TCBRepository
from .infra.tcb_client import TCBClient
from .infra.wechat_client import WeChatAuthClient
from .infra.storage import LocalStorage, COSStorage
from .services.auth import AuthService
from .services.content import ContentService
from .services.vocab import VocabService
from .services.study import StudyService
from .services.import_ import ImportService
from .services.export import ExportService
from .services.billing import BillingService
from .services.wishlist import WishlistService
from .services.plan import PlanService
from .services.events import EventsService
from .schemas.auth import MeRequest, MeResponse, User
from .schemas.content import ContentItem, ContentListResponse
from .schemas.study import SaveProgressRequest, OkResponse
from .schemas.vocab import (
    VocabAddRequest,
    VocabListResponse,
    VocabReviewRequest,
    VocabReviewResponse,
)
from .schemas.import_ import ImportRequest, ImportResponse
from .schemas.export import ExportLongshotRequest, ExportLongshotResponse
from .schemas.billing import CreateIntentRequest, OkResponse as BillingOk
from .schemas.wishlist import WishlistRequest, OkResponse as WishlistOk
from .schemas.cron import DailyDigestRequest, OkResponse as CronOk
from datetime import datetime, timezone
from .schemas.plan import PlanStatsResponse
from .schemas.events import TrackEventRequest, OkResponse as TrackOk


app = FastAPI(title="Language Learning Platform Backend", version="0.1.0")
add_middleware(app)


# Global exception handlers
@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    logger.error(
        "Service error occurred",
        extra={
            "error_code": exc.error_code,
            "error_message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
            "method": request.method
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.message,
            "code": exc.error_code,
            "details": exc.details
        }
    )


@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    logger.info(
        "Resource not found",
        extra={
            "error_code": exc.error_code,
            "error_message": exc.message,
            "details": exc.details,
            "path": str(request.url.path)
        }
    )
    return JSONResponse(
        status_code=404,
        content={
            "error": exc.message,
            "code": exc.error_code,
            "details": exc.details
        }
    )


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    logger.warning(
        "Authentication error",
        extra={
            "error_code": exc.error_code,
            "error_message": exc.message,
            "path": str(request.url.path)
        }
    )
    return JSONResponse(
        status_code=401,
        content={
            "error": exc.message,
            "code": exc.error_code
        }
    )


@app.exception_handler(ExternalServiceError)
async def external_service_error_handler(request: Request, exc: ExternalServiceError):
    logger.error(
        "External service error",
        extra={
            "error_code": exc.error_code,
            "error_message": exc.message,
            "service": exc.service_name,
            "details": exc.details,
            "path": str(request.url.path)
        }
    )
    return JSONResponse(
        status_code=503,
        content={
            "error": "Service temporarily unavailable",
            "code": exc.error_code,
            "retry_after": 60  # Suggest retry after 60 seconds
        }
    )

# Simple DI bootstrap with provider toggle
if settings.repo_provider == "tcb":
    client = TCBClient.from_settings(settings)
    repo = TCBRepository(client)
else:
    repo = MemoryRepository()
    seed(repo)
wechat_client = None
if settings.wechat_auth_enabled and settings.wechat_appid and settings.wechat_secret:
    try:
        wechat_client = WeChatAuthClient.from_settings(settings)
    except Exception:
        wechat_client = None
auth_service = AuthService(repo, wechat_client)
content_service = ContentService(repo)
vocab_service = VocabService(repo)
study_service = StudyService(repo)
import_service = ImportService(repo)
if settings.storage_provider == "cos" and all([settings.cos_bucket, settings.cos_region, settings.cos_secret_id, settings.cos_secret_key]):
    storage = COSStorage(
        bucket=settings.cos_bucket, region=settings.cos_region,
        secret_id=settings.cos_secret_id, secret_key=settings.cos_secret_key,
        cdn_base=settings.cos_cdn_base or settings.cdn_base,
    )
else:
    storage = LocalStorage(settings.cdn_base)
export_service = ExportService(repo, storage)
billing_service = BillingService(repo)
wishlist_service = WishlistService(repo)
plan_service = PlanService(repo)
events_service = EventsService(repo)


# Initialize health checker
health_checker = HealthChecker(repo=repo)


# Health and monitoring endpoints
@app.get("/health")
def health():
    """Basic health check endpoint."""
    return {"status": "ok", "env": settings.env}


@app.get("/health/detailed")
def health_detailed():
    """Detailed health check with component status."""
    return health_checker.get_health_status()


@app.get("/metrics")
def metrics():
    """Application metrics endpoint."""
    return metrics_collector.get_metrics_summary()


@app.post("/auth/me", response_model=MeResponse)
def auth_me(payload: MeRequest) -> MeResponse:
    openid = auth_service.exchange_code_for_openid(payload.code)
    user = auth_service.get_or_create_user(openid)
    return MeResponse(user=user, featureFlags=settings.feature_flags)


@app.get("/content", response_model=ContentListResponse)
def content_list(page: int = 1, pageSize: int = 20, type: str | None = None, level: str | None = None):
    items, total = content_service.list(page, pageSize, type, level)
    return ContentListResponse(items=items, total=total)


@app.get("/content/{id}", response_model=ContentItem)
def content_get(id: str):
    return content_service.get(id)


@app.post("/study/progress", response_model=OkResponse)
def study_save_progress(
    payload: SaveProgressRequest,
    user_id: str = Depends(get_current_user_openid)
) -> OkResponse:
    study_service.save_progress(payload, user_id=user_id)
    return OkResponse(ok=True)


@app.post("/vocab", response_model=OkResponse)
def vocab_add(
    payload: VocabAddRequest,
    user_id: str = Depends(get_current_user_openid)
) -> OkResponse:
    vocab_service.add(payload, user_id=user_id)
    return OkResponse(ok=True)


@app.get("/vocab", response_model=VocabListResponse)
def vocab_list(
    page: int = 1,
    pageSize: int = 50,
    user_id: str = Depends(get_current_user_openid)
):
    items, total = vocab_service.list(page, pageSize, user_id=user_id)
    return VocabListResponse(items=items, total=total)


@app.delete("/vocab/{word}", response_model=OkResponse)
def vocab_remove(
    word: str,
    user_id: str = Depends(get_current_user_openid)
) -> OkResponse:
    vocab_service.remove(word, user_id=user_id)
    return OkResponse(ok=True)


@app.post("/vocab/review", response_model=VocabReviewResponse)
def vocab_review(
    payload: VocabReviewRequest,
    user_id: str = Depends(get_current_user_openid)
) -> VocabReviewResponse:
    item = vocab_service.review(user_id=user_id, word=payload.word, rating=payload.rating)
    return VocabReviewResponse(item=item)


@app.get("/vocab/due", response_model=VocabListResponse)
def vocab_due(
    before: str | None = None,
    page: int = 1,
    pageSize: int = 50,
    user_id: str = Depends(get_current_user_openid)
) -> VocabListResponse:
    if before:
        try:
            bdt = datetime.fromisoformat(before)
            if bdt.tzinfo is None:
                bdt = bdt.replace(tzinfo=timezone.utc)
        except Exception:
            bdt = datetime.now(timezone.utc)
    else:
        bdt = datetime.now(timezone.utc)
    items, total = vocab_service.due(user_id=user_id, before=bdt, page=page, page_size=pageSize)
    return VocabListResponse(items=items, total=total)


@app.post("/import", response_model=ImportResponse)
def import_from_url_or_text(payload: ImportRequest) -> ImportResponse:
    new_id, segs = import_service.run(payload)
    return ImportResponse(id=new_id, type=payload.type, segments=segs)


@app.post("/export/longshot", response_model=ExportLongshotResponse)
def export_longshot(payload: ExportLongshotRequest) -> ExportLongshotResponse:
    url = export_service.longshot(payload.contentId)
    return ExportLongshotResponse(url=url)


@app.post("/billing/intent", response_model=BillingOk)
def billing_create_intent(
    payload: CreateIntentRequest,
    user_id: str | None = Depends(get_optional_user_openid)
) -> BillingOk:
    # optional openid, included when available
    billing_service.create_intent(payload, user_id=user_id)
    return BillingOk(ok=True)


@app.post("/wishlist", response_model=WishlistOk)
def wishlist_submit(
    payload: WishlistRequest,
    user_id: str | None = Depends(get_optional_user_openid)
) -> WishlistOk:
    wishlist_service.submit(payload, user_id=user_id)
    return WishlistOk(ok=True)


@app.post("/cron/daily-digest", response_model=CronOk)
def cron_daily_digest(payload: DailyDigestRequest | None = None) -> CronOk:
    # TODO: Send scheduled notifications
    return CronOk(ok=True)


@app.get("/plan/stats", response_model=PlanStatsResponse)
def plan_stats(user_id: str = Depends(get_current_user_openid)) -> PlanStatsResponse:
    data = plan_service.stats(user_id)
    return PlanStatsResponse(**data)


@app.post("/events", response_model=TrackOk)
def events_track(
    payload: TrackEventRequest,
    user_id: str = Depends(get_current_user_openid)
) -> TrackOk:
    events_service.track(user_id, payload.event, payload.props or {}, payload.ts)
    return TrackOk(ok=True)


# ============ Assessment APIs (Mock) ============
import uuid

# 存储评估会话 (内存模拟)
_assessments = {}

@app.post("/api/assessment/start")
def assessment_start():
    """启动评估"""
    assessment_id = f"assess_{uuid.uuid4().hex[:12]}"

    _assessments[assessment_id] = {
        "id": assessment_id,
        "current_question": 1,
        "answers": []
    }

    # 返回第一题
    question_text = "What does 'Hello' mean?"
    # 使用后端代理的TTS URL（完整URL）
    # 注意：微信小程序不支持localhost，必须使用127.0.0.1
    base_url = "http://127.0.0.1:8000"  # TODO: 从配置读取
    audio_url = f"{base_url}/api/tts/audio?text={urllib.parse.quote(question_text)}&lang=en"

    return {
        "assessment_id": assessment_id,
        "first_question": {
            "id": "q_001",
            "type": "reading",
            "level": "A2",
            "content": {
                "question": question_text,
                "question_zh": "'Hello' 是什么意思？",
                "passage": "Hello is a common greeting in English.",
                "audio_url": audio_url,
                "options": ["你好", "再见", "谢谢", "对不起"]
            },
            "correct_index": 0
        }
    }


@app.post("/api/assessment/answer")
def assessment_answer(payload: dict):
    """提交答案"""
    assessment_id = payload.get("assessment_id")
    answer_index = payload.get("answer_index", 0)

    assessment = _assessments.get(assessment_id, {})
    current = assessment.get("current_question", 1)

    # 模拟答案正确性
    is_correct = (answer_index == 0)

    # 记录答案
    if "answers" not in assessment:
        assessment["answers"] = []
    assessment["answers"].append({
        "question_id": f"q_{current:03d}",
        "is_correct": is_correct,
        "answer_index": answer_index
    })

    # 下一题
    next_num = current + 1
    assessment["current_question"] = next_num

    if next_num <= 10:
        # 返回下一题
        question_types = ["reading", "listening", "vocabulary", "grammar"]
        q_type = question_types[(next_num - 1) % 4]

        question_text = f"Question {next_num}: Choose the correct answer"

        # 生成TTS音频URL（使用后端代理，完整URL）
        base_url = "http://127.0.0.1:8000"
        if q_type == "listening":
            # 听力题使用完整句子
            audio_text = "Listen carefully. The cat is sitting on the mat."
            audio_url = f"{base_url}/api/tts/audio?text={urllib.parse.quote(audio_text)}&lang=en"
        else:
            # 其他题型也提供问题朗读
            audio_url = f"{base_url}/api/tts/audio?text={urllib.parse.quote(question_text)}&lang=en"

        return {
            "is_correct": is_correct,
            "explanation": "正确答案是 '你好'" if not is_correct else None,
            "next_question": {
                "id": f"q_{next_num:03d}",
                "type": q_type,
                "level": "B1",
                "content": {
                    "question": question_text,
                    "question_zh": f"问题 {next_num}：选择正确答案",
                    "passage": "This is a sample passage for reading comprehension." if q_type == "reading" else None,
                    "audio_url": audio_url,
                    "options": ["Option A", "Option B", "Option C", "Option D"]
                },
                "correct_index": 0
            }
        }
    else:
        # 完成
        return {
            "is_correct": is_correct,
            "explanation": None,
            "next_question": None
        }


@app.post("/api/assessment/complete")
def assessment_complete(payload: dict):
    """完成评估"""
    assessment_id = payload.get("assessment_id")
    assessment = _assessments.get(assessment_id, {})
    answers = assessment.get("answers", [])

    # 计算准确率
    correct_count = sum(1 for a in answers if a.get("is_correct"))
    accuracy = correct_count / len(answers) if answers else 0.5

    # 模拟结果
    return {
        "overall_level": "B1" if accuracy >= 0.6 else "A2",
        "ability_score": accuracy * 5,
        "confidence": 0.85,
        "dimensions": {
            "listening": {
                "level": "A2",
                "accuracy": 0.7,
                "ability": 1.2
            },
            "reading": {
                "level": "B1",
                "accuracy": 0.8,
                "ability": 1.5
            },
            "vocabulary": {
                "level": "A2",
                "accuracy": 0.65,
                "ability": 1.0
            },
            "grammar": {
                "level": "B1",
                "accuracy": 0.75,
                "ability": 1.3
            }
        },
        "weak_areas": ["listening", "vocabulary"],
        "strong_areas": ["reading"],
        "recommendations": {
            "suggested_scenarios": ["机场场景", "酒店场景", "餐厅用餐"],
            "focus_areas": ["听力理解", "词汇掌握"],
            "estimated_study_days": 30
        }
    }


@app.get("/api/assessment/history")
def assessment_history():
    """获取评估历史"""
    return {
        "assessments": []
    }


# ============ TTS API ============
from .services.tts_service import TTSService

# 创建TTS服务实例
tts_service = TTSService()

@app.get("/api/tts/audio")
async def tts_audio(text: str, lang: str = "en", engine: str = "edge"):
    """
    生成并返回TTS音频文件（默认使用Edge TTS获得更自然的老师风格声音）

    参数:
    - text: 要转换的文本
    - lang: 语言代码 (en, zh-CN等)
    - engine: TTS引擎 (edge=高质量, google=降级)

    返回: MP3音频文件
    """
    print(f"\n{'='*80}")
    print(f"🎯 [API] /api/tts/audio 被调用")
    print(f"   文本: {text}")
    print(f"   语言: {lang}")
    print(f"   引擎: {engine}")
    print(f"{'='*80}\n")
    logger.info(f"🎯 [API] /api/tts/audio 被调用 | text='{text}' | lang={lang} | engine={engine}")
    try:
        # 使用Edge TTS生成音频（更自然的声音）- 异步调用
        audio_file = await tts_service.get_tts_url_async(text, lang, engine)

        if audio_file and Path(audio_file).exists():
            return FileResponse(
                audio_file,
                media_type="audio/mpeg",
                headers={
                    "Cache-Control": "public, max-age=31536000",  # 缓存1年
                    "Access-Control-Allow-Origin": "*"
                }
            )
        else:
            # 降级方案：返回空音频或错误
            return Response(
                content="TTS generation failed",
                status_code=500,
                media_type="text/plain"
            )

    except Exception as e:
        logger.error(f"TTS音频生成失败: {e}")
        return Response(
            content=str(e),
            status_code=500,
            media_type="text/plain"
        )


# ============ Dialogue API (Mock with TTS) ============

@app.get("/api/dialogues/{dialogue_id}")
def get_dialogue(dialogue_id: str):
    """
    获取对话详情 (带TTS音频)

    返回对话的所有句子，每句都有TTS生成的音频URL
    """
    # 模拟对话数据
    dialogue_data = {
        "airport-checkin-001": {
            "id": "airport-checkin-001",
            "scenario_id": "airport-basics",
            "title_en": "Airport Check-in",
            "title_zh": "机场值机办理",
            "sentences": [
                {
                    "order": 1,
                    "speaker": "Staff",
                    "text_en": "Good morning! May I see your passport and ticket, please?",
                    "text_zh": "早上好！请出示您的护照和机票？",
                    "phonetic": "/ɡʊd ˈmɔːrnɪŋ meɪ aɪ siː jɔːr ˈpæspɔːrt ənd ˈtɪkɪt pliːz/",
                    "key_words": ["passport", "ticket"]
                },
                {
                    "order": 2,
                    "speaker": "Passenger",
                    "text_en": "Here you are.",
                    "text_zh": "给您。",
                    "phonetic": "/hɪər juː ɑːr/",
                    "key_words": []
                },
                {
                    "order": 3,
                    "speaker": "Staff",
                    "text_en": "Would you like a window seat or an aisle seat?",
                    "text_zh": "您想要靠窗的座位还是靠过道的座位？",
                    "phonetic": "/wʊd juː laɪk ə ˈwɪndəʊ siːt ɔːr ən aɪl siːt/",
                    "key_words": ["window seat", "aisle seat"]
                },
                {
                    "order": 4,
                    "speaker": "Passenger",
                    "text_en": "A window seat, please.",
                    "text_zh": "靠窗的座位，谢谢。",
                    "phonetic": "/ə ˈwɪndəʊ siːt pliːz/",
                    "key_words": []
                },
                {
                    "order": 5,
                    "speaker": "Staff",
                    "text_en": "Here is your boarding pass. Have a nice flight!",
                    "text_zh": "这是您的登机牌。祝您旅途愉快！",
                    "phonetic": "/hɪər ɪz jɔːr ˈbɔːrdɪŋ pæs hæv ə naɪs flaɪt/",
                    "key_words": ["boarding pass", "flight"]
                }
            ]
        }
    }

    dialogue = dialogue_data.get(dialogue_id)

    if not dialogue:
        # 默认返回一个简单对话
        dialogue = {
            "id": dialogue_id,
            "title_en": "Sample Dialogue",
            "title_zh": "示例对话",
            "sentences": [
                {
                    "order": 1,
                    "speaker": "Person A",
                    "text_en": "Hello, how are you?",
                    "text_zh": "你好，你好吗？",
                    "phonetic": "/həˈloʊ haʊ ɑːr juː/",
                    "key_words": ["hello"]
                }
            ]
        }

    # 为每个句子生成TTS音频URL（使用后端代理，完整URL）
    base_url = "http://localhost:8000"
    for sentence in dialogue["sentences"]:
        text_encoded = urllib.parse.quote(sentence["text_en"])
        sentence["audio_url"] = f"{base_url}/api/tts/audio?text={text_encoded}&lang=en"

    return dialogue
