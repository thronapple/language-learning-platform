# UI/UX 优化方案

## 📊 当前问题分析

### 1. 设计系统不统一
- **颜色系统混乱**：全局定义蓝色主题（#1677ff），但页面大量使用紫色渐变（#667eea → #764ba2）
- **CSS变量未使用**：定义了`--primary-color`等变量但实际未应用
- **图标系统**：使用表情符号（🎯📊）不够专业，缺乏一致性

### 2. 交互体验不足
- **缺少加载状态**：无骨架屏、加载动画
- **无触觉反馈**：点击按钮无震动反馈
- **过渡生硬**：页面切换、状态变化缺少过渡动画
- **手势操作缺失**：无左右滑动切换句子等手势

### 3. 视觉层次不清晰
- **信息密度过高**：学习计划页内容过于拥挤
- **对比度不足**：部分文字颜色太浅（opacity: 0.9）
- **缺少呼吸感**：间距不够，元素过于紧凑

### 4. 用户反馈不明确
- **成功/失败状态**：无toast提示
- **操作确认**：关键操作（跳过评估）无二次确认
- **进度可见性**：音频播放进度不可视化

---

## 🎨 优化方案

### 第一阶段：设计系统统一（2-3天）

#### 1.1 色彩系统重构

**主题色选择**：统一使用紫色系（符合教育类产品调性）

```wxss
/* styles/design-tokens.wxss */
:root {
  /* 主色 - 紫色系 */
  --primary-50: #f5f3ff;
  --primary-100: #ede9fe;
  --primary-200: #ddd6fe;
  --primary-300: #c4b5fd;
  --primary-400: #a78bfa;
  --primary-500: #8b5cf6;  /* 主色 */
  --primary-600: #7c3aed;
  --primary-700: #6d28d9;
  --primary-800: #5b21b6;
  --primary-900: #4c1d95;

  /* 渐变色 */
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-warm: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --gradient-cool: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);

  /* 功能色 */
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;

  /* 中性色 */
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-200: #e5e7eb;
  --gray-300: #d1d5db;
  --gray-400: #9ca3af;
  --gray-500: #6b7280;
  --gray-600: #4b5563;
  --gray-700: #374151;
  --gray-800: #1f2937;
  --gray-900: #111827;

  /* 文字色 */
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --text-tertiary: #9ca3af;
  --text-inverse: #ffffff;

  /* 背景色 */
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --bg-tertiary: #f3f4f6;

  /* 边框 */
  --border-light: #e5e7eb;
  --border-medium: #d1d5db;
  --border-dark: #9ca3af;

  /* 阴影 */
  --shadow-sm: 0 1rpx 2rpx rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4rpx 6rpx -1rpx rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10rpx 15rpx -3rpx rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20rpx 25rpx -5rpx rgba(0, 0, 0, 0.1);

  /* 圆角 */
  --radius-sm: 8rpx;
  --radius-md: 12rpx;
  --radius-lg: 16rpx;
  --radius-xl: 24rpx;
  --radius-full: 9999rpx;

  /* 间距 */
  --space-1: 4rpx;
  --space-2: 8rpx;
  --space-3: 12rpx;
  --space-4: 16rpx;
  --space-5: 20rpx;
  --space-6: 24rpx;
  --space-8: 32rpx;
  --space-10: 40rpx;
  --space-12: 48rpx;
  --space-16: 64rpx;

  /* 动画时长 */
  --duration-fast: 150ms;
  --duration-base: 300ms;
  --duration-slow: 500ms;

  /* 缓动函数 */
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
```

#### 1.2 图标系统升级

**替换方案**：
1. 使用iconfont（阿里巴巴矢量图标库）
2. 或使用微信官方weui图标
3. 关键图标使用SVG

```javascript
// 示例：引入iconfont
// 1. 在iconfont.cn创建项目，添加图标
// 2. 生成CSS，复制到项目
// 3. 使用class引用
<text class="iconfont icon-audio"></text>
```

#### 1.3 排版系统规范

