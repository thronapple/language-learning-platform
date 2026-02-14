"""
CloudBase (TCB) 评估仓储实现
"""

from typing import Optional, List
from datetime import datetime

from app.domain.assessment import Assessment, AssessmentQuestion
from app.repositories.interfaces import AssessmentRepository, QuestionRepository
from app.infra.tcb_client import TCBClient


class TCBAssessmentRepository(AssessmentRepository):
    """CloudBase评估仓储"""

    def __init__(self, tcb_client: TCBClient):
        self.tcb = tcb_client
        self.collection = "assessments"

    async def create(self, assessment: Assessment) -> str:
        """创建评估"""
        data = assessment.to_dict()
        data["_updated_at"] = datetime.now().isoformat()

        result = await self.tcb.add(
            collection=self.collection,
            document=data
        )

        return result["_id"]

    async def get(self, assessment_id: str) -> Optional[Assessment]:
        """获取评估"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={"_id": assessment_id},
            limit=1
        )

        if not docs:
            return None

        return Assessment.from_dict(docs[0])

    async def update(self, assessment: Assessment) -> bool:
        """更新评估"""
        data = assessment.to_dict()
        data["_updated_at"] = datetime.now().isoformat()
        data["_version"] = assessment._version + 1

        result = await self.tcb.update(
            collection=self.collection,
            doc_id=assessment.id,
            data=data
        )

        return result.get("updated", 0) > 0

    async def find_by_user(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Assessment]:
        """查询用户评估历史"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={"user_id": user_id, "status": "completed"},
            sort=[("completed_at", -1)],
            limit=limit
        )

        return [Assessment.from_dict(doc) for doc in docs]


class TCBQuestionRepository(QuestionRepository):
    """CloudBase题库仓储"""

    def __init__(self, tcb_client: TCBClient):
        self.tcb = tcb_client
        self.collection = "assessment_questions"

    async def get(self, question_id: str) -> Optional[AssessmentQuestion]:
        """获取题目"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={"_id": question_id},
            limit=1
        )

        if not docs:
            return None

        return self._to_domain(docs[0])

    async def find_closest(
        self,
        level: str,
        type: str,
        exclude_ids: List[str]
    ) -> Optional[AssessmentQuestion]:
        """
        自适应选题

        策略:
        1. 优先选择目标等级+题型
        2. 如果没有,选择相近等级
        3. 避开已答题目
        """

        # 构建查询条件
        query_filter = {
            "level": level,
            "type": type,
            "is_active": True
        }

        if exclude_ids:
            query_filter["_id"] = {"$nin": exclude_ids}

        # 查询
        docs = await self.tcb.query(
            collection=self.collection,
            filter=query_filter,
            limit=5
        )

        if not docs:
            # 降级: 忽略等级限制,只按题型
            query_filter = {
                "type": type,
                "is_active": True,
                "_id": {"$nin": exclude_ids} if exclude_ids else {}
            }

            docs = await self.tcb.query(
                collection=self.collection,
                filter=query_filter,
                limit=5
            )

        if not docs:
            return None

        # 随机选择一个(避免总是选第一个)
        import random
        selected = random.choice(docs)

        return self._to_domain(selected)

    async def find_by_level(
        self,
        level: str,
        limit: int = 20
    ) -> List[AssessmentQuestion]:
        """按等级查询题目"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={"level": level, "is_active": True},
            limit=limit
        )

        return [self._to_domain(doc) for doc in docs]

    def _to_domain(self, doc: dict) -> AssessmentQuestion:
        """转换为领域对象"""
        return AssessmentQuestion(
            id=doc["_id"],
            type=doc["type"],
            level=doc["level"],
            difficulty=doc["difficulty"],
            scenario_id=doc.get("scenario_id"),
            skill_tested=doc["skill_tested"],
            content=doc["content"],
            metadata=doc.get("metadata", {}),
            is_active=doc.get("is_active", True),
            created_at=datetime.fromisoformat(doc["created_at"])
            if isinstance(doc.get("created_at"), str)
            else doc.get("created_at")
        )
