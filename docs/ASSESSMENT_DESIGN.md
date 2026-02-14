# 水平评估系统设计方案

## 一、设计目标

为短期突击学习用户提供**快速、精准的语言水平评估**,避免:
- ❌ "从零开始"的挫败感
- ❌ "太简单"的时间浪费
- ✅ 5-10分钟完成评估
- ✅ 精准定位当前水平(A1-C2)
- ✅ 识别薄弱环节(听/说/读/写/词汇/语法)

---

## 二、评估维度与分级

### 2.1 欧标CEFR映射

| 等级 | 描述 | 词汇量 | 典型场景 |
|------|------|--------|----------|
| **A1** | 入门级 | 500-1000 | 打招呼/点餐 |
| **A2** | 初级 | 1000-2000 | 购物/问路 |
| **B1** | 中级 | 2000-4000 | 工作会议/旅游 |
| **B2** | 中高级 | 4000-6000 | 商务谈判/学术讨论 |
| **C1** | 高级 | 6000-8000 | 专业领域交流 |
| **C2** | 精通 | 8000+ | 母语水平 |

### 2.2 能力维度细分

```json
{
  "dimensions": {
    "listening": { "weight": 0.25, "测试类型": "音频理解" },
    "speaking": { "weight": 0.20, "测试类型": "跟读评分" },
    "reading": { "weight": 0.25, "测试类型": "阅读理解" },
    "writing": { "weight": 0.15, "测试类型": "填空/语法" },
    "vocabulary": { "weight": 0.15, "测试类型": "词汇选择" }
  }
}
```

---

## 三、自适应测试算法 (CAT - Computerized Adaptive Testing)

### 3.1 核心流程

```
开始 → 中等难度题(B1)
  ↓
  答对 → 提高难度(B2) ──┐
  答错 → 降低难度(A2) ──┤
                        ↓
                   达到收敛条件?
                        ↓
                   输出评估结果
```

### 3.2 题库结构

```json
{
  "question": {
    "id": "q_listen_b1_001",
    "type": "listening",
    "level": "B1",
    "difficulty": 0.65,  // IRT难度参数
    "content": {
      "audio_url": "https://cdn.../airport_checkin.mp3",
      "question": "What gate does the passenger need?",
      "options": ["Gate 12", "Gate 20", "Gate 22", "Gate 32"],
      "correct": 2,
      "time_limit": 30
    },
    "metadata": {
      "scenario": "airport",
      "skill": "detail_understanding"
    }
  }
}
```

### 3.3 自适应规则

**IRT模型 (Item Response Theory)**

```python
# 能力估计公式
P(correct | ability, difficulty) = 1 / (1 + e^(-(ability - difficulty)))

# 收敛条件
if std_error(ability_estimate) < 0.3 or questions_answered >= 12:
    return final_level
```

**实现伪码**
```python
class AdaptiveAssessment:
    def __init__(self):
        self.ability_estimate = 0  # B1对应0
        self.std_error = 1.0
        self.questions_asked = []

    def select_next_question(self):
        # 选择信息量最大的题目(难度接近当前能力估计)
        target_difficulty = self.ability_estimate
        return question_pool.find_closest(target_difficulty)

    def update_ability(self, question_id, is_correct):
        # 贝叶斯更新能力估计
        difficulty = question_pool[question_id].difficulty
        if is_correct:
            self.ability_estimate += 0.2 * (1 - sigmoid(self.ability_estimate - difficulty))
        else:
            self.ability_estimate -= 0.2 * sigmoid(self.ability_estimate - difficulty)

        # 更新标准误差
        self.std_error = calculate_std_error(self.questions_asked)
```

---

## 四、MVP实现方案(简化版)

### 4.1 快速评估流程(10题完成)

**题型配置**
```json
{
  "assessment_config": {
    "total_questions": 10,
    "breakdown": {
      "vocabulary": 3,  // 词汇选择(快速判断基础)
      "listening": 3,   // 音频理解
      "reading": 2,     // 短文阅读
      "grammar": 2      // 语法填空
    },
    "time_limit": 600,  // 10分钟
    "adaptive": true
  }
}
```