```wxss
/* 字体大小 */
--font-xs: 20rpx;   /* 辅助文字 */
--font-sm: 24rpx;   /* 次要文字 */
--font-base: 28rpx; /* 正文 */
--font-lg: 32rpx;   /* 小标题 */
--font-xl: 36rpx;   /* 大标题 */
--font-2xl: 40rpx;  /* 特大标题 */
--font-3xl: 48rpx;  /* 超大标题 */

/* 行高 */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;

/* 字重 */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

---

### 第二阶段：交互体验优化（3-4天）

#### 2.1 微交互动画

**按钮按下效果**：
```wxss
/* 按钮通用样式 */
.btn {
  transition: all var(--duration-fast) var(--ease-out);
  position: relative;
  overflow: hidden;
}

.btn:active {
  transform: scale(0.98);
  opacity: 0.9;
}

/* 水波纹效果 */
.btn::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width var(--duration-base), height var(--duration-base);
}

.btn:active::after {
  width: 300rpx;
  height: 300rpx;
}
```

**卡片悬浮效果**：
```wxss
.card-interactive {
  transition: all var(--duration-base) var(--ease-out);
}

.card-interactive:active {
  transform: translateY(4rpx);
  box-shadow: var(--shadow-sm);
}
```

#### 2.2 触觉反馈

```typescript
// utils/haptics.ts
export const haptics = {
  /** 轻触反馈 - 用于按钮点击 */
  light() {
    wx.vibrateShort({ type: 'light' })
  },

  /** 中等反馈 - 用于重要操作 */
  medium() {
    wx.vibrateShort({ type: 'medium' })
  },

  /** 强烈反馈 - 用于完成、成功 */
  heavy() {
    wx.vibrateShort({ type: 'heavy' })
  },

  /** 成功反馈 */
  success() {
    wx.vibrateShort({ type: 'heavy' })
  },

  /** 警告反馈 */
  warning() {
    wx.vibrateShort({ type: 'medium' })
  },

  /** 错误反馈 */
  error() {
    wx.vibrateLong()
  }
}

// 使用示例
import { haptics } from '@/utils/haptics'

onButtonClick() {
  haptics.light()
  // 执行操作...
}

onComplete() {
  haptics.success()
  // 显示完成状态...
}
```

#### 2.3 加载状态

**骨架屏组件**：
```wxml
<!-- components/skeleton/skeleton.wxml -->
<view class="skeleton">
  <view class="skeleton-header">
    <view class="skeleton-circle"></view>
    <view class="skeleton-lines">
      <view class="skeleton-line" style="width: 60%;"></view>
      <view class="skeleton-line" style="width: 40%;"></view>
    </view>
  </view>

  <view class="skeleton-content">
    <view class="skeleton-line"></view>
    <view class="skeleton-line"></view>
    <view class="skeleton-line" style="width: 80%;"></view>
  </view>
</view>
```

```wxss
/* components/skeleton/skeleton.wxss */
.skeleton-line,
.skeleton-circle {
  background: linear-gradient(
    90deg,
    var(--gray-200) 25%,
    var(--gray-100) 50%,
    var(--gray-200) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.skeleton-line {
  height: 28rpx;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-3);
}

.skeleton-circle {
  width: 80rpx;
  height: 80rpx;
  border-radius: var(--radius-full);
}
```

**加载指示器**：
```typescript
// utils/loading.ts
export const loading = {
  show(title = '加载中...') {
    wx.showLoading({ title, mask: true })
  },

  hide() {
    wx.hideLoading()
  },

  async wrap<T>(promise: Promise<T>, title?: string): Promise<T> {
    this.show(title)
    try {
      return await promise
    } finally {
      this.hide()
    }
  }
}

// 使用
await loading.wrap(
  api.getDialogue(id),
  '加载对话中...'
)
```

#### 2.4 手势操作

**左右滑动切换句子**：
```typescript
// pages/study/dialogue/dialogue.ts
data: {
  touchStartX: 0,
  touchStartY: 0
},

onTouchStart(e: any) {
  this.setData({
    touchStartX: e.touches[0].pageX,
    touchStartY: e.touches[0].pageY
  })
},

onTouchEnd(e: any) {
  const { touchStartX, touchStartY, currentIndex, dialogue } = this.data
  const touchEndX = e.changedTouches[0].pageX
  const touchEndY = e.changedTouches[0].pageY

  const deltaX = touchEndX - touchStartX
  const deltaY = touchEndY - touchStartY

  // 判断是否为横向滑动（横向距离 > 纵向距离）
  if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
    if (deltaX > 0 && currentIndex > 0) {
      // 右滑：上一句
      haptics.light()
      this.previousSentence()
    } else if (deltaX < 0 && currentIndex < dialogue.sentences.length - 1) {
      // 左滑：下一句
      haptics.light()
      this.nextSentence()
    }
  }
}
```

```wxml
<!-- 在句子容器上添加手势事件 -->
<view
  class="sentence-container"
  bindtouchstart="onTouchStart"
  bindtouchend="onTouchEnd"
