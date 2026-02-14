"""
评估服务 - 自适应测试

功能:
- 启动评估会话
- 自适应选择下一题
- 计算能力值和等级
- 生成学习建议
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import random
import math

from app.domain.assessment import (
    Assessment,
    AssessmentQuestion,
    AssessmentResult,
    DimensionResult
)
from app.repositories.interfaces import (
    AssessmentRepository,
    QuestionRepository
)


class AdaptiveQuestionSelector:
    """简化自适应选题算法 (MVP版本)"""

    # CEFR等级映射到能力值
    LEVEL_MAP = {
        "A1": -2.0,
        "A2": -1.0,
        "B1": 0.0,
        "B2": 1.0,
        "C1": 2.0,
        "C2": 3.0
    }

    def __init__(self, question_repo: QuestionRepository):
        self.question_repo = question_repo

    async def select_next(
        self,
        answered_questions: List[Dict[str, Any]],
        total_questions: int = 10
    ) -> Optional[AssessmentQuestion]:
        """选择下一题"""

        if len(answered_questions) >= total_questions:
            return None  # 已完成

        # 计算当前能力估计
        ability = self._estimate_ability(answered_questions)

        # 映射到CEFR等级
        target_level = self._ability_to_level(ability)

        # 选择题型(保证多样性)
        answered_types = [q["type"] for q in answered_questions]
        next_type = self._select_diverse_type(answered_types)

        # 从题库选择
        question = await self.question_repo.find_closest(
            level=target_level,
            type=next_type,
            exclude_ids=[q["question_id"] for q in answered_questions]
        )

        return question

    def _estimate_ability(self, questions: List[Dict[str, Any]]) -> float:
        """估计当前能力值 (简化IRT)"""

        if not questions:
            return 0.0  # B1初始值

        correct_count = sum(1 for q in questions if q["is_correct"])
        total_count = len(questions)
        accuracy = correct_count / total_count

        # 简化映射: 正确率 → 能力值
        # 50%正确率 → 0.0 (B1)
        # 每提高10%正确率 → +0.4能力值
        ability = (accuracy - 0.5) * 4
        return max(-2.5, min(ability, 3.0))

    def _ability_to_level(self, ability: float) -> str:
        """能力值映射到CEFR等级"""

        for level, threshold in sorted(
            self.LEVEL_MAP.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if ability >= threshold:
                return level
        return "A1"

    def _select_diverse_type(self, answered_types: List[str]) -> str:
        """选择题型以保证多样性"""

        type_counts = {
            "vocabulary": answered_types.count("vocabulary"),
            "listening": answered_types.count("listening"),
            "reading": answered_types.count("reading"),
            "grammar": answered_types.count("grammar")
        }

        # 返回出现次数最少的题型
        min_type = min(type_counts, key=type_counts.get)
        return min_type


class AssessmentEvaluator:
    """评估结果计算"""

    def __init__(self):
        self.selector = AdaptiveQuestionSelector(None)

    def calculate_result(self, assessment: Assessment) -> AssessmentResult:
        """计算评估结果"""

        # 整体能力值
        overall_ability = self._calculate_overall_ability(assessment.questions)
        overall_level = self.selector._ability_to_level(overall_ability)

        # 各维度能力
        dimensions = self._calculate_dimensions(assessment.questions)

        # 识别强弱项
        weak_areas = [
            dim for dim, result in dimensions.items()
            if result.ability < overall_ability - 0.5
        ]
        strong_areas = [
            dim for dim, result in dimensions.items()
            if result.ability > overall_ability + 0.5
        ]

        # 置信度 (基于题目数量)
        confidence = min(0.5 + len(assessment.questions) * 0.05, 0.95)

        return AssessmentResult(
            overall_level=overall_level,
            ability_score=overall_ability,
            confidence=confidence,
            dimensions=dimensions,
            weak_areas=weak_areas,
            strong_areas=strong_areas
        )

    def _calculate_overall_ability(
        self,
        questions: List[Dict[str, Any]]
    ) -> float:
        """计算整体能力值"""

        if not questions:
            return 0.0

        correct_count = sum(1 for q in questions if q["is_correct"])
        total_count = len(questions)
        accuracy = correct_count / total_count

        # 考虑题目难度的加权
        weighted_sum = 0.0
        weight_total = 0.0

        for q in questions:
            difficulty = q.get("difficulty", 0.5)
            weight = 1.0  # 可根据难度调整权重

            if q["is_correct"]:
                weighted_sum += difficulty * weight
            else:
                weighted_sum -= (1 - difficulty) * weight

            weight_total += weight

        # 归一化到 -2.5 到 3.0
        if weight_total > 0:
            normalized = (weighted_sum / weight_total) * 4
            return max(-2.5, min(normalized, 3.0))

        return (accuracy - 0.5) * 4

    def _calculate_dimensions(
        self,
        questions: List[Dict[str, Any]]
    ) -> Dict[str, DimensionResult]:
        """计算各维度能力"""

        dimensions = {}
        question_types = ["listening", "reading", "vocabulary", "grammar"]

        for qtype in question_types:
            type_questions = [q for q in questions if q["type"] == qtype]

            if not type_questions:
                continue

            correct = sum(1 for q in type_questions if q["is_correct"])
            total = len(type_questions)
            accuracy = correct / total

            ability = (accuracy - 0.5) * 4
            level = self.selector._ability_to_level(ability)

            dimensions[qtype] = DimensionResult(
                level=level,
                accuracy=accuracy,
                ability=ability
            )

        return dimensions

    def generate_recommendations(
        self,
        result: AssessmentResult,
        target_scenario: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成学习建议"""

        recommendations = {
            "suggested_scenarios": [],
            "focus_areas": [],
            "estimated_study_days": 14
        }

        # 根据薄弱环节推荐场景
        if "listening" in result.weak_areas:
            recommendations["suggested_scenarios"].extend([
                "scenario_airport_checkin",
                "scenario_hotel_checkin"
            ])
            recommendations["focus_areas"].append("听力练习")

        if "vocabulary" in result.weak_areas or "grammar" in result.weak_areas:
            recommendations["focus_areas"].append("词汇积累")

        # 根据水平推荐场景
        if result.overall_level in ["A1", "A2"]:
            recommendations["suggested_scenarios"].extend([
                "scenario_greetings",
                "scenario_shopping"
            ])
        elif result.overall_level in ["B1", "B2"]:
            recommendations["suggested_scenarios"].extend([
                "scenario_business_meeting_intro",
                "scenario_hotel_checkin"
            ])

        # 去重
        recommendations["suggested_scenarios"] = list(
            set(recommendations["suggested_scenarios"])
        )[:8]

        return recommendations


