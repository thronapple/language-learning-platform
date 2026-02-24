/**
 * 全局状态管理
 * - 支持订阅/通知机制，页面自动更新
 * - 关键数据持久化到 localStorage
 */

const PERSIST_KEYS = ['user', 'todayStats']

const store = {
  state: {
    user: null,
    loggedIn: false,
    plan: null,
    todayStats: null,   // { secsToday, streak }
    vocabCount: 0,
    vocabDueCount: 0,
  },

  _listeners: {},

  /**
   * 设置状态
   */
  set(key, value) {
    this.state[key] = value
    // 持久化
    if (PERSIST_KEYS.indexOf(key) >= 0 && value != null) {
      try { wx.setStorageSync('store_' + key, JSON.stringify(value)) } catch (e) {}
    }
    // 通知订阅者
    const cbs = this._listeners[key] || []
    for (let i = 0; i < cbs.length; i++) {
      try { cbs[i](value) } catch (e) {}
    }
  },

  /**
   * 获取状态
   */
  get(key) {
    return this.state[key]
  },

  /**
   * 订阅状态变化（返回取消订阅函数）
   */
  on(key, callback) {
    if (!this._listeners[key]) this._listeners[key] = []
    this._listeners[key].push(callback)
    return () => {
      this._listeners[key] = (this._listeners[key] || []).filter((cb) => cb !== callback)
    }
  },

  /**
   * 从持久化存储恢复状态
   */
  restore() {
    for (let i = 0; i < PERSIST_KEYS.length; i++) {
      const key = PERSIST_KEYS[i]
      try {
        const raw = wx.getStorageSync('store_' + key)
        if (raw) {
          this.state[key] = JSON.parse(raw)
        }
      } catch (e) {}
    }
    if (this.state.user) {
      this.state.loggedIn = true
    }
  },

  /**
   * 清除所有状态（登出时使用）
   */
  clear() {
    Object.keys(this.state).forEach((key) => { this.state[key] = null })
    this.state.loggedIn = false
    this.state.vocabCount = 0
    this.state.vocabDueCount = 0
    PERSIST_KEYS.forEach((key) => {
      try { wx.removeStorageSync('store_' + key) } catch (e) {}
    })
  },
}

// 启动时恢复
store.restore()

module.exports = store
