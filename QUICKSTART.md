# 快速开始指南

> 按照本指南，1-2天内完成MVP上线

## 📋 准备工作检查清单

在开始之前，确保你已经拥有：

- [ ] 腾讯云账号
- [ ] 微信小程序账号
- [ ] Python 3.10+环境
- [ ] Git工具

---

## 🚀 Phase 1: MVP上线（1-2天）

### Step 1: CloudBase环境配置（1-2小时）

#### 1.1 创建CloudBase环境

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/tcb)
2. 点击「新建环境」
3. 选择「按量计费」
4. 记录环境ID（如：`env-xxxxx`）

#### 1.2 创建数据库集合

进入「数据库」→「集合管理」，创建以下8个集合：

```
✓ users        - 用户信息
✓ content      - 学习内容
✓ progress     - 学习进度
✓ vocab        - 词汇本
✓ plans        - 学习计划
✓ orders       - 订单记录
✓ events       - 事件追踪
✓ wishlists    - 用户反馈
```

#### 1.3 配置安全规则

1. 进入「数据库」→「安全规则」
2. 复制 `cloudbase/security.rules.json` 内容
3. 粘贴并保存

#### 1.4 创建索引

参考 `cloudbase/collections.indexes.json` 创建以下关键索引：

- **vocab**: `user_id` + `next_review_at`
- **progress**: `user_id` + `contentId`
- **events**: `user_id` + `event` + `ts`

---

### Step 2: 环境变量配置（30分钟）

#### 2.1 复制配置模板

```bash
cd backend
cp .env.example .env
```

#### 2.2 填写必需配置

编辑 `.env` 文件：

```bash
# CloudBase配置
REPO_PROVIDER=tcb
TCB_ENV_ID=env-xxxxx           # 步骤1.1获取的环境ID
TCB_SECRET_ID=AKID...          # 腾讯云API密钥
TCB_SECRET_KEY=...             # 腾讯云API密钥
TCB_REGION=ap-guangzhou        # 根据实际选择

# 微信配置
WECHAT_APPID=wx...             # 小程序AppID
WECHAT_SECRET=...              # 小程序Secret
WECHAT_AUTH_ENABLED=true
```

#### 2.3 验证配置

```bash
python scripts/setup_cloudbase.py --check
```

如果看到所有 ✅，配置成功！

---

### Step 3: 微信订阅消息配置（1-2小时）

#### 3.1 申请模板

1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 进入「功能」→「订阅消息」
3. 申请以下模板：

**复习提醒模板：**
```
{{thing1.DATA}}
今日待复习：{{number2.DATA}}个词汇
{{thing3.DATA}}
```

**打卡提醒模板：**
```
{{thing1.DATA}}
当前连击：{{number2.DATA}}天
{{thing3.DATA}}
```

#### 3.2 配置模板ID

将获取的模板ID填入 `.env`：

```bash
WECHAT_TEMPLATE_REVIEW=模板ID1
WECHAT_TEMPLATE_STREAK=模板ID2
```

#### 3.3 前端集成（可选）

如果需要订阅功能，在小程序中添加：

```javascript
// 引入订阅工具
const { guideSubscribe } = require('../../utils/subscribe')

// 在适当时机调用
guideSubscribe('lesson_complete')  // 完成学习后
```

---

### Step 4: 后端部署（1小时）

#### 4.1 安装依赖

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 4.2 运行测试

```bash
pytest tests/ -v
```

确保所有40个测试通过 ✅

#### 4.3 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 4.4 验证健康检查

打开浏览器访问：
- http://localhost:8000/health
- http://localhost:8000/health/detailed

---

### Step 5: 前端部署（1小时）

#### 5.1 配置小程序AppID

编辑 `miniprogram/project.config.json`：

```json
{
  "appid": "你的小程序AppID",
  "projectname": "language-learning"
}
```

#### 5.2 配置后端API地址

编辑 `miniprogram/services/request.js`：

