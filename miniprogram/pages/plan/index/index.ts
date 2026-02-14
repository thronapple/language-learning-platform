/**
 * 学习计划页 - 优化版
 * 添加触觉反馈、流畅交互和加载状态优化
 */

import { haptics } from '../../../utils/haptics';
import { toast } from '../../../utils/toast';

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
}

Page({
  data: {
    plan: null as LearningPlan | null,
    todayTasks: [] as DailyTask[],
    todayTasksCount: 0,
    totalVocabulary: 0,
    loading: true
  },

  onLoad() {
    console.log('[Plan] Page loaded');
    this.loadPlan();
  },

  onShow() {
    console.log('[Plan] Page show');
    // 轻触反馈
    haptics.light();

    // 每次显示时刷新数据
    if (this.data.plan) {
      this.loadPlan();
    }
  },

  /**
   * 加载学习计划
   */
  async loadPlan() {
    this.setData({ loading: true });

    try {
      // TODO: 调用API获取当前计划
      // const plan = await planService.getCurrentPlan();

      // 使用延迟加载避免闪烁
      await new Promise(resolve => setTimeout(resolve, 300));

      // 模拟数据
      const mockPlan: LearningPlan = {
        id: 'plan-001',
        overall_level: 'B1',
        overall_progress: 35,
        target_date: '2025-10-30',
        days_remaining: 27,
        available_days: 30,
        daily_minutes: 30,
        total_scenarios: 3,
        completed_scenarios: 0,
        total_dialogues: 9,
        completed_dialogues: 3,
        scenario_goals: [
          {
            scenario_id: 'airport-basics',
            scenario_name: '机场场景',
            icon: '✈️',
            priority: 'high',
            target_readiness: 0.85,
            current_readiness: 0.6,
            readinessPercent: 60,
            estimated_days: 5,
            dialogue_ids: ['airport-checkin-001', 'airport-security-001', 'airport-boarding-001'],
            key_vocabulary: ['passport', 'baggage', 'boarding pass', 'security', 'gate', 'flight'],
            reason: '高优先级travel场景；针对您的薄弱环节: listening'
          },
          {
            scenario_id: 'hotel-stay',
            scenario_name: '酒店场景',
            icon: '🏨',
            priority: 'medium',
            target_readiness: 0.85,
            current_readiness: 0.2,
            readinessPercent: 20,
            estimated_days: 6,
            dialogue_ids: ['hotel-checkin-001', 'hotel-service-001', 'hotel-checkout-001'],
            key_vocabulary: ['reservation', 'room service', 'check-out', 'bill', 'minibar'],
            reason: '包含3个核心学习目标'
          },
          {
            scenario_id: 'business-meeting',
            scenario_name: '商务会议',
            icon: '💼',
            priority: 'low',
            target_readiness: 0.85,
            current_readiness: 0.0,
            readinessPercent: 0,
            estimated_days: 7,
            dialogue_ids: ['meeting-intro-001', 'meeting-agenda-001', 'meeting-summary-001'],
            key_vocabulary: ['agenda', 'initiative', 'collaborate', 'summary', 'action items'],
            reason: '推荐的学习场景'
          }
        ],
        daily_tasks: []
      };

      // 模拟今日任务
      const today = new Date().toISOString().split('T')[0];
      const mockTodayTasks: DailyTask[] = [
        {
          date: today,
          scenario_id: 'airport-basics',
          dialogue_id: 'airport-checkin-001',
          dialogue_title: '机场值机办理',
          vocabulary_count: 8,
          estimated_minutes: 15,
          is_completed: false
        },
        {
          date: today,
          scenario_id: 'airport-basics',
          dialogue_id: 'airport-security-001',
          dialogue_title: '通过安检',
          vocabulary_count: 8,
          estimated_minutes: 12,
          is_completed: false
        }
      ];

      // 计算总词汇数
      const totalVocabulary = mockPlan.scenario_goals.reduce(
        (sum, goal) => sum + goal.key_vocabulary.length,
        0
      );

      this.setData({
        plan: mockPlan,
        todayTasks: mockTodayTasks,
        todayTasksCount: mockTodayTasks.filter(t => !t.is_completed).length,
        totalVocabulary,
        loading: false
      });

      // 埋点
      wx.reportAnalytics('plan_view', {
        plan_id: mockPlan.id,
        progress: mockPlan.overall_progress
      });

    } catch (error) {
      console.error('[Plan] Load failed:', error);
      toast.error('加载计划失败');
      this.setData({ loading: false });
    }
  },

  /**
   * 开始学习对话
   */
  startDialogue(e: any) {
    const { dialogueId } = e.currentTarget.dataset;

    console.log('[Plan] Start dialogue:', dialogueId);
    // 中等反馈 - 重要操作
    haptics.medium();

    // 埋点
    wx.reportAnalytics('dialogue_start', {
      dialogue_id: dialogueId,
      from: 'plan_page'
    });

    // 短暂延迟，让动画完成
    setTimeout(() => {
      wx.navigateTo({
        url: `/pages/study/dialogue/dialogue?id=${dialogueId}`,
        fail: (err) => {
          console.error('[Plan] Navigate failed:', err);
          toast.error('页面跳转失败');
        }
      });
    }, 150);
  },

  /**
   * 查看场景详情
   */
  viewScenario(e: any) {
    const { scenarioId } = e.currentTarget.dataset;

    console.log('[Plan] View scenario:', scenarioId);
    // 轻触反馈
    haptics.light();

    // 埋点
    wx.reportAnalytics('scenario_view', {
      scenario_id: scenarioId,
      from: 'plan_page'
    });

    // 跳转到场景详情页
    wx.navigateTo({
      url: `/pages/scenario/detail/detail?id=${scenarioId}`,
      fail: () => {
        toast.info('场景详情页开发中');
      }
    });
  },

  /**
   * 继续学习
   */
  continueStudy() {
    const { todayTasks } = this.data;

    // 找到第一个未完成的任务
    const nextTask = todayTasks.find(t => !t.is_completed);
    if (!nextTask) {
      haptics.light();
      toast.success('今日任务已完成！');
      return;
    }

    console.log('[Plan] Continue study:', nextTask.dialogue_id);
    // 重要操作反馈
    haptics.medium();

    // 埋点
    wx.reportAnalytics('continue_study', {
      dialogue_id: nextTask.dialogue_id
    });

    // 短暂延迟
    setTimeout(() => {
      wx.navigateTo({
        url: `/pages/study/dialogue/dialogue?id=${nextTask.dialogue_id}`,
        fail: (err) => {
          console.error('[Plan] Navigate failed:', err);
          toast.error('页面跳转失败');
        }
      });
    }, 150);
  },

  /**
   * 调整计划
   */
  async adjustPlan() {
    console.log('[Plan] Adjust plan');
    haptics.light();

    const confirmed = await toast.confirm({
      title: '调整学习计划',
      content: '调整计划会重新生成学习任务，是否继续？',
      confirmText: '确定',
      cancelText: '取消'
    });

    if (confirmed) {
      haptics.medium();
      // TODO: 实现计划调整功能
      toast.info('计划调整功能开发中');
    }
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    console.log('[Plan] Pull down refresh');
    haptics.light();

    this.loadPlan().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 页面卸载
   */
  onUnload() {
    console.log('[Plan] Page unload');
  }
});
