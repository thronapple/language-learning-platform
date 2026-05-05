const store = require('../../store/index');

Page({
  data: {
    secsToday: 0,
    todayValue: 0,
    todayLabel: '今日秒数',
    streak: 0,
    vocabCount: 0,
    totalHours: '4.2',
    calendarCells: [] as Array<{ level: number }>,
    achievements: [
      { icon: 'flame', name: '7 日连击', earned: true, stateClass: 'earned', tone: 'brand' },
      { icon: 'trophy', name: '百词达成', earned: true, stateClass: 'earned', tone: 'lemon' },
      { icon: 'bolt', name: '速记之星', earned: true, stateClass: 'earned', tone: 'indigo' },
      { icon: 'star', name: '完美一周', earned: false, stateClass: 'locked', tone: 'ink' },
      { icon: 'globe', name: '环游 10 城', earned: false, stateClass: 'locked', tone: 'ink' },
    ],
  },

  _unsubStats: null as (() => void) | null,
  _unsubVocab: null as (() => void) | null,

  onLoad() {
    this._unsubStats = store.on('todayStats', () => this.syncFromStore());
    this._unsubVocab = store.on('vocabCount', () => this.syncFromStore());
    this.initCalendar();
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 });
    }
    this.syncFromStore();
  },

  onUnload() {
    if (this._unsubStats) this._unsubStats();
    if (this._unsubVocab) this._unsubVocab();
  },

  syncFromStore() {
    const stats = store.get('todayStats') || {};
    const secsToday = stats.secsToday || 0;
    this.setData({
      secsToday,
      todayValue: secsToday >= 60 ? Math.floor(secsToday / 60) : secsToday,
      todayLabel: secsToday >= 60 ? '今日分钟' : '今日秒数',
      streak: stats.streak || 0,
      vocabCount: store.get('vocabCount') || 0,
    });
  },

  initCalendar() {
    const calendarCells = Array.from({ length: 84 }).map((_, i) => {
      const seed = (i * 37 + 11) % 100;
      const level = seed < 30 ? 0 : seed < 55 ? 1 : seed < 75 ? 2 : seed < 90 ? 3 : 4;
      return { level };
    });
    this.setData({ calendarCells });
  },

  goUpgrade() { wx.navigateTo({ url: '/pages/upgrade/upgrade' }); },
  goImport() { wx.navigateTo({ url: '/pages/import/import' }); },
  goExport() { wx.navigateTo({ url: '/pages/export/export' }); },
  goPrivacy() { wx.navigateTo({ url: '/pages/privacy/privacy' }); },
  goTerms() { wx.navigateTo({ url: '/pages/terms/terms' }); },
  goAssessment() { wx.navigateTo({ url: '/pages/assessment/intro/intro' }); },
  goPlan() { wx.navigateTo({ url: '/pages/plan/index/index' }); },
  openSettings() { wx.showToast({ title: '设置功能开发中', icon: 'none' }); },
});
