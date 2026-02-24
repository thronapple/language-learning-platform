/**
 * 对话学习页 - 优化版
 * 添加触觉反馈、手势交互和流畅动画
 */

import { haptics } from '../../../utils/haptics';
import { toast } from '../../../utils/toast';
import { loading } from '../../../utils/loading';
import { request } from '../../../services/request';

interface Sentence {
  order: number;
  speaker: string;
  text_en: string;
  text_zh: string;
  audio_url: string;
  phonetic: string;
  key_words: string[];
  grammar_points: string[];
}

interface Dialogue {
  id: string;
  title_en: string;
  title_zh: string;
  level: string;
  sentences: Sentence[];
}

Page({
  data: {
    dialogue: null as Dialogue | null,
    currentIndex: 0,
    showPhonetic: true,
    showTranslation: false,
    loading: true,

    // 音频相关
    audioContext: null as any,
    isPlaying: false,
    playCount: 0,
    playbackRate: 1.0,

    // 录音相关
    recorderManager: null as any,
    isRecording: false,
    recordCount: 0,
    recognizedText: '',
    scoreInfo: null as { score: number; level: string; color: string } | null,
    showScore: false,
    evaluating: false,

    // 完成相关
    showCompletion: false,
    startTime: 0,

    // 手势相关
    touchStartX: 0,
    touchStartY: 0
  },

  onLoad(options: any) {
    console.log('[Dialogue] Page loaded, id:', options.id);
    const { id } = options;
    this.setData({ startTime: Date.now() });
    this.loadDialogue(id);
    this.initRecorder();
  },

  onShow() {
    // 页面显示时轻触反馈
    haptics.light();
  },

  onUnload() {
    console.log('[Dialogue] Page unload');
    this.cleanup();
  },

  /**
   * 加载对话数据
   */
  async loadDialogue(dialogueId: string) {
    this.setData({ loading: true });

    try {
      // 调用后端API获取对话（带TTS音频）
      const dialogue = await loading.delayWrap(
        request.get<Dialogue>(`/api/dialogues/${dialogueId}`),
        '加载对话中...',
        300
      );

      console.log('[Dialogue] Data loaded:', dialogue);

      this.setData({
        dialogue: dialogue,
        loading: false
      });

      this.initAudioContext();

      // 埋点
      wx.reportAnalytics('dialogue_load', {
        dialogue_id: dialogueId,
        sentence_count: dialogue.sentences.length
      });

    } catch (error) {
      console.error('[Dialogue] Load failed:', error);
      this.setData({ loading: false });
      toast.error('加载对话失败');

      // 返回上一页
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }
  },

  /**
   * 初始化音频上下文
   */
  initAudioContext() {
    const audioContext = wx.createInnerAudioContext();

    audioContext.onPlay(() => {
      this.setData({ isPlaying: true });
    });

    audioContext.onEnded(() => {
      this.setData({
        isPlaying: false,
        playCount: this.data.playCount + 1
      });
    });

    audioContext.onError((error) => {
      console.error('音频播放失败:', error);
      this.setData({ isPlaying: false });
    });

    this.setData({ audioContext });
    this.loadCurrentAudio();
  },

  /**
   * 加载当前句子音频
   */
  loadCurrentAudio() {
    const { dialogue, currentIndex, audioContext } = this.data;
    if (!dialogue || !audioContext) return;

    const currentSentence = dialogue.sentences[currentIndex];
    audioContext.src = currentSentence.audio_url;
  },

  /**
   * 切换音频播放
   */
  toggleAudio() {
    const { audioContext, isPlaying } = this.data;
    if (!audioContext) return;

    // 触觉反馈
    haptics.light();

    if (isPlaying) {
      audioContext.pause();
      this.setData({ isPlaying: false });
    } else {
      audioContext.play();
    }
  },

  /**
   * 切换播放速度
   */
  toggleSpeed() {
    const rates = [0.8, 1.0, 1.2, 1.5];
    const currentRate = this.data.playbackRate;
    const currentIndex = rates.indexOf(currentRate);
    const nextRate = rates[(currentIndex + 1) % rates.length];

    // 触觉反馈
    haptics.light();

    this.data.audioContext.playbackRate = nextRate;
    this.setData({ playbackRate: nextRate });

    toast.info(`播放速度: ${nextRate}x`);
  },

  /**
   * 初始化录音器
   */
  initRecorder() {
    const recorderManager = wx.getRecorderManager();

    recorderManager.onStart(() => {
      console.log('[Dialogue] 录音开始');
    });

    recorderManager.onStop((res: any) => {
      console.log('[Dialogue] 录音停止', res);
      this.setData({
        isRecording: false,
        recordCount: this.data.recordCount + 1,
      });

      // 上传录音到后端评测
      this.uploadAndEvaluate(res.tempFilePath);
    });

    recorderManager.onError((error: any) => {
      console.error('[Dialogue] 录音失败:', error);
      this.setData({ isRecording: false });
      toast.error('录音失败');
    });

    this.setData({ recorderManager });
  },

  /**
   * 上传录音并评测发音
   */
  uploadAndEvaluate(filePath: string) {
    const { dialogue, currentIndex } = this.data;
    if (!dialogue) return;

    const reference = dialogue.sentences[currentIndex].text_en;
    this.setData({ evaluating: true, showScore: false });

    const baseUrl = request.getBaseUrl();

    wx.uploadFile({
      url: `${baseUrl}/api/speech/evaluate`,
      filePath,
      name: 'file',
      formData: { reference },
      success: (res) => {
        try {
          const data = JSON.parse(res.data);
          this.setData({
            evaluating: false,
            showScore: true,
            recognizedText: data.recognized || '',
            scoreInfo: {
              score: data.score ?? 0,
              level: data.level || '识别失败',
              color: data.color || '#999',
            },
          });
          // 3秒后自动隐藏
          setTimeout(() => this.setData({ showScore: false }), 3000);
        } catch (e) {
          console.error('[Dialogue] Parse evaluate result failed:', e);
          this.setData({ evaluating: false });
        }
      },
      fail: (err) => {
        console.error('[Dialogue] Upload evaluate failed:', err);
        this.setData({ evaluating: false });
        toast.error('评测失败，请重试');
      },
    });
  },

  /**
   * 开始录音
   */
  startRecording() {
    const { recorderManager } = this.data;
    if (!recorderManager) return;

    try {
      haptics.medium();

      recorderManager.start({
        duration: 15000,
        format: 'mp3',
        sampleRate: 16000,
        numberOfChannels: 1,
      });
      this.setData({ isRecording: true, recognizedText: '', showScore: false });

      wx.reportAnalytics('recording_start', {
        sentence_index: this.data.currentIndex,
      });
    } catch (error) {
      console.error('[Dialogue] Record start failed:', error);
      toast.error('录音启动失败');
    }
  },

  /**
   * 停止录音
   */
  stopRecording() {
    const { recorderManager, isRecording } = this.data;
    if (!recorderManager || !isRecording) return;

    haptics.light();
    recorderManager.stop();
    this.setData({ isRecording: false });
  },

  /**
   * 切换音标显示
   */
  togglePhonetic() {
    haptics.light();
    this.setData({ showPhonetic: !this.data.showPhonetic });
  },

  /**
   * 切换翻译显示
   */
  toggleTranslation() {
    haptics.light();
    this.setData({ showTranslation: !this.data.showTranslation });
  },

  /**
   * 重复播放
   */
  repeatSentence() {
    const { audioContext } = this.data;
    if (!audioContext) return;

    haptics.light();
    audioContext.seek(0);
    audioContext.play();
  },

  /**
   * 显示笔记
   */
  showNotes() {
    haptics.light();
    toast.info('笔记功能开发中');
  },

  /**
   * 上一句
   */
  previousSentence() {
    const { currentIndex, audioContext } = this.data;
    if (currentIndex === 0) {
      toast.info('已经是第一句了');
      return;
    }

    // 触觉反馈
    haptics.light();

    // 停止当前音频
    if (audioContext) {
      audioContext.stop();
    }

    const newIndex = currentIndex - 1;
    this.setData({
      currentIndex: newIndex,
      isPlaying: false
    });

    this.loadCurrentAudio();
  },

  /**
   * 下一句
   */
  nextSentence() {
    const { dialogue, currentIndex, audioContext } = this.data;
    if (!dialogue) return;

    // 触觉反馈
    haptics.light();

    // 停止当前音频
    if (audioContext) {
      audioContext.stop();
    }

    // 检查是否最后一句
    if (currentIndex === dialogue.sentences.length - 1) {
      this.showCompletionModal();
      return;
    }

    const newIndex = currentIndex + 1;
    this.setData({
      currentIndex: newIndex,
      isPlaying: false
    });

    this.loadCurrentAudio();

    // 埋点
    wx.reportAnalytics('sentence_complete', {
      sentence_index: currentIndex
    });
  },

  /**
   * 手势开始
   */
  onTouchStart(e: any) {
    this.setData({
      touchStartX: e.touches[0].pageX,
      touchStartY: e.touches[0].pageY
    });
  },

  /**
   * 手势结束 - 左右滑动切换句子
   */
  onTouchEnd(e: any) {
    const { touchStartX, touchStartY, currentIndex, dialogue } = this.data;
    const touchEndX = e.changedTouches[0].pageX;
    const touchEndY = e.changedTouches[0].pageY;

    const deltaX = touchEndX - touchStartX;
    const deltaY = touchEndY - touchStartY;

    // 判断是否为横向滑动（横向距离 > 纵向距离 && 横向距离 > 阈值）
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
      if (deltaX > 0 && currentIndex > 0) {
        // 右滑：上一句
        console.log('[Dialogue] Swipe right, previous sentence');
        this.previousSentence();
      } else if (deltaX < 0 && dialogue && currentIndex < dialogue.sentences.length - 1) {
        // 左滑：下一句
        console.log('[Dialogue] Swipe left, next sentence');
        this.nextSentence();
      }
    }
  },

  /**
   * 显示完成弹窗
   */
  showCompletionModal() {
    // 成功反馈
    haptics.success();

    this.setData({ showCompletion: true });

    // 埋点
    const duration = Math.floor((Date.now() - this.data.startTime) / 1000);
    wx.reportAnalytics('dialogue_complete', {
      dialogue_id: this.data.dialogue?.id,
      duration,
      play_count: this.data.playCount,
      record_count: this.data.recordCount
    });
  },

  /**
   * 完成学习
   */
  async finishDialogue() {
    console.log('[Dialogue] Finish dialogue');
    haptics.success();

    // Save progress to server
    try {
      const duration = Math.floor((Date.now() - this.data.startTime) / 1000);
      await request.post('/api/dialogue/complete', {
        dialogue_id: this.data.dialogue?.id,
        play_count: this.data.playCount,
        record_count: this.data.recordCount,
        duration,
      });
    } catch (err) {
      console.warn('[Dialogue] Progress save failed:', err);
    }

    toast.success('学习完成！');

    setTimeout(() => {
      wx.navigateBack();
    }, 1500);
  },

  /**
   * 再次复习
   */
  reviewDialogue() {
    console.log('[Dialogue] Review dialogue');
    // 轻触反馈
    haptics.light();

    this.setData({
      currentIndex: 0,
      showCompletion: false,
      playCount: 0,
      recordCount: 0,
      startTime: Date.now()
    });

    this.loadCurrentAudio();
    toast.info('开始复习');
  },

  /**
   * 清理资源
   */
  cleanup() {
    const { audioContext, recorderManager, isRecording } = this.data;

    // 停止音频
    if (audioContext) {
      audioContext.stop();
      audioContext.destroy();
    }

    // 停止录音
    if (recorderManager && isRecording) {
      recorderManager.stop();
    }
  }
});
