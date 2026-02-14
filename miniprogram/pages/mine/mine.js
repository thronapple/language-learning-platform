const { request } = require('../../services/request')

Page({
  data: { secsToday: 0, streak: 0 },
  onShow() {
    request('/plan/stats').then((res) => {
      this.setData({ secsToday: res.secsToday || 0, streak: res.streak || 0 })
    })
  },
  goUpgrade() { wx.navigateTo({ url: '/pages/upgrade/upgrade' }) },
  goPrivacy() { wx.navigateTo({ url: '/pages/privacy/privacy' }) },
  goTerms() { wx.navigateTo({ url: '/pages/terms/terms' }) },
})