>
  <!-- 句子内容 -->
</view>
```

#### 2.5 Toast反馈系统

```typescript
// utils/toast.ts
export const toast = {
  success(title: string, duration = 2000) {
    wx.showToast({
      title,
      icon: 'success',
      duration
    })
    haptics.success()
  },

  error(title: string, duration = 2000) {
    wx.showToast({
      title,
      icon: 'error',
      duration
    })
    haptics.error()
  },

  info(title: string, duration = 2000) {
    wx.showToast({
      title,
      icon: 'none',
      duration
    })
  },

  loading(title = '加载中...') {
    wx.showLoading({ title, mask: true })
  },

  hide() {
    wx.hideToast()
    wx.hideLoading()
  }
}
```

---

### 第三阶段：页面级优化（4-5天）

#### 3.1 学习计划页优化

**问题**：
- 信息密度过高
- 今日任务和场景目标视觉权重相同
- 操作按钮固定底部占用空间

**优化方案**：
```wxml
<!-- 优化后的布局 -->
<view class="plan-page">
  <!-- 1. 头部简化 - 突出关键信息 -->
  <view class="hero-section">
    <view class="level-indicator">
      <text class="level">{{plan.overall_level}}</text>
      <text class="label">当前等级</text>
    </view>

    <view class="progress-ring">
      <!-- 环形进度条 -->
      <canvas canvas-id="progressRing"></canvas>
      <view class="progress-center">
        <text class="percentage">{{plan.overall_progress}}%</text>
      </view>
    </view>

    <view class="streak-info">
      <text class="streak-number">{{plan.streak_days}}</text>
      <text class="streak-label">天连续学习</text>
    </view>
  </view>

  <!-- 2. 今日任务 - 卡片式，可滑动 -->
  <view class="section">
    <view class="section-header">
      <text class="title">今日任务</text>
      <text class="badge">{{todayTasksCount}}</text>
    </view>

    <scroll-view
      class="tasks-scroll"
      scroll-x
      show-scrollbar="{{false}}"
    >
      <view
        wx:for="{{todayTasks}}"
        wx:key="dialogue_id"
        class="task-card {{item.is_completed ? 'completed' : ''}}"
        bindtap="startDialogue"
        data-dialogue-id="{{item.dialogue_id}}"
      >
        <view class="task-status">
          <view class="checkbox {{item.is_completed ? 'checked' : ''}}">
            <text class="icon" wx:if="{{item.is_completed}}">✓</text>
          </view>
        </view>
        <text class="task-title">{{item.dialogue_title}}</text>
        <view class="task-meta">
          <text class="meta-item">
            <text class="icon">⏱</text>
            {{item.estimated_minutes}}分钟
          </text>
          <text class="meta-item">
            <text class="icon">📚</text>
            {{item.vocabulary_count}}词
          </text>
        </view>
      </view>
    </scroll-view>
  </view>

  <!-- 3. 快捷操作 - 取代固定底部按钮 -->
  <view class="quick-actions">
    <view class="action-card primary" bindtap="continueStudy">
      <view class="action-icon">▶️</view>
      <view class="action-content">
        <text class="action-title">继续学习</text>
        <text class="action-subtitle">{{nextTask}}</text>
      </view>
    </view>

    <view class="action-card-grid">
      <view class="action-card-small" bindtap="viewVocabulary">
        <text class="icon">📖</text>
        <text class="label">词汇复习</text>
      </view>
      <view class="action-card-small" bindtap="viewStatistics">
        <text class="icon">📊</text>
        <text class="label">学习统计</text>
      </view>
    </view>
  </view>

  <!-- 4. 场景目标 - 可折叠，默认只显示高优先级 -->
  <view class="section">
    <view class="section-header" bindtap="toggleScenarios">
      <text class="title">学习场景</text>
      <text class="expand-icon">{{scenariosExpanded ? '▼' : '▶'}}</text>
    </view>

    <view class="scenarios" wx:if="{{scenariosExpanded}}">
      <!-- 场景列表 -->
    </view>
  </view>