**简化自适应逻辑**
```python
# MVP版本: 3档难度快速定位
def simple_adaptive_test():
    # 第1-3题: 混合难度(A2/B1/B2)
    initial_score = test_questions([
        {"level": "A2", "weight": 1},
        {"level": "B1", "weight": 1},
        {"level": "B2", "weight": 1}
    ])

    # 根据初始得分选择后续难度
    if initial_score >= 2:
        difficulty_range = ["B1", "B2", "C1"]
    elif initial_score >= 1:
        difficulty_range = ["A2", "B1", "B2"]
    else:
        difficulty_range = ["A1", "A2", "B1"]

    # 第4-10题: 在选定范围内测试
    return test_questions_from_range(difficulty_range, count=7)
```

### 4.2 数据库设计

**新增集合: `assessments`**
```json
{
  "_id": "assess_user123_20251003",
  "user_id": "openid_123",
  "started_at": "2025-10-03T10:00:00Z",
  "completed_at": "2025-10-03T10:09:30Z",
  "duration_secs": 570,

  "results": {
    "overall_level": "B1",
    "ability_score": 0.15,  // IRT能力值
    "confidence": 0.85,     // 评估置信度

    "dimensions": {
      "listening": { "level": "B2", "accuracy": 0.83 },
      "reading": { "level": "B1", "accuracy": 0.75 },
      "vocabulary": { "level": "B1", "accuracy": 0.67 },
      "grammar": { "level": "A2", "accuracy": 0.50 }
    },

    "weak_areas": ["grammar", "vocabulary"],
    "strong_areas": ["listening"]
  },

  "questions": [
    {
      "q_id": "q_vocab_b1_001",
      "type": "vocabulary",
      "level": "B1",
      "is_correct": true,
      "time_spent": 12,
      "answer_selected": 2
    }
  ],

  "recommendations": {
    "suggested_scenario": "business_trip",
    "focus_areas": ["grammar_basics", "business_vocabulary"],
    "estimated_study_days": 14
  }
}
```

**新增集合: `assessment_questions`**
```json
{
  "_id": "q_listen_b1_airport_001",
  "type": "listening",
  "level": "B1",
  "difficulty": 0.65,
  "scenario": "airport",

  "content": {
    "audio_url": "https://cdn.../airport_checkin.mp3",
    "duration": 25,
    "transcript": "Excuse me, which gate is the flight to London?",

    "question": "What information does the passenger need?",
    "options": [
      "Boarding time",
      "Gate number",
      "Seat number",
      "Baggage claim"
    ],
    "correct_index": 1
  },

  "metadata": {
    "skill": "detail_listening",
    "vocab_level": "A2",
    "grammar_points": ["question_formation"],
    "usage_count": 1234,
    "avg_accuracy": 0.72
  }
}
```

---

## 五、前端交互设计

### 5.1 评估流程页面

**页面1: 引导页 (`pages/assessment/intro`)**
```xml
<view class="assessment-intro">
  <text class="title">快速评估您的语言水平</text>
  <text class="subtitle">10道题 · 预计10分钟</text>

  <view class="features">
    <view class="feature-item">
      <icon type="success"/>
      <text>精准定位当前水平</text>
    </view>
    <view class="feature-item">
      <icon type="success"/>
      <text>识别薄弱环节</text>
    </view>
    <view class="feature-item">
      <icon type="success"/>
      <text>定制学习计划</text>
    </view>
  </view>

  <button bindtap="startAssessment">开始评估</button>
  <text class="skip" bindtap="skipAssessment">暂时跳过</text>
</view>
```

**页面2: 答题页 (`pages/assessment/test`)**
```xml
<view class="assessment-test">
  <!-- 进度条 -->
  <view class="progress">
    <text>{{currentQuestion}}/{{totalQuestions}}</text>
    <progress percent="{{progress}}" />
  </view>

  <!-- 题目内容 -->
  <view class="question-content">
    <!-- 听力题: 音频播放器 -->
    <audio wx:if="{{questionType === 'listening'}}"
           src="{{audioUrl}}"
           controls />

    <!-- 阅读题: 文本内容 -->
    <text wx:if="{{questionType === 'reading'}}"
          class="passage">{{passage}}</text>

    <!-- 问题 -->
    <text class="question">{{question}}</text>

    <!-- 选项 -->
    <view class="options">
      <button wx:for="{{options}}"
              wx:key="index"
              class="option {{selectedIndex === index ? 'selected' : ''}}"
              bindtap="selectOption"
              data-index="{{index}}">
        {{item}}
      </button>
    </view>
  </view>

  <!-- 倒计时 -->
  <view class="timer">
    <text>剩余时间: {{timeLeft}}秒</text>
  </view>

  <button bindtap="nextQuestion" disabled="{{selectedIndex === null}}">
    {{isLastQuestion ? '完成评估' : '下一题'}}
  </button>
</view>
```

