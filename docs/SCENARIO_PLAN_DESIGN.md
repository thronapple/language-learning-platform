# 场景化学习计划生成系统设计

## 一、核心差异化价值

### 与通用词包学习的本质区别

| 维度 | 通用词包 | 场景化计划 |
|------|----------|------------|
| **学习动机** | 长期提升 | 短期应急(2周出差) |
| **内容组织** | 字母/频率 | 真实对话场景 |
| **进度呈现** | "已背500词" | "机场通关98%就绪" |
| **压力可视化** | ❌ | ✅ "距离出发还需掌握8个场景" |
| **成就感** | 数字累积 | 情景通关 |

**核心洞察**: 用户不是想"学会1000个单词",而是想**"2周后在德国机场/会议室不尴尬"**

---

## 二、场景化内容体系

### 2.1 场景分类树

```
场景化学习内容
├── 🌍 旅游出行 (Tourism)
│   ├── 机场/航班 (Airport & Flight)
│   │   ├── 办理值机 (Check-in)
│   │   ├── 安检通关 (Security)
│   │   ├── 登机/转机 (Boarding & Transfer)
│   │   └── 行李托运/提取 (Baggage)
│   ├── 酒店住宿 (Hotel)
│   │   ├── 预订确认 (Reservation)
│   │   ├── 入住登记 (Check-in)
│   │   ├── 客房服务 (Room Service)
│   │   └── 退房结账 (Check-out)
│   ├── 餐厅用餐 (Dining)
│   │   ├── 预订座位 (Booking)
│   │   ├── 点餐 (Ordering)
│   │   ├── 特殊要求 (Special Requests)
│   │   └── 买单 (Payment)
│   ├── 交通出行 (Transportation)
│   │   ├── 问路导航 (Directions)
│   │   ├── 公共交通 (Public Transit)
│   │   ├── 租车/打车 (Car Rental & Taxi)
│   │   └── 紧急情况 (Emergencies)
│   └── 购物娱乐 (Shopping & Entertainment)
│       ├── 超市购物 (Grocery)
│       ├── 讨价还价 (Bargaining)
│       ├── 退换货 (Returns)
│       └── 景点门票 (Attractions)
│
├── 💼 商务工作 (Business)
│   ├── 会议交流 (Meetings)
│   │   ├── 自我介绍 (Introductions)
│   │   ├── 议程讨论 (Agenda Discussion)
│   │   ├── 意见表达 (Expressing Opinions)
│   │   └── 会议总结 (Summary)
│   ├── 邮件沟通 (Email Communication)
│   │   ├── 邮件开头/结尾 (Opening & Closing)
│   │   ├── 安排会议 (Schedule Meetings)
│   │   ├── 请求/确认 (Requests & Confirmations)
│   │   └── 道歉/感谢 (Apologies & Thanks)
│   ├── 演示汇报 (Presentations)
│   │   ├── 开场白 (Opening)
│   │   ├── 数据呈现 (Data Presentation)
│   │   ├── 过渡衔接 (Transitions)
│   │   └── Q&A应对 (Q&A Handling)
│   ├── 谈判协商 (Negotiation)
│   │   ├── 报价/还价 (Pricing)
│   │   ├── 条款讨论 (Terms Discussion)
│   │   ├── 妥协/让步 (Compromise)
│   │   └── 达成协议 (Agreement)
│   └── 社交场合 (Networking)
│       ├── 破冰寒暄 (Small Talk)
│       ├── 商务宴请 (Business Dinner)
│       └── 名片交换 (Card Exchange)
│
├── 🎓 学术交流 (Academic)
│   ├── 课堂讨论 (Class Discussion)
│   ├── 论文写作 (Academic Writing)
│   ├── 导师沟通 (Advisor Meeting)
│   └── 学术会议 (Conferences)
│
└── 🏥 生活应急 (Life Essentials)
    ├── 医疗就诊 (Medical)
    ├── 银行业务 (Banking)
    ├── 报警求助 (Emergency Services)
    └── 租房办理 (Accommodation)
```

### 2.2 场景内容结构

