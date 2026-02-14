const { request } = require('../../services/request')

Page({
  data: { percent: 0, streak: 0 },
  onShow() {
    request('/plan/stats').then((res) => {
      const secs = res.secsToday || 0
      const percent = Math.min(100, Math.round((secs / 300) * 100))
      this.setData({ percent, streak: res.streak || 0 })
    })
  },
})
