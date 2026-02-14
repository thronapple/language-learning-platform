const { request } = require('../../services/request')
const auth = require('../../services/auth')
const store = require('../../store/index')

Page({
  data: {
    loading: false,
  },
  onLoad() {
    // 登录并拉取用户档案
    this.setData({ loading: true })
    wx.login({
      success: (res) => {
        const code = (res && res.code) || 'test_code_dev'
        console.log('微信登录获取code:', code)
        auth
          .me(code)
          .then((data) => {
            console.log('登录成功:', data)
            store.set('user', data.user)
            wx.showToast({ title: '登录成功', icon: 'success' })
          })
          .catch((err) => {
            console.error('登录失败:', err)
            // 开发环境fallback：创建临时用户
            const mockUser = { openid: 'dev_user_' + Date.now() }
            store.set('user', mockUser)
            console.log('使用开发用户:', mockUser)
            wx.showToast({ title: '开发模式登录', icon: 'none' })
          })
          .finally(() => {
            // 预拉取内容页，作为冒烟
            request('/content')
              .finally(() => this.setData({ loading: false }))
          })
      },
      fail: (err) => {
        console.error('wx.login失败:', err)
        // 完全fallback：无微信环境
        const mockUser = { openid: 'fallback_user_' + Date.now() }
        store.set('user', mockUser)
        console.log('使用fallback用户:', mockUser)
        this.setData({ loading: false })
        wx.showToast({ title: 'Fallback模式', icon: 'none' })
      },
    })
  },
  goStudy() {
    wx.navigateTo({ url: '/pages/study/study' })
  },
})
