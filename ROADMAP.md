# 语言学习平台后续计划

> 更新时间：2025-10-02
> 当前状态：测试全部通过，准备上线阶段

## 📊 项目当前状态

### ✅ 已完成

- **后端核心功能**
  - [x] 40个单元测试全部通过
  - [x] 认证系统（微信小程序授权）
  - [x] 内容管理（句子/对话/单词）
  - [x] 词汇管理（SRS间隔重复算法）
  - [x] 学习进度追踪
  - [x] 导入/导出功能
  - [x] 速率限制保护
  - [x] 订阅消息基础设施
  - [x] CloudBase/TCB集成代码
  - [x] 异常处理和监控

- **文档完整性**
  - [x] CloudBase配置指南
  - [x] 微信订阅消息指南
  - [x] 音频资源配置方案
  - [x] P0问题处理总结

### ⚠️ 待处理

- **生产环境配置** - 阻塞上线
- **音频资源准备** - 阻塞完整体验
- **前端体验优化** - 影响留存率

---

## 🎯 上线路线图

### Phase 1: MVP上线（1-2天）🔥

**目标**：灰度发布可用产品，验证核心功能

#### 1.1 CloudBase环境配置 ⏱️ 1-2小时

**参考文档**：`backend/TCB_SETUP.md`

```bash
# 1. 创建CloudBase环境
- 登录腾讯云控制台
- 创建CloudBase环境（按量计费）
- 记录环境ID

# 2. 创建数据库集合
- users
- content
- progress
- vocab
- plans
- orders
- events
- wishlists

# 3. 配置安全规则
- 上传 cloudbase/security.rules.json
- 验证读写权限

# 4. 创建索引
- 按照 cloudbase/collections.indexes.json 配置
- 关键索引：
  - vocab: user_id + next_review_at
  - progress: user_id + contentId
  - events: user_id + event + ts
```

**验证步骤**：
```bash
python backend/scripts/verify_tcb_connection.py
```

#### 1.2 环境变量配置 ⏱️ 30分钟

```bash
# backend/.env.production
REPO_PROVIDER=tcb
TCB_ENV_ID=your-env-xxxxx
TCB_SECRET_ID=AKIDxxxxx
TCB_SECRET_KEY=xxxxx
TCB_REGION=ap-guangzhou

WECHAT_APPID=wxxxxxx
WECHAT_SECRET=xxxxx
WECHAT_AUTH_ENABLED=true

# 功能开关
IMPORT_WHITELIST=example.com,wikipedia.org
STORAGE_PROVIDER=cos  # 或 local

# 监控
ENV=production
```

#### 1.3 微信小程序配置 ⏱️ 1-2小时

**参考文档**：`backend/WECHAT_TEMPLATE_SETUP.md`

**任务清单**：
- [ ] 登录微信公众平台
- [ ] 申请订阅消息模板
  - 复习提醒模板
  - 打卡提醒模板
- [ ] 记录模板ID
- [ ] 配置环境变量
  ```bash
  WECHAT_TEMPLATE_REVIEW=模板ID1
  WECHAT_TEMPLATE_STREAK=模板ID2
  ```
- [ ] 创建CloudBase定时触发器
  - 名称：每日通知
  - Cron：`0 9,20 * * *`
  - 调用：`POST /cron/daily-digest`

**前端代码添加**（miniprogram/utils/subscribe.js）：
```javascript
// 在适当时机请求订阅
function requestSubscribe() {
  wx.requestSubscribeMessage({
    tmplIds: [
      'TEMPLATE_ID_REVIEW',
      'TEMPLATE_ID_STREAK'
    ],
    success(res) {
      console.log('订阅成功', res)
    }
  })
}

// 在完成学习、添加生词等操作后调用
module.exports = { requestSubscribe }
```

#### 1.4 音频降级方案 ⏱️ 1小时

**策略**：先上线功能，音频显示"暂无"

**前端修改**（miniprogram/pages/study/study.js）：
```javascript
// 移除测试音频URL
- const testAudioUrl = 'https://sample-videos.com/...'
- this.setData({ audioUrl: testAudioUrl })

// 改为
+ this.setData({
+   audioUrl: res.audio_url || '',
+   audioAvailable: !!res.audio_url
+ })

// UI显示
+ if (!this.data.audioAvailable) {
+   wx.showToast({
+     title: '音频资源准备中',
+     icon: 'none'
+   })
+ }
```

#### 1.5 部署验证 ⏱️ 1小时

**后端部署**：
```bash
# 1. 安装依赖
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. 运行测试
pytest tests/ -v

# 3. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. 验证健康检查
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

**前端部署**：
```bash
# 1. 配置小程序AppID
# 修改 project.config.json 中的 appid

# 2. 上传代码
# 使用微信开发者工具上传代码

