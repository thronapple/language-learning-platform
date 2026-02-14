"""
场景路由 - Scenario Routes
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ..domain.scenario import ScenarioCategory, CEFRLevel
from ..services.scenario_service import ScenarioService


router = APIRouter(prefix="/scenarios", tags=["scenarios"])


# 依赖注入
def get_scenario_service() -> ScenarioService:
    """获取场景服务实例"""
    return ScenarioService(data_dir="data")


# Response Models
class ScenarioListResponse(BaseModel):
    """场景列表响应"""
    scenarios: List[dict]
    total: int


class DialogueListResponse(BaseModel):
    """对话列表响应"""
    dialogues: List[dict]
    total: int


class ScenarioDetailResponse(BaseModel):
    """场景详情响应"""
    scenario: dict
    dialogues: List[dict]


class StatisticsResponse(BaseModel):
    """统计信息响应"""
    total_scenarios: int
    total_dialogues: int
    total_sentences: int
    total_vocabulary: int
    by_category: dict
    by_level: dict


@router.get("", response_model=ScenarioListResponse)
async def get_scenarios(
    category: Optional[str] = Query(None, description="场景分类过滤"),
    level: Optional[str] = Query(None, description="CEFR等级过滤"),
    service: ScenarioService = Depends(get_scenario_service)
):
    """
    获取场景列表

    支持按分类和等级过滤
    """
    # 转换枚举
    category_enum = ScenarioCategory(category) if category else None
    level_enum = CEFRLevel(level) if level else None

    scenarios = await service.get_all_scenarios(
        category=category_enum,
        level=level_enum
    )

    return ScenarioListResponse(
        scenarios=[s.to_dict() for s in scenarios],
        total=len(scenarios)
    )


@router.get("/search", response_model=ScenarioListResponse)
async def search_scenarios(
    q: str = Query(..., description="搜索关键词"),
    category: Optional[str] = Query(None, description="场景分类过滤"),
    service: ScenarioService = Depends(get_scenario_service)
):
    """
    搜索场景

    支持按名称、描述、标签搜索
    """
    category_enum = ScenarioCategory(category) if category else None

    scenarios = await service.search_scenarios(
        keyword=q,
        category=category_enum
    )

    return ScenarioListResponse(
        scenarios=[s.to_dict() for s in scenarios],
        total=len(scenarios)
    )


@router.get("/recommended", response_model=ScenarioListResponse)
async def get_recommended_scenarios(
    user_level: str = Query(..., description="用户CEFR等级"),
    weak_areas: str = Query("", description="薄弱领域，逗号分隔"),
    limit: int = Query(3, ge=1, le=10, description="返回数量"),
    service: ScenarioService = Depends(get_scenario_service)
):
    """
    获取推荐场景

    基于用户等级和薄弱领域推荐
    """
    level_enum = CEFRLevel(user_level)
    weak_areas_list = [area.strip() for area in weak_areas.split(",") if area.strip()]

    scenarios = await service.get_recommended_scenarios(
        user_level=level_enum,
        weak_areas=weak_areas_list,
        limit=limit
    )

    return ScenarioListResponse(
        scenarios=[s.to_dict() for s in scenarios],
        total=len(scenarios)
    )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    service: ScenarioService = Depends(get_scenario_service)
):
    """
    获取场景统计信息

    包括场景数量、对话数量、句子数量等
    """
    stats = service.get_scenario_statistics()
    return StatisticsResponse(**stats)


@router.get("/{scenario_id}", response_model=ScenarioDetailResponse)
async def get_scenario_detail(
    scenario_id: str,
    service: ScenarioService = Depends(get_scenario_service)
):
    """
    获取场景详情

    包括场景信息和所有对话
    """
    scenario = await service.get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    dialogues = await service.get_dialogues_by_scenario(scenario_id)

    return ScenarioDetailResponse(
        scenario=scenario.to_dict(),
        dialogues=[d.to_dict() for d in dialogues]
    )


@router.get("/{scenario_id}/dialogues", response_model=DialogueListResponse)
async def get_scenario_dialogues(
    scenario_id: str,
    sub_scenario_id: Optional[str] = Query(None, description="子场景ID过滤"),
    service: ScenarioService = Depends(get_scenario_service)
):
    """
    获取场景的对话列表

    可选按子场景过滤
    """
    # 验证场景存在
    scenario = await service.get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    dialogues = await service.get_dialogues_by_scenario(
        scenario_id=scenario_id,
        sub_scenario_id=sub_scenario_id
    )

    return DialogueListResponse(
        dialogues=[d.to_dict() for d in dialogues],
        total=len(dialogues)
    )


@router.get("/{scenario_id}/dialogues/{dialogue_id}")
async def get_dialogue_detail(
    scenario_id: str,
    dialogue_id: str,
    service: ScenarioService = Depends(get_scenario_service)
):
    """
    获取对话详情

    包括完整的句子、词汇、文化注释等
    """
    dialogue = await service.get_dialogue_by_id(dialogue_id)
    if not dialogue:
        raise HTTPException(status_code=404, detail="Dialogue not found")

    # 验证对话属于该场景
    if dialogue.scenario_id != scenario_id:
        raise HTTPException(status_code=400, detail="Dialogue does not belong to this scenario")

    return dialogue.to_dict()