**单个场景包 (Scenario Pack)**
```json
{
  "scenario_id": "airport_checkin",
  "title": "机场办理值机",
  "category": "tourism.airport",
  "estimated_duration": 45,  // 分钟

  "difficulty_range": {
    "A2": { "core_phrases": 8, "vocab": 30 },
    "B1": { "core_phrases": 12, "vocab": 50 },
    "B2": { "core_phrases": 15, "vocab": 80 }
  },

  "content": {
    "core_dialogues": [
      {
        "id": "checkin_basic",
        "level": "A2",
        "situation": "向柜台出示护照和机票",
        "dialogue": [
          { "role": "staff", "text": "Good morning. Passport and ticket, please." },
          { "role": "you", "text": "Here you are." },
          { "role": "staff", "text": "Any baggage to check in?" },
          { "role": "you", "text": "Yes, one suitcase." }
        ],
        "key_phrases": [
          "Here you are",
          "check in baggage",
          "window seat / aisle seat"
        ],
        "audio_url": "https://cdn.../airport_checkin_basic.mp3"
      },
      {
        "id": "checkin_special_request",
        "level": "B1",
        "situation": "请求特殊座位/餐食",
        "dialogue": [
          { "role": "you", "text": "Could I have an aisle seat, please?" },
          { "role": "staff", "text": "Let me check... Yes, I can arrange that." },
          { "role": "you", "text": "And I'd like to request a vegetarian meal." }
        ],
        "key_phrases": [
          "Could I have...",
          "I'd like to request...",
          "vegetarian meal"
        ]
      }
    ],

    "vocabulary": [
      { "word": "boarding pass", "phonetic": "/ˈbɔːdɪŋ pæs/", "meaning": "登机牌", "level": "A2" },
      { "word": "carry-on luggage", "phonetic": "/ˈkæri ɒn/", "meaning": "随身行李", "level": "A2" },
      { "word": "overweight baggage", "phonetic": "/ˌoʊvərˈweɪt/", "meaning": "超重行李", "level": "B1" }
    ],

    "grammar_points": [
      { "pattern": "Could I have...?", "usage": "礼貌请求", "example": "Could I have a window seat?" },
      { "pattern": "I'd like to...", "usage": "表达意愿", "example": "I'd like to check in now." }
    ],

    "cultural_tips": [
      "欧美机场建议提前2小时到达",
      "液体物品需放在透明袋中(100ml以下)"
    ]
  },

  "practice_tasks": [
    {
      "type": "dialogue_completion",
      "prompt": "柜台问你'Any bags to check?',你该如何回答?",
      "expected": ["Yes, one suitcase", "No, just carry-on"],
      "points": 10
    },
    {
      "type": "role_play",
      "scenario": "你的行李超重了,需要支付额外费用",
      "audio_cue": "Your baggage is 3kg over the limit...",
      "evaluation": "跟读评分"
    }
  ],

  "completion_criteria": {
    "listen_count": 3,
    "follow_read_score": 0.75,
    "vocab_mastery": 0.8,
    "practice_passed": 2
  }
}
```

---

## 三、计划生成算法

### 3.1 输入参数

```python
class PlanGenerationInput:
    # 评估结果
    user_level: str  # "B1"
    weak_areas: list[str]  # ["grammar", "listening"]

    # 场景选择
    primary_scenario: str  # "business_trip"
    sub_scenarios: list[str]  # ["airport", "hotel", "meeting"]

    # 时间约束
    days_available: int  # 14
    daily_minutes: int  # 30

    # 个性化偏�好
    focus_mode: str  # "balanced" | "speaking_first" | "vocab_first"
```

### 3.2 生成流程

```
用户输入
  ↓
[1] 场景优先级排序
  ├─ 评估高频场景(机场>酒店>会议)
  ├─ 考虑用户水平(A2跳过高级商务谈判)
  └─ 识别依赖关系(基础问候 → 商务寒暄)
  ↓
[2] 时间预算分配
  ├─ 总时长 = 14天 × 30分钟 = 420分钟
  ├─ 核心场景(60%) = 252分钟
  ├─ 词汇复习(25%) = 105分钟
  └─ 模拟演练(15%) = 63分钟
  ↓
[3] 每日任务生成
  ├─ Day 1-3: 基础场景(机场/酒店)
  ├─ Day 4-7: 核心场景(会议/邮件)
  ├─ Day 8-11: 进阶场景(谈判/社交)
  └─ Day 12-14: 综合模拟+复习
  ↓
[4] 动态调整机制
  └─ 根据完成情况每日重新计算优先级
```

### 3.3 算法实现

