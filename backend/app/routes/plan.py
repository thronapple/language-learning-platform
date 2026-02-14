"""
学习计划路由 - Learning Plan Routes
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..domain.learning_plan import PlanGenerationRequest
from ..services.plan_generator import PlanGenerator
from ..services.scenario_service import ScenarioService
from ..services.assessment_service import AssessmentService


router = APIRouter(prefix="/plans", tags=["plans"])


# Request Models
class GeneratePlanRequest(BaseModel):
    """生成计划请求"""
    assessment_id: str
    target_date: Optional[str] = None
    daily_minutes: int = 30
    focus_categories: list[str] = []
    custom_goals: list[str] = []


class UpdateProgressRequest(BaseModel):
    """更新进度请求"""
    dialogue_id: str
    mastery_score: float = 0.8


# Dependencies
def get_plan_generator() -> PlanGenerator:
    """获取计划生成器"""
    scenario_service = ScenarioService(data_dir="data")
    assessment_service = AssessmentService(
        question_repo=None,  # 从实际依赖注入获取
        assessment_repo=None
    )
    return PlanGenerator(
        scenario_service=scenario_service,
        assessment_service=assessment_service
    )


@router.post("/generate")
async def generate_plan(
    request: GeneratePlanRequest,
    user_id: str,  # 从认证中间件获取
    generator: PlanGenerator = Depends(get_plan_generator)
):
    """
    生成学习计划

    基于评估结果和用户目标生成个性化学习计划
    """
    try:
        plan_request = PlanGenerationRequest(
            user_id=user_id,
            assessment_id=request.assessment_id,
            target_date=request.target_date,
            daily_minutes=request.daily_minutes,
            focus_categories=request.focus_categories,
            custom_goals=request.custom_goals
        )

        plan = await generator.generate_plan(plan_request)

        return {
            "success": True,
            "plan": plan.to_dict()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate plan")


@router.get("/current")
async def get_current_plan(
    user_id: str  # 从认证中间件获取
):
    """
    获取当前学习计划

    返回用户当前激活的学习计划
    """
    # TODO: 从数据库获取当前计划
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{plan_id}")
async def get_plan_detail(
    plan_id: str,
    user_id: str  # 从认证中间件获取
):
    """
    获取计划详情

    包括场景目标、每日任务、进度等完整信息
    """
    # TODO: 从数据库获取计划
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{plan_id}/progress")
async def update_plan_progress(
    plan_id: str,
    request: UpdateProgressRequest,
    user_id: str,  # 从认证中间件获取
    generator: PlanGenerator = Depends(get_plan_generator)
):
    """
    更新学习进度

    记录完成的对话，更新场景就绪度和整体进度
    """
    try:
        # TODO: 从数据库获取计划
        # plan = await plan_repo.find_by_id(plan_id)
        # if not plan or plan.user_id != user_id:
        #     raise HTTPException(status_code=404, detail="Plan not found")

        # updated_plan = await generator.update_plan_progress(
        #     plan=plan,
        #     completed_dialogue_id=request.dialogue_id
        # )

        # await plan_repo.update(updated_plan)

        # return {
        #     "success": True,
        #     "plan": updated_plan.to_dict()
        # }

        raise HTTPException(status_code=501, detail="Not implemented yet")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{plan_id}/today")
async def get_today_tasks(
    plan_id: str,
    user_id: str  # 从认证中间件获取
):
    """
    获取今日任务

    返回今天需要完成的学习任务
    """
    # TODO: 从数据库获取计划并筛选今日任务
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{plan_id}/pause")
async def pause_plan(
    plan_id: str,
    user_id: str  # 从认证中间件获取
):
    """
    暂停计划

    暂停当前学习计划
    """
    # TODO: 更新计划状态为PAUSED
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{plan_id}/resume")
async def resume_plan(
    plan_id: str,
    user_id: str,  # 从认证中间件获取
    extend_days: int = 0
):
    """
    恢复计划

    恢复暂停的学习计划，可选延长天数
    """
    # TODO: 更新计划状态为ACTIVE，调整任务日期
    raise HTTPException(status_code=501, detail="Not implemented yet")