**页面3: 结果页 (`pages/assessment/result`)**
```xml
<view class="assessment-result">
  <!-- 等级徽章 -->
  <view class="level-badge">
    <image src="/images/badges/{{level}}.png" />
    <text class="level">{{level}}</text>
    <text class="level-desc">{{levelDescription}}</text>
  </view>

  <!-- 维度雷达图 -->
  <canvas canvas-id="radarChart" class="radar-chart"></canvas>

  <!-- 详细结果 -->
  <view class="dimension-details">
    <view wx:for="{{dimensions}}" wx:key="name" class="dimension-item">
      <text class="dimension-name">{{item.name}}</text>
      <progress percent="{{item.score * 100}}" />
      <text class="dimension-level">{{item.level}}</text>
    </view>
  </view>

  <!-- 薄弱环节 -->
  <view class="weak-areas">
    <text class="section-title">建议加强</text>
    <view wx:for="{{weakAreas}}" class="weak-item">
      <icon type="warn" />
      <text>{{item}}</text>
    </view>
  </view>

  <!-- CTA按钮 -->
  <button type="primary" bindtap="generatePlan">
    生成专属学习计划
  </button>
</view>
```

### 5.2 服务层实现

**`services/assessment.ts`**
```typescript
class AssessmentService {
  private currentAssessment: Assessment | null = null;
  private startTime: number = 0;

  async startAssessment(): Promise<void> {
    const res = await request.post('/assessment/start');
    this.currentAssessment = res.data;
    this.startTime = Date.now();
  }

  async getNextQuestion(): Promise<Question> {
    return await request.get('/assessment/question', {
      params: {
        assessment_id: this.currentAssessment.id,
        answered_count: this.currentAssessment.questions.length
      }
    });
  }

  async submitAnswer(questionId: string, answerIndex: number): Promise<void> {
    await request.post('/assessment/answer', {
      assessment_id: this.currentAssessment.id,
      question_id: questionId,
      answer_index: answerIndex,
      time_spent: Date.now() - this.startTime
    });
  }

  async completeAssessment(): Promise<AssessmentResult> {
    const res = await request.post('/assessment/complete', {
      assessment_id: this.currentAssessment.id
    });
    return res.data;
  }
}
```

---

## 六、后端实现

### 6.1 云函数/API接口

**`POST /assessment/start`**
```python
@router.post("/assessment/start")
async def start_assessment(
    user: User = Depends(get_current_user)
) -> AssessmentStartResponse:
    """初始化评估会话"""
    assessment = Assessment(
        user_id=user.openid,
        started_at=datetime.now(),
        status="in_progress"
    )
    await assessment_repo.create(assessment)

    # 返回第一题(中等难度)
    first_question = await question_repo.get_by_level_and_type(
        level="B1",
        type="vocabulary"
    )

    return {
        "assessment_id": assessment.id,
        "first_question": first_question.to_dict()
    }
```

**`POST /assessment/answer`**
```python
@router.post("/assessment/answer")
async def submit_answer(
    payload: AnswerSubmission,
    user: User = Depends(get_current_user)
) -> NextQuestionResponse:
    """提交答案并获取下一题"""
    # 验证答案
    question = await question_repo.get(payload.question_id)
    is_correct = (payload.answer_index == question.correct_index)

    # 更新评估记录
    assessment = await assessment_repo.get(payload.assessment_id)
    assessment.questions.append({
        "q_id": payload.question_id,
        "is_correct": is_correct,
        "time_spent": payload.time_spent
    })

    # 自适应选择下一题
    next_question = await adaptive_selector.select_next(
        assessment=assessment,
        last_result=is_correct
    )

    await assessment_repo.update(assessment)

    return {
        "is_correct": is_correct,
        "next_question": next_question.to_dict() if next_question else None
    }
```

