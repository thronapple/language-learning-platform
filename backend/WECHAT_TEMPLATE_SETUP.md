# 微信订阅消息配置指南

## 概述

本项目使用微信小程序订阅消息功能发送以下通知：
- **复习提醒**：提醒用户今日有待复习的词汇
- **打卡提醒**：提醒用户保持学习连击

## 前置要求

1. 已注册并通过审核的微信小程序
2. 小程序AppID和AppSecret
3. 订阅消息功能已开通

## 配置步骤

### 1. 获取模板ID

1. 登录[微信公众平台](https://mp.weixin.qq.com/)
2. 进入「功能」->「订阅消息」
3. 选择或创建以下模板：

#### 复习提醒模板

**模板内容建议：**
```
{{thing1.DATA}}
今日待复习：{{number2.DATA}}个词汇
{{thing3.DATA}}
```

**参数说明：**
- `thing1`: 提醒类型（如：词汇复习提醒）
- `number2`: 待复习词汇数量
- `thing3`: 提示文案（如：点击查看今日待复习词汇）

#### 打卡提醒模板

**模板内容建议：**
```
{{thing1.DATA}}
当前连击：{{number2.DATA}}天
{{thing3.DATA}}
```

**参数说明：**
- `thing1`: 提醒类型（如：学习打卡提醒）
- `number2`: 当前连击天数
- `thing3`: 提示文案（如：继续保持连续学习记录）

### 2. 配置环境变量

在后端配置以下环境变量：

```bash
# 微信小程序配置
export WECHAT_APPID=your-appid
export WECHAT_SECRET=your-app-secret

# 模板ID配置
export WECHAT_TEMPLATE_REVIEW=模板ID1  # 复习提醒模板
export WECHAT_TEMPLATE_STREAK=模板ID2  # 打卡提醒模板
```

### 3. 前端订阅授权

在小程序端需要用户授权订阅消息，参考代码：

```javascript
// miniprogram/utils/subscribe.js
function requestSubscribe(templateIds) {
  return new Promise((resolve, reject) => {
    wx.requestSubscribeMessage({
      tmplIds: templateIds,
      success(res) {
        console.log('订阅成功', res)
        resolve(res)
      },
      fail(err) {
        console.error('订阅失败', err)
        reject(err)
      }
    })
  })
}

// 使用示例
// 在适当时机（如完成学习、添加生词等）请求订阅
requestSubscribe([
  'TEMPLATE_ID_REVIEW',  // 复习提醒
  'TEMPLATE_ID_STREAK'   // 打卡提醒
])
```

### 4. 定时任务配置

使用CloudBase定时触发器或服务器cron job：

#### CloudBase定时触发器

1. 登录CloudBase控制台
2. 创建云函数 `dailyDigest`
3. 配置定时触发器：
   - **名称**：每日通知
   - **触发周期**：`0 9,20 * * *`（每天9:00和20:00）
   - **触发配置**：`{}`

云函数代码示例：

```javascript
// cloudbase/functions/dailyDigest/index.js
const cloud = require('wx-server-sdk')
cloud.init()

exports.main = async (event, context) => {
  // 调用后端API
  const result = await cloud.callFunction({
    name: 'httpapi',
    data: {
      path: '/cron/daily-digest',
      method: 'POST',
      data: { dryRun: false }
    }
  })

  return result
}
```

#### 服务器Cron Job

在服务器上配置crontab：

```bash
# 每天9:00和20:00执行
0 9,20 * * * curl -X POST https://your-api.com/cron/daily-digest
```

## API接口

### POST /cron/daily-digest

发送每日摘要通知。

**请求参数：**
```json
{
  "dryRun": false  // true时仅测试不实际发送
}
```

**响应：**
```json
{
  "review_reminders": 15,   // 发送的复习提醒数
  "streak_reminders": 8,    // 发送的打卡提醒数
  "errors": 0               // 错误数量
}
```

## 测试

### 本地测试

```bash
# 设置环境变量
export WECHAT_APPID=your-appid
export WECHAT_SECRET=your-secret
export WECHAT_TEMPLATE_REVIEW=template-id-1
export WECHAT_TEMPLATE_STREAK=template-id-2

# 测试运行（dryRun模式）
curl -X POST http://localhost:8000/cron/daily-digest \
  -H "Content-Type: application/json" \
  -d '{"dryRun": true}'
```

### 验证消息发送

1. 确保测试用户已订阅消息
2. 在CloudBase数据库添加测试数据：
   - 添加到期词汇到 `vocab` 集合
   - 添加用户进度到 `progress` 集合
3. 触发定时任务或手动调用API
4. 检查用户微信消息通知

## 注意事项

### 1. 订阅消息限制

- ⚠️ 用户必须手动订阅才能接收消息
- 📅 每次订阅仅可发送一次，需重新订阅
- 🔄 建议在关键操作后引导用户订阅（完成学习、添加生词等）

### 2. 模板内容规范

- 📝 遵守微信平台内容规范
- 🚫 禁止营销推广内容
- ✅ 仅发送与用户操作相关的服务通知

### 3. 频率控制

- ⏰ 每天最多发送2次（早/晚）
- 🎯 仅对有需要的用户发送（有到期词汇/连击≥3天）
- 🛡️ 实现退订机制（用户可关闭通知）

### 4. 错误处理

常见错误码：

| 错误码 | 说明 | 解决方案 |
|-------|------|---------|
| 43101 | 用户拒绝接受消息 | 正常情况，记录日志 |
| 43104 | 订阅关系已过期 | 引导用户重新订阅 |
| 47003 | 模板参数不正确 | 检查模板格式 |
| 40037 | 模板ID不正确 | 确认模板ID配置 |

## 监控与优化

### 关键指标

- 📊 消息发送成功率
- 👥 用户订阅率
- 📈 消息点击率（通过page参数追踪）
- ⏱️ 发送耗时

### 优化建议

1. **批量发送**：将消息分批处理，避免API限流
2. **重试机制**：对失败消息实现指数退避重试
3. **用户偏好**：允许用户设置通知时间偏好
4. **A/B测试**：测试不同文案的点击率

## 成本估算

- 订阅消息：**免费**（微信官方提供）
- API调用：按CloudBase/服务器资源计费
- 预估：1000用户/天 < ¥10/月

## 故障排查

### 消息未收到

1. 确认用户已订阅该模板
2. 检查access_token是否有效
3. 验证模板ID是否正确
4. 查看后端日志错误信息

### Access Token失效

- Token自动刷新机制已实现
- 缓存有效期7200秒，提前5分钟刷新
- 如持续失败，检查AppID/AppSecret配置

### 数据查询为空

- 确认数据库集合已创建
- 检查数据库索引（next_review_at, user_id）
- 验证查询过滤条件

## 相关文档

- [微信订阅消息官方文档](https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/subscribe-message.html)
- [消息模板管理](https://mp.weixin.qq.com/)
- [CloudBase定时触发器](https://cloud.tencent.com/document/product/876/32314)