# 3. 提交审核
# 在微信公众平台提交审核
```

**灰度发布**：
- [ ] 设置灰度比例：10%
- [ ] 监控错误日志
- [ ] 收集用户反馈
- [ ] 逐步提升至100%

---

### Phase 2: 音频资源完善（1周内）

**目标**：提供完整音频学习体验

**参考文档**：`AUDIO_SETUP.md`

#### 2.1 音频方案选择

**推荐方案**：CloudBase对象存储 + TTS服务

| 方案 | 成本 | 工作量 | 质量 |
|------|------|--------|------|
| 预录制 | ¥0 | 高 | 最好 |
| TTS服务 | ¥0.002/次 | 中 | 良好 |
| CloudBase存储 | ¥0.12/GB/月 | 低 | 取决于源 |

**建议**：
1. 常用内容（Top 100）→ 预录制
2. 其他内容 → 腾讯云TTS动态生成
3. 存储 → CloudBase对象存储

#### 2.2 实施步骤 ⏱️ 6-8小时

**Step 1: TTS服务集成**
```python
# backend/app/services/tts.py
from tencentcloud.tts.v20190823 import tts_client, models

class TTSService:
    def synthesize(self, text: str) -> bytes:
        # 调用腾讯云TTS
        # 返回音频数据
        pass
```

**Step 2: 批量生成音频**
```bash
# 运行脚本生成音频
python scripts/generate_audio.py \
  --limit 500 \
  --output ./audio/
```

**Step 3: 上传到CloudBase**
```bash
# 使用CloudBase CLI
cloudbase storage upload audio/ /audio/ --recursive
```

**Step 4: 更新数据库**
```python
# scripts/update_audio_urls.py
# 批量更新content表的audio_url字段
```

**Step 5: 前端恢复音频功能**
```javascript
// 移除降级逻辑
// 测试音频播放
```

#### 2.3 验收标准

- [ ] Top 100内容有音频
- [ ] 音频加载时间 < 2秒
- [ ] 播放流畅无卡顿
- [ ] CDN缓存配置正确

---

### Phase 3: 前端体验优化（2-3周）

**目标**：提升用户留存率和满意度

#### 3.1 全局状态管理 ⏱️ 4-6小时

**问题**：
- 数据在页面间重复加载
- 状态不同步
- 内存浪费

**解决方案**：实现轻量级Store

**实现**（miniprogram/store/index.js）：
```javascript
// 全局状态
const state = {
  user: null,
  settings: {},
  cachedContent: new Map(),
  audioManager: null
}

// 响应式订阅
const subscribers = new Set()

function setState(updates) {
  Object.assign(state, updates)
  subscribers.forEach(fn => fn(state))
}

function subscribe(callback) {
  subscribers.add(callback)
  return () => subscribers.delete(callback)
}

module.exports = { state, setState, subscribe }
```

**迁移重点**：
- 用户信息跨页面共享
- 学习进度全局缓存
- 音频播放器单例

#### 3.2 加载/空/错三态组件 ⏱️ 2-3小时

**创建通用组件**（miniprogram/components/state-view/）：

```javascript
// state-view.js
Component({
  properties: {
    status: String, // loading/empty/error/success
    emptyText: String,
    errorText: String
  },
  data: {
    showLoading: false,
    showEmpty: false,
    showError: false
  }
})
```

**使用示例**：
```xml
<state-view status="{{pageStatus}}" emptyText="暂无学习内容">
  <view slot="content">
    <!-- 实际内容 -->
  </view>
</state-view>
```

#### 3.3 音频服务抽象 ⏱️ 3-4小时

**创建AudioManager**（miniprogram/services/audio-manager.js）：

```javascript
class AudioManager {
  constructor() {
    this.ctx = wx.createInnerAudioContext()
    this.preloadQueue = []
    this.cache = new Map()
  }

  play(url) {
    // 播放音频
  }

  preload(url) {
    // 预加载下一句
  }

  pause() {
    // 暂停播放
  }

  destroy() {
    // 清理资源
  }
}

