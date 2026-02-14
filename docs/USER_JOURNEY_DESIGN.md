# 用户旅程与交互流程设计

## 一、核心用户画像

### 1.1 主要用户

**商务人士 - 张晨 (35岁)**
```
场景: 2周后去德国参加商务会议
痛点:
- 英语基础B1,但商务场景生疏
- 时间紧迫,需要高效学习
- 担心机场/酒店/会议临场卡壳

需求:
- 快速评估当前水平
- 针对性学习商务+旅游场景
- 碎片时间学习(通勤/午休)
- 看到明确进度和就绪度
```

**出国旅游者 - 李梅 (28岁)**
```
场景: 1个月后去法国蜜月旅行
痛点:
- 英语A2水平,法语零基础
- 担心点餐/问路/应急情况

需求:
- 实用旅游口语
- 真实对话场景
- 能随时复习关键短语
```

**留学生 - 王浩 (23岁)**
```
场景: 3个月后去美国读研
痛点:
- 托福90分,但口语弱
- 需要适应学术讨论/社交

需求:
- 学术场景对话
- 提升口语流利度
- 词汇长期记忆
```

---

## 二、完整用户旅程

### 2.1 旅程地图

```
发现 → 注册 → 评估 → 计划生成 → 学习 → 复习 → 达成目标
 ↓      ↓      ↓        ↓          ↓      ↓        ↓
广告   授权   10题     定制计划    场景   SRS    导出成果
扫码   引导   测试     14天       对话   词汇    分享证书
```

### 2.2 详细流程

#### **阶段1: 发现与注册 (0-2分钟)**

**入口1: 公众号文章**
```
用户看到文章: "2周突击商务英语,机场/会议不尴尬"
  ↓
点击"立即评估" → 跳转小程序
  ↓
微信授权登录
  ↓
快速引导(3屏滑动)
```

**引导页内容**
```
第1屏: "评估 → 定制 → 突击"
- 动画: 3步流程图
- 文案: "10分钟评估,14天通关"

第2屏: "真实场景,不背单词"
- 动画: 机场对话卡片翻转
- 文案: "机场/酒店/会议,实战演练"

第3屏: "进度可视,压力可控"
- 动画: 倒计时+就绪度环形图
- 文案: "距离出发还有12天,机场场景85%就绪"

[开始评估] [暂时跳过]
```

**代码示例**
```xml
<!-- pages/onboarding/onboarding.wxml -->
<swiper class="onboarding-swiper" indicator-dots>
  <swiper-item>
    <view class="onboarding-slide">
      <image src="/images/onboarding/step1.png" />
      <text class="title">评估 → 定制 → 突击</text>
      <text class="desc">10分钟评估,14天通关</text>
    </view>
  </swiper-item>
  <!-- 其他slides -->
</swiper>

<view class="onboarding-actions">
  <button type="primary" bindtap="startAssessment">开始评估</button>
  <text class="skip" bindtap="skipOnboarding">暂时跳过</text>
</view>
```

---

#### **阶段2: 水平评估 (5-10分钟)**

**评估引导页**
```
[头部]
快速评估您的语言水平
10道题 · 预计10分钟

[特性卡片]
✓ 精准定位当前水平 (A1-C2)
✓ 识别薄弱环节
✓ 定制专属学习计划

[按钮]
[开始评估]
```

**答题页**
```
[进度条] 3/10
[倒计时] 剩余25秒

[题目区域]
🎧 音频播放器 (听力题)
或
📖 阅读段落 (阅读题)

问题: What gate does the passenger need?

[选项]
○ Gate 12
○ Gate 20  ← 用户选中(高亮)
○ Gate 22
○ Gate 32

[下一题按钮]
```

**结果页**
```
[徽章动画]
🏆 B1 中级

[雷达图]
听力 ████░ B2
阅读 ███░░ B1
词汇 ███░░ B1
语法 ██░░░ A2

[薄弱环节]
⚠️ 建议加强: 语法基础, 商务词汇

[CTA按钮]
[生成专属学习计划] → 跳转场景选择
```

