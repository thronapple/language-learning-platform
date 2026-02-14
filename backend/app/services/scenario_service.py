"""
场景服务 - Scenario Service
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from ..domain.scenario import (
    Scenario, Dialogue, ScenarioProgress, SubScenario,
    Sentence, VocabularyItem, ScenarioCategory, CEFRLevel
)


class ScenarioService:
    """场景管理服务"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化场景服务

        Args:
            data_dir: 数据文件目录
        """
        self.data_dir = Path(data_dir)
        self._scenarios_cache: Optional[List[Scenario]] = None
        self._dialogues_cache: Optional[List[Dialogue]] = None

    def _load_scenarios(self) -> List[Scenario]:
        """加载场景数据"""
        if self._scenarios_cache is not None:
            return self._scenarios_cache

        scenarios_file = self.data_dir / "scenarios.json"
        with open(scenarios_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        scenarios = []
        for item in data:
            # 转换子场景
            sub_scenarios = [
                SubScenario(
                    id=s['id'],
                    order=s['order'],
                    title_en=s['title_en'],
                    title_zh=s['title_zh'],
                    difficulty=s['difficulty']
                )
                for s in item['scenarios']
            ]

            scenario = Scenario(
                id=item['id'],
                name_en=item['name_en'],
                name_zh=item['name_zh'],
                category=ScenarioCategory(item['category']),
                level=CEFRLevel(item['level']),
                priority=item['priority'],
                description_en=item['description_en'],
                description_zh=item['description_zh'],
                icon=item['icon'],
                estimated_duration_minutes=item['estimated_duration_minutes'],
                dialogue_count=item['dialogue_count'],
                vocabulary_count=item['vocabulary_count'],
                tags=item['tags'],
                scenarios=sub_scenarios,
                learning_objectives=item['learning_objectives'],
                created_at=datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            )
            scenarios.append(scenario)

        self._scenarios_cache = scenarios
        return scenarios

    def _load_dialogues(self) -> List[Dialogue]:
        """加载对话数据"""
        if self._dialogues_cache is not None:
            return self._dialogues_cache

        dialogues_file = self.data_dir / "dialogues.json"
        with open(dialogues_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        dialogues = []
        for item in data:
            # 转换句子
            sentences = [
                Sentence(
                    order=s['order'],
                    speaker=s['speaker'],
                    text_en=s['text_en'],
                    text_zh=s['text_zh'],
                    audio_url=s['audio_url'],
                    phonetic=s['phonetic'],
                    key_words=s['key_words'],
                    grammar_points=s['grammar_points']
                )
                for s in item['sentences']
            ]

            # 转换词汇
            vocabulary = [
                VocabularyItem(
                    word=v['word'],
                    translation=v['translation'],
                    level=v['level']
                )
                for v in item['vocabulary']
            ]

            dialogue = Dialogue(
                id=item['id'],
                scenario_id=item['scenario_id'],
                sub_scenario_id=item['sub_scenario_id'],
                order=item['order'],
                title_en=item['title_en'],
                title_zh=item['title_zh'],
                level=CEFRLevel(item['level']),
                sentences=sentences,
                vocabulary=vocabulary,
                cultural_notes=item['cultural_notes'],
                practice_tips=item['practice_tips'],
                created_at=datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            )
            dialogues.append(dialogue)

        self._dialogues_cache = dialogues
        return dialogues

    async def get_all_scenarios(
        self,
        category: Optional[ScenarioCategory] = None,
        level: Optional[CEFRLevel] = None
    ) -> List[Scenario]:
        """
        获取所有场景

        Args:
            category: 可选的分类过滤
            level: 可选的等级过滤

        Returns:
            场景列表
        """
        scenarios = self._load_scenarios()

        # 过滤
        if category:
            scenarios = [s for s in scenarios if s.category == category]
        if level:
            scenarios = [s for s in scenarios if s.level == level]

        # 按优先级排序
        scenarios.sort(key=lambda s: s.priority)

        return scenarios

    async def get_scenario_by_id(self, scenario_id: str) -> Optional[Scenario]:
        """
        根据ID获取场景

        Args:
            scenario_id: 场景ID

        Returns:
            场景对象，如果不存在返回None
        """
        scenarios = self._load_scenarios()
        for scenario in scenarios:
            if scenario.id == scenario_id:
                return scenario
        return None

    async def get_dialogues_by_scenario(
        self,
        scenario_id: str,
        sub_scenario_id: Optional[str] = None
    ) -> List[Dialogue]:
        """
        获取场景的对话列表

        Args:
            scenario_id: 场景ID
            sub_scenario_id: 可选的子场景ID过滤

        Returns:
            对话列表
        """
        dialogues = self._load_dialogues()

        # 过滤场景ID
        dialogues = [d for d in dialogues if d.scenario_id == scenario_id]

        # 可选的子场景过滤
        if sub_scenario_id:
            dialogues = [d for d in dialogues if d.sub_scenario_id == sub_scenario_id]

        # 按order排序
        dialogues.sort(key=lambda d: d.order)

        return dialogues

    async def get_dialogue_by_id(self, dialogue_id: str) -> Optional[Dialogue]:
        """
        根据ID获取对话

        Args:
            dialogue_id: 对话ID

        Returns:
            对话对象，如果不存在返回None
        """
        dialogues = self._load_dialogues()
        for dialogue in dialogues:
            if dialogue.id == dialogue_id:
                return dialogue
        return None

    async def get_recommended_scenarios(
        self,
        user_level: CEFRLevel,
        weak_areas: List[str],
        limit: int = 3
    ) -> List[Scenario]:
        """
        根据用户水平和薄弱环节推荐场景

        Args:
            user_level: 用户CEFR等级
            weak_areas: 薄弱领域列表
            limit: 返回数量限制

        Returns:
            推荐的场景列表
        """
        scenarios = self._load_scenarios()

        # 等级匹配：推荐当前等级或稍高一级
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        current_index = level_order.index(user_level.value)
        target_levels = [level_order[current_index]]
        if current_index < len(level_order) - 1:
            target_levels.append(level_order[current_index + 1])

        # 过滤等级匹配的场景
        matched_scenarios = [
            s for s in scenarios if s.level.value in target_levels
        ]

        # 计算推荐分数（基于优先级和标签匹配）
        scored_scenarios = []
        for scenario in matched_scenarios:
            score = 100 - scenario.priority  # 优先级越高分数越高

            # 标签匹配加分
            for weak_area in weak_areas:
                if weak_area.lower() in [tag.lower() for tag in scenario.tags]:
                    score += 20

            scored_scenarios.append((scenario, score))

        # 排序并返回top N
        scored_scenarios.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored_scenarios[:limit]]

    async def search_scenarios(
        self,
        keyword: str,
        category: Optional[ScenarioCategory] = None
    ) -> List[Scenario]:
        """
        搜索场景

        Args:
            keyword: 搜索关键词
            category: 可选的分类过滤

        Returns:
            匹配的场景列表
        """
        scenarios = self._load_scenarios()

        # 分类过滤
        if category:
            scenarios = [s for s in scenarios if s.category == category]

        # 关键词匹配（名称、描述、标签）
        keyword_lower = keyword.lower()
        matched_scenarios = []

        for scenario in scenarios:
            if (
                keyword_lower in scenario.name_en.lower() or
                keyword_lower in scenario.name_zh.lower() or
                keyword_lower in scenario.description_en.lower() or
                keyword_lower in scenario.description_zh.lower() or
                any(keyword_lower in tag.lower() for tag in scenario.tags)
            ):
                matched_scenarios.append(scenario)

        return matched_scenarios

    def get_scenario_statistics(self) -> Dict[str, Any]:
        """
        获取场景统计信息

        Returns:
            统计数据字典
        """
        scenarios = self._load_scenarios()
        dialogues = self._load_dialogues()

        total_sentences = sum(d.sentence_count for d in dialogues)
        total_vocabulary = sum(d.vocabulary_count for d in dialogues)

        # 按分类统计
        category_stats = {}
        for category in ScenarioCategory:
            count = len([s for s in scenarios if s.category == category])
            category_stats[category.value] = count

        # 按等级统计
        level_stats = {}
        for level in CEFRLevel:
            count = len([s for s in scenarios if s.level == level])
            level_stats[level.value] = count

        return {
            "total_scenarios": len(scenarios),
            "total_dialogues": len(dialogues),
            "total_sentences": total_sentences,
            "total_vocabulary": total_vocabulary,
            "by_category": category_stats,
            "by_level": level_stats
        }