**场景优先级计算**
```python
class ScenarioPrioritizer:
    def calculate_priority(
        self,
        scenario: Scenario,
        user_level: str,
        target_scenarios: list[str],
        days_left: int
    ) -> float:
        """计算场景优先级分数(0-1)"""
        score = 0.0

        # 1. 匹配度(40%)
        if scenario.id in target_scenarios:
            score += 0.4

        # 2. 紧迫度(30%)
        if scenario.category == "emergency" or days_left <= 3:
            score += 0.3
        elif scenario.is_prerequisite:
            score += 0.2

        # 3. 难度适配(20%)
        level_diff = abs(
            self.level_to_score(user_level) -
            self.level_to_score(scenario.min_level)
        )
        score += 0.2 * (1 - level_diff / 5)  # 归一化

        # 4. 高频使用(10%)
        if scenario.usage_frequency == "high":
            score += 0.1

        return min(score, 1.0)

    def level_to_score(self, level: str) -> int:
        return {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}[level]
```

**时间预算分配器**
```python
class TimeBudgetAllocator:
    def allocate(
        self,
        total_minutes: int,
        scenarios: list[Scenario],
        priorities: dict[str, float]
    ) -> dict[str, int]:
        """分配学习时间预算"""
        # 按优先级归一化分配
        total_priority = sum(priorities.values())

        allocations = {}
        for scenario in scenarios:
            priority = priorities[scenario.id]
            base_allocation = (priority / total_priority) * total_minutes

            # 确保每个场景至少15分钟
            allocations[scenario.id] = max(15, int(base_allocation))

        # 预留15%作为弹性时间(复习/补足)
        buffer = total_minutes * 0.15
        allocations["_buffer"] = int(buffer)

        return allocations
```

**每日计划生成器**
```python
class DailyPlanGenerator:
    def generate(
        self,
        scenarios: list[Scenario],
        time_allocations: dict[str, int],
        days_available: int,
        daily_minutes: int
    ) -> list[DailyPlan]:
        """生成每日学习计划"""
        plans = []
        remaining_allocations = time_allocations.copy()

        for day in range(1, days_available + 1):
            daily_tasks = []
            minutes_left = daily_minutes

            # 选择当天任务(优先高优先级且未完成的)
            for scenario in self._sort_by_urgency(scenarios, day, days_available):
                if remaining_allocations[scenario.id] <= 0:
                    continue

                # 计算当天该场景的学习时长
                task_duration = min(
                    remaining_allocations[scenario.id],
                    minutes_left,
                    20  # 单个场景每天最多20分钟
                )

                if task_duration < 10:
                    continue  # 不足10分钟跳过

                # 添加任务
                daily_tasks.append(DailyTask(
                    scenario_id=scenario.id,
                    duration=task_duration,
                    activities=self._select_activities(scenario, task_duration)
                ))

                remaining_allocations[scenario.id] -= task_duration
                minutes_left -= task_duration

                if minutes_left < 10:
                    break

            # 填充复习任务
            if minutes_left >= 5:
                daily_tasks.append(self._create_review_task(minutes_left, day))

            plans.append(DailyPlan(
                day=day,
                tasks=daily_tasks,
                total_duration=sum(t.duration for t in daily_tasks)
            ))

        return plans

    def _select_activities(self, scenario: Scenario, duration: int) -> list[Activity]:
        """根据时长选择学习活动"""
        activities = []

        if duration >= 20:
            # 完整流程: 听 → 跟读 → 练习
            activities = [
                {"type": "listen", "times": 2, "duration": 6},
                {"type": "follow_read", "times": 3, "duration": 9},
                {"type": "practice", "count": 1, "duration": 5}
            ]
        elif duration >= 10:
            # 精简流程: 听 → 跟读
            activities = [
                {"type": "listen", "times": 1, "duration": 3},
                {"type": "follow_read", "times": 2, "duration": 7}
            ]
        else:
            # 快速复习: 仅听力
            activities = [
                {"type": "listen", "times": 2, "duration": duration}
            ]

        return activities
```

---

## 四、进度可视化设计

### 4.1 核心指标

