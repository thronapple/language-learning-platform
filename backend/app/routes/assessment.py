"""
评估API路由
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.domain.assessment import Assessment, AssessmentResult
from app.services.assessment_service import AssessmentService
from app.dependencies import (
    get_current_user,
    get_assessment_service
)
from app.domain.user import User


router = APIRouter(prefix="/assessment", tags=["assessment"])


# ============ Request/Response Models ============

class StartAssessmentResponse(BaseModel):
    """启动评估响应"""
    assessment_id: str
    first_question: Dict[str, Any]


class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    assessment_id: str
    question_id: str
    answer_index: int = Field(..., ge=0, le=3)
    time_spent: int = Field(..., ge=0, description="答题时间(秒)")


class SubmitAnswerResponse(BaseModel):
    """提交答案响应"""
    is_correct: bool
    explanation: Optional[str]
    next_question: Optional[Dict[str, Any]]


class CompleteAssessmentRequest(BaseModel):
    """完成评估请求"""
    assessment_id: str


class CompleteAssessmentResponse(BaseModel):
    """完成评估响应"""
    overall_level: str
    ability_score: float
    confidence: float
    dimensions: Dict[str, Dict[str, Any]]
    weak_areas: List[str]
    strong_areas: List[str]
    recommendations: Dict[str, Any]


# ============ API Endpoints ============

@router.post("/start", response_model=StartAssessmentResponse)
async def start_assessment(
    user: User = Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service)
):
    """
    启动评估会话

    返回评估ID和第一题
    """
    try:
        # 创建评估
        assessment = await service.start_assessment(user.openid)

        # 获取第一题
        first_question = await service.get_next_question(assessment.id)

        if not first_question:
            raise HTTPException(
                status_code=500,
                detail="Failed to get first question"
            )

        return {
            "assessment_id": assessment.id,
            "first_question": first_question.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    payload: SubmitAnswerRequest,
    user: User = Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service)
):
    """
    提交答案并获取下一题

    - 验证答案正确性
    - 返回解释
    - 自适应选择下一题
    """
    try:
        result = await service.submit_answer(
            assessment_id=payload.assessment_id,
            question_id=payload.question_id,
            answer_index=payload.answer_index,
            time_spent=payload.time_spent
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete", response_model=CompleteAssessmentResponse)
async def complete_assessment(
    payload: CompleteAssessmentRequest,
    user: User = Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service)
):
    """
    完成评估并计算结果

    - 计算整体能力值和等级
    - 分析各维度表现
    - 生成学习建议
    """
    try:
        # 完成评估
        result = await service.complete_assessment(payload.assessment_id)

        # 获取评估记录(含推荐)
        assessment = await service.assessment_repo.get(payload.assessment_id)

        return {
            "overall_level": result.overall_level,
            "ability_score": result.ability_score,
            "confidence": result.confidence,
            "dimensions": {
                k: v.to_dict() for k, v in result.dimensions.items()
            },
            "weak_areas": result.weak_areas,
            "strong_areas": result.strong_areas,
            "recommendations": assessment.recommendations or {}
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_assessment_history(
    user: User = Depends(get_current_user),
    service: AssessmentService = Depends(get_assessment_service)
):
    """
    获取用户评估历史

    返回最近5次评估结果
    """
    try:
        assessments = await service.assessment_repo.find_by_user(
            user_id=user.openid,
            limit=5
        )

        return {
            "assessments": [
                {
                    "id": a.id,
                    "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                    "overall_level": a.results.get("overall_level") if a.results else None,
                    "duration_secs": a.duration_secs
                }
                for a in assessments
                if a.status == "completed"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
