const auth = require('./services/auth')
const { request } = require('./services/request')
const store = require('./store/index')

App({
  onLaunch() {
    wx.cloud.init({ traceUser: true })
    this.login()
  },

  /**
   * 全局错误捕获 — 上报至后端 /events
   */
  onError(msg) {
    console.error('[App] onError:', msg)
    try {
      const errQueue = wx.getStorageSync('_err_queue') || []
      errQueue.push({
        msg: String(msg).slice(0, 500),
        ts: new Date().toISOString(),
        page: getCurrentPages().slice(-1)[0]?.route || '',
      })
      // 最多缓存 20 条，防止刷屏
      if (errQueue.length > 20) errQueue.shift()
      wx.setStorageSync('_err_queue', errQueue)
    } catch (_) {}
    // 尝试即时上报
    this.flushErrors()
  },

  onPageNotFound(res) {
    console.warn('[App] Page not found:', res.path)
    wx.reLaunch({ url: '/pages/index/index' })
  },

  /**
   * 批量上报缓存的前端错误
   */
  flushErrors() {
    try {
      const errQueue = wx.getStorageSync('_err_queue')
      if (!errQueue || !errQueue.length) return
      wx.setStorageSync('_err_queue', [])
      request.post('/events', {
        event: 'client_error',
        props: { errors: errQueue },
        ts: new Date().toISOString(),
      }).catch(() => {
        // 上报失败则放回队列
        try {
          const existing = wx.getStorageSync('_err_queue') || []
          wx.setStorageSync('_err_queue', existing.concat(errQueue).slice(-20))
        } catch (_) {}
      })
    } catch (_) {}
  },

  login() {
    wx.login({
      success: (res) => {
        if (!res.code) {
          console.error('wx.login: no code returned')
          return
        }
        auth
          .me(res.code)
          .then((data) => {
            console.log('登录成功')
            store.set('user', data.user)
            store.set('loggedIn', true)
            // 登录成功后加载用户数据
            this.loadUserData()
          })
          .catch((err) => {
            console.error('登录失败:', err)
          })
      },
      fail: (err) => {
        console.error('wx.login失败:', err)
      },
    })
  },

  /**
   * 加载用户关联数据（统计、词汇数量等）
   */
  loadUserData() {
    // 加载学习统计
    request.get('/plan/stats')
      .then((res) => {
        store.set('todayStats', {
          secsToday: res.secsToday || 0,
          streak: res.streak || 0,
        })
      })
      .catch(() => {})

    // 加载词汇数量
    request.get('/vocab', { page: 1, page_size: 1 })
      .then((res) => {
        store.set('vocabCount', (res.items || []).length || res.total || 0)
      })
      .catch(() => {})

    // 加载待复习数量
    request.get('/vocab/due', { before: new Date().toISOString() })
      .then((res) => {
        store.set('vocabDueCount', (res.items || []).length || 0)
      })
      .catch(() => {})
  },
})
