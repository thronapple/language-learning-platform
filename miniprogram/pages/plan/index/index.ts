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

interface WeekDayView {
  label: string;
  day: number;
  state: 'done' | 'today' | 'future';
}

interface TaskView {
  dialogue_id: string;
  icon: string;
  tone: 'brand' | 'indigo' | 'mint' | 'lemon';
  statusClass: 'done' | 'active' | 'pending';
  tailClass: string;
  tag: string;
  title: string;
  meta: string;
  extra: string;
  progressPercent: number;
  completed: boolean;
  showProgress: boolean;
}

interface PathWeekView {
  week: number;
  title: string;
  range: string;
  summary: string;
  status: 'done' | 'active' | 'locked';
  chipText: string;
  chipClass: string;
  showChip: boolean;
  showChevron: boolean;
  scenario_id: string;
}

Page({
  data: {
    plan: null as LearningPlan | null,
    todayTasks: [] as DailyTask[],
    taskViews: [] as TaskView[],
    pathWeeks: [] as PathWeekView[],
    weekDays: [] as WeekDayView[],
    todayTasksCount: 0,
    totalVocabulary: 0,
    planTitle: '30 天 A1 → B1 计划',
    planSubtitle: '第 1 天 · 准备开始',
    completedDays: 0,
    remainingDays: 0,
    currentWeek: 1,
    weekDoneCount: 0,
    todayDateLabel: '',
    completedTaskCount: 0,
    todayMinutesDone: 0,
    todayMinutesRemaining: 0,
    dailyGoalPercent: 0,
    hasTodayTasks: false,
    continueDisabled: true,
    continueLabel: '今日已完成',
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
      const viewData = this.buildPlanView(plan, todayTasks);

      this.setData({
        plan,
        todayTasks,
        todayTasksCount: todayTasks.filter(t => !t.is_completed).length,
        totalVocabulary,
        loading: false,
        ...viewData
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

  /** CEFR 阶梯：从当前等级跳两档作为合理近期目标 */
  nextTargetLevel(current?: string): string {
    const order = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
    const idx = order.indexOf(current || '');
    if (idx < 0) return 'B1';
    return order[Math.min(idx + 2, order.length - 1)];
  },

  buildPlanView(plan: LearningPlan, todayTasks: DailyTask[]) {
    const availableDays = plan.available_days || 30;
    const remainingDays = typeof plan.days_remaining === 'number'
      ? Math.max(0, plan.days_remaining)
      : Math.max(0, availableDays - Math.round((plan.overall_progress || 0) / 100 * availableDays));
    const completedDays = Math.max(0, availableDays - remainingDays);
    const currentWeek = Math.max(1, Math.ceil(Math.max(1, completedDays || 1) / 7));
    const weekStartDay = (currentWeek - 1) * 7 + 1;
    const todayIndex = Math.min(6, Math.max(0, completedDays - weekStartDay + 1));
    const weekDoneCount = Math.min(7, Math.max(0, completedDays - weekStartDay + 1));
    const labels = ['一', '二', '三', '四', '五', '六', '日'];
    const weekDays: WeekDayView[] = labels.map((label, index) => ({
      label,
      day: weekStartDay + index,
      state: index < todayIndex ? 'done' : index === todayIndex ? 'today' : 'future',
    }));

    const todayMinutesDone = todayTasks
      .filter(t => t.is_completed)
      .reduce((sum, task) => sum + (task.estimated_minutes || 0), 0);
    const dailyMinutes = plan.daily_minutes || 20;
    const todayMinutesRemaining = Math.max(0, dailyMinutes - todayMinutesDone);
    const dailyGoalPercent = Math.min(100, Math.round(todayMinutesDone / dailyMinutes * 100));

    const taskViews: TaskView[] = todayTasks.map((task, index) => {
      const completed = !!task.is_completed;
      const isActive = !completed && todayTasks.findIndex(t => !t.is_completed) === index;
      const tone: TaskView['tone'] = index === 0 ? 'mint' : index === 1 ? 'indigo' : 'lemon';
      return {
        dialogue_id: task.dialogue_id,
        icon: index === 0 ? 'cards' : index === 1 ? 'chat' : 'headphones',
        tone,
        statusClass: completed ? 'done' : isActive ? 'active' : 'pending',
        tailClass: completed ? 'checked' : '',
        tag: index === 0 ? '词汇 · SRS' : index === 1 ? '对话 · 场景' : '听力 · 精听',
        title: task.dialogue_title || '学习任务',
        meta: `${task.estimated_minutes || 0} 分钟 · ${task.vocabulary_count || 0} 个词汇`,
        extra: completed ? '+12 XP' : isActive ? '进行中' : '',
        progressPercent: completed ? 100 : isActive ? 66 : 0,
        completed,
        showProgress: !completed && isActive,
      };
    });

    const pathWeeks = this.buildPathWeeks(plan);
    const month = new Date().getMonth() + 1;
    const day = new Date().getDate();
    const hasTodayTasks = todayTasks.length > 0;
    const completedTaskCount = todayTasks.filter(t => t.is_completed).length;

    return {
      taskViews,
      pathWeeks,
      weekDays,
      planTitle: `${availableDays} 天 ${plan.overall_level || 'A1'} → ${this.nextTargetLevel(plan.overall_level)} 计划`,
      planSubtitle: `第 ${Math.max(1, completedDays)} 天 · ${plan.overall_progress >= 70 ? '接近目标' : plan.overall_progress >= 30 ? '进展顺利' : '稳步开始'}`,
      completedDays,
      remainingDays,
      currentWeek,
      weekDoneCount,
      todayDateLabel: `${month} 月 ${day} 日`,
      completedTaskCount,
      todayMinutesDone,
      todayMinutesRemaining,
      dailyGoalPercent,
      hasTodayTasks,
      continueDisabled: !hasTodayTasks,
      continueLabel: hasTodayTasks ? '继续学习' : '今日已完成',
    };
  },

  goBack() {
    if (getCurrentPages().length > 1) {
      wx.navigateBack();
      return;
    }

    wx.switchTab({
      url: '/pages/index/index'
    });
  },

  buildPathWeeks(plan: LearningPlan): PathWeekView[] {
    const goals = plan.scenario_goals || [];
    const totalWeeks = Math.max(4, Math.ceil((plan.available_days || 30) / 7));
    let activeAssigned = false;

    return Array.from({ length: Math.min(4, totalWeeks) }).map((_, index) => {
      const goal = goals[index];
      const done = goal ? goal.current_readiness >= goal.target_readiness : false;
      const status: 'done' | 'active' | 'locked' = done
        ? 'done'
        : !activeAssigned
          ? 'active'
          : 'locked';
      if (status === 'active') activeAssigned = true;

      const week = index + 1;
      const start = index * 7 + 1;
      const end = week === 4 ? (plan.available_days || 30) : Math.min((plan.available_days || 30), start + 6);

      return {
        week,
        title: goal?.scenario_name || ['基础巩固', '场景应用', '听力突破', '冲刺测评'][index] || `第 ${week} 周`,
        range: `Day ${start}-${end}`,
        summary: goal
          ? `${goal.estimated_days || 7} 天 · ${goal.key_vocabulary?.length || 0} 个关键词`
          : ['B1 核心词汇 · 200 词', '5 个生活场景对话', 'BBC + TED 精泛听', '模拟测试 · 升级到 B2'][index],
        status,
        chipText: status === 'done' ? '已完成' : status === 'active' ? '进行中' : '',
        chipClass: status === 'done' ? 'done' : status === 'active' ? 'active' : '',
        showChip: status !== 'locked',
        showChevron: status === 'locked',
        scenario_id: goal?.scenario_id || '',
      };
    });
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