</view>
```

```wxss
/* 环形进度条样式 */
.hero-section {
  background: var(--gradient-primary);
  padding: var(--space-10);
  display: flex;
  justify-content: space-around;
  align-items: center;
  color: var(--text-inverse);
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}

.progress-ring {
  position: relative;
  width: 160rpx;
  height: 160rpx;
}

.progress-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.percentage {
  font-size: var(--font-3xl);
  font-weight: var(--font-bold);
}

/* 横向滚动任务卡片 */
.tasks-scroll {
  white-space: nowrap;
  padding: var(--space-4) 0;
}

.task-card {
  display: inline-block;
  width: 280rpx;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-right: var(--space-4);
  box-shadow: var(--shadow-md);
  vertical-align: top;
  white-space: normal;
  transition: all var(--duration-base) var(--ease-out);
}

.task-card:active {
  transform: translateY(4rpx) scale(0.98);
  box-shadow: var(--shadow-sm);
}

.task-card.completed {
  opacity: 0.6;
  background: var(--gray-50);
}

/* 快捷操作卡片 */
.quick-actions {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.action-card.primary {
  background: var(--gradient-primary);
  color: var(--text-inverse);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  box-shadow: var(--shadow-lg);
}

.action-card-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.action-card-small {
  background: var(--bg-primary);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  box-shadow: var(--shadow-md);
}
```

#### 3.2 对话学习页优化

**音频进度可视化**：
```wxml
<view class="audio-player-enhanced">
  <view class="waveform">
    <!-- 音频波形可视化 -->
    <view
      wx:for="{{waveformBars}}"
      wx:key="index"
      class="waveform-bar"
      style="height: {{item}}%;"
    ></view>
  </view>

  <view class="playback-progress">
    <view class="progress-track">
      <view
        class="progress-played"
        style="width: {{audioProgress}}%;"
      ></view>
      <view
        class="progress-handle"
        style="left: {{audioProgress}}%;"
      ></view>
    </view>
    <view class="time-display">
      <text class="current-time">{{formatTime(currentTime)}}</text>
      <text class="total-time">{{formatTime(duration)}}</text>
    </view>
  </view>
</view>
```

**录音反馈优化**：
```wxml
<view class="record-section-enhanced">
  <button
    class="record-btn {{recordState}}"
    bindtouchstart="startRecording"
    bindtouchend="stopRecording"
  >
    <view class="record-icon">
      <view class="mic-icon"></view>
      <view
        class="sound-wave"
        wx:if="{{isRecording}}"
      >
        <!-- 录音声波动画 -->
        <view class="wave"></view>
        <view class="wave"></view>
        <view class="wave"></view>
      </view>
    </view>
    <text class="record-text">
      {{isRecording ? '松开结束' : '按住说话'}}
    </text>
  </button>

  <!-- 录音后播放 -->
  <view class="recording-playback" wx:if="{{lastRecording}}">
    <button class="play-recording" bindtap="playRecording">
      <text class="icon">{{recordingPlaying ? '⏸' : '▶️'}}</text>
    </button>
    <view class="recording-waveform">
      <!-- 录音波形 -->
    </view>
    <button class="delete-recording" bindtap="deleteRecording">
      <text class="icon">🗑</text>
    </button>
  </view>
</view>
```

```wxss
/* 声波动画 */
.sound-wave {
  position: absolute;
  display: flex;
  gap: 6rpx;
  align-items: center;
}

.wave {
  width: 6rpx;
  height: 40rpx;
  background: var(--text-inverse);
  border-radius: var(--radius-full);
  animation: wave-animation 1s ease-in-out infinite;
}

.wave:nth-child(2) {
  animation-delay: 0.2s;
}

.wave:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes wave-animation {
  0%, 100% {
    transform: scaleY(0.5);
  }
  50% {
    transform: scaleY(1.5);
  }
}
```

#### 3.3 评估结果页优化

**成就感增强**：
```wxml
<view class="result-page">
  <!-- 1. 庆祝动画 -->
  <view class="celebration" wx:if="{{showCelebration}}">
    <lottie-animation class="confetti" path="/animations/confetti.json" />
  </view>

  <!-- 2. 等级徽章 - 3D效果 -->
  <view class="badge-showcase">
    <view class="badge-3d {{level}}">
      <view class="badge-front">
        <text class="badge-level">{{level}}</text>
      </view>
      <view class="badge-glow"></view>
    </view>
    <text class="level-name">{{levelName}}</text>
    <text class="level-desc">{{levelDesc}}</text>
  </view>

  <!-- 3. 能力雷达图 - 交互式 -->
  <view class="radar-section">
    <canvas
      canvas-id="radarChart"
      class="radar-canvas"
      bindtap="onRadarTap"
    ></canvas>
    <view class="dimension-details">
      <view
        wx:for="{{dimensions}}"
        wx:key="name"
        class="dimension-item {{selectedDimension === item.name ? 'active' : ''}}"
        bindtap="selectDimension"
        data-dimension="{{item.name}}"
      >
        <view class="dimension-icon" style="color: {{item.color}};">
          {{item.icon}}
        </view>
        <view class="dimension-info">
          <text class="dimension-name">{{item.name}}</text>
          <view class="dimension-bar">
            <view
              class="dimension-fill"
              style="width: {{item.score}}%; background: {{item.color}};"
            ></view>
          </view>
          <text class="dimension-score">{{item.score}}/100</text>
        </view>
      </view>
    </view>
  </view>

  <!-- 4. 建议卡片 - 可操作 -->
  <view class="recommendations">
    <view class="section-title">为你推荐</view>
    <view
      wx:for="{{recommendations}}"
      wx:key="id"
      class="recommendation-card"
      bindtap="startScenario"
      data-id="{{item.id}}"
    >
      <view class="card-badge">推荐</view>
      <view class="card-content">
        <text class="card-title">{{item.title}}</text>
        <text class="card-reason">{{item.reason}}</text>
      </view>
      <view class="card-action">
        <text class="action-text">开始学习</text>
        <text class="action-icon">→</text>
      </view>
    </view>
  </view>

  <!-- 5. CTA按钮 - 渐变动画 -->
  <button class="cta-btn" bindtap="generatePlan">
    <view class="btn-gradient"></view>
    <text class="btn-text">生成专属学习计划</text>
    <text class="btn-icon">✨</text>
  </button>
</view>
```

```wxss
/* 3D徽章效果 */
.badge-3d {
  position: relative;
  width: 200rpx;
  height: 200rpx;
  transform-style: preserve-3d;
  animation: badge-rotate 3s ease-in-out infinite;
}

@keyframes badge-rotate {
  0%, 100% {
    transform: rotateY(0deg);
  }
  50% {
    transform: rotateY(15deg);
  }
}

.badge-front {
  width: 100%;
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 20rpx 60rpx rgba(123, 97, 255, 0.4);
}

.badge-glow {
  position: absolute;
  top: -10rpx;
  left: -10rpx;
  right: -10rpx;
  bottom: -10rpx;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  filter: blur(20rpx);
  opacity: 0.6;
  z-index: -1;
  animation: glow-pulse 2s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 0.9;
  }
}