```javascript
const baseURL = 'https://your-backend-api.com'  // 替换为实际地址
```

#### 5.3 上传代码

1. 使用微信开发者工具打开 `miniprogram` 目录
2. 点击「上传」
3. 填写版本号和备注

#### 5.4 提交审核

1. 登录微信公众平台
2. 进入「版本管理」
3. 提交审核

---

### Step 6: 灰度发布（30分钟）

#### 6.1 设置灰度

审核通过后：
1. 进入「版本管理」→「灰度发布」
2. 设置灰度比例：10%
3. 发布

#### 6.2 监控指标

关注以下指标：
- 错误率
- 响应时间
- 用户反馈

#### 6.3 逐步放量

如果一切正常：
- 第1天：10% → 30%
- 第2天：30% → 50%
- 第3天：50% → 100%

---

## 🔍 快速验证脚本

### 一键检查所有配置

```bash
cd backend
bash scripts/deployment_check.sh
```

这个脚本会自动检查：
- ✓ Python环境
- ✓ 虚拟环境
- ✓ 依赖安装
- ✓ 测试通过
- ✓ 环境变量配置
- ✓ CloudBase连接
- ✓ 数据库集合

---

## 🐛 常见问题

### 问题1：CloudBase连接失败

**可能原因**：
- 密钥配置错误
- 环境ID不存在
- 网络问题

**解决方案**：
```bash
# 验证配置
python scripts/setup_cloudbase.py --verify

# 检查环境变量
env | grep TCB
```

### 问题2：测试失败

**解决方案**：
```bash
# 查看详细错误
pytest tests/ -v -s

# 单独运行失败的测试
pytest tests/test_xxx.py::test_func -v
```

### 问题3：小程序审核不通过

**常见原因**：
- 缺少隐私政策
- 功能描述不清
- 涉及敏感内容

**解决方案**：
- 添加隐私政策页面
- 完善功能说明文档
- 按审核意见修改

---

## 📞 获取帮助

### 技术文档

- [CloudBase配置详细指南](backend/TCB_SETUP.md)
- [微信订阅消息配置](backend/WECHAT_TEMPLATE_SETUP.md)
- [音频资源配置方案](AUDIO_SETUP.md)
- [完整路线图](ROADMAP.md)

### 验证工具

```bash
# CloudBase配置检查
python backend/scripts/setup_cloudbase.py --full

# 部署前完整检查
bash backend/scripts/deployment_check.sh
```

---

## ✅ 上线检查清单

MVP上线前，确认以下事项全部完成：

### 后端
- [ ] CloudBase环境已创建
- [ ] 8个数据库集合已创建
- [ ] 安全规则已配置
- [ ] 索引已创建
- [ ] 环境变量已配置
- [ ] 40个测试全部通过
- [ ] 健康检查接口正常

### 前端
- [ ] AppID已配置
- [ ] 后端API地址已配置
- [ ] 代码已上传
- [ ] 审核已通过
- [ ] 灰度发布已配置

### 微信配置
- [ ] 订阅消息模板已申请
- [ ] 模板ID已配置
- [ ] 定时触发器已创建（可选）

### 监控
- [ ] 日志系统正常
- [ ] 错误追踪配置
- [ ] 性能监控启用

---

## 🎉 恭喜！

完成以上步骤后，你的语言学习平台MVP已经成功上线！

**下一步计划**：

1. **收集用户反馈**（1周）
   - 关注用户留存率
   - 收集功能建议
   - 修复紧急bug

2. **完善音频资源**（1-2周）
   - 参考 [AUDIO_SETUP.md](AUDIO_SETUP.md)
   - 集成TTS服务或上传预录制音频

3. **前端体验优化**（2-3周）
   - 参考 [ROADMAP.md](ROADMAP.md) Phase 3
   - 全局状态管理
   - 组件化重构

---

**需要帮助？** 查看 [ROADMAP.md](ROADMAP.md) 获取完整开发计划
