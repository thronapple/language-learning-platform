// 根据环境自动切换BASE_URL
const getBaseUrl = () => {
  // 可以通过编译条件或配置来切换
  const isDev = true // 开发环境标记，生产时改为false
  if (isDev) {
    // 开发环境：支持多个可能的本地地址
    return 'http://127.0.0.1:8000' // 默认本地IP
  } else {
    // 生产环境：使用正式域名
    return 'https://api.your-domain.com'
  }
}

const BASE_URL = getBaseUrl()
const store = require('../store/index')

function request(path, options = {}) {
  const { method = 'GET', data = {}, headers = {} } = options
  const user = store.get('user')
  const openid = user ? user.openid : ''
  
  console.log(`[Request] ${method} ${BASE_URL}${path}`, { openid: openid ? '***' + openid.slice(-4) : 'none' })
  
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + path,
      method,
      data,
      header: {
        'content-type': 'application/json',
        'x-openid': openid,
        ...headers,
      },
      timeout: 8000,
      success: (res) => {
        console.log(`[Response] ${res.statusCode}`, res.data)
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else if (res.statusCode === 429) {
          // Rate limit exceeded
          const detail = res.data.detail || {}
          const message = detail.message || '请求过于频繁，请稍后再试'
          const limits = detail.limits || {}
          console.error(`[Rate Limit] ${message}`, limits)
          reject(new Error(message))
        } else {
          console.error(`[Error] HTTP ${res.statusCode}:`, res.data)
          reject(new Error(`HTTP ${res.statusCode}: ${res.data.detail || 'Unknown error'}`))
        }
      },
      fail: (err) => {
        console.error('[Request Failed]:', err)
        reject(err)
      },
    })
  })
}

module.exports = { request }