**`POST /assessment/complete`**
```python
@router.post("/assessment/complete")
async def complete_assessment(
    payload: CompleteAssessmentPayload,
    user: User = Depends(get_current_user)
) -> AssessmentResult:
    """完成评估并计算结果"""
    assessment = await assessment_repo.get(payload.assessment_id)

    # 计算能力值和等级
    evaluator = AssessmentEvaluator(assessment)
    result = evaluator.calculate_result()

    # 更新记录
    assessment.completed_at = datetime.now()
    assessment.results = result
    await assessment_repo.update(assessment)

    # 触发埋点
    await event_bus.track("assessment_completed", {
        "user_id": user.openid,
        "level": result.overall_level,
        "duration": assessment.duration_secs
    })

    return result
```

### 6.2 自适应算法实现

**`services/adaptive_selector.py`**
```python
class AdaptiveQuestionSelector:
    def __init__(self, question_repo: QuestionRepository):
        self.question_repo = question_repo
        self.level_map = {
            "A1": -2.0, "A2": -1.0, "B1": 0.0,
            "B2": 1.0, "C1": 2.0, "C2": 3.0
        }

    async def select_next(
        self,
        assessment: Assessment,
        last_result: bool
    ) -> Question | None:
        """自适应选择下一题"""
        if len(assessment.questions) >= 10:
            return None  # 达到题目上限

        # 计算当前能力估计
        ability = self._estimate_ability(assessment.questions)

        # 根据上一题结果微调
        if last_result:
            ability += 0.3
        else:
            ability -= 0.3

        # 映射到CEFR等级
        target_level = self._ability_to_level(ability)

        # 选择题型(保证多样性)
        answered_types = [q["type"] for q in assessment.questions]
        next_type = self._select_diverse_type(answered_types)

        # 从题库选择
        question = await self.question_repo.find_closest(
            level=target_level,
            type=next_type,
            exclude_ids=[q["q_id"] for q in assessment.questions]
        )

        return question

    def _estimate_ability(self, questions: list) -> float:
        """基于IRT模型估计能力值"""
        if not questions:
            return 0.0  # B1初始值

        correct_count = sum(1 for q in questions if q["is_correct"])
        total_count = len(questions)
        accuracy = correct_count / total_count

        # 简化IRT: 正确率映射到能力值
        ability = (accuracy - 0.5) * 4  # -2.0 到 2.0
        return ability

    def _ability_to_level(self, ability: float) -> str:
        """能力值映射到CEFR等级"""
        for level, threshold in sorted(
            self.level_map.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if ability >= threshold:
                return level
        return "A1"

    def _select_diverse_type(self, answered_types: list) -> str:
        """选择题型以保证多样性"""
        type_counts = {
            "vocabulary": answered_types.count("vocabulary"),
            "listening": answered_types.count("listening"),
            "reading": answered_types.count("reading"),
            "grammar": answered_types.count("grammar")
        }
        # 返回出现次数最少的题型
        return min(type_counts, key=type_counts.get)
```

---

## 七、题库准备策略

### 7.1 初期题库规模

**MVP最小题库**
```
总题数: 60题
├── A1: 10题
├── A2: 12题
├── B1: 15题
├── B2: 12题
├── C1: 8题
└── C2: 3题

题型分布(每个等级):
├── vocabulary: 30%
├── listening: 30%
├── reading: 25%
└── grammar: 15%
```

### 7.2 题目来源

**方案1: 手工精选(推荐MVP)**
- 从现有教材/考试真题改编
- 确保版权合规
- 质量可控
- 预计工作量: 1周(2人)

**方案2: 外部API**
- 对接第三方题库API(如词典API)
- 快速但需付费
- 需要二次标注难度

**方案3: AI生成+人工校验**
- 使用GPT-4生成题目
- 人工审核和难度标注
- 成本适中、速度快

### 7.3 题目标注工具

**内部管理后台 (`admin/questions`)**
```
功能需求:
- 题目CRUD
- 批量导入(CSV/JSON)
- 难度校准(根据用户答题数据)
- 预览和测试
```

---

## 八、数据分析与优化

### 8.1 题目质量指标