// 全局单例
const audioManager = new AudioManager()
module.exports = audioManager
```

**优化**：
- 预加载下一句音频
- 播放队列管理
- 错误重试机制

#### 3.4 组件化重构 ⏱️ 4-5小时

**player组件完善**：
```
miniprogram/components/player/
├── player.js
├── player.wxml
├── player.wxss
└── player.json
```

**sentence-list组件**：
```
miniprogram/components/sentence-list/
├── sentence-list.js
├── sentence-list.wxml
├── sentence-list.wxss
└── sentence-list.json
```

**解耦目标**：
- 学习页面 < 300行代码
- 组件可在多个页面复用
- 单元测试覆盖组件

#### 3.5 样式系统规范 ⏱️ 2-3小时

**创建样式规范**（miniprogram/styles/）：

```
styles/
├── variables.wxss   # 颜色、字体变量
├── mixins.wxss      # 通用样式混入
├── base.wxss        # 基础样式重置
└── utils.wxss       # 工具类
```

**重构重点**：
- 减少 `!important` 使用
- 采用BEM命名：`.block__element--modifier`
- 提取重复样式到变量

---

## 🔄 持续优化计划

### 性能优化

**后端**：
- [ ] 添加Redis缓存层
- [ ] 数据库查询优化（索引分析）
- [ ] API响应时间监控
- [ ] 实现GraphQL（按需查询）

**前端**：
- [ ] 图片懒加载
- [ ] 分包加载
- [ ] 首屏渲染优化
- [ ] 内存泄漏检测

### 功能扩展

**短期（1-2月）**：
- [ ] AI跟读评分
- [ ] 社交分享功能
- [ ] 学习报告
- [ ] 每日推荐

**中期（3-6月）**：
- [ ] 多语言支持
- [ ] 自定义学习计划
- [ ] 离线模式
- [ ] 小组学习

**长期（6-12月）**：
- [ ] 语音识别纠音
- [ ] AR/VR场景学习
- [ ] 真人教师对接
- [ ] 企业版定制

### 商业化

**付费功能**：
- [ ] 高级学习计划
- [ ] 无限词汇量
- [ ] 专属内容库
- [ ] 数据分析报告

**运营指标**：
- DAU/MAU目标
- 留存率跟踪
- 付费转化率
- NPS评分

---

## 📋 检查清单

### 上线前（Phase 1）

- [ ] CloudBase环境配置完成
- [ ] 数据库集合创建
- [ ] 安全规则上传
- [ ] 索引创建完成
- [ ] 环境变量配置
- [ ] 微信订阅消息申请
- [ ] 定时任务配置
- [ ] 前端音频降级
- [ ] 后端测试通过
- [ ] 前端提审通过
- [ ] 灰度发布启用

### 音频完善（Phase 2）

- [ ] TTS服务集成
- [ ] Top 100音频生成
- [ ] 音频上传存储
- [ ] 数据库URL更新
- [ ] 前端音频测试
- [ ] CDN缓存验证

### 体验优化（Phase 3）

- [ ] 全局状态管理
- [ ] 三态组件完成
- [ ] AudioManager封装
- [ ] player组件独立
- [ ] sentence-list组件
- [ ] 样式规范应用
- [ ] 代码审查通过

---

## 🚨 风险与应对

### 技术风险

| 风险 | 影响 | 概率 | 应对方案 |
|------|------|------|----------|
| CloudBase服务不稳定 | 高 | 低 | 备份方案：阿里云/AWS |
| TTS配额超限 | 中 | 中 | 混合方案：预录制+TTS |
| 小程序审核不通过 | 高 | 中 | 准备合规说明文档 |
| 音频加载慢 | 中 | 中 | CDN加速+预加载 |

### 业务风险

| 风险 | 影响 | 概率 | 应对方案 |
|------|------|------|----------|
| 用户留存低 | 高 | 中 | 提升内容质量和交互 |
| 付费转化低 | 中 | 高 | 优化免费体验，明确价值 |
| 运营成本高 | 中 | 低 | 优化资源使用，按量计费 |

---

## 📞 支持与文档

### 技术文档

- `backend/TCB_SETUP.md` - CloudBase配置
- `backend/WECHAT_TEMPLATE_SETUP.md` - 微信订阅消息
- `AUDIO_SETUP.md` - 音频资源方案
- `P0_IMPLEMENTATION_SUMMARY.md` - P0问题总结
- `TESTING.md` - 测试说明

### 运维文档

- [ ] 部署流程文档（待补充）
- [ ] 监控告警配置（待补充）
- [ ] 数据备份策略（待补充）
- [ ] 应急预案（待补充）

### 开发规范

- [ ] 代码风格指南（待补充）
- [ ] Git提交规范（待补充）
- [ ] API设计规范（待补充）
- [ ] 数据库设计规范（待补充）

---

## 🎉 里程碑

- **2025-10-02** - 测试全部通过 ✅
- **2025-10-04** - 预计MVP上线 🎯
- **2025-10-11** - 预计音频完善 🎯
- **2025-10-25** - 预计体验优化完成 🎯
- **2025-11-01** - 预计正式版发布 🎯

---

**注意事项**：
1. 所有密钥严格保密，不提交到代码仓库
2. 生产环境定期备份数据库
3. 监控日志和错误，及时响应
4. 保持文档更新，记录重要决策
5. 定期code review，保证代码质量

**下一步行动**：根据Phase 1清单，开始配置CloudBase环境 🚀
