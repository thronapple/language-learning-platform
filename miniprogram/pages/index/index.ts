Page({
  data: {
    loading: false as boolean,
    dueCount: 23,
    totalToday: 35,
    streak: 12,
    completedTasks: 2,
    totalTasks: 3,
    completionPercent: 67,
    weekProgress: 70,
    vocabCount: 342,
    scenarioCount: 8,
    studyTime: '4h 12m',
    weekDays: [
      { label: '一', done: true, dotClass: 'done' },
      { label: '二', done: true, dotClass: 'done' },
      { label: '三', done: true, dotClass: 'done' },
      { label: '四', done: true, dotClass: 'done' },
      { label: '五', done: true, dotClass: 'done' },
      { label: '六', done: false, dotClass: '' },
      { label: '日', done: false, dotClass: '' },
    ],
    tasks: [
      { icon: 'cards', label: 'SRS 词汇复习', meta: '23 / 35 卡片', done: false, rowClass: '', statusClass: '', action: 'vocab' },
      { icon: 'chat', label: '场景对话 · 咖啡馆', meta: '6 轮对话', done: false, rowClass: '', statusClass: '', action: 'dialogue' },
      { icon: 'listen', label: '听力练习 · BBC 6 分钟', meta: '听完一遍', done: true, rowClass: 'done', statusClass: 'checked', action: 'study' },
    ],
    scenarios: [
      { icon: 'coffee', label: '咖啡馆点单', tag: 'A2', tone: 'brand' },
      { icon: 'work', label: '商务会议', tag: 'B2', tone: 'indigo' },
      { icon: 'plane', label: '机场出行', tag: 'A2', tone: 'mint' },
      { icon: 'school', label: '校园生活', tag: 'B1', tone: 'lemon' },
    ],
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 });
    }
  },

  goStudy() {
    this.setData({ loading: true });
    wx.navigateTo({
      url: '/pages/study/study',
      complete: () => this.setData({ loading: false }),
    });
  },

  goVocab() {
    wx.switchTab({ url: '/pages/vocab/vocab' });
  },

  goDialogue() {
    // TODO(backend): 接入后端后改为按场景/计划实际 dialogue_id 跳转
    wx.navigateTo({ url: '/pages/study/dialogue/dialogue?id=stub' });
  },

  onTaskTap(e: WechatMiniprogram.TouchEvent) {
    const action = e.currentTarget.dataset.action as string;
    if (action === 'vocab') {
      this.goVocab();
      return;
    }
    if (action === 'dialogue') {
      this.goDialogue();
      return;
    }
    this.goStudy();
  },

  goAssessment() {
    wx.navigateTo({ url: '/pages/assessment/intro/intro' });
  },

  goPlan() {
    wx.navigateTo({ url: '/pages/plan/index/index' });
  },
});