```python
# 每日定时任务: 计算题目质量
@cron("0 2 * * *")  # 每天凌晨2点
async def calibrate_questions():
    """校准题目难度"""
    questions = await question_repo.get_all()

    for question in questions:
        # 获取最近100次答题记录
        answers = await assessment_repo.get_answers(
            question_id=question.id,
            limit=100
        )

        if len(answers) < 30:
            continue  # 样本不足

        # 计算实际难度
        accuracy = sum(a.is_correct for a in answers) / len(answers)
        actual_difficulty = 1 - accuracy

        # 更新难度参数
        question.difficulty = actual_difficulty
        question.metadata.usage_count = len(answers)
        question.metadata.avg_accuracy = accuracy

        await question_repo.update(question)
```

### 8.2 评估准确性验证

**A/B测试框架**
```python
# 对比不同自适应算法的效果
class AssessmentABTest:
    async def run_experiment(self, user_id: str):
        variant = hash(user_id) % 2

        if variant == 0:
            # 算法A: 简化3档难度
            selector = SimpleAdaptiveSelector()
        else:
            # 算法B: 完整IRT模型
            selector = IRTAdaptiveSelector()

        result = await run_assessment(user_id, selector)

        # 记录实验数据
        await ab_test_repo.log({
            "user_id": user_id,
            "variant": "A" if variant == 0 else "B",
            "result": result,
            "duration": result.duration_secs
        })
```

---

## 九、成本与排期

### 9.1 开发工作量

| 任务 | 预计时间 | 优先级 |
|------|----------|--------|
| 题库准备(60题) | 3天 | P0 |
| 后端API(评估流程) | 2天 | P0 |
| 简化自适应算法 | 1天 | P0 |
| 前端3个页面 | 2天 | P0 |
| 数据库集合设计 | 0.5天 | P0 |
| 雷达图可视化 | 1天 | P1 |
| 完整IRT算法 | 3天 | P2(后期优化) |
| 题目标注工具 | 2天 | P2 |

**MVP总计: 8.5天 (1人)**

### 9.2 运营成本

```
题库维护: ¥0/月 (自建)
CloudBase存储: ¥5/月 (音频文件约500MB)
TTS音频生成: ¥10/月 (按需生成60题音频)
数据库: ¥0 (包含在CloudBase套餐内)

总计: ¥15/月
```

---

## 十、风险与兜底

### 10.1 技术风险

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|----------|
| 题库不足 | 中 | 高 | 优先准备核心题,逐步扩充 |
| 算法不准 | 高 | 中 | 允许用户手动选择等级 |
| 音频加载慢 | 中 | 中 | 预加载+CDN加速 |

### 10.2 产品风险

**用户跳过评估率高**
- 应对: 在onboarding强调价值
- 提供"快速3题版"降低门槛
- 后期可补测

**评估结果不可信**
- 应对: 首页显示"重新评估"入口
- 结合后续学习数据动态调整

---

## 十一、后续优化方向

### Phase 2: 智能化(1-2个月后)

- [ ] 完整IRT模型(区分度/猜测度参数)
- [ ] 动态难度校准(基于真实答题数据)
- [ ] 口语跟读评分集成
- [ ] 个性化题型配比

### Phase 3: 场景化(3-6个月后)

- [ ] 分场景评估(商务/旅游/学术)
- [ ] 垂直领域词汇测试
- [ ] 对标真实考试(托福/雅思)
- [ ] 定期复测追踪进步

---

## 附录: 示例题目

### A2级 - 词汇题
```json
{
  "question": "I need to _____ a flight to Paris.",
  "options": ["book", "cook", "look", "took"],
  "correct": 0,
  "scenario": "travel",
  "explanation": "'book a flight' 表示预订航班"
}
```

### B1级 - 听力题
```json
{
  "audio_url": "https://cdn.../business_meeting.mp3",
  "transcript": "The quarterly report shows a 15% increase in sales.",
  "question": "What does the report indicate?",
  "options": [
    "Sales decreased",
    "Sales increased by 15%",
    "Sales remained stable",
    "Sales doubled"
  ],
  "correct": 1
}
```

### B2级 - 阅读题
```json
{
  "passage": "Despite initial setbacks, the project team persevered and ultimately delivered ahead of schedule...",
  "question": "What does 'persevered' mean in this context?",
  "options": [
    "Gave up",
    "Continued despite difficulties",
    "Requested help",
    "Changed strategy"
  ],
  "correct": 1
}
```