/* CTA按钮渐变动画 */
.cta-btn {
  position: relative;
  overflow: hidden;
  background: var(--gradient-primary);
  color: var(--text-inverse);
  border-radius: var(--radius-full);
  padding: var(--space-6) var(--space-10);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  box-shadow: var(--shadow-xl);
}

.btn-gradient {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: gradient-slide 2s ease-in-out infinite;
}

@keyframes gradient-slide {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}
```

---

### 第四阶段：性能优化（2-3天）

#### 4.1 图片优化

```typescript
// 使用webp格式，添加占位符
<image
  src="{{imageUrl}}"
  webp
  lazy-load
  mode="aspectFill"
  bindload="onImageLoad"
  binderror="onImageError"
>
  <view class="image-placeholder" wx:if="{{!imageLoaded}}">
    <view class="skeleton-image"></view>
  </view>
</image>

// 图片CDN优化
const optimizeImage = (url: string, width: number) => {
  // 使用微信云存储的图片处理
  return `${url}?imageMogr2/thumbnail/${width}x/format/webp/quality/80`
}
```

#### 4.2 列表虚拟化

```wxml
<!-- 使用recycle-view组件实现虚拟列表 -->
<recycle-view
  batch="{{batchSetRecycleData}}"
  id="recycleId"
  height="{{windowHeight}}"
