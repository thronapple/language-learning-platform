# MVP实施启动指南

> **状态**: 🚀 已启动
> **目标**: 3周完成可演示MVP
> **当前进度**: Week 1 Day 1

---

## ✅ 已完成工作

### 1. 设计文档 (100%)
- [x] 水平评估系统设计
- [x] 场景化学习计划设计
- [x] 多端同步架构设计
- [x] 数据库重构方案
- [x] 用户旅程设计
- [x] 技术实施路线图

### 2. 数据库设计 (100%)
- [x] 12个新集合schema定义 (`cloudbase/collections.schema.json`)
- [x] 完整索引策略 (`cloudbase/collections.indexes.v2.json`)
- [x] 数据初始化脚本模板 (`scripts/init_mvp_data.py`)

### 3. 后端基础代码 (30%)
- [x] 评估领域模型 (`app/domain/assessment.py`)
- [x] 评估服务实现 (`app/services/assessment_service.py`)
  - 自适应选题算法(简化版)
  - 能力值计算(IRT简化)
  - 结果评估逻辑
- [x] 评估API路由 (`app/routes/assessment.py`)
  - POST /assessment/start
  - POST /assessment/answer
  - POST /assessment/complete
  - GET /assessment/history

---

## 📋 MVP Week 1 任务清单

### Day 1: 数据库与评估基础 ✅ (已完成)
- [x] 数据库集合设计
- [x] 评估后端核心代码
- [x] 评估API路由

### Day 2: 评估题库准备 (进行中)

**任务**:
1. **准备60道评估题**
   - A1: 10题 (词汇5 + 听力3 + 阅读2)
   - A2: 12题 (词汇4 + 听力4 + 阅读3 + 语法1)
   - B1: 15题 (听力5 + 阅读5 + 词汇3 + 语法2)
   - B2: 12题 (听力4 + 阅读4 + 语法4)
   - C1: 8题 (听力3 + 阅读3 + 语法2)
   - C2: 3题 (阅读2 + 语法1)

2. **录制/生成听力音频**
   - 使用TTS服务生成(腾讯云/Azure)
   - 或使用免费TTS工具(Google TTS/edge-tts)
   - 上传到CloudBase存储

3. **导入题库到数据库**
   - 扩展 `scripts/init_mvp_data.py`
   - 运行导入脚本

**输出**:
- `data/assessment_questions.json` (60题完整数据)
- 音频文件上传到对象存储
- 数据库`assessment_questions`集合有数据

**验收**:
```bash
# 连接CloudBase,验证题库
python scripts/verify_questions.py
# 预期输出: 60道题,各等级分布正确,音频URL可访问
```

---

### Day 3: 评估后端集成测试

**任务**:
1. **实现Repository层**
   ```python
   # app/repositories/assessment_repo.py
   class TCBAssessmentRepository(AssessmentRepository):
       async def create(self, assessment: Assessment) -> str:
           # 实现CloudBase插入
           pass

       async def get(self, assessment_id: str) -> Assessment:
           # 实现查询
           pass
   ```

2. **实现QuestionRepository**
   ```python
   # app/repositories/question_repo.py
   class TCBQuestionRepository(QuestionRepository):
       async def find_closest(
           self, level: str, type: str, exclude_ids: List[str]
       ) -> AssessmentQuestion:
           # 实现自适应选题查询
           pass
   ```

3. **集成测试**
   ```bash
   pytest tests/test_assessment_flow.py -v
   ```

**输出**:
- Repository层实现完成
- 单元测试通过(>80%覆盖率)
- Postman集合测试通过

**验收**:
- 可通过API完成完整评估流程
- 10题自适应选题正确
- 能力值计算合理

---

### Day 4: 评估前端页面 (引导+答题)

**任务**:
1. **创建评估引导页** (`miniprogram/pages/assessment/intro`)
   ```xml
   <!-- intro.wxml -->
   <view class="assessment-intro">
     <text class="title">快速评估您的语言水平</text>
     <view class="features">...</view>
     <button bindtap="startAssessment">开始评估</button>
   </view>
   ```