**交互细节**
```typescript
// pages/assessment/test.ts
Page({
  data: {
    currentQuestion: 1,
    totalQuestions: 10,
    selectedIndex: null,
    timeLeft: 30
  },

  onLoad() {
    this.startTimer();
    this.loadQuestion();
  },

  selectOption(e: any) {
    const index = e.currentTarget.dataset.index;
    this.setData({ selectedIndex: index });
  },

  async nextQuestion() {
    // 提交答案
    await api.post('/assessment/answer', {
      question_id: this.data.questionId,
      answer_index: this.data.selectedIndex,
      time_spent: 30 - this.data.timeLeft
    });

    // 获取下一题(自适应)
    const next = await api.get('/assessment/next');

    if (next) {
      this.loadQuestion(next);
    } else {
      // 完成评估
      this.completeAssessment();
    }
  }
});
```

---

#### **阶段3: 计划生成 (2-3分钟)**

**场景选择页**
```
[标题]
你即将面对什么场景?

[主场景卡片 - 单选]
┌─────────────────┐
│ ✈️ 旅游出行      │
│ 机场/酒店/餐厅   │  ← 选中(边框高亮)
└─────────────────┘

┌─────────────────┐
│ 💼 商务工作      │
│ 会议/邮件/谈判   │
└─────────────────┘

┌─────────────────┐
│ 🎓 学术交流      │
│ 课堂/论文/会议   │
└─────────────────┘

[子场景多选]
具体会遇到哪些情况? (可多选)
☑ 机场值机/安检
☑ 酒店入住/退房
☐ 餐厅点餐
☑ 交通问路

[下一步]
```

**时间设置页**
```
[日期选择器]
目标日期: 2025-10-17
         ↓
    还有 14 天 ⏰

[滑块]
每天可学习时间: 30分钟
[━━━━━━●━━━] 10-120分钟

[预估]
总计: 420分钟 (7小时)
预计完成场景: 8个
目标就绪度: 85%

[生成计划]
```

**计划预览页**
```
[横幅]
🎯 你的专属学习计划已生成!

[摘要卡片]
┌────────────────────┐
│ 📊 8个核心场景     │
│ ⏱️ 7小时学习      │
│ 🎯 85%就绪度      │
└────────────────────┘

[场景时间轴]
Day 1-3: 机场通关 ████░░░ 60分钟
Day 4-7: 酒店入住 ███░░░░ 45分钟
Day 8-11: 商务会议 ███░░░░ 50分钟
Day 12-14: 综合复习 ██░░░░░ 30分钟

[开始学习] ← 主按钮
```

---

#### **阶段4: 学习循环 (每天20-30分钟)**

**首页/今日任务**
```
[倒计时横幅 - 红色渐变,脉动动画]
⚠️ 距离出发还有 12 天
目标: 德国商务出差

[整体就绪度 - 环形进度]
    ┌───────┐
    │  67%  │  整体就绪
    └───────┘
继续加油,接近目标!

[今日任务 2/3]
☑ 机场值机对话 (已完成 20分钟)
☑ 词汇复习15个 (已完成 8分钟)
☐ 酒店入住场景 (待学习 15分钟)
   [继续学习] ← 橙色按钮

[学习打卡日历]
一 二 三 四 五 六 日
✓  ✓  ✓  ✓  ○  ○  ○
连续 4 天 🔥
```

**学习页 - 场景对话**
```
[顶部]
场景: 机场办理值机
进度: 对话 2/5

[对话卡片]
┌──────────────────┐
│ 👨‍✈️ 柜台工作人员  │
│                  │
│ "Good morning.   │
│  Passport and    │
│  ticket, please."│
│                  │
│ 早上好。请出示护  │
│ 照和机票。        │
└──────────────────┘

[音频控制]
🎧 [播放] [0.75x] [1.0x] [1.25x]
━━━━━━●━━━━━ 00:03 / 00:05

[操作区]
[听一遍] (已听2次)
[跟读录音] ← 主按钮

[关键短语卡片 - 可折叠]
▼ Key Phrases (3)
- "Passport and ticket, please" = 请出示护照和机票
- "Here you are" = 给您
- "Check in baggage" = 托运行李

[下一句] [加入生词本]
```

