"""
场景领域模型 - Scenario Domain Models
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ScenarioCategory(str, Enum):
    """场景分类"""
    TRAVEL = "travel"
    BUSINESS = "business"
    ACADEMIC = "academic"
    DAILY_LIFE = "daily_life"
    SOCIAL = "social"


class CEFRLevel(str, Enum):
    """CEFR等级"""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


@dataclass
class SubScenario:
    """子场景"""
    id: str
    order: int
    title_en: str
    title_zh: str
    difficulty: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order": self.order,
            "title_en": self.title_en,
            "title_zh": self.title_zh,
            "difficulty": self.difficulty
        }


@dataclass
class Scenario:
    """场景"""
    id: str
    name_en: str
    name_zh: str
    category: ScenarioCategory
    level: CEFRLevel
    priority: int
    description_en: str
    description_zh: str
    icon: str
    estimated_duration_minutes: int
    dialogue_count: int
    vocabulary_count: int
    tags: List[str]
    scenarios: List[SubScenario]
    learning_objectives: List[str]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name_en": self.name_en,
            "name_zh": self.name_zh,
            "category": self.category.value,
            "level": self.level.value,
            "priority": self.priority,
            "description_en": self.description_en,
            "description_zh": self.description_zh,
            "icon": self.icon,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "dialogue_count": self.dialogue_count,
            "vocabulary_count": self.vocabulary_count,
            "tags": self.tags,
            "scenarios": [s.to_dict() for s in self.scenarios],
            "learning_objectives": self.learning_objectives,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class Sentence:
    """对话句子"""
    order: int
    speaker: str
    text_en: str
    text_zh: str
    audio_url: str
    phonetic: str
    key_words: List[str]
    grammar_points: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "speaker": self.speaker,
            "text_en": self.text_en,
            "text_zh": self.text_zh,
            "audio_url": self.audio_url,
            "phonetic": self.phonetic,
            "key_words": self.key_words,
            "grammar_points": self.grammar_points
        }


@dataclass
class VocabularyItem:
    """词汇项"""
    word: str
    translation: str
    level: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "translation": self.translation,
            "level": self.level
        }


@dataclass
class Dialogue:
    """对话"""
    id: str
    scenario_id: str
    sub_scenario_id: str
    order: int
    title_en: str
    title_zh: str
    level: CEFRLevel
    sentences: List[Sentence]
    vocabulary: List[VocabularyItem]
    cultural_notes: str
    practice_tips: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "sub_scenario_id": self.sub_scenario_id,
            "order": self.order,
            "title_en": self.title_en,
            "title_zh": self.title_zh,
            "level": self.level.value,
            "sentences": [s.to_dict() for s in self.sentences],
            "vocabulary": [v.to_dict() for v in self.vocabulary],
            "cultural_notes": self.cultural_notes,
            "practice_tips": self.practice_tips,
            "created_at": self.created_at.isoformat()
        }

    @property
    def sentence_count(self) -> int:
        """句子数量"""
        return len(self.sentences)

    @property
    def vocabulary_count(self) -> int:
        """词汇数量"""
        return len(self.vocabulary)


@dataclass
class ScenarioProgress:
    """场景学习进度"""
    user_id: str
    scenario_id: str
    sub_scenario_id: str
    dialogue_id: str
    completed_sentences: List[int]  # 已完成的句子order列表
    vocabulary_learned: List[str]   # 已学习的词汇
    completion_percentage: float
    last_studied_at: datetime
    mastery_score: float  # 0-1, 掌握程度评分

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "scenario_id": self.scenario_id,
            "sub_scenario_id": self.sub_scenario_id,
            "dialogue_id": self.dialogue_id,
            "completed_sentences": self.completed_sentences,
            "vocabulary_learned": self.vocabulary_learned,
            "completion_percentage": self.completion_percentage,
            "last_studied_at": self.last_studied_at.isoformat(),
            "mastery_score": self.mastery_score
        }

    @property
    def is_completed(self) -> bool:
        """是否完成"""
        return self.completion_percentage >= 100.0
