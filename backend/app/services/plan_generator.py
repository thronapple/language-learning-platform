"""
学习计划生成服务 - Learning Plan Generator
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid

from ..domain.learning_plan import (
    LearningPlan, ScenarioGoal, DailyTask,
    PlanStatus, ScenarioPriority, PlanGenerationRequest
)
from ..domain.scenario import Scenario, Dialogue, CEFRLevel, ScenarioCategory
from ..services.scenario_service import ScenarioService
from ..services.assessment_service import AssessmentService


class PlanGenerator:
    """学习计划生成器"""

    def __init__(
        self,
        scenario_service: ScenarioService,
        assessment_service: AssessmentService
    ):
        self.scenario_service = scenario_service
        self.assessment_service = assessment_service

    async def generate_plan(
        self,
        request: PlanGenerationRequest
    ) -> LearningPlan:
        """
        生成学习计划

        Args:
            request: 计划生成请求

        Returns:
            生成的学习计划
        """
        # 1. 获取评估结果
        assessment = await self.assessment_service.get_assessment_result(
            request.assessment_id
        )
        if not assessment:
            raise ValueError(f"Assessment {request.assessment_id} not found")

        # 2. 计算可用天数
        target_date = None
        available_days = 30  # 默认30天
        if request.target_date:
            target_date = date.fromisoformat(request.target_date)
            delta = target_date - date.today()
            available_days = max(7, delta.days)  # 最少7天

        # 3. 推荐场景
        recommended_scenarios = await self._recommend_scenarios(
            user_level=assessment.overall_level,
            weak_areas=assessment.weak_areas,
            focus_categories=request.focus_categories,
            available_days=available_days
        )

        # 4. 生成场景目标
        scenario_goals = await self._generate_scenario_goals(
            scenarios=recommended_scenarios,
            user_level=assessment.overall_level,
            weak_areas=assessment.weak_areas,
            available_days=available_days,
            daily_minutes=request.daily_minutes
        )

        # 5. 生成每日任务
        daily_tasks = await self._generate_daily_tasks(
            scenario_goals=scenario_goals,
            available_days=available_days,
            daily_minutes=request.daily_minutes
        )

        # 6. 创建学习计划
        plan_id = str(uuid.uuid4())
        now = datetime.utcnow()

        total_dialogues = sum(len(g.dialogue_ids) for g in scenario_goals)

        plan = LearningPlan(
            id=plan_id,
            user_id=request.user_id,
            status=PlanStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            target_date=target_date,
            available_days=available_days,
            daily_minutes=request.daily_minutes,
            overall_level=assessment.overall_level,
            weak_areas=assessment.weak_areas,
            strong_areas=assessment.strong_areas,
            scenario_goals=scenario_goals,
            daily_tasks=daily_tasks,
            total_scenarios=len(scenario_goals),
            completed_scenarios=0,
            total_dialogues=total_dialogues,
            completed_dialogues=0,
            overall_progress=0.0
        )

        return plan

    async def _recommend_scenarios(
        self,
        user_level: str,
        weak_areas: List[str],
        focus_categories: List[str],
        available_days: int
    ) -> List[Scenario]:
        """推荐场景"""
        # 获取所有场景
        all_scenarios = await self.scenario_service.get_all_scenarios()

        # 过滤分类
        if focus_categories:
            categories = [ScenarioCategory(cat) for cat in focus_categories]
            filtered_scenarios = [
                s for s in all_scenarios
                if s.category in categories
            ]
        else:
            filtered_scenarios = all_scenarios

        # 等级匹配
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        current_index = level_order.index(user_level)
        target_levels = [level_order[current_index]]
        if current_index < len(level_order) - 1:
            target_levels.append(level_order[current_index + 1])

        matched_scenarios = [
            s for s in filtered_scenarios
            if s.level.value in target_levels
        ]

        # 计算推荐分数
        scored_scenarios = []
        for scenario in matched_scenarios:
            score = self._calculate_scenario_score(
                scenario=scenario,
                weak_areas=weak_areas,
                user_level=user_level
            )
            scored_scenarios.append((scenario, score))

        # 排序
        scored_scenarios.sort(key=lambda x: x[1], reverse=True)

        # 根据可用天数确定场景数量
        max_scenarios = min(5, max(3, available_days // 7))
        return [s[0] for s in scored_scenarios[:max_scenarios]]

    def _calculate_scenario_score(
        self,
        scenario: Scenario,
        weak_areas: List[str],
        user_level: str
    ) -> float:
        """计算场景推荐分数"""
        score = 0.0

        # 基础优先级分数 (0-50)
        score += (10 - scenario.priority) * 5

        # 薄弱领域匹配 (0-30)
        for weak_area in weak_areas:
            if weak_area.lower() in [tag.lower() for tag in scenario.tags]:
                score += 15

        # 等级适配性 (0-20)
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        user_index = level_order.index(user_level)
        scenario_index = level_order.index(scenario.level.value)
        if scenario_index == user_index:
            score += 20
        elif scenario_index == user_index + 1:
            score += 15
        elif scenario_index == user_index - 1:
            score += 10

        return score

    async def _generate_scenario_goals(
        self,
        scenarios: List[Scenario],
        user_level: str,
        weak_areas: List[str],
        available_days: int,
        daily_minutes: int
    ) -> List[ScenarioGoal]:
        """生成场景目标"""
        goals = []

        # 计算每个场景的预估天数
        total_estimated_minutes = sum(
            s.estimated_duration_minutes for s in scenarios
        )
        daily_capacity_minutes = daily_minutes * 0.8  # 80%有效学习时间

        for i, scenario in enumerate(scenarios):
            # 确定优先级
            if i == 0:
                priority = ScenarioPriority.HIGH
            elif i < len(scenarios) // 2:
                priority = ScenarioPriority.MEDIUM
            else:
                priority = ScenarioPriority.LOW

            # 计算预估天数
            scenario_minutes = scenario.estimated_duration_minutes
            estimated_days = max(
                2,
                int(scenario_minutes / daily_capacity_minutes) + 1
            )

            # 获取对话列表
            dialogues = await self.scenario_service.get_dialogues_by_scenario(
                scenario_id=scenario.id
            )
            dialogue_ids = [d.id for d in dialogues]

            # 提取关键词汇
            key_vocabulary = self._extract_key_vocabulary(dialogues, limit=10)

            # 生成推荐原因
            reason = self._generate_recommendation_reason(
                scenario=scenario,
                weak_areas=weak_areas,
                priority=priority
            )

            goal = ScenarioGoal(
                scenario_id=scenario.id,
                scenario_name=scenario.name_zh,
                priority=priority,
                target_readiness=0.85,  # 目标85%就绪度
                current_readiness=0.0,
                estimated_days=estimated_days,
                dialogue_ids=dialogue_ids,
                key_vocabulary=key_vocabulary,
                reason=reason
            )
            goals.append(goal)

        return goals

    def _extract_key_vocabulary(
        self,
        dialogues: List[Dialogue],
        limit: int = 10
    ) -> List[str]:
        """提取关键词汇"""
        # 收集所有词汇
        all_vocab = []
        for dialogue in dialogues:
            all_vocab.extend([v.word for v in dialogue.vocabulary])

        # 去重并取前N个
        unique_vocab = list(dict.fromkeys(all_vocab))
        return unique_vocab[:limit]

    def _generate_recommendation_reason(
        self,
        scenario: Scenario,
        weak_areas: List[str],
        priority: ScenarioPriority
    ) -> str:
        """生成推荐原因"""
        reasons = []

        if priority == ScenarioPriority.HIGH:
            reasons.append(f"高优先级{scenario.category.value}场景")

        # 薄弱领域匹配
        matched_weak_areas = [
            area for area in weak_areas
            if area.lower() in [tag.lower() for tag in scenario.tags]
        ]
        if matched_weak_areas:
            reasons.append(f"针对您的薄弱环节: {', '.join(matched_weak_areas)}")

        # 学习目标
        if scenario.learning_objectives:
            reasons.append(f"包含{len(scenario.learning_objectives)}个核心学习目标")

        return "；".join(reasons) if reasons else "推荐的学习场景"

    async def _generate_daily_tasks(
        self,
        scenario_goals: List[ScenarioGoal],
        available_days: int,
        daily_minutes: int
    ) -> List[DailyTask]:
        """生成每日任务"""
        daily_tasks = []
        current_date = date.today()

        # 按优先级排序场景
        sorted_goals = sorted(
            scenario_goals,
            key=lambda g: (g.priority.value, g.estimated_days)
        )

        # 分配任务到每一天
        day_index = 0
        for goal in sorted_goals:
            dialogues = await self.scenario_service.get_dialogues_by_scenario(
                scenario_id=goal.scenario_id
            )

            # 计算每天可以学习的对话数
            dialogues_per_day = max(1, len(dialogues) // goal.estimated_days)

            for i in range(0, len(dialogues), dialogues_per_day):
                if day_index >= available_days:
                    break

                batch_dialogues = dialogues[i:i + dialogues_per_day]
                batch_dialogue_ids = [d.id for d in batch_dialogues]

                # 计算词汇数量
                vocab_count = sum(d.vocabulary_count for d in batch_dialogues)

                # 估算时间
                estimated_minutes = sum(
                    d.sentence_count * 2  # 每句2分钟
                    for d in batch_dialogues
                )
                estimated_minutes = min(estimated_minutes, daily_minutes)

                task = DailyTask(
                    date=current_date + timedelta(days=day_index),
                    scenario_id=goal.scenario_id,
                    dialogue_ids=batch_dialogue_ids,
                    vocabulary_count=vocab_count,
                    estimated_minutes=estimated_minutes,
                    is_completed=False
                )
                daily_tasks.append(task)
                day_index += 1

        return daily_tasks[:available_days]

    async def update_plan_progress(
        self,
        plan: LearningPlan,
        completed_dialogue_id: str
    ) -> LearningPlan:
        """
        更新计划进度

        Args:
            plan: 学习计划
            completed_dialogue_id: 完成的对话ID

        Returns:
            更新后的计划
        """
        # 更新场景目标进度
        for goal in plan.scenario_goals:
            if completed_dialogue_id in goal.dialogue_ids:
                completed_count = sum(
                    1 for task in plan.daily_tasks
                    if task.scenario_id == goal.scenario_id
                    and completed_dialogue_id in task.dialogue_ids
                    and task.is_completed
                )
                total_count = len(goal.dialogue_ids)
                goal.current_readiness = min(
                    1.0,
                    completed_count / total_count
                )

        # 更新每日任务状态
        for task in plan.daily_tasks:
            if completed_dialogue_id in task.dialogue_ids:
                task.is_completed = True

        # 更新整体进度
        plan.completed_dialogues = sum(
            1 for task in plan.daily_tasks
            if task.is_completed
        )

        plan.completed_scenarios = sum(
            1 for goal in plan.scenario_goals
            if goal.current_readiness >= goal.target_readiness
        )

        if plan.total_dialogues > 0:
            plan.overall_progress = (
                plan.completed_dialogues / plan.total_dialogues
            ) * 100

        # 更新时间戳
        plan.updated_at = datetime.utcnow()

        # 检查是否完成
        if plan.overall_progress >= 100.0:
            plan.status = PlanStatus.COMPLETED

        return plan