**场景就绪度 (Scenario Readiness)**
```python
class ScenarioReadiness:
    def calculate(self, scenario: Scenario, user_progress: UserProgress) -> float:
        """计算场景掌握度(0-1)"""
        weights = {
            "dialogue_listened": 0.2,
            "follow_read_score": 0.4,
            "vocab_mastery": 0.25,
            "practice_passed": 0.15
        }

        score = 0.0
        criteria = scenario.completion_criteria

        # 听力完成度
        listened = user_progress.listen_count / criteria.listen_count
        score += weights["dialogue_listened"] * min(listened, 1.0)

        # 跟读得分
        if user_progress.follow_read_score:
            score += weights["follow_read_score"] * (
                user_progress.follow_read_score / criteria.follow_read_score
            )

        # 词汇掌握
        mastered_vocab = len(user_progress.mastered_vocab)
        total_vocab = len(scenario.vocabulary)
        vocab_ratio = mastered_vocab / total_vocab if total_vocab > 0 else 0
        score += weights["vocab_mastery"] * (vocab_ratio / criteria.vocab_mastery)

        # 练习通过
        passed = user_progress.practice_passed / criteria.practice_passed
        score += weights["practice_passed"] * min(passed, 1.0)

        return min(score, 1.0)
```

### 4.2 前端呈现

**计划页 (`pages/plan/scenario-plan`)**
```xml
<view class="scenario-plan">
  <!-- 倒计时 -->
  <view class="countdown-banner">
    <icon type="warn" class="urgent-icon"/>
    <text class="countdown">距离出发还有 {{daysLeft}} 天</text>
    <text class="target">目标: {{targetScenario}}</text>
  </view>

  <!-- 整体进度 -->
  <view class="overall-progress">
    <text class="title">整体就绪度</text>
    <view class="progress-ring">
      <canvas canvas-id="progressRing" class="ring-canvas"></canvas>
      <text class="percentage">{{overallReadiness}}%</text>
    </view>
    <text class="status">{{readinessStatus}}</text>
  </view>

  <!-- 场景列表 -->
  <view class="scenarios">
    <view wx:for="{{scenarios}}" wx:key="id" class="scenario-card">
      <view class="scenario-header">
        <icon type="{{item.icon}}" />
        <text class="scenario-name">{{item.name}}</text>
        <view class="priority-badge {{item.priority}}">
          {{item.priorityLabel}}
        </view>
      </view>

      <!-- 进度条 -->
      <view class="scenario-progress">
        <progress percent="{{item.readiness * 100}}"
                  stroke-width="8"
                  activeColor="{{item.readiness >= 0.8 ? '#52c41a' : '#1890ff'}}" />
        <text class="readiness-text">{{item.readiness * 100}}% 就绪</text>
      </view>

      <!-- 待办任务 -->
      <view class="todo-items">
        <text wx:if="{{item.remainingTasks > 0}}" class="todo-count">
          还需完成 {{item.remainingTasks}} 个对话场景
        </text>
        <text wx:else class="completed">✓ 已掌握</text>
      </view>

      <button wx:if="{{item.readiness < 1.0}}"
              class="study-btn"
              bindtap="enterScenario"
              data-id="{{item.id}}">
        继续学习
      </button>
    </view>
  </view>

  <!-- 今日任务 -->
  <view class="today-tasks">
    <text class="section-title">今日任务 ({{todayRemaining}}/{{todayTotal}})</text>
    <view wx:for="{{todayTasks}}" wx:key="id" class="task-item">
      <checkbox checked="{{item.completed}}" bindtap="toggleTask" data-id="{{item.id}}" />
      <text class="task-name">{{item.name}}</text>
      <text class="task-duration">{{item.duration}}分钟</text>
    </view>
  </view>

  <!-- 每日打卡 -->
  <view class="daily-checkin">
    <text class="checkin-title">学习打卡</text>
    <view class="calendar">
      <view wx:for="{{checkinDays}}" wx:key="day" class="calendar-day {{item.status}}">
        <text class="day-number">{{item.day}}</text>
        <icon wx:if="{{item.completed}}" type="success_circle" size="20" />
      </view>
    </view>
    <text class="streak">连续 {{streakDays}} 天</text>
  </view>
</view>
```

**样式示例**
```css
/* 紧急感设计 */
.countdown-banner {
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);
  color: white;
  padding: 20rpx;
  border-radius: 12rpx;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.9; }
}

/* 就绪度颜色 */
.scenario-progress progress {
  transition: all 0.3s ease;
}

.scenario-card[data-readiness="high"] {
  border-left: 4px solid #52c41a;
}

.scenario-card[data-readiness="medium"] {
  border-left: 4px solid #faad14;
}

.scenario-card[data-readiness="low"] {
  border-left: 4px solid #f5222d;
}
```

---

## 五、智能推荐与调整

### 5.1 动态重排优先级

