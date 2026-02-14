// miniprogram/pages/assessment/test/test.ts
import { assessmentService } from '../../../services/assessment';

Page({
  data: {
    // 评估信息
    assessmentId: '',
    currentQuestion: 1,
    totalQuestions: 10,
    progress: 0,

    // 题目信息
    question: null as any,
    selectedIndex: null as number | null,
    isLastQuestion: false,

    // 音频相关
    isPlaying: false,
    listenCount: 0,
    audioContext: null as any,

    // 计时器
    timeLeft: 30,
    timerId: null as any,
    startTime: 0,

    // 状态
    loading: false
  },

  onLoad() {
    this.startAssessment();
  },

  onUnload() {
    // 清理定时器和音频
    this.cleanup();
  },

  /**
   * 启动评估
   */
  async startAssessment() {
    this.setData({ loading: true });

    try {
      const result = await assessmentService.startAssessment();

      this.setData({
        assessmentId: result.assessment_id,
        question: result.first_question,
        loading: false,
        startTime: Date.now()
      });

      // 启动计时器
      this.startTimer();

      // 如果是听力题，创建音频上下文
      if (result.first_question.type === 'listening') {
        this.initAudioContext();
      }

      // 埋点 (开发环境暂时禁用)
      // wx.reportAnalytics('question_shown', {
      //   question_id: result.first_question.id,
      //   type: result.first_question.type,
      //   level: result.first_question.level
      // });

    } catch (error) {
      console.error('启动评估失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
      this.setData({ loading: false });
    }
  },

  /**
   * 初始化音频上下文
   */
  initAudioContext() {
    const audioContext = wx.createInnerAudioContext();
    const question = this.data.question;

    console.log('🔊 设置音频URL:', question.content.audio_url);
    audioContext.src = question.content.audio_url;
    audioContext.onPlay(() => {
      console.log('✅ 音频开始播放');
      this.setData({
        isPlaying: true,
        listenCount: this.data.listenCount + 1
      });
    });

    audioContext.onEnded(() => {
      console.log('⏹️ 音频播放结束');
      this.setData({ isPlaying: false });
    });

    audioContext.onError((error) => {
      console.error('❌ 音频播放失败:', error);
      wx.showToast({
        title: '音频加载失败',
        icon: 'none'
      });
      this.setData({ isPlaying: false });
    });

    audioContext.onWaiting(() => {
      console.log('⏳ 音频加载中...');
    });

    audioContext.onCanplay(() => {
      console.log('✅ 音频可以播放');
    });

    this.setData({ audioContext });
  },

  /**
   * 切换音频播放
   */
  toggleAudio() {
    const { audioContext, isPlaying } = this.data;

    if (!audioContext) {
      wx.showToast({
        title: '音频未准备好',
        icon: 'none'
      });
      return;
    }

    if (isPlaying) {
      audioContext.pause();
      this.setData({ isPlaying: false });
    } else {
      console.log('▶️ 开始播放音频');
      audioContext.play();
    }
  },

  /**
   * 启动计时器
   */
  startTimer() {
    // 清除旧计时器
    if (this.data.timerId) {
      clearInterval(this.data.timerId);
    }

    // 重置时间
    this.setData({ timeLeft: 30 });

    // 启动新计时器
    const timerId = setInterval(() => {
      const timeLeft = this.data.timeLeft - 1;

      if (timeLeft <= 0) {
        clearInterval(this.data.timerId);
        this.setData({ timeLeft: 0 });

        // 时间到,自动提交(选择-1表示未作答)
        if (this.data.selectedIndex === null) {
          wx.showToast({
            title: '时间到,自动跳过',
            icon: 'none'
          });
          setTimeout(() => {
            this.nextQuestion();
          }, 1500);
        }
      } else {
        this.setData({ timeLeft });
      }
    }, 1000);

    this.setData({ timerId });
  },

  /**
   * 选择选项
   */
  selectOption(e: any) {
    const index = e.currentTarget.dataset.index;
    console.log('选择选项:', index, '类型:', typeof index);
    this.setData({ selectedIndex: index });
    console.log('选择后 selectedIndex:', this.data.selectedIndex);
  },

  /**
   * 下一题
   */
  async nextQuestion() {
    const { assessmentId, question, selectedIndex, startTime } = this.data;

    console.log('nextQuestion 被调用, selectedIndex:', selectedIndex, '类型:', typeof selectedIndex);

    // 计算答题时间
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);

    // 停止计时器
    if (this.data.timerId) {
      clearInterval(this.data.timerId);
    }

    // 停止音频
    if (this.data.audioContext) {
      try {
        this.data.audioContext.stop();
        this.data.audioContext.destroy();
      } catch (e) {
        console.log('音频停止失败:', e);
      }
      this.setData({ audioContext: null });
    }

    this.setData({ loading: true });

    try {
      // 提交答案
      const result = await assessmentService.submitAnswer({
        assessment_id: assessmentId,
        question_id: question.id,
        answer_index: selectedIndex !== null ? selectedIndex : -1,
        time_spent: timeSpent
      });

      // 埋点 (开发环境暂时禁用)
      // wx.reportAnalytics('question_answered', {
      //   question_id: question.id,
      //   is_correct: result.is_correct,
      //   time_spent: timeSpent
      // });

      // 显示反馈
      if (result.is_correct) {
        wx.showToast({
          title: '✓ 正确',
          icon: 'success',
          duration: 800
        });
      } else {
        wx.showToast({
          title: '✗ 错误',
          icon: 'none',
          duration: 800
        });
      }

      // 等待反馈显示
      await new Promise(resolve => setTimeout(resolve, 1000));

      // 检查是否有下一题
      if (result.next_question) {
        // 更新进度
        const currentQuestion = this.data.currentQuestion + 1;
        const progress = (currentQuestion / this.data.totalQuestions) * 100;
        const isLastQuestion = currentQuestion === this.data.totalQuestions;

        console.log('更新到下一题, currentQuestion:', currentQuestion, 'progress:', progress);

        this.setData({
          question: result.next_question,
          selectedIndex: null,
          currentQuestion,
          progress,
          isLastQuestion,
          loading: false,
          startTime: Date.now(),
          listenCount: 0,
          isPlaying: false
        });

        console.log('setData 后, selectedIndex:', this.data.selectedIndex, 'currentQuestion:', this.data.currentQuestion);

        // 重新启动计时器
        this.startTimer();

        // 如果是听力题，创建新的音频上下文
        if (result.next_question.type === 'listening') {
          this.initAudioContext();
        }

      } else {
        // 评估完成
        await this.completeAssessment();
      }

    } catch (error) {
      console.error('提交答案失败:', error);
      wx.showToast({
        title: '提交失败',
        icon: 'none'
      });
      this.setData({ loading: false });
    }
  },

  /**
   * 完成评估
   */
  async completeAssessment() {
    try {
      const result = await assessmentService.completeAssessment({
        assessment_id: this.data.assessmentId
      });

      // 埋点 (开发环境暂时禁用)
      // wx.reportAnalytics('assessment_completed', {
      //   assessment_id: this.data.assessmentId,
      //   overall_level: result.overall_level,
      //   duration: result.duration
      // });

      // 跳转到结果页
      wx.redirectTo({
        url: `/pages/assessment/result/result?data=${encodeURIComponent(JSON.stringify(result))}`
      });

    } catch (error) {
      console.error('完成评估失败:', error);
      wx.showToast({
        title: '评估失败',
        icon: 'none'
      });
    }
  },

  /**
   * 清理资源
   */
  cleanup() {
    // 清除定时器
    if (this.data.timerId) {
      clearInterval(this.data.timerId);
    }

    // 销毁音频
    if (this.data.audioContext) {
      try {
        this.data.audioContext.stop();
        this.data.audioContext.destroy();
      } catch (e) {
        console.log('清理音频失败:', e);
      }
    }
  }
});
