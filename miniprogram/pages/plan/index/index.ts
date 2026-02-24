/**
 * 学习计划页
 */

import { haptics } from '../../../utils/haptics';
import { toast } from '../../../utils/toast';
import { request } from '../../../services/request';

interface ScenarioGoal {
  scenario_id: string;
  scenario_name: string;
  icon: string;
  priority: 'high' | 'medium' | 'low';
  target_readiness: number;
  current_readiness: number;
  readinessPercent: number;
  estimated_days: number;
  dialogue_ids: string[];
  key_vocabulary: string[];
  reason: string;
}

interface DailyTask {
  date: string;
  scenario_id: string;
  dialogue_id: string;
  dialogue_title: string;
  vocabulary_count: number;
  estimated_minutes: number;
  is_completed: boolean;
}

interface LearningPlan {
  id: string;
  overall_level: string;
  overall_progress: number;
  target_date?: string;
  days_remaining?: number;
  available_days: number;
  daily_minutes: number;
  total_scenarios: number;
  completed_scenarios: number;
  total_dialogues: number;
  completed_dialogues: number;
  scenario_goals: ScenarioGoal[];
  daily_tasks: DailyTask[];
  today_tasks?: DailyTask[];
}

Page({
  data: {
    plan: null as LearningPlan | null,
    todayTasks: [] as DailyTask[],
    todayTasksCount: 0,
    totalVocabulary: 0,
    loading: true,
    noPlan: false,
  },

  onLoad() {
    console.log('[Plan] Page loaded');
    this.loadPlan();
  },

  onShow() {
    haptics.light();
    if (this.data.plan) {
      this.loadPlan();
    }
  },

  /**
   * 加载学习计划
   */
  async loadPlan() {
    this.setData({ loading: true, noPlan: false });

    try {
      const plan = await request.get<LearningPlan>('/api/plan/current');

      // Compute today's tasks from API or filter locally
      const today = new Date().toISOString().split('T')[0];
      const todayTasks = plan.today_tasks ||
        plan.daily_tasks.filter(t => t.date === today);

      const totalVocabulary = plan.scenario_goals.reduce(
        (sum, goal) => sum + goal.key_vocabulary.length,
        0
      );

      this.setData({
        plan,
        todayTasks,
        todayTasksCount: todayTasks.filter(t => !t.is_completed).length,
        totalVocabulary,
        loading: false
      });

      wx.reportAnalytics('plan_view', {
        plan_id: plan.id,
        progress: plan.overall_progress
      });

    } catch (error: any) {
      console.error('[Plan] Load failed:', error);
      // 404 means no plan yet - show empty state
      if (error.message?.includes('404') || error.message?.includes('No active plan')) {
        this.setData({ loading: false, noPlan: true });
      } else {
        toast.error('加载计划失败');
        this.setData({ loading: false });
      }
    }
  },

  /**
   * 开始学习对话
   */
  startDialogue(e: any) {
    const { dialogueId } = e.currentTarget.dataset;
    haptics.medium();

    wx.reportAnalytics('dialogue_start', {
      dialogue_id: dialogueId,
      from: 'plan_page'
    });

    setTimeout(() => {
      wx.navigateTo({
        url: `/pages/study/dialogue/dialogue?id=${dialogueId}`,
        fail: () => toast.error('页面跳转失败')
      });
    }, 150);
  },

  /**
   * 查看场景详情
   */
  viewScenario(e: any) {
    const { scenarioId } = e.currentTarget.dataset;
    haptics.light();

    wx.reportAnalytics('scenario_view', {
      scenario_id: scenarioId,
      from: 'plan_page'
    });

    wx.navigateTo({
      url: `/pages/scenario/detail/detail?id=${scenarioId}`,
      fail: () => toast.info('场景详情页开发中')
    });
  },

  /**
   * 继续学习
   */
  continueStudy() {
    const { todayTasks } = this.data;
    const nextTask = todayTasks.find(t => !t.is_completed);
    if (!nextTask) {
      haptics.light();
      toast.success('今日任务已完成！');
      return;
    }

    haptics.medium();
    wx.reportAnalytics('continue_study', { dialogue_id: nextTask.dialogue_id });

    setTimeout(() => {
      wx.navigateTo({
        url: `/pages/study/dialogue/dialogue?id=${nextTask.dialogue_id}`,
        fail: () => toast.error('页面跳转失败')
      });
    }, 150);
  },

  /**
   * 跳转到水平测评
   */
  goAssessment() {
    haptics.medium();
    wx.navigateTo({
      url: '/pages/assessment/test/test',
      fail: () => toast.error('页面跳转失败')
    });
  },

  /**
   * 调整计划
   */
  async adjustPlan() {
    haptics.light();

    const confirmed = await toast.confirm({
      title: '调整学习计划',
      content: '调整计划会重新生成学习任务，是否继续？',
      confirmText: '确定',
      cancelText: '取消'
    });

    if (confirmed) {
      haptics.medium();
      toast.info('计划调整功能开发中');
    }
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    haptics.light();
    this.loadPlan().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  onUnload() {
    console.log('[Plan] Page unload');
  }
});
