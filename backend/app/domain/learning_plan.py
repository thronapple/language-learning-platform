"""
学习计划领域模型 - Learning Plan Domain Models
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from enum import Enum


class PlanStatus(str, Enum):
    """计划状态"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    EXPIRED = "expired"


class ScenarioPriority(str, Enum):
    """场景优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ScenarioGoal:
    """场景学习目标"""
    scenario_id: str
    scenario_name: str
    priority: ScenarioPriority
    target_readiness: float  # 0-1, 目标就绪度
    current_readiness: float  # 0-1, 当前就绪度
    estimated_days: int
    dialogue_ids: List[str]
    key_vocabulary: List[str]
    reason: str  # 推荐原因

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "priority": self.priority.value,
            "target_readiness": self.target_readiness,
            "current_readiness": self.current_readiness,
            "estimated_days": self.estimated_days,
            "dialogue_ids": self.dialogue_ids,
            "key_vocabulary": self.key_vocabulary,
            "reason": self.reason
        }

    @property
    def readiness_gap(self) -> float:
        """就绪度差距"""
        return self.target_readiness - self.current_readiness

    @property
    def readiness_percentage(self) -> float:
        """就绪度百分比"""
        return self.current_readiness * 100


@dataclass
class DailyTask:
    """每日任务"""
    date: date
    scenario_id: str
    dialogue_ids: List[str]
    vocabulary_count: int
    estimated_minutes: int
    is_completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "scenario_id": self.scenario_id,
            "dialogue_ids": self.dialogue_ids,
            "vocabulary_count": self.vocabulary_count,
            "estimated_minutes": self.estimated_minutes,
            "is_completed": self.is_completed
        }


@dataclass
class LearningPlan:
    """学习计划"""
    id: str
    user_id: str
    status: PlanStatus
    created_at: datetime
    updated_at: datetime

    # 用户目标
    target_date: Optional[date]  # 目标日期（如出国日期）
    available_days: int  # 可用天数
    daily_minutes: int  # 每日学习时间（分钟）

    # 评估结果
    overall_level: str  # CEFR等级
    weak_areas: List[str]
    strong_areas: List[str]

    # 场景目标
    scenario_goals: List[ScenarioGoal]

    # 每日任务
    daily_tasks: List[DailyTask]

    # 进度追踪
    total_scenarios: int
    completed_scenarios: int
    total_dialogues: int
    completed_dialogues: int
    overall_progress: float  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "available_days": self.available_days,
            "daily_minutes": self.daily_minutes,
            "overall_level": self.overall_level,
            "weak_areas": self.weak_areas,
            "strong_areas": self.strong_areas,
            "scenario_goals": [g.to_dict() for g in self.scenario_goals],
            "daily_tasks": [t.to_dict() for t in self.daily_tasks],
            "total_scenarios": self.total_scenarios,
            "completed_scenarios": self.completed_scenarios,
            "total_dialogues": self.total_dialogues,
            "completed_dialogues": self.completed_dialogues,
            "overall_progress": self.overall_progress
        }

    @property
    def days_until_target(self) -> Optional[int]:
        """距离目标日期的天数"""
        if not self.target_date:
            return None
        delta = self.target_date - date.today()
        return max(0, delta.days)

    @property
    def is_on_track(self) -> bool:
        """是否按计划进行"""
        if not self.target_date:
            return True

        days_passed = self.available_days - (self.days_until_target or 0)
        if days_passed <= 0:
            return True

        expected_progress = (days_passed / self.available_days) * 100
        return self.overall_progress >= expected_progress * 0.9  # 90%容差


@dataclass
class PlanGenerationRequest:
    """计划生成请求"""
    user_id: str
    assessment_id: str
    target_date: Optional[str] = None  # ISO format date
    daily_minutes: int = 30
    focus_categories: List[str] = field(default_factory=list)  # travel, business, etc.
    custom_goals: List[str] = field(default_factory=list)  # 自定义学习目标
