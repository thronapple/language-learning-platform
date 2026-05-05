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
  score?: number;
}

interface Dialogue {
  id: string;
  title_en: string;
  title_zh: string;
  level: string;
  sentences: Sentence[];
}

interface DisplaySentence extends Sentence {
  isUser: boolean;
  isCurrent: boolean;
  isCompleted: boolean;
  avatarText: string;
  score?: number;
  scoreLabel?: string;
}

Page({
  data: {
    dialogue: null as Dialogue | null,
    displaySentences: [] as DisplaySentence[],
    currentIndex: 0,
    progressPercent: 0,
    currentPromptZh: '',
    showPhonetic: true,
    showTranslation: false,
    loading: true,
    newWordsCount: 0,

    // 音频相关
    audioContext: null as any,
    isPlaying: false,
    playCount: 0,
    playbackRate: 1.0,

    // 录音相关
    recorderManager: null as any,
    isRecording: false,
    recordTouchActive: false,
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

  goBack() {
    wx.navigateBack();
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

      const uniqueWords = new Set<string>();
      (dialogue.sentences || []).forEach((s) => {
        (s.key_words || []).forEach((w) => {
          if (w) uniqueWords.add(w.trim().toLowerCase());
        });
      });

      this.setData({
        dialogue: dialogue,
        loading: false,
        newWordsCount: uniqueWords.size,
      });
      this.updateDisplaySentences();

      this.initAudioContext();

      // 埋点
      wx.reportAnalytics('dialogue_load', {
        dialogue_id: dialogueId,
        sentence_count: dialogue.sentences.length
      });

    } catch (error) {
      console.error('[Dialogue] Load failed, using stub:', error);

      // 后端不通时用兜底数据，便于开发期预览页面（生产上线前可删除此分支）
      const stub: Dialogue = {
        id: dialogueId || 'stub',
        title_en: 'Ordering at a Café',
        title_zh: '咖啡馆点单',
        level: 'A2',
        sentences: [
          {
            order: 1, speaker: 'Barista',
            text_en: 'Hi there! What can I get started for you today?',
            text_zh: '你好！今天想要点什么？',
            audio_url: '', phonetic: '/haɪ ðɛr/',
            key_words: ['get', 'started'], grammar_points: [],
          },
          {
            order: 2, speaker: 'You',
            text_en: "I'll have a medium oat milk latte, please.",
            text_zh: '我要一杯中杯燕麦拿铁。',
            audio_url: '', phonetic: '/aɪl hæv/',
            key_words: ['medium', 'oat', 'milk', 'latte'], grammar_points: [],
            score: 92,
          },
          {
            order: 3, speaker: 'Barista',
            text_en: 'Sure thing. Hot or iced?',
            text_zh: '好的。要热的还是冰的？',
            audio_url: '', phonetic: '/ʃʊr θɪŋ/',
            key_words: ['hot', 'iced'], grammar_points: [],
          },
          {
            order: 4, speaker: 'You',
            text_en: 'Hot, please. And can I get an extra shot?',
            text_zh: '热的，麻烦。能多加一份浓缩吗？',
            audio_url: '', phonetic: '/hɑt pliːz/',
            key_words: ['extra', 'shot'], grammar_points: [],
          },
        ],
      };

      const uniqueWords = new Set<string>();
      stub.sentences.forEach((s) => {
        (s.key_words || []).forEach((w) => uniqueWords.add(w.trim().toLowerCase()));
      });

      this.setData({
        dialogue: stub,
        loading: false,
        newWordsCount: uniqueWords.size,
      });
      this.updateDisplaySentences();
    }
  },

  /**
   * 初始化音频上下文
   */
  initAudioContext() {
    const existing = this.data.audioContext;
    if (existing) {
      try {
        existing.destroy();
      } catch (_) {}
    }

    const audioContext = wx.createInnerAudioContext();
    audioContext.obeyMuteSwitch = false;

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
      toast.error('音频播放失败');
    });

    this.setData({ audioContext });
    this.loadCurrentAudio();
  },

  ensureAudioContext() {
    if (this.data.audioContext) return this.data.audioContext;
    this.initAudioContext();
    return this.data.audioContext;
  },

  /**
   * 加载当前句子音频
   */
  loadCurrentAudio() {
    const { dialogue, currentIndex, audioContext } = this.data;
    if (!dialogue || !audioContext) return;

    const currentSentence = dialogue.sentences[currentIndex];
    audioContext.src = currentSentence?.audio_url || '';
  },

  loadAudioForIndex(index: number) {
    const { dialogue } = this.data;
    const audioContext = this.ensureAudioContext();
    if (!dialogue || !audioContext) return '';

    const sentence = dialogue.sentences[index];
    const audioUrl = sentence?.audio_url || '';
    audioContext.src = audioUrl;
    return audioUrl;
  },

  /**
   * 切换音频播放
   */
  toggleAudio(e?: any) {
    const index = Number(e?.currentTarget?.dataset?.index ?? this.data.currentIndex);
    const { isPlaying } = this.data;
    const audioContext = this.ensureAudioContext();
    if (!audioContext) return;

    // 触觉反馈
    haptics.light();

    if (isPlaying) {
      audioContext.pause();
      this.setData({ isPlaying: false });
    } else {
      const audioUrl = this.loadAudioForIndex(index);
      if (!audioUrl) {
        toast.info('当前句子暂无音频');
        return;
      }
      audioContext.play();
    }
  },

  /**
   * 切换播放速度
   */
  toggleSpeed() {
    const audioContext = this.ensureAudioContext();
    if (!audioContext) return;

    const rates = [0.8, 1.0, 1.2, 1.5];
    const currentRate = this.data.playbackRate;
    const currentIndex = rates.indexOf(currentRate);
    const nextRate = rates[(currentIndex + 1) % rates.length];

    // 触觉反馈
    haptics.light();

    audioContext.playbackRate = nextRate;
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

  ensureRecordAuthorized(): Promise<boolean> {
    return new Promise((resolve) => {
      wx.getSetting({
        success: (setting) => {
          const auth = setting.authSetting || {};
          if (auth['scope.record']) {
            resolve(true);
            return;
          }

          if (auth['scope.record'] === false) {
            wx.showModal({
              title: '需要麦克风权限',
              content: '请允许麦克风权限，用于跟读录音和口语评测。',
              confirmText: '去设置',
              success: (modalRes) => {
                if (!modalRes.confirm) {
                  resolve(false);
                  return;
                }
                wx.openSetting({
                  success: (openRes) => {
                    resolve(!!openRes.authSetting?.['scope.record']);
                  },
                  fail: () => resolve(false),
                });
              },
              fail: () => resolve(false),
            });
            return;
          }

          wx.authorize({
            scope: 'scope.record',
            success: () => resolve(true),
            fail: () => resolve(false),
          });
        },
        fail: () => resolve(false),
      });
    });
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
              color: data.color || '#8e8a82',
            },
          });
          this.updateDisplaySentences();
          // 3秒后自动隐藏
          setTimeout(() => {
            this.setData({ showScore: false });
            this.updateDisplaySentences();
          }, 3000);
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
  async startRecording() {
    const { recorderManager } = this.data;
    if (!recorderManager || this.data.evaluating || this.data.isRecording) return;

    this.setData({ recordTouchActive: true });
    const authorized = await this.ensureRecordAuthorized();
    if (!authorized) {
      this.setData({ recordTouchActive: false });
      toast.info('未获得麦克风权限');
      return;
    }
    if (!this.data.recordTouchActive) return;

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
      this.setData({ recordTouchActive: false, isRecording: false });
      toast.error('录音启动失败');
    }
  },

  /**
   * 停止录音
   */
  stopRecording() {
    const { recorderManager, isRecording } = this.data;
    this.setData({ recordTouchActive: false });
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
    const audioContext = this.ensureAudioContext();
    if (!audioContext) return;

    haptics.light();
    const audioUrl = this.loadAudioForIndex(this.data.currentIndex);
    if (!audioUrl) {
      toast.info('当前句子暂无音频');
      return;
    }
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
   * 重新录制：清空当前句的评分状态，等待用户重新长按录音
   */
  reRecord() {
    haptics.light();
    if (!this.data.showScore && !this.data.scoreInfo) return;
    this.setData({
      showScore: false,
      scoreInfo: null,
      recognizedText: '',
    });
    this.updateDisplaySentences();
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
    this.updateDisplaySentences();

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
    this.updateDisplaySentences();

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
    this.updateDisplaySentences();

    this.loadCurrentAudio();
    toast.info('开始复习');
  },

  updateDisplaySentences() {
    const { dialogue, currentIndex, scoreInfo, showScore } = this.data;
    if (!dialogue) return;

    const labelOf = (s?: number) => {
      if (s == null) return '';
      if (s >= 90) return '发音很棒';
      if (s >= 80) return '挺不错';
      if (s >= 70) return '还可以';
      if (s >= 60) return '继续加油';
      return '再试一次';
    };

    const displaySentences = dialogue.sentences.map((sentence, index) => {
      const isUser = sentence.speaker === 'B' || sentence.speaker === 'You' || sentence.speaker === 'YOU';
      const liveScore = isUser && showScore && index === currentIndex && scoreInfo
        ? scoreInfo.score
        : undefined;
      // 历史分数：用户句子若自带 score 字段（stub 数据或后端历史评测）也展示
      const historyScore = isUser ? sentence.score : undefined;
      const score = liveScore ?? historyScore;
      return {
        ...sentence,
        isUser,
        isCurrent: index === currentIndex,
        isCompleted: index < currentIndex,
        avatarText: isUser ? 'YOU' : (sentence.speaker || 'A').slice(0, 1),
        score,
        scoreLabel: labelOf(score),
      };
    });

    this.setData({
      displaySentences,
      currentPromptZh: dialogue.sentences[currentIndex]?.text_zh || '',
      progressPercent: dialogue.sentences.length
        ? Math.round(((currentIndex + 1) / dialogue.sentences.length) * 100)
        : 0,
    });
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
    this.setData({ audioContext: null, isPlaying: false });

    // 停止录音
    if (recorderManager && isRecording) {
      recorderManager.stop();
    }
  }
});