```python
class AdaptivePlanAdjuster:
    async def adjust_daily(self, user_id: str):
        """每日重新计算优先级"""
        plan = await plan_repo.get_active(user_id)
        progress = await progress_repo.get_all(user_id)

        # 识别落后场景
        behind_scenarios = []
        for scenario in plan.scenarios:
            expected_progress = self._calculate_expected_progress(
                scenario,
                plan.days_elapsed,
                plan.total_days
            )
            actual_progress = self._get_actual_progress(scenario.id, progress)

            if actual_progress < expected_progress - 0.15:
                behind_scenarios.append(scenario)

        # 提升落后场景优先级
        if behind_scenarios:
            await self._boost_priority(plan, behind_scenarios)
            await self._send_notification(user_id, behind_scenarios)

    def _calculate_expected_progress(
        self,
        scenario: Scenario,
        days_elapsed: int,
        total_days: int
    ) -> float:
        """计算理论进度"""
        # 线性进度模型
        return (days_elapsed / total_days) * scenario.target_readiness
```

### 5.2 个性化推荐

```python
class PersonalizedRecommender:
    async def recommend_next_task(
        self,
        user_id: str,
        available_minutes: int
    ) -> Task:
        """推荐下一个学习任务"""
        user_profile = await self._build_user_profile(user_id)

        # 考虑因素
        factors = {
            "urgency": self._calculate_urgency(user_profile),
            "energy_level": self._estimate_energy(user_profile),
            "retention_curve": self._get_forgetting_curve(user_profile),
            "difficulty_preference": user_profile.difficulty_preference
        }

        # 场景池
        candidates = await self._get_candidate_scenarios(user_profile)

        # 评分排序
        scored_scenarios = []
        for scenario in candidates:
            score = self._score_scenario(scenario, factors, available_minutes)
            scored_scenarios.append((scenario, score))

        # 返回最高分
        best_scenario, _ = max(scored_scenarios, key=lambda x: x[1])
        return self._create_task_from_scenario(best_scenario, available_minutes)

    def _estimate_energy(self, user_profile: UserProfile) -> str:
        """根据时间估算精力水平"""
        hour = datetime.now().hour

        if 6 <= hour < 9:
            return "high"  # 早晨: 推荐新内容
        elif 12 <= hour < 14:
            return "medium"  # 午间: 复习
        elif 20 <= hour < 23:
            return "low"  # 晚间: 轻松内容
        else:
            return "medium"
```

---

## 六、数据库设计

### 6.1 新增集合: `scenarios`

```json
{
  "_id": "scenario_airport_checkin",
  "title": "机场办理值机",
  "category": "tourism.airport",
  "level_range": ["A2", "B1", "B2"],
  "estimated_duration": 45,
  "priority_tier": "high",

  "dialogues": [
    {
      "id": "dialog_001",
      "level": "A2",
      "audio_url": "https://cdn.../airport_checkin_basic.mp3",
      "transcript": [...],
      "key_phrases": [...]
    }
  ],

  "vocabulary": [
    { "word": "boarding pass", "level": "A2", "phonetic": "...", "meaning": "..." }
  ],

  "completion_criteria": {
    "listen_count": 3,
    "follow_read_score": 0.75,
    "vocab_mastery": 0.8,
    "practice_passed": 2
  },

  "metadata": {
    "usage_count": 1234,
    "avg_completion_rate": 0.87,
    "avg_time_to_master": 38
  }
}
```

### 6.2 重构集合: `plans`

```json
{
  "_id": "plan_user123_20251003",
  "user_id": "openid_123",
  "created_at": "2025-10-03T10:00:00Z",

  "goal": {
    "type": "business_trip",
    "target_date": "2025-10-17",
    "days_available": 14,
    "daily_minutes": 30
  },

  "assessment_result": {
    "overall_level": "B1",
    "weak_areas": ["grammar", "listening"]
  },

  "selected_scenarios": [
    {
      "scenario_id": "airport_checkin",
      "priority": 0.95,
      "allocated_minutes": 60,
      "target_readiness": 0.9,
      "current_readiness": 0.45,
      "days_scheduled": [1, 2, 5, 8]
    },
    {
      "scenario_id": "hotel_checkin",
      "priority": 0.85,
      "allocated_minutes": 45,
      "target_readiness": 0.85,
      "current_readiness": 0.20,
      "days_scheduled": [1, 3, 6]
    }
  ],

  "daily_plans": [
    {
      "day": 1,
      "date": "2025-10-03",
      "tasks": [
        {
          "scenario_id": "airport_checkin",
          "duration": 20,
          "activities": [
            { "type": "listen", "times": 2 },
            { "type": "follow_read", "times": 3 }
          ],
          "completed": true,
          "completed_at": "2025-10-03T20:30:00Z"
        },
        {
          "scenario_id": "hotel_checkin",
          "duration": 10,
          "activities": [{ "type": "vocab_review", "count": 15 }],
          "completed": false
        }
      ],
      "total_duration": 30,
      "actual_duration": 20,
      "completion_rate": 0.67
    }
  ],

  "streak": {
    "current": 5,
    "longest": 7,
    "last_checkin": "2025-10-03"
  },

  "overall_progress": {
    "total_scenarios": 8,
    "completed_scenarios": 2,
    "avg_readiness": 0.58,
    "total_minutes_studied": 150,
    "days_elapsed": 5,
    "on_track": true
  }
}
```

