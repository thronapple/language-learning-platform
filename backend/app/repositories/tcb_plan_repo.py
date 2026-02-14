"""
学习计划仓储 - CloudBase实现
Learning Plan Repository - CloudBase Implementation
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from ..domain.learning_plan import (
    LearningPlan, ScenarioGoal, DailyTask,
    PlanStatus, ScenarioPriority
)
from ..infra.tcb_client import TCBClient


class TCBPlanRepository:
    """学习计划仓储 - CloudBase实现"""

    def __init__(self, tcb_client: TCBClient):
        self.tcb = tcb_client
        self.collection = "learning_plans"

    async def create(self, plan: LearningPlan) -> LearningPlan:
        """创建学习计划"""
        doc = self._to_document(plan)
        await self.tcb.insert(collection=self.collection, data=doc)
        return plan

    async def find_by_id(self, plan_id: str) -> Optional[LearningPlan]:
        """根据ID查询计划"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={"id": plan_id},
            limit=1
        )

        if not docs:
            return None

        return self._to_domain(docs[0])

    async def find_by_user(
        self,
        user_id: str,
        status: Optional[PlanStatus] = None
    ) -> List[LearningPlan]:
        """查询用户的学习计划"""
        query_filter = {"user_id": user_id}
        if status:
            query_filter["status"] = status.value

        docs = await self.tcb.query(
            collection=self.collection,
            filter=query_filter,
            sort=[("created_at", -1)]
        )

        return [self._to_domain(doc) for doc in docs]

    async def find_active_plan(self, user_id: str) -> Optional[LearningPlan]:
        """查询用户的活跃计划"""
        docs = await self.tcb.query(
            collection=self.collection,
            filter={
                "user_id": user_id,
                "status": PlanStatus.ACTIVE.value
            },
            sort=[("created_at", -1)],
            limit=1
        )

        if not docs:
            return None

        return self._to_domain(docs[0])

    async def update(self, plan: LearningPlan) -> LearningPlan:
        """更新学习计划"""
        plan.updated_at = datetime.utcnow()
        doc = self._to_document(plan)

        await self.tcb.update(
            collection=self.collection,
            filter={"id": plan.id},
            data=doc
        )

        return plan

    async def delete(self, plan_id: str) -> bool:
        """删除学习计划"""
        result = await self.tcb.delete(
            collection=self.collection,
            filter={"id": plan_id}
        )

        return result.get("deleted", 0) > 0

    def _to_domain(self, doc: Dict[str, Any]) -> LearningPlan:
        """文档转领域模型"""
        # 转换场景目标
        scenario_goals = [
            ScenarioGoal(
                scenario_id=g["scenario_id"],
                scenario_name=g["scenario_name"],
                priority=ScenarioPriority(g["priority"]),
                target_readiness=g["target_readiness"],
                current_readiness=g["current_readiness"],
                estimated_days=g["estimated_days"],
                dialogue_ids=g["dialogue_ids"],
                key_vocabulary=g["key_vocabulary"],
                reason=g["reason"]
            )
            for g in doc.get("scenario_goals", [])
        ]

        # 转换每日任务
        daily_tasks = [
            DailyTask(
                date=date.fromisoformat(t["date"]),
                scenario_id=t["scenario_id"],
                dialogue_ids=t["dialogue_ids"],
                vocabulary_count=t["vocabulary_count"],
                estimated_minutes=t["estimated_minutes"],
                is_completed=t.get("is_completed", False)
            )
            for t in doc.get("daily_tasks", [])
        ]

        # 处理target_date
        target_date = None
        if doc.get("target_date"):
            target_date = date.fromisoformat(doc["target_date"])

        return LearningPlan(
            id=doc["id"],
            user_id=doc["user_id"],
            status=PlanStatus(doc["status"]),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            target_date=target_date,
            available_days=doc["available_days"],
            daily_minutes=doc["daily_minutes"],
            overall_level=doc["overall_level"],
            weak_areas=doc["weak_areas"],
            strong_areas=doc["strong_areas"],
            scenario_goals=scenario_goals,
            daily_tasks=daily_tasks,
            total_scenarios=doc["total_scenarios"],
            completed_scenarios=doc["completed_scenarios"],
            total_dialogues=doc["total_dialogues"],
            completed_dialogues=doc["completed_dialogues"],
            overall_progress=doc["overall_progress"]
        )

    def _to_document(self, plan: LearningPlan) -> Dict[str, Any]:
        """领域模型转文档"""
        return {
            "id": plan.id,
            "user_id": plan.user_id,
            "status": plan.status.value,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "target_date": plan.target_date.isoformat() if plan.target_date else None,
            "available_days": plan.available_days,
            "daily_minutes": plan.daily_minutes,
            "overall_level": plan.overall_level,
            "weak_areas": plan.weak_areas,
            "strong_areas": plan.strong_areas,
            "scenario_goals": [g.to_dict() for g in plan.scenario_goals],
            "daily_tasks": [t.to_dict() for t in plan.daily_tasks],
            "total_scenarios": plan.total_scenarios,
            "completed_scenarios": plan.completed_scenarios,
            "total_dialogues": plan.total_dialogues,
            "completed_dialogues": plan.completed_dialogues,
            "overall_progress": plan.overall_progress
        }
