import logging
import time
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
from .schemas.auth import MeRequest, MeResponse, RefreshRequest, RefreshResponse, User
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

# Mount pre-generated audio files
from fastapi.staticfiles import StaticFiles
_static_audio = Path(__file__).resolve().parent.parent / "static" / "audio"
if _static_audio.is_dir():
    app.mount("/static/audio", StaticFiles(directory=str(_static_audio)), name="static-audio")


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
    from .infra.jwt_utils import create_token
    token = create_token(openid)
    return MeResponse(user=user, token=token, featureFlags=settings.feature_flags)


@app.post("/auth/refresh", response_model=RefreshResponse)
def auth_refresh(payload: RefreshRequest) -> RefreshResponse:
    """Refresh a JWT token. Accepts valid or recently expired tokens (within 7 days)."""
    from .infra.jwt_utils import refresh_token
    new_token, openid = refresh_token(payload.token)
    if not new_token or not openid:
        raise HTTPException(status_code=401, detail="Token cannot be refreshed")
    return RefreshResponse(token=new_token, openid=openid)


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


# ============ Assessment APIs (Real) ============
import uuid
import random

from .services.assessment_service import AdaptiveQuestionSelector, AssessmentEvaluator
from .domain.assessment import Assessment, AssessmentQuestion, DimensionResult

# In-memory assessment sessions (keyed by assessment_id)
_assessments: dict[str, dict] = {}
_assessment_timestamps: dict[str, float] = {}
_ASSESSMENT_TTL_SECONDS = 30 * 60  # 30 minutes


def _cleanup_stale_sessions() -> None:
    """Remove assessment sessions older than TTL (lazy cleanup)."""
    now = time.monotonic()
    expired = [k for k, ts in _assessment_timestamps.items() if now - ts > _ASSESSMENT_TTL_SECONDS]
    for k in expired:
        _assessments.pop(k, None)
        _assessment_timestamps.pop(k, None)


# Evaluator instance (stateless, reusable)
_evaluator = AssessmentEvaluator()


class _MemoryQuestionRepo:
    """Thin adapter: lets AdaptiveQuestionSelector query the MemoryRepository."""

    def __init__(self, repository):
        self._repo = repository

    async def get(self, question_id: str):
        doc = self._repo.get("assessment_questions", question_id)
        if not doc:
            return None
        return self._to_domain(doc)

    async def find_closest(self, level: str, type: str, exclude_ids: list[str]):
        items, _ = self._repo.query("assessment_questions", {"level": level, "type": type}, limit=100, offset=0)
        candidates = [it for it in items if it["id"] not in exclude_ids and it.get("is_active", True)]
        if not candidates:
            # Fallback: ignore level, just match type
            items, _ = self._repo.query("assessment_questions", {"type": type}, limit=100, offset=0)
            candidates = [it for it in items if it["id"] not in exclude_ids and it.get("is_active", True)]
        if not candidates:
            # Final fallback: any active question not yet answered
            items, _ = self._repo.query("assessment_questions", None, limit=200, offset=0)
            candidates = [it for it in items if it["id"] not in exclude_ids and it.get("is_active", True)]
        if not candidates:
            return None
        return self._to_domain(random.choice(candidates))

    @staticmethod
    def _to_domain(doc: dict) -> AssessmentQuestion:
        from datetime import datetime as _dt
        return AssessmentQuestion(
            id=doc["id"],
            type=doc["type"],
            level=doc["level"],
            difficulty=doc.get("difficulty", 0.5),
            scenario_id=doc.get("scenario_id"),
            skill_tested=doc.get("skill_tested", ""),
            content=doc["content"],
            metadata=doc.get("metadata", {}),
            is_active=doc.get("is_active", True),
            created_at=_dt.fromisoformat(doc["created_at"]) if isinstance(doc.get("created_at"), str) else doc.get("created_at"),
        )


_question_repo = _MemoryQuestionRepo(repo)
_selector = AdaptiveQuestionSelector(_question_repo)