### 6.3 新增集合: `scenario_progress`

```json
{
  "_id": "progress_user123_airport_checkin",
  "user_id": "openid_123",
  "scenario_id": "airport_checkin",
  "started_at": "2025-10-03T10:00:00Z",
  "last_practiced": "2025-10-05T20:30:00Z",

  "dialogue_progress": [
    {
      "dialogue_id": "dialog_001",
      "listen_count": 5,
      "follow_read_attempts": 8,
      "best_score": 0.88,
      "last_score": 0.85,
      "mastered": true
    }
  ],

  "vocabulary_progress": {
    "total": 30,
    "learned": 25,
    "mastered": 18,
    "review_due": 7,
    "next_review_at": "2025-10-06T09:00:00Z"
  },

  "practice_results": [
    {
      "practice_id": "prac_001",
      "type": "dialogue_completion",
      "passed": true,
      "score": 0.9,
      "completed_at": "2025-10-05T20:25:00Z"
    }
  ],

  "readiness": 0.78,
  "completed": false,

  "time_spent": {
    "total_minutes": 65,
    "listen": 20,
    "follow_read": 30,
    "practice": 15
  }
}
```

---

## 七、后端API设计

### 7.1 计划生成

**`POST /plans/generate`**
```python
@router.post("/plans/generate")
async def generate_plan(
    payload: PlanGenerationInput,
    user: User = Depends(get_current_user)
) -> Plan:
    """生成场景化学习计划"""
    # 1. 获取匹配场景
    scenarios = await scenario_repo.get_by_category(
        payload.primary_scenario
    )

    # 2. 计算优先级
    prioritizer = ScenarioPrioritizer()
    priorities = {
        s.id: prioritizer.calculate_priority(
            s,
            payload.user_level,
            payload.sub_scenarios,
            payload.days_available
        )
        for s in scenarios
    }

    # 3. 分配时间预算
    total_minutes = payload.days_available * payload.daily_minutes
    allocator = TimeBudgetAllocator()
    time_allocations = allocator.allocate(
        total_minutes,
        scenarios,
        priorities
    )

    # 4. 生成每日计划
    generator = DailyPlanGenerator()
    daily_plans = generator.generate(
        scenarios,
        time_allocations,
        payload.days_available,
        payload.daily_minutes
    )

    # 5. 保存计划
    plan = Plan(
        user_id=user.openid,
        goal={
            "type": payload.primary_scenario,
            "target_date": (datetime.now() + timedelta(days=payload.days_available)).isoformat(),
            "days_available": payload.days_available,
            "daily_minutes": payload.daily_minutes
        },
        selected_scenarios=[
            {
                "scenario_id": s.id,
                "priority": priorities[s.id],
                "allocated_minutes": time_allocations[s.id],
                "target_readiness": 0.8 if priorities[s.id] > 0.7 else 0.6
            }
            for s in scenarios
        ],
        daily_plans=daily_plans
    )

    await plan_repo.create(plan)

    # 6. 埋点
    await event_bus.track("plan_generated", {
        "user_id": user.openid,
        "scenario_count": len(scenarios),
        "total_days": payload.days_available
    })

    return plan
```

### 7.2 进度更新