class AssessmentService:
    """评估服务"""

    def __init__(
        self,
        assessment_repo: AssessmentRepository,
        question_repo: QuestionRepository
    ):
        self.assessment_repo = assessment_repo
        self.question_repo = question_repo
        self.selector = AdaptiveQuestionSelector(question_repo)
        self.evaluator = AssessmentEvaluator()

    async def start_assessment(self, user_id: str) -> Assessment:
        """启动评估"""

        assessment = Assessment(
            user_id=user_id,
            started_at=datetime.now(),
            status="in_progress",
            questions=[]
        )

        assessment_id = await self.assessment_repo.create(assessment)
        assessment.id = assessment_id

        return assessment

    async def get_next_question(
        self,
        assessment_id: str
    ) -> Optional[AssessmentQuestion]:
        """获取下一题"""

        assessment = await self.assessment_repo.get(assessment_id)

        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        if assessment.status != "in_progress":
            return None

        # 自适应选题
        next_question = await self.selector.select_next(
            assessment.questions,
            total_questions=10
        )

        return next_question

    async def submit_answer(
        self,
        assessment_id: str,
        question_id: str,
        answer_index: int,
        time_spent: int
    ) -> Dict[str, Any]:
        """提交答案"""

        assessment = await self.assessment_repo.get(assessment_id)
        question = await self.question_repo.get(question_id)

        if not assessment or not question:
            raise ValueError("Invalid assessment or question")

        # 判断正确性
        is_correct = (answer_index == question.content["correct_index"])

        # 记录答题
        assessment.questions.append({
            "question_id": question_id,
            "type": question.type,
            "level": question.level,
            "difficulty": question.difficulty,
            "is_correct": is_correct,
            "time_spent": time_spent,
            "answer_selected": answer_index
        })

        # 更新评估记录
        await self.assessment_repo.update(assessment)

        # 获取下一题
        next_question = await self.get_next_question(assessment_id)

        return {
            "is_correct": is_correct,
            "explanation": question.content.get("explanation"),
            "next_question": next_question.to_dict() if next_question else None
        }

    async def complete_assessment(
        self,
        assessment_id: str
    ) -> AssessmentResult:
        """完成评估"""

        assessment = await self.assessment_repo.get(assessment_id)

        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        # 计算结果
        result = self.evaluator.calculate_result(assessment)

        # 生成建议
        recommendations = self.evaluator.generate_recommendations(result)

        # 更新评估记录
        assessment.status = "completed"
        assessment.completed_at = datetime.now()
        assessment.duration_secs = int(
            (assessment.completed_at - assessment.started_at).total_seconds()
        )
        assessment.results = result.to_dict()
        assessment.recommendations = recommendations

        await self.assessment_repo.update(assessment)

        return result