**跟读评分页**
```
[提示]
请在3秒后开始跟读

[倒计时动画]
3... 2... 1... 🎤

[录音中]
🔴 录音中... 00:03
[波形动画]

[评分结果]
得分: 85/100 ⭐⭐⭐⭐

[详细反馈]
✓ 流利度: 90%
✓ 发音: 82%
△ 语调: 78% (可以更自然)

[重新录音] [继续]
```

**完成页**
```
[庆祝动画]
🎉 太棒了!

[本次学习总结]
┌────────────────┐
│ 完成对话: 5段   │
│ 学习时长: 22分钟│
│ 跟读得分: 85分  │
│ 新增生词: 8个   │
└────────────────┘

[场景就绪度更新]
机场值机: 45% → 78% ⬆

[插屏广告位 - 可跳过]
[5秒后自动跳过]

[继续学习] [返回首页]
```

---

#### **阶段5: 词汇复习 (SRS)**

**词汇本首页**
```
[Tab切换]
[今日复习 (15)] [我的词汇 (120)] [已掌握 (68)]

[今日复习]
┌──────────────────┐
│ boarding pass    │
│ /ˈbɔːrdɪŋ pæs/  │
│                  │
│ 🔊 播放发音      │
│                  │
│ 登机牌           │
│                  │
│ Don't forget... │
└──────────────────┘

[自评按钮]
[忘记了] [模糊] [记得] [熟练]
  ↓        ↓      ↓       ↓
+1天    +3天   +7天   +15天
```

**复习完成页**
```
[进度环]
    ┌───────┐
    │ 15/15 │
    └───────┘
今日复习完成!

[统计]
忘记: 2个
模糊: 5个
记得: 6个
熟练: 2个

[预告]
明日待复习: 12个
下次复习: 明天 09:00

[完成打卡]
```

---

#### **阶段6: 进度追踪**

**场景进度页**
```
[Tab] [计划] [进度] [我的]

[场景列表]
┌────────────────────┐
│ ✈️ 机场办理值机     │
│ ████████░░ 78%     │
│ 还需完成 1个对话    │
│ [继续学习]         │
└────────────────────┘

┌────────────────────┐
│ 🏨 酒店入住        │
│ ████░░░░░░ 45%    │
│ 还需完成 3个对话    │
│ [继续学习]         │
└────────────────────┘

┌────────────────────┐
│ 💼 商务会议自我介绍 │
│ ██░░░░░░░░ 20%    │
│ 还需完成 4个对话    │
│ [继续学习]         │
└────────────────────┘

✓ 基础问候 (已掌握)
✓ 自我介绍 (已掌握)
```

**学习报告页**
```
[周期选择]
[本周] [本月] [全部]

[核心数据]
┌──────┬──────┬──────┐
│ 学习  │ 完成  │ 掌握  │
│ 150  │  5   │ 120  │
│ 分钟  │ 场景  │ 词汇  │
└──────┴──────┴──────┘

[学习曲线图]
分钟
60 │     ●
40 │   ●   ●
20 │ ●       ●
 0 └─────────────
   一 二 三 四 五

[成就徽章]
🏆 连续学习7天
🎯 完成5个场景
📚 掌握100+词汇

[导出报告] [分享成就]
```

---

#### **阶段7: 达成目标**

**目标达成页**
```
[动画: 烟花+奖杯]
🎉 恭喜完成学习计划!

[成果摘要]
┌────────────────────┐
│ 学习天数: 14天     │
│ 总时长: 6.8小时    │
│ 完成场景: 8个      │
│ 掌握词汇: 156个    │
│ 平均就绪度: 87%    │
└────────────────────┘

[证书预览]
┌────────────────────┐
│  CERTIFICATE      │
│                   │
│  张晨             │
│  已完成            │
│  "商务出差英语突击"│
│  2025-10-17       │
└────────────────────┘

[导出证书] [分享朋友圈]

[继续提升]
→ 解锁更多场景
→ 订阅专业版
```