**`POST /scenarios/{scenario_id}/progress`**
```python
@router.post("/scenarios/{scenario_id}/progress")
async def update_scenario_progress(
    scenario_id: str,
    payload: ProgressUpdate,
    user: User = Depends(get_current_user)
) -> ScenarioProgress:
    """更新场景学习进度"""
    progress = await scenario_progress_repo.get_or_create(
        user.openid,
        scenario_id
    )

    # 更新对话进度
    if payload.dialogue_id:
        dialogue_progress = next(
            (d for d in progress.dialogue_progress if d.dialogue_id == payload.dialogue_id),
            None
        )
        if not dialogue_progress:
            progress.dialogue_progress.append({
                "dialogue_id": payload.dialogue_id,
                "listen_count": 0,
                "follow_read_attempts": 0,
                "best_score": 0.0
            })

        dialogue_progress.listen_count += payload.listen_increment or 0
        if payload.follow_read_score:
            dialogue_progress.follow_read_attempts += 1
            dialogue_progress.best_score = max(
                dialogue_progress.best_score,
                payload.follow_read_score
            )
            dialogue_progress.last_score = payload.follow_read_score

    # 重新计算就绪度
    scenario = await scenario_repo.get(scenario_id)
    readiness_calculator = ScenarioReadiness()
    progress.readiness = readiness_calculator.calculate(scenario, progress)

    # 检查是否完成
    if progress.readiness >= scenario.target_readiness:
        progress.completed = True
        await event_bus.track("scenario_completed", {
            "user_id": user.openid,
            "scenario_id": scenario_id,
            "readiness": progress.readiness
        })

    await scenario_progress_repo.update(progress)

    return progress
```

### 7.3 每日推荐

**`GET /plans/today`**
```python
@router.get("/plans/today")
async def get_today_plan(
    user: User = Depends(get_current_user)
) -> TodayPlan:
    """获取今日学习计划"""
    plan = await plan_repo.get_active(user.openid)
    if not plan:
        raise HTTPException(404, "No active plan")

    # 获取今日任务
    today = datetime.now().date()
    day_index = (today - plan.created_at.date()).days + 1

    if day_index > plan.goal.days_available:
        return TodayPlan(
            message="计划已完成",
            tasks=[],
            summary=await _generate_summary(plan)
        )

    daily_plan = plan.daily_plans[day_index - 1]

    # 获取未完成任务
    pending_tasks = [
        t for t in daily_plan.tasks if not t.completed
    ]

    # 个性化推荐
    if not pending_tasks:
        recommender = PersonalizedRecommender()
        next_task = await recommender.recommend_next_task(
            user.openid,
            available_minutes=plan.goal.daily_minutes
        )
        pending_tasks = [next_task] if next_task else []

    return TodayPlan(
        day=day_index,
        total_days=plan.goal.days_available,
        tasks=pending_tasks,
        completed_today=len([t for t in daily_plan.tasks if t.completed]),
        total_today=len(daily_plan.tasks),
        streak=plan.streak.current,
        overall_readiness=plan.overall_progress.avg_readiness
    )
```

---

## 八、前端交互流程

### 8.1 计划生成引导

**Step 1: 场景选择**
```xml
<view class="scenario-selection">
  <text class="title">你即将面对什么场景?</text>

  <view class="primary-scenarios">
    <button wx:for="{{primaryScenarios}}" wx:key="id"
            class="scenario-btn {{selectedPrimary === item.id ? 'active' : ''}}"
            bindtap="selectPrimary"
            data-id="{{item.id}}">
      <icon type="{{item.icon}}" />
      <text>{{item.name}}</text>
      <text class="desc">{{item.description}}</text>
    </button>
  </view>

  <!-- 子场景多选 -->
  <view wx:if="{{selectedPrimary}}" class="sub-scenarios">
    <text class="subtitle">具体会遇到哪些情况? (多选)</text>
    <checkbox-group bindchange="onSubScenariosChange">
      <label wx:for="{{subScenarios}}" wx:key="id" class="sub-scenario-item">
        <checkbox value="{{item.id}}" />
        <text>{{item.name}}</text>
      </label>
    </checkbox-group>
  </view>

  <button type="primary" bindtap="nextStep" disabled="{{!canProceed}}">
    下一步
  </button>
</view>
```

**Step 2: 时间设置**
```xml
<view class="time-settings">
  <text class="title">你有多少时间准备?</text>

  <picker mode="date" bindchange="onDateChange" start="{{today}}" end="{{maxDate}}">
    <view class="picker-item">
      <text>目标日期</text>
      <text class="value">{{targetDate}}</text>
    </view>
  </picker>

  <text class="days-left">还有 {{daysLeft}} 天</text>

  <view class="daily-minutes">
    <text>每天可学习时间</text>
    <slider min="10" max="120" step="5" value="{{dailyMinutes}}"
            bindchange="onMinutesChange" show-value />
  </view>

  <view class="total-estimate">
    <text>总计: {{totalMinutes}} 分钟 (约 {{totalHours}} 小时)</text>
  </view>

  <button type="primary" bindtap="generatePlan">
    生成计划
  </button>
</view>
```