def _question_to_response(q: AssessmentQuestion, request: Request) -> dict:
    """Convert domain question to API response dict with TTS audio URL."""
    base_url = f"https://{request.headers.get('host', request.url.netloc)}"
    content = dict(q.content)
    # Generate TTS audio_url for the question text (or listening transcript)
    if q.type == "listening" and content.get("transcript"):
        audio_text = content["transcript"]
    else:
        audio_text = content.get("question", "")
    content["audio_url"] = f"{base_url}/api/tts/audio?text={urllib.parse.quote(audio_text)}&lang=en"
    return {
        "id": q.id,
        "type": q.type,
        "level": q.level,
        "content": content,
        "correct_index": content.get("correct_index", 0),
    }


@app.post("/api/assessment/start")
async def assessment_start(request: Request):
    """启动评估 — 创建会话并返回第一题"""
    _cleanup_stale_sessions()
    assessment_id = f"assess_{uuid.uuid4().hex[:12]}"

    _assessment_timestamps[assessment_id] = time.monotonic()
    _assessments[assessment_id] = {
        "id": assessment_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "questions": [],  # answered question records
    }

    # Select the first question via adaptive algorithm
    first_q = await _selector.select_next([], total_questions=10)
    if not first_q:
        raise HTTPException(status_code=500, detail="No questions available in the question bank")

    return {
        "assessment_id": assessment_id,
        "first_question": _question_to_response(first_q, request),
    }


@app.post("/api/assessment/answer")
async def assessment_answer(payload: dict, request: Request):
    """提交答案 — 判断正误，自适应选下一题"""
    _cleanup_stale_sessions()
    assessment_id = payload.get("assessment_id")
    question_id = payload.get("question_id", "")
    answer_index = payload.get("answer_index", -1)
    time_spent = payload.get("time_spent", 0)

    session = _assessments.get(assessment_id)
    if not session:
        raise HTTPException(status_code=404, detail="Assessment session not found")

    # Look up the question from the repo to check correctness
    question = await _question_repo.get(question_id)
    if question:
        correct_index = question.content.get("correct_index", 0)
        is_correct = (answer_index == correct_index)
        explanation = question.content.get("explanation") if not is_correct else None
        q_type = question.type
        q_level = question.level
        difficulty = question.difficulty
    else:
        # Fallback if question not found (shouldn't happen normally)
        is_correct = False
        explanation = None
        q_type = "vocabulary"
        q_level = "B1"
        difficulty = 0.5

    # Record the answer
    session["questions"].append({
        "question_id": question_id,
        "type": q_type,
        "level": q_level,
        "difficulty": difficulty,
        "is_correct": is_correct,
        "time_spent": time_spent,
        "answer_selected": answer_index,
    })

    # Select next question (adaptive)
    next_q = await _selector.select_next(session["questions"], total_questions=10)

    return {
        "is_correct": is_correct,
        "explanation": explanation,
        "next_question": _question_to_response(next_q, request) if next_q else None,
    }


@app.post("/api/assessment/complete")
def assessment_complete(
    payload: dict,
    request: Request,
    user_id: str | None = Depends(get_optional_user_openid),
):
    """完成评估 — 使用 AssessmentEvaluator 计算真实结果"""
    assessment_id = payload.get("assessment_id")
    session = _assessments.get(assessment_id)
    if not session:
        raise HTTPException(status_code=404, detail="Assessment session not found")

    # Build a domain Assessment object for the evaluator
    assessment_obj = Assessment(
        user_id=user_id or "anonymous",
        started_at=datetime.fromisoformat(session["started_at"]),
        status="in_progress",
        questions=session["questions"],
    )

    result = _evaluator.calculate_result(assessment_obj)
    recommendations = _evaluator.generate_recommendations(result)

    # Clean up session
    _assessments.pop(assessment_id, None)
    _assessment_timestamps.pop(assessment_id, None)

    # Persist result to repo for history
    result_dict = result.to_dict()
    result_dict["recommendations"] = recommendations
    result_dict["assessment_id"] = assessment_id
    result_dict["user_id"] = user_id or "anonymous"
    result_dict["completed_at"] = datetime.now(timezone.utc).isoformat()
    result_dict["question_count"] = len(session["questions"])
    repo.put("assessment_results", result_dict)

    return {
        **result.to_dict(),
        "recommendations": recommendations,
    }