2. **创建答题页** (`miniprogram/pages/assessment/test`)
   - 进度条组件
   - 题目展示(支持听力/阅读/词汇/语法)
   - 选项选择
   - 倒计时
   - 音频播放器(听力题)

3. **服务层封装**
   ```typescript
   // services/assessment.ts
   class AssessmentService {
     async startAssessment(): Promise<Assessment>
     async submitAnswer(questionId, answerIndex): Promise<NextQuestion>
   }
   ```

**输出**:
- 2个页面可用(intro + test)
- 音频播放流畅
- 交互顺畅

**验收**:
- 真机测试完成10题<10分钟
- 音频无卡顿
- 选项点击响应<100ms

---

### Day 5: 评估结果页 + 集成测试

**任务**:
1. **创建结果页** (`miniprogram/pages/assessment/result`)
   - 等级徽章动画
   - 雷达图(Canvas绘制)
   - 维度详情列表
   - 薄弱环节提示
   - CTA按钮"生成学习计划"

2. **端到端测试**
   - 完整评估流程测试
   - 不同等级结果测试
   - 边界条件测试

3. **性能优化**
   - 接口响应时间优化
   - 页面加载优化
   - 音频预加载

**输出**:
- 评估完整流程可用
- 结果页视觉效果符合设计
- 性能达标

**验收**:
- 从引导→答题→结果全流程<12分钟
- 结果准确性人工验证
- 无阻塞性bug

---

## 📊 Week 1 验收标准

### 功能完整性
- [ ] 评估流程完整(引导→10题→结果)
- [ ] 自适应选题正确
- [ ] 能力值计算合理
- [ ] 结果页展示清晰

### 性能指标
- [ ] 评估完成时间 < 12分钟
- [ ] API响应时间 < 300ms
- [ ] 页面加载时间 < 2秒
- [ ] 音频播放流畅无卡顿

### 质量指标
- [ ] 后端单元测试覆盖率 > 80%
- [ ] 无P0/P1级bug
- [ ] 代码通过Lint检查

---

## 🚀 下一步 (Week 2)

### Day 6-8: 场景内容准备
- 编写3个核心场景(机场/酒店/商务会议)
- 每个场景3个对话(A2/B1/B2)
- 录制/生成音频
- 准备词汇库(~80词)
- 导入数据库

### Day 9-10: 场景后端API
- 实现场景管理API
- 实现对话查询API
- 实现词汇API
- 实现场景进度追踪

---

## 🛠️ 开发环境设置

### 后端环境
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env.dev
# 编辑 .env.dev,填入CloudBase凭证

# 运行开发服务器
uvicorn app.main:app --reload --port 8000
```

### 前端环境
```bash
# 安装微信开发者工具
# 导入项目: miniprogram/

# 配置AppID (project.config.json)
# 启动项目
```

### 数据库初始化
```bash
# 创建CloudBase环境(腾讯云控制台)
# 记录环境ID

# 初始化集合
python scripts/create_collections.py --env dev

# 导入初始数据
python scripts/init_mvp_data.py --env dev
```

---

## 📞 问题与支持

### 技术问题
- 查看设计文档: `docs/ASSESSMENT_DESIGN.md`
- 查看API文档: `docs/openapi.yaml`
- 查看实施路线: `docs/IMPLEMENTATION_ROADMAP.md`

### 进度跟踪
- 使用TodoWrite工具更新进度
- 每日站会同步问题
- 周五演示当周成果

---

## 📈 成功指标

### Week 1 目标
- ✅ 评估系统可用
- ✅ 10人内测无阻塞bug
- ✅ 评估准确性验证通过

### Week 3 目标 (MVP)
- 50+用户测试
- D1留存 > 30%
- 核心流程完整可演示

---

**当前状态**: 🟢 进展顺利
**下一个里程碑**: Day 2 完成60题题库准备
**预计完成时间**: 2025-10-05

**Let's build! 🚀**