**Step 3: 计划预览**
```xml
<view class="plan-preview">
  <text class="title">你的专属学习计划</text>

  <view class="plan-summary">
    <view class="summary-item">
      <text class="label">总场景数</text>
      <text class="value">{{scenarioCount}}</text>
    </view>
    <view class="summary-item">
      <text class="label">预计学习</text>
      <text class="value">{{totalHours}}小时</text>
    </view>
    <view class="summary-item">
      <text class="label">目标就绪度</text>
      <text class="value">{{targetReadiness}}%</text>
    </view>
  </view>

  <!-- 场景时间轴 -->
  <view class="scenario-timeline">
    <view wx:for="{{scenarios}}" wx:key="id" class="timeline-item">
      <view class="timeline-marker {{item.priority}}"></view>
      <view class="timeline-content">
        <text class="scenario-name">{{item.name}}</text>
        <text class="duration">{{item.allocatedMinutes}}分钟</text>
        <text class="days">Day {{item.daysScheduled[0]}}-{{item.daysScheduled[item.daysScheduled.length - 1]}}</text>
      </view>
    </view>
  </view>

  <button type="primary" bindtap="startPlan">
    开始学习
  </button>
</view>
```

---

## 九、成本与排期

### 9.1 内容准备

**核心场景内容矩阵**
```
旅游出行(5个场景) × 3个难度 = 15个对话包
商务工作(5个场景) × 3个难度 = 15个对话包
总计: 30个对话包

每个对话包:
- 核心对话: 3-5段
- 词汇: 20-50个
- 练习: 2-3个

预计工作量:
- 内容编写: 5天 (2人)
- 音频录制/TTS: 3天
- 测试校验: 2天
总计: 10天
```

### 9.2 开发工作量

| 模块 | 预计时间 | 依赖 |
|------|----------|------|
| 场景内容结构设计 | 1天 | - |
| 数据库集合迁移 | 1天 | - |
| 优先级算法 | 2天 | 评估系统 |
| 计划生成API | 2天 | 优先级算法 |
| 就绪度计算 | 1天 | - |
| 前端计划页面 | 3天 | 计划API |
| 进度追踪UI | 2天 | - |
| 动态调整逻辑 | 2天 | 计划API |

**总计: 14天 (1人全职)**

---

## 十、验收标准

### 10.1 功能完整性

- [ ] 用户可选择场景并生成计划
- [ ] 计划包含每日任务分解
- [ ] 场景就绪度实时更新
- [ ] 倒计时提醒可见
- [ ] 落后场景自动提升优先级

### 10.2 体验指标

- [ ] 计划生成 < 3秒
- [ ] 就绪度计算 < 500ms
- [ ] 每日任务加载 < 1秒
- [ ] 进度条动画流畅(60fps)

### 10.3 数据准确性

- [ ] 就绪度计算与实际能力相符(A/B测试验证)
- [ ] 时间预算误差 < 15%
- [ ] 场景优先级排序合理(用户调研验证)

---

## 附录: 示例场景内容

### 商务会议 - B1级对话

```json
{
  "scenario_id": "business_meeting_intro",
  "dialogue": [
    {
      "role": "you",
      "text": "Good morning everyone. Let me introduce myself.",
      "translation": "大家早上好,让我自我介绍一下。"
    },
    {
      "role": "you",
      "text": "I'm Li Ming from the Beijing office. I'm responsible for market analysis.",
      "translation": "我是北京办公室的李明,负责市场分析。"
    },
    {
      "role": "colleague",
      "text": "Nice to meet you, Li Ming. I'm Sarah, the project manager.",
      "translation": "很高兴认识你,李明。我是项目经理Sarah。"
    },
    {
      "role": "you",
      "text": "Pleasure to meet you too. I'm looking forward to working with you.",
      "translation": "我也很高兴认识你。期待与您合作。"
    }
  ],
  "key_phrases": [
    "Let me introduce myself",
    "I'm responsible for...",
    "I'm looking forward to..."
  ],
  "practice": {
    "type": "role_play",
    "prompt": "在会议上介绍你的职责和团队",
    "expected_keywords": ["introduce", "responsible", "looking forward"]
  }
}
```
