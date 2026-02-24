const store = require('../../store/index');

Page({
  data: {
    secsToday: 0,
    streak: 0,
    vocabCount: 0,
  },

  _unsubStats: null as (() => void) | null,
  _unsubVocab: null as (() => void) | null,

  onLoad() {
    this._unsubStats = store.on('todayStats', () => this.syncFromStore());
    this._unsubVocab = store.on('vocabCount', () => this.syncFromStore());
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
    this.setData({
      secsToday: stats.secsToday || 0,
      streak: stats.streak || 0,
      vocabCount: store.get('vocabCount') || 0,
    });
  },

  goUpgrade() { wx.navigateTo({ url: '/pages/upgrade/upgrade' }); },
  goImport() { wx.navigateTo({ url: '/pages/import/import' }); },
  goExport() { wx.navigateTo({ url: '/pages/export/export' }); },
  goPrivacy() { wx.navigateTo({ url: '/pages/privacy/privacy' }); },
  goTerms() { wx.navigateTo({ url: '/pages/terms/terms' }); },
});
