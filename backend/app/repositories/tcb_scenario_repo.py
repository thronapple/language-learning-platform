"""
场景仓储 - CloudBase实现
Scenario Repository - CloudBase Implementation
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.scenario import (
    Scenario, Dialogue, ScenarioProgress,
    SubScenario, Sentence, VocabularyItem,
    ScenarioCategory, CEFRLevel
)
from ..infra.tcb_client import TCBClient


class TCBScenarioRepository:
    """场景仓储 - CloudBase实现"""

    def __init__(self, tcb_client: TCBClient):
        self.tcb = tcb_client
        self.collection = "scenarios"

    async def find_all(
        self,
        category: Optional[ScenarioCategory] = None,
        level: Optional[CEFRLevel] = None
    ) -> List[Scenario]:
        """查询所有场景"""
        query_filter = {}
        if category:
            query_filter["category"] = category.value
        if level:
            query_filter["level"] = level.value

        docs = await self.tcb.query(
            collection=self.collection,
            filter=query_filter,
            sort=[("priority", 1)]
        )

        return [self._to_domain(doc) for doc in docs]

    async def find_by_id(self, scenario_id: str) -> Optional[Scenario]:
        """根据ID查询场景"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={"id": scenario_id},
            limit=1
        )

        if not docs:
            return None

        return self._to_domain(docs[0])

    async def create(self, scenario: Scenario) -> Scenario:
        """创建场景"""
        doc = self._to_document(scenario)
        await self.tcb.insert(collection=self.collection, data=doc)
        return scenario

    async def update(self, scenario: Scenario) -> Scenario:
        """更新场景"""
        doc = self._to_document(scenario)
        doc["updated_at"] = datetime.utcnow()

        await self.tcb.update(
            collection=self.collection,
            filter={"id": scenario.id},
            data=doc
        )

        return scenario

    def _to_domain(self, doc: Dict[str, Any]) -> Scenario:
        """文档转领域模型"""
        sub_scenarios = [
            SubScenario(
                id=s["id"],
                order=s["order"],
                title_en=s["title_en"],
                title_zh=s["title_zh"],
                difficulty=s["difficulty"]
            )
            for s in doc.get("scenarios", [])
        ]

        return Scenario(
            id=doc["id"],
            name_en=doc["name_en"],
            name_zh=doc["name_zh"],
            category=ScenarioCategory(doc["category"]),
            level=CEFRLevel(doc["level"]),
            priority=doc["priority"],
            description_en=doc["description_en"],
            description_zh=doc["description_zh"],
            icon=doc["icon"],
            estimated_duration_minutes=doc["estimated_duration_minutes"],
            dialogue_count=doc["dialogue_count"],
            vocabulary_count=doc["vocabulary_count"],
            tags=doc["tags"],
            scenarios=sub_scenarios,
            learning_objectives=doc["learning_objectives"],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        )

    def _to_document(self, scenario: Scenario) -> Dict[str, Any]:
        """领域模型转文档"""
        return {
            "id": scenario.id,
            "name_en": scenario.name_en,
            "name_zh": scenario.name_zh,
            "category": scenario.category.value,
            "level": scenario.level.value,
            "priority": scenario.priority,
            "description_en": scenario.description_en,
            "description_zh": scenario.description_zh,
            "icon": scenario.icon,
            "estimated_duration_minutes": scenario.estimated_duration_minutes,
            "dialogue_count": scenario.dialogue_count,
            "vocabulary_count": scenario.vocabulary_count,
            "tags": scenario.tags,
            "scenarios": [s.to_dict() for s in scenario.scenarios],
            "learning_objectives": scenario.learning_objectives,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at
        }


