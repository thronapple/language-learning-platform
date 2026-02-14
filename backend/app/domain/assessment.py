"""
评估领域模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class QuestionType(str, Enum):
    """题目类型"""
    LISTENING = "listening"
    READING = "reading"
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"


class AssessmentStatus(str, Enum):
    """评估状态"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class AssessmentQuestion:
    """评估题目"""
    id: str
    type: QuestionType
    level: str  # A1, A2, B1, B2, C1, C2
    difficulty: float  # 0-1
    scenario_id: Optional[str]
    skill_tested: str

    content: Dict[str, Any]  # 题目内容
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type,
            "level": self.level,
            "difficulty": self.difficulty,
            "content": self.content
        }


@dataclass
class DimensionResult:
    """维度评估结果"""
    level: str
    accuracy: float
    ability: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "accuracy": round(self.accuracy, 2),
            "ability": round(self.ability, 2)
        }


@dataclass
class AssessmentResult:
    """评估结果"""
    overall_level: str
    ability_score: float
    confidence: float

    dimensions: Dict[str, DimensionResult]
    weak_areas: List[str]
    strong_areas: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_level": self.overall_level,
            "ability_score": round(self.ability_score, 2),
            "confidence": round(self.confidence, 2),
            "dimensions": {
                k: v.to_dict() for k, v in self.dimensions.items()
            },
            "weak_areas": self.weak_areas,
            "strong_areas": self.strong_areas
        }


@dataclass
class Assessment:
    """评估会话"""
    user_id: str
    started_at: datetime
    status: AssessmentStatus
    questions: List[Dict[str, Any]] = field(default_factory=list)

    id: Optional[str] = None
    completed_at: Optional[datetime] = None
    duration_secs: int = 0
    results: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None

    _version: int = 1
    _updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "status": self.status,
            "questions": self.questions,
            "duration_secs": self.duration_secs,
            "_version": self._version
        }

        if self.id:
            data["_id"] = self.id
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        if self.results:
            data["results"] = self.results
        if self.recommendations:
            data["recommendations"] = self.recommendations
        if self._updated_at:
            data["_updated_at"] = self._updated_at.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Assessment":
        """从字典创建"""
        return cls(
            id=data.get("_id"),
            user_id=data["user_id"],
            started_at=datetime.fromisoformat(data["started_at"])
            if isinstance(data["started_at"], str)
            else data["started_at"],
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            duration_secs=data.get("duration_secs", 0),
            status=data["status"],
            questions=data.get("questions", []),
            results=data.get("results"),
            recommendations=data.get("recommendations"),
            _version=data.get("_version", 1),
            _updated_at=datetime.fromisoformat(data["_updated_at"])
            if data.get("_updated_at")
            else None
        )