---

## 三、关键交互细节

### 3.1 进度可视化

**倒计时紧迫感**
```css
.countdown-banner {
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}
```

**就绪度环形图**
```javascript
// utils/chart.ts
function drawReadinessRing(canvasId: string, percentage: number) {
  const ctx = wx.createCanvasContext(canvasId);

  // 背景圆环
  ctx.setLineWidth(8);
  ctx.setStrokeStyle('#e0e0e0');
  ctx.arc(100, 100, 80, 0, 2 * Math.PI);
  ctx.stroke();

  // 进度圆环
  const gradient = ctx.createLinearGradient(0, 0, 200, 200);
  gradient.addColorStop(0, '#52c41a');
  gradient.addColorStop(1, '#1890ff');

  ctx.setStrokeStyle(gradient);
  ctx.arc(100, 100, 80, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * percentage);
  ctx.stroke();

  ctx.draw();
}
```

### 3.2 动画与反馈

**学习完成动画**
```javascript
// components/celebration/celebration.ts
function showCelebration() {
  wx.showToast({
    title: '🎉 太棒了!',
    icon: 'success',
    duration: 2000
  });

  // 五彩纸屑动画
  this.triggerConfetti();
}
```

**跟读评分动效**
```xml
<view class="score-display">
  <view class="score-number" animation="{{scoreAnimation}}">
    {{score}}
  </view>
  <view class="stars">
    <icon wx:for="{{stars}}" type="{{item}}" />
  </view>
</view>
```

### 3.3 错误处理

**网络错误**
```javascript
// utils/error-handler.ts
function handleNetworkError(error: any) {
  if (error.code === 'NETWORK_TIMEOUT') {
    wx.showModal({
      title: '网络超时',
      content: '请检查网络连接后重试',
      confirmText: '重试',
      success: (res) => {
        if (res.confirm) {
          retry();
        }
      }
    });
  }
}
```

**数据加载失败**
```xml
<view wx:if="{{loadingState === 'error'}}" class="error-state">
  <image src="/images/error.png" />
  <text>加载失败</text>
  <button bindtap="reload">重新加载</button>
</view>
```

---

## 四、页面结构树

```
app
├── pages
│   ├── onboarding           # 引导页
│   ├── assessment
│   │   ├── intro            # 评估介绍
│   │   ├── test             # 答题页
│   │   └── result           # 结果页
│   ├── plan
│   │   ├── scenario-select  # 场景选择
│   │   ├── time-setting     # 时间设置
│   │   └── preview          # 计划预览
│   ├── home                 # 首页/今日任务
│   ├── study
│   │   ├── dialogue         # 对话学习
│   │   ├── follow-read      # 跟读评分
│   │   └── complete         # 完成页
│   ├── vocab
│   │   ├── review           # 今日复习
│   │   ├── list             # 词汇列表
│   │   └── detail           # 词汇详情
│   ├── progress
│   │   ├── scenarios        # 场景进度
│   │   └── report           # 学习报告
│   └── profile              # 个人中心
└── components
    ├── countdown-banner     # 倒计时横幅
    ├── readiness-ring       # 就绪度环形图
    ├── dialogue-card        # 对话卡片
    ├── audio-player         # 音频播放器
    ├── phrase-list          # 短语列表
    ├── vocab-card           # 词汇卡片
    └── celebration          # 庆祝动画
```

---

## 五、状态管理