class TCBDialogueRepository:
    """对话仓储 - CloudBase实现"""

    def __init__(self, tcb_client: TCBClient):
        self.tcb = tcb_client
        self.collection = "scenario_dialogues"

    async def find_by_scenario(
        self,
        scenario_id: str,
        sub_scenario_id: Optional[str] = None
    ) -> List[Dialogue]:
        """根据场景查询对话"""
        query_filter = {"scenario_id": scenario_id}
        if sub_scenario_id:
            query_filter["sub_scenario_id"] = sub_scenario_id

        docs = await self.tcb.query(
            collection=self.collection,
            filter=query_filter,
            sort=[("order", 1)]
        )

        return [self._to_domain(doc) for doc in docs]

    async def find_by_id(self, dialogue_id: str) -> Optional[Dialogue]:
        """根据ID查询对话"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={"id": dialogue_id},
            limit=1
        )

        if not docs:
            return None

        return self._to_domain(docs[0])

    async def create(self, dialogue: Dialogue) -> Dialogue:
        """创建对话"""
        doc = self._to_document(dialogue)
        await self.tcb.insert(collection=self.collection, data=doc)
        return dialogue

    def _to_domain(self, doc: Dict[str, Any]) -> Dialogue:
        """文档转领域模型"""
        sentences = [
            Sentence(
                order=s["order"],
                speaker=s["speaker"],
                text_en=s["text_en"],
                text_zh=s["text_zh"],
                audio_url=s["audio_url"],
                phonetic=s["phonetic"],
                key_words=s["key_words"],
                grammar_points=s["grammar_points"]
            )
            for s in doc.get("sentences", [])
        ]

        vocabulary = [
            VocabularyItem(
                word=v["word"],
                translation=v["translation"],
                level=v["level"]
            )
            for v in doc.get("vocabulary", [])
        ]

        return Dialogue(
            id=doc["id"],
            scenario_id=doc["scenario_id"],
            sub_scenario_id=doc["sub_scenario_id"],
            order=doc["order"],
            title_en=doc["title_en"],
            title_zh=doc["title_zh"],
            level=CEFRLevel(doc["level"]),
            sentences=sentences,
            vocabulary=vocabulary,
            cultural_notes=doc["cultural_notes"],
            practice_tips=doc["practice_tips"],
            created_at=doc["created_at"]
        )

    def _to_document(self, dialogue: Dialogue) -> Dict[str, Any]:
        """领域模型转文档"""
        return {
            "id": dialogue.id,
            "scenario_id": dialogue.scenario_id,
            "sub_scenario_id": dialogue.sub_scenario_id,
            "order": dialogue.order,
            "title_en": dialogue.title_en,
            "title_zh": dialogue.title_zh,
            "level": dialogue.level.value,
            "sentences": [s.to_dict() for s in dialogue.sentences],
            "vocabulary": [v.to_dict() for v in dialogue.vocabulary],
            "cultural_notes": dialogue.cultural_notes,
            "practice_tips": dialogue.practice_tips,
            "created_at": dialogue.created_at
        }


class TCBScenarioProgressRepository:
    """场景进度仓储 - CloudBase实现"""

    def __init__(self, tcb_client: TCBClient):
        self.tcb = tcb_client
        self.collection = "scenario_progress"

    async def find_by_user(self, user_id: str) -> List[ScenarioProgress]:
        """查询用户的所有场景进度"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={"user_id": user_id},
            sort=[("last_studied_at", -1)]
        )

        return [self._to_domain(doc) for doc in docs]

    async def find_by_user_and_dialogue(
        self,
        user_id: str,
        dialogue_id: str
    ) -> Optional[ScenarioProgress]:
        """查询用户特定对话的进度"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={
                "user_id": user_id,
                "dialogue_id": dialogue_id
            },
            limit=1
        )

        if not docs:
            return None

        return self._to_domain(docs[0])

    async def upsert(self, progress: ScenarioProgress) -> ScenarioProgress:
        """创建或更新进度"""
        doc = self._to_document(progress)

        # 尝试更新，如果不存在则插入
        result = await self.tcb.update(
            collection=self.collection,
            filter={
                "user_id": progress.user_id,
                "dialogue_id": progress.dialogue_id
            },
            data=doc
        )

        if result.get("matched", 0) == 0:
            await self.tcb.insert(collection=self.collection, data=doc)

        return progress

    def _to_domain(self, doc: Dict[str, Any]) -> ScenarioProgress:
        """文档转领域模型"""
        return ScenarioProgress(
            user_id=doc["user_id"],
            scenario_id=doc["scenario_id"],
            sub_scenario_id=doc["sub_scenario_id"],
            dialogue_id=doc["dialogue_id"],
            completed_sentences=doc["completed_sentences"],
            vocabulary_learned=doc["vocabulary_learned"],
            completion_percentage=doc["completion_percentage"],
            last_studied_at=doc["last_studied_at"],
            mastery_score=doc["mastery_score"]
        )

    def _to_document(self, progress: ScenarioProgress) -> Dict[str, Any]:
        """领域模型转文档"""
        return {
            "user_id": progress.user_id,
            "scenario_id": progress.scenario_id,
            "sub_scenario_id": progress.sub_scenario_id,
            "dialogue_id": progress.dialogue_id,
            "completed_sentences": progress.completed_sentences,
            "vocabulary_learned": progress.vocabulary_learned,
            "completion_percentage": progress.completion_percentage,
            "last_studied_at": progress.last_studied_at,
            "mastery_score": progress.mastery_score
        }
