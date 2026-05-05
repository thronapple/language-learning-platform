const auth = require('./services/auth')
const { request } = require('./services/request')
const store = require('./store/index')

App({
  onLaunch() {
    wx.cloud.init({ traceUser: true })
    this.loadFonts()
    this.login()
  },

  /**
   * 加载设计稿同款 Web 字体（Nunito + Geist Mono）。
   * 失败时静默降级到系统字体（PingFang SC），不阻塞登录。
   * 注意：开发期需在开发者工具勾选"不校验合法域名"；
   * 上线前需把 cdn.jsdelivr.net 加入小程序后台 downloadFile 合法域名。
   */
  loadFonts() {
    const FONT_CDN = 'https://cdn.jsdelivr.net/fontsource/fonts'
    const fonts = [
      { family: 'Nunito',     weight: '700', url: `${FONT_CDN}/nunito@latest/latin-700-normal.woff2` },
      { family: 'Nunito',     weight: '900', url: `${FONT_CDN}/nunito@latest/latin-900-normal.woff2` },
      { family: 'Geist Mono', weight: '700', url: `${FONT_CDN}/geist-mono@latest/latin-700-normal.woff2` },
    ]
    fonts.forEach((f) => {
      wx.loadFontFace({
        family: f.family,
        source: `url("${f.url}")`,
        weight: f.weight,
        scope: 'global',
        fail: (err) => console.warn('[font] load failed:', f.family, f.weight, err && err.errMsg),
      })
    })
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
