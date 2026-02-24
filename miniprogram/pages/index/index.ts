Page({
  data: {
    loading: false as boolean,
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

  goAssessment() {
    wx.navigateTo({ url: '/pages/assessment/intro/intro' });
  },

  goPlan() {
    wx.navigateTo({ url: '/pages/plan/index/index' });
  },
});