@app.get("/api/assessment/history")
def assessment_history(user_id: str | None = Depends(get_optional_user_openid)):
    """获取评估历史"""
    filters = {"user_id": user_id} if user_id else None
    items, total = repo.query("assessment_results", filters, limit=20, offset=0)
    # Sort by completed_at descending
    items.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
    return {
        "assessments": items,
        "total": total
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
    logger.info("TTS audio requested", extra={"text": text[:50], "lang": lang, "engine": engine})
    try:
        # 使用Edge TTS生成音频（更自然的声音）- 异步调用
        audio_file = await tts_service.get_tts_url_async(text, lang, engine)

        if audio_file and Path(audio_file).exists():
            return FileResponse(
                audio_file,
                media_type="audio/mpeg",
                headers={
                    "Cache-Control": "public, max-age=31536000",
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


# ============ Speech Evaluation API ============
from fastapi import UploadFile, File, Form
from .services.speech import evaluate as speech_evaluate

@app.post("/api/speech/evaluate")
async def api_speech_evaluate(
    file: UploadFile = File(...),
    reference: str = Form(...),
):
    """接收录音文件，语音识别后与原文比对打分。"""
    audio_bytes = await file.read()
    result = speech_evaluate(audio_bytes, reference)
    return result


# ============ Dialogue Progress API ============

@app.post("/api/dialogue/complete")
def dialogue_complete(
    payload: dict,
    user_id: str = Depends(get_current_user_openid),
):
    """Record dialogue completion and update plan progress if applicable."""
    dialogue_id = payload.get("dialogue_id")
    play_count = payload.get("play_count", 0)
    record_count = payload.get("record_count", 0)
    duration = payload.get("duration", 0)

    if not dialogue_id:
        raise HTTPException(status_code=400, detail="dialogue_id is required")

    if not repo.get("dialogues", dialogue_id):
        raise HTTPException(status_code=404, detail=f"Dialogue '{dialogue_id}' not found")

    # Save progress record
    progress = {
        "user_id": user_id,
        "dialogue_id": dialogue_id,
        "play_count": play_count,
        "record_count": record_count,
        "duration": duration,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    repo.put("dialogue_progress", progress)

    # Update active plan progress if a plan exists
    plans, _ = repo.query("plans", {"user_id": user_id, "status": "active"}, limit=1, offset=0)
    plan_updated = False
    if plans:
        plan = plans[0]
        for task in plan.get("daily_tasks", []):
            if task.get("dialogue_id") == dialogue_id and not task.get("is_completed"):
                task["is_completed"] = True
                plan_updated = True
                break

        if plan_updated:
            # Recalculate progress
            for goal in plan.get("scenario_goals", []):
                if dialogue_id in goal.get("dialogue_ids", []):
                    completed_in_scenario = sum(
                        1 for t in plan.get("daily_tasks", [])
                        if t.get("scenario_id") == goal["scenario_id"] and t.get("is_completed")
                    )
                    total_in_scenario = len(goal["dialogue_ids"])
                    goal["current_readiness"] = round(completed_in_scenario / max(1, total_in_scenario) * 0.85, 2)
                    goal["readinessPercent"] = round(goal["current_readiness"] * 100)

            total = plan.get("total_dialogues", 1)
            completed = sum(1 for t in plan.get("daily_tasks", []) if t.get("is_completed"))
            plan["completed_dialogues"] = completed
            plan["overall_progress"] = round(completed / max(1, total) * 100)
            plan["completed_scenarios"] = sum(
                1 for g in plan.get("scenario_goals", []) if g.get("current_readiness", 0) >= 0.85
            )
            if plan["overall_progress"] >= 100:
                plan["status"] = "completed"
            plan["updated_at"] = datetime.now(timezone.utc).isoformat()
            repo.put("plans", plan)

    return {"ok": True, "plan_updated": plan_updated}


# ============ Dialogue API (Real Data) ============

@app.get("/api/dialogues/{dialogue_id}")
def get_dialogue(dialogue_id: str, request: Request):
    """
    获取对话详情 (带TTS音频)

    从 dialogues 集合读取真实数据，为每句生成TTS音频URL
    """
    dialogue = repo.get("dialogues", dialogue_id)

    if not dialogue:
        raise HTTPException(status_code=404, detail=f"Dialogue '{dialogue_id}' not found")

    # Build TTS audio URLs — prefer pre-generated static files, fallback to dynamic TTS
    base_url = f"https://{request.headers.get('host', request.url.netloc)}"
    for sentence in dialogue.get("sentences", []):
        audio_url = sentence.get("audio_url", "")
        if audio_url.startswith("/static/audio/"):
            continue
        text_encoded = urllib.parse.quote(sentence["text_en"])
        sentence["audio_url"] = f"{base_url}/api/tts/audio?text={text_encoded}&lang=en"

    return dialogue


@app.get("/api/scenarios")
def list_scenarios():
    """获取场景列表"""
    items, total = repo.query("scenarios", None, limit=50, offset=0)
    return {"scenarios": items, "total": total}


@app.get("/api/scenarios/{scenario_id}")
def get_scenario(scenario_id: str):
    """获取场景详情"""
    scenario = repo.get("scenarios", scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return scenario


@app.get("/api/scenarios/{scenario_id}/dialogues")
def list_scenario_dialogues(scenario_id: str, request: Request):
    """获取场景下的所有对话"""
    items, _ = repo.query("dialogues", {"scenario_id": scenario_id}, limit=50, offset=0)

    base_url = f"https://{request.headers.get('host', request.url.netloc)}"
    for dialogue in items:
        for sentence in dialogue.get("sentences", []):
            audio_url = sentence.get("audio_url", "")
            if audio_url.startswith("/static/audio/"):
                continue
            text_encoded = urllib.parse.quote(sentence["text_en"])
            sentence["audio_url"] = f"{base_url}/api/tts/audio?text={text_encoded}&lang=en"

    return {"dialogues": items, "total": len(items)}


# ============ Plan API ============

# Level ordering for comparison
_LEVEL_ORDER = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}


@app.post("/api/plan/generate")
def generate_plan(
    payload: dict,
    user_id: str = Depends(get_current_user_openid),
):
    """
    Generate a learning plan based on assessment results.

    Expects: overall_level, weak_areas, strong_areas, target_date?, daily_minutes?, focus_categories?
    """
    overall_level = payload.get("overall_level", "A2")
    weak_areas = payload.get("weak_areas", [])
    strong_areas = payload.get("strong_areas", [])
    target_date_str = payload.get("target_date")
    daily_minutes = payload.get("daily_minutes", 30)
    focus_categories = payload.get("focus_categories", [])

    from datetime import date as _date, timedelta as _timedelta

    # Calculate available days
    available_days = 30
    target_date = None
    if target_date_str:
        try:
            target_date = _date.fromisoformat(target_date_str)
            available_days = max(7, (target_date - _date.today()).days)
        except ValueError:
            pass

    # 1. Get all scenarios and pick recommended ones
    all_scenarios, _ = repo.query("scenarios", None, limit=50, offset=0)
    user_level_idx = _LEVEL_ORDER.get(overall_level, 1)

    def _score_scenario(s: dict) -> int:
        score = 0
        s_level_idx = _LEVEL_ORDER.get(s.get("level", "A2"), 1)
        # Level fit: same level or one level up
        if s_level_idx == user_level_idx or s_level_idx == user_level_idx + 1:
            score += 20
        # Priority bonus
        score += max(0, 10 - s.get("priority", 5)) * 5
        # Weak area match via tags
        s_tags = set(s.get("tags", []))
        for wa in weak_areas:
            if wa in s_tags:
                score += 30
        # Focus category match
        if focus_categories and s.get("category") in focus_categories:
            score += 25
        return score

    scored = sorted(all_scenarios, key=_score_scenario, reverse=True)
    num_scenarios = min(len(scored), 5 if available_days >= 21 else 3)
    selected = scored[:num_scenarios]

    # 2. Build scenario goals
    scenario_goals = []
    all_dialogue_ids = []
    priority_labels = ["high", "medium", "low"]

    for i, sc in enumerate(selected):
        sid = sc["id"]
        # Get dialogues for this scenario
        dialogues, _ = repo.query("dialogues", {"scenario_id": sid}, limit=20, offset=0)
        d_ids = [d["id"] for d in dialogues]
        all_dialogue_ids.extend(d_ids)

        # Collect key vocabulary from dialogues
        key_vocab = []
        for d in dialogues:
            for sent in d.get("sentences", []):
                key_vocab.extend(sent.get("key_words", []))
        key_vocab = list(dict.fromkeys(key_vocab))[:10]  # dedupe, top 10

        priority = priority_labels[min(i, 2)]

        # Generate reason
        reasons = []
        if priority == "high":
            reasons.append(f"高优先级{sc.get('category', '')}场景")
        if any(wa in set(sc.get("tags", [])) for wa in weak_areas):
            reasons.append(f"针对薄弱环节: {', '.join(weak_areas[:2])}")
        if not reasons:
            reasons.append(f"包含{len(d_ids)}个核心学习目标")

        scenario_goals.append({
            "scenario_id": sid,
            "scenario_name": sc.get("name_zh", sc.get("name_en", sid)),
            "icon": sc.get("icon", "📚"),
            "priority": priority,
            "target_readiness": 0.85,
            "current_readiness": 0.0,
            "readinessPercent": 0,
            "estimated_days": max(1, len(d_ids) * 2),
            "dialogue_ids": d_ids,
            "key_vocabulary": key_vocab,
            "reason": "；".join(reasons),
        })

    # 3. Generate daily tasks
    today = _date.today()
    daily_tasks = []
    for idx, did in enumerate(all_dialogue_ids):
        task_date = today + _timedelta(days=idx)
        # Find dialogue info
        dlg = repo.get("dialogues", did)
        sentence_count = len(dlg.get("sentences", [])) if dlg else 5
        # Find which scenario this belongs to
        scenario_id = dlg.get("scenario_id", "") if dlg else ""
        daily_tasks.append({
            "date": task_date.isoformat(),
            "scenario_id": scenario_id,
            "dialogue_id": did,
            "dialogue_title": dlg.get("title_zh", did) if dlg else did,
            "vocabulary_count": sentence_count,
            "estimated_minutes": max(10, sentence_count * 2),
            "is_completed": False,
        })

    # 4. Build plan object
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    plan = {
        "id": plan_id,
        "user_id": user_id,
        "status": "active",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "target_date": target_date.isoformat() if target_date else None,
        "available_days": available_days,
        "daily_minutes": daily_minutes,
        "overall_level": overall_level,
        "weak_areas": weak_areas,
        "strong_areas": strong_areas,
        "scenario_goals": scenario_goals,
        "daily_tasks": daily_tasks,
        "total_scenarios": len(scenario_goals),
        "completed_scenarios": 0,
        "total_dialogues": len(all_dialogue_ids),
        "completed_dialogues": 0,
        "overall_progress": 0,
    }

    # Deactivate any previous active plan for this user
    old_plans, _ = repo.query("plans", {"user_id": user_id, "status": "active"}, limit=10, offset=0)
    for op in old_plans:
        op["status"] = "completed"
        repo.put("plans", op)

    repo.put("plans", plan)
    return plan


@app.get("/api/plan/current")
def get_current_plan(user_id: str = Depends(get_current_user_openid)):
    """Get the user's current active learning plan."""
    items, total = repo.query("plans", {"user_id": user_id, "status": "active"}, limit=1, offset=0)
    if not items:
        raise HTTPException(status_code=404, detail="No active plan found")

    plan = items[0]
    # Add computed fields
    if plan.get("target_date"):
        from datetime import date as _date
        try:
            td = _date.fromisoformat(plan["target_date"])
            plan["days_remaining"] = max(0, (td - _date.today()).days)
        except ValueError:
            plan["days_remaining"] = None

    # Filter today's tasks
    from datetime import date as _date
    today_str = _date.today().isoformat()
    plan["today_tasks"] = [t for t in plan.get("daily_tasks", []) if t.get("date") == today_str]

    return plan


@app.get("/api/plan/{plan_id}")
def get_plan_detail(plan_id: str, user_id: str = Depends(get_current_user_openid)):
    """Get plan details by ID."""
    plan = repo.get("plans", plan_id)
    if not plan or plan.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@app.put("/api/plan/{plan_id}/progress")
def update_plan_progress(
    plan_id: str,
    payload: dict,
    user_id: str = Depends(get_current_user_openid),
):
    """Update plan progress when a dialogue is completed."""
    plan = repo.get("plans", plan_id)
    if not plan or plan.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")

    completed_dialogue_id = payload.get("dialogue_id")
    if not completed_dialogue_id:
        raise HTTPException(status_code=400, detail="dialogue_id is required")

    # Mark daily task as completed
    for task in plan.get("daily_tasks", []):
        if task.get("dialogue_id") == completed_dialogue_id:
            task["is_completed"] = True
            break

    # Update scenario readiness
    for goal in plan.get("scenario_goals", []):
        if completed_dialogue_id in goal.get("dialogue_ids", []):
            completed_in_scenario = sum(
                1 for t in plan.get("daily_tasks", [])
                if t.get("scenario_id") == goal["scenario_id"] and t.get("is_completed")
            )
            total_in_scenario = len(goal["dialogue_ids"])
            goal["current_readiness"] = round(completed_in_scenario / max(1, total_in_scenario) * 0.85, 2)
            goal["readinessPercent"] = round(goal["current_readiness"] * 100)

    # Recalculate overall progress
    total = plan.get("total_dialogues", 1)
    completed = sum(1 for t in plan.get("daily_tasks", []) if t.get("is_completed"))
    plan["completed_dialogues"] = completed
    plan["overall_progress"] = round(completed / max(1, total) * 100)
    plan["completed_scenarios"] = sum(
        1 for g in plan.get("scenario_goals", []) if g.get("current_readiness", 0) >= 0.85
    )

    # Auto-complete plan
    if plan["overall_progress"] >= 100:
        plan["status"] = "completed"

    plan["updated_at"] = datetime.now(timezone.utc).isoformat()
    repo.put("plans", plan)
    return plan


@app.put("/api/plan/{plan_id}/pause")
def pause_plan(plan_id: str, user_id: str = Depends(get_current_user_openid)):
    """Pause a learning plan."""
    plan = repo.get("plans", plan_id)
    if not plan or plan.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.get("status") != "active":
        raise HTTPException(status_code=400, detail="Only active plans can be paused")

    plan["status"] = "paused"
    plan["paused_at"] = datetime.now(timezone.utc).isoformat()
    plan["updated_at"] = plan["paused_at"]
    repo.put("plans", plan)
    return {"ok": True, "status": "paused"}


@app.put("/api/plan/{plan_id}/resume")
def resume_plan(plan_id: str, user_id: str = Depends(get_current_user_openid)):
    """Resume a paused learning plan."""
    plan = repo.get("plans", plan_id)
    if not plan or plan.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.get("status") != "paused":
        raise HTTPException(status_code=400, detail="Only paused plans can be resumed")

    plan["status"] = "active"
    plan["updated_at"] = datetime.now(timezone.utc).isoformat()
    repo.put("plans", plan)
    return {"ok": True, "status": "active"}