>
  <recycle-item wx:for="{{recycleList}}" wx:key="id">
    <view class="item">{{item.title}}</view>
  </recycle-item>
</recycle-view>
```

#### 4.3 音频预加载

```typescript
// services/audio-preloader.ts
class AudioPreloader {
  private cache: Map<string, wx.InnerAudioContext> = new Map()

  preload(urls: string[]) {
    urls.forEach(url => {
      if (!this.cache.has(url)) {
        const audio = wx.createInnerAudioContext()
        audio.src = url
        audio.onCanplay(() => {
          console.log(`Audio preloaded: ${url}`)
        })
        this.cache.set(url, audio)
      }
    })
  }

  get(url: string): wx.InnerAudioContext | undefined {
    return this.cache.get(url)
  }

  clear() {
    this.cache.forEach(audio => audio.destroy())
    this.cache.clear()
  }
}

export const audioPreloader = new AudioPreloader()

// 使用
onLoad() {
  const urls = this.data.dialogue.sentences.map(s => s.audio_url)
  audioPreloader.preload(urls)
}
```

---

## 📋 实施计划

### Week 1: 设计系统基础
- **Day 1-2**: 设计token定义，创建组件库
- **Day 3-4**: 替换全局样式，统一颜色/字体/间距
- **Day 5**: 图标系统迁移

### Week 2: 交互优化
- **Day 1-2**: 微交互动画、触觉反馈
- **Day 3-4**: 加载状态、手势操作
- **Day 5**: Toast系统、错误处理

### Week 3: 页面优化
- **Day 1-2**: 学习计划页重构
- **Day 3-4**: 对话学习页优化
- **Day 5**: 评估结果页优化

### Week 4: 性能与细节
- **Day 1-2**: 性能优化（图片、列表、音频）
- **Day 3-4**: 细节打磨、动画调优
- **Day 5**: 测试、bug修复

---

## ✅ 验收标准

### 视觉一致性
- [ ] 所有页面使用统一的设计token
- [ ] 色彩使用符合设计规范
- [ ] 间距、圆角、阴影统一

### 交互流畅度
- [ ] 所有按钮有触觉反馈
- [ ] 页面切换有过渡动画
- [ ] 加载状态有骨架屏
- [ ] 60fps流畅度

### 用户反馈
- [ ] 操作有即时反馈（toast/vibrate）
- [ ] 错误有友好提示
- [ ] 成功有庆祝动画

### 性能指标
- [ ] 首屏加载 < 1.5s
- [ ] 页面切换 < 300ms
- [ ] 音频播放延迟 < 200ms
- [ ] 内存占用 < 100MB

---

## 🎯 预期效果

### 数据指标提升
- **留存率**: D1 +15%, D7 +10%
- **使用时长**: +30%
- **完成率**: +25%
- **NPS评分**: +20分

### 用户体验改善
- 界面更现代、专业
- 操作更流畅、直观
- 反馈更及时、友好
- 学习更有成就感

---

*最后更新: 2025-10-03*
