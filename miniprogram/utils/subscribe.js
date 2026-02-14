/**
 * 微信订阅消息工具模块
 *
 * 用于请求用户订阅消息权限
 */

// 模板ID配置 - 需要从后端环境变量或配置中获取
const TEMPLATE_IDS = {
  REVIEW_REMINDER: '',  // 复习提醒模板ID - 待配置
  STREAK_REMINDER: ''   // 打卡提醒模板ID - 待配置
}

/**
 * 请求订阅单个或多个消息模板
 * @param {Array<string>} templateIds - 模板ID数组
 * @returns {Promise<Object>} 订阅结果
 */
function requestSubscribe(templateIds) {
  return new Promise((resolve, reject) => {
    if (!templateIds || templateIds.length === 0) {
      console.warn('[Subscribe] 未提供模板ID')
      reject(new Error('未提供模板ID'))
      return
    }

    // 过滤掉空的模板ID
    const validTemplateIds = templateIds.filter(id => id && id.trim())

    if (validTemplateIds.length === 0) {
      console.warn('[Subscribe] 模板ID未配置')
      reject(new Error('模板ID未配置'))
      return
    }

    wx.requestSubscribeMessage({
      tmplIds: validTemplateIds,
      success(res) {
        console.log('[Subscribe] 订阅成功', res)

        // 统计订阅结果
        const result = {
          total: validTemplateIds.length,
          accepted: 0,
          rejected: 0,
          details: res
        }

        validTemplateIds.forEach(id => {
          if (res[id] === 'accept') {
            result.accepted++
          } else {
            result.rejected++
          }
        })

        console.log(`[Subscribe] 接受: ${result.accepted}/${result.total}`)
        resolve(result)
      },
      fail(err) {
        console.error('[Subscribe] 订阅失败', err)
        reject(err)
      }
    })
  })
}

/**
 * 请求复习提醒订阅
 */
function requestReviewReminder() {
  if (!TEMPLATE_IDS.REVIEW_REMINDER) {
    console.warn('[Subscribe] 复习提醒模板ID未配置')
    return Promise.reject(new Error('模板ID未配置'))
  }

  return requestSubscribe([TEMPLATE_IDS.REVIEW_REMINDER])
}

/**
 * 请求打卡提醒订阅
 */
function requestStreakReminder() {
  if (!TEMPLATE_IDS.STREAK_REMINDER) {
    console.warn('[Subscribe] 打卡提醒模板ID未配置')
    return Promise.reject(new Error('模板ID未配置'))
  }

  return requestSubscribe([TEMPLATE_IDS.STREAK_REMINDER])
}

/**
 * 请求所有提醒订阅
 */
function requestAllReminders() {
  const templateIds = []

  if (TEMPLATE_IDS.REVIEW_REMINDER) {
    templateIds.push(TEMPLATE_IDS.REVIEW_REMINDER)
  }

  if (TEMPLATE_IDS.STREAK_REMINDER) {
    templateIds.push(TEMPLATE_IDS.STREAK_REMINDER)
  }

  if (templateIds.length === 0) {
    console.warn('[Subscribe] 未配置任何模板ID')
    return Promise.reject(new Error('未配置模板ID'))
  }

  return requestSubscribe(templateIds)
}

/**
 * 检查是否应该显示订阅引导
 * 策略：每完成3次学习提示一次
 */
function shouldShowSubscribeGuide() {
  const key = 'subscribe_guide_count'
  const count = wx.getStorageSync(key) || 0

  // 每3次提示一次
  if (count > 0 && count % 3 === 0) {
    return true
  }

  return false
}

/**
 * 记录订阅引导显示次数
 */
function incrementSubscribeGuideCount() {
  const key = 'subscribe_guide_count'
  const count = wx.getStorageSync(key) || 0
  wx.setStorageSync(key, count + 1)
}

/**
 * 在适当时机引导用户订阅
 * 建议调用时机：
 * 1. 完成一次学习后
 * 2. 添加生词后
 * 3. 完成词汇复习后
 *
 * @param {string} context - 调用上下文
 */
function guideSubscribe(context = 'unknown') {
  console.log(`[Subscribe] 订阅引导触发: ${context}`)

  incrementSubscribeGuideCount()

  if (!shouldShowSubscribeGuide()) {
    console.log('[Subscribe] 不需要显示引导')
    return
  }

  // 显示订阅引导弹窗
  wx.showModal({
    title: '开启学习提醒',
    content: '订阅消息后，我们会在合适的时间提醒你复习，帮助你保持学习习惯。',
    confirmText: '开启提醒',
    cancelText: '暂不开启',
    success(res) {
      if (res.confirm) {
        requestAllReminders()
          .then(result => {
            if (result.accepted > 0) {
              wx.showToast({
                title: '订阅成功',
                icon: 'success'
              })
            }
          })
          .catch(err => {
            console.error('[Subscribe] 订阅失败', err)
          })
      }
    }
  })
}

/**
 * 配置模板ID（从后端获取或本地配置）
 * @param {Object} config - 配置对象
 */
function setTemplateIds(config) {
  if (config.reviewReminder) {
    TEMPLATE_IDS.REVIEW_REMINDER = config.reviewReminder
  }
  if (config.streakReminder) {
    TEMPLATE_IDS.STREAK_REMINDER = config.streakReminder
  }
  console.log('[Subscribe] 模板ID已配置', TEMPLATE_IDS)
}

module.exports = {
  requestSubscribe,
  requestReviewReminder,
  requestStreakReminder,
  requestAllReminders,
  guideSubscribe,
  setTemplateIds,
  TEMPLATE_IDS
}