```typescript
// store/index.ts
interface AppState {
  user: {
    openid: string;
    level: string;
    subscription: string;
  };

  currentPlan: {
    id: string;
    daysLeft: number;
    todayTasks: Task[];
    overallReadiness: number;
  };

  studySession: {
    scenarioId: string;
    dialogueIndex: number;
    startTime: number;
  };

  cache: {
    scenarios: Map<string, Scenario>;
    dialogues: Map<string, Dialogue>;
  };
}

const store = {
  state: reactive<AppState>({...}),

  // Actions
  async loadTodayTasks() {
    const tasks = await api.get('/plans/today');
    this.state.currentPlan.todayTasks = tasks;
  },

  async completeTask(taskId: string) {
    await api.post(`/plans/tasks/${taskId}/complete`);
    await this.loadTodayTasks();
  }
};
```

---

## 六、性能优化

### 6.1 预加载策略

```typescript
// 在评估完成后预加载计划数据
onAssessmentComplete() {
  // 后台预加载场景列表
  this.preloadScenarios();
  // 预生成计划草稿
  this.prefetchPlanDraft();
}
```

### 6.2 缓存策略

```typescript
// 缓存场景元数据(1小时)
const scenarioCache = new TTLCache<Scenario>(3600);

async function getScenario(id: string): Promise<Scenario> {
  let scenario = scenarioCache.get(id);
  if (!scenario) {
    scenario = await api.get(`/scenarios/${id}`);
    scenarioCache.set(id, scenario);
  }
  return scenario;
}
```

### 6.3 图片懒加载

```xml
<image
  src="{{item.coverImage}}"
  lazy-load="{{true}}"
  mode="aspectFill"
/>
```

---

## 七、埋点方案

### 7.1 关键埋点

```typescript
// 页面浏览
track('page_view', {
  page: 'assessment_test',
  question_number: 3
});

// 用户操作
track('assessment_answer', {
  question_id: 'q_001',
  is_correct: true,
  time_spent: 15
});

track('scenario_completed', {
  scenario_id: 'airport_checkin',
  readiness: 0.85,
  time_spent: 65
});

track('plan_generated', {
  scenario_count: 8,
  total_days: 14,
  target_readiness: 0.85
});
```

### 7.2 漏斗分析

```
注册 (100%)
  ↓ 85%
评估开始 (85%)
  ↓ 70%
评估完成 (60%)
  ↓ 90%
计划生成 (54%)
  ↓ 80%
首次学习 (43%)
  ↓ 60%
Day 7留存 (26%)
```

---

## 八、A/B测试方案

### 8.1 测试变量

**测试1: 倒计时显示**
```
变体A: "距离出发还有12天" (紧迫感)
变体B: "还有12天准备时间" (积极)
指标: 学习频率,完成率
```

**测试2: 就绪度呈现**
```
变体A: 百分比 "67%"
变体B: 文案 "接近目标"
变体C: 混合 "67% 接近目标"
指标: 用户满意度,NPS
```

**测试3: 跟读评分标准**
```
变体A: 严格 (>85分显示"优秀")
变体B: 宽松 (>75分显示"优秀")
指标: 练习次数,放弃率
```

---

## 九、无障碍设计

```xml
<!-- 语音朗读支持 -->
<view aria-label="机场办理值机场景,当前就绪度78%">
  <text>机场办理值机</text>
  <progress percent="78" />
</view>

<!-- 键盘导航 -->
<button
  bindtap="nextQuestion"
  aria-label="下一题"
  tabindex="1">
  下一题
</button>
```

---

## 十、验收标准

### 10.1 功能完整性

- [ ] 从引导到学习全流程可走通
- [ ] 所有页面加载时间 < 2秒
- [ ] 音频播放流畅无卡顿
- [ ] 跟读评分准确率 > 85%

### 10.2 体验指标

- [ ] 新用户完成评估率 > 60%
- [ ] Day 1留存 > 40%
- [ ] Day 7留存 > 25%
- [ ] NPS评分 > 40

### 10.3 性能指标

- [ ] 首屏渲染 < 1.5秒
- [ ] 页面切换动画 60fps
- [ ] 内存占用 < 100MB
- [ ] 包体积 < 4MB

---

**下一步**: 基于此用户旅程设计,制定技术实施路线图
