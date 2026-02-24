import { request } from '../../services/request';
import * as content from '../../services/content';
import * as study from '../../services/study';
import { track } from '../../utils/track';

function makeTtsUrl(text: string): string {
  if (!text) return '';
  const base = request.getBaseUrl();
  return `${base}/api/tts/audio?text=${encodeURIComponent(text)}&lang=en`;
}

interface ContentDoc {
  id: string;
  text: string;
  audio_url?: string;
  segments?: string[];
  segments_audio?: string[];
}

Page({
  data: {
    contentId: '',
    sentences: ['Hello world.', 'Nice to meet you.'] as string[],
    segmentsAudio: [] as string[],
    activeIndex: 0,
    activeAnchor: 'sentence-0',
    timer: null as number | null,
    secs: 0,
    autoNext: false,
    nextTimer: null as number | null,
    audio: null as WechatMiniprogram.InnerAudioContext | null,
    audioUrl: '',
    audioAvailable: false,
    isPlaying: false,
    audioRate: 1.0,
  },

  _finished: false,

  onLoad(options: Record<string, string | undefined>) {
    const id = options?.id;
    if (id) {
      this.loadContent(id);
    } else {
      this.loadFirstContent();
    }
  },

  onUnload() {
    if (this.data.nextTimer) clearTimeout(this.data.nextTimer);
    this.stopTimer();
    if (this.data.audio) {
      try { this.data.audio.stop(); this.data.audio.destroy(); } catch (_) {}
      this.setData({ audio: null, isPlaying: false });
    }
  },

  loadContent(id: string) {
    content.get(id).then((res: ContentDoc) => {
      this.applyContent(res, id);
    });
  },

  loadFirstContent() {
    content.list().then((res: any) => {
      const items = res?.items || [];
      if (items.length) {
        const first = items[0];
        content.get(first.id).then((doc: ContentDoc) => {
          this.applyContent(doc, first.id);
        });
      } else {
        this.applyDefaults();
      }
    }).catch(() => {
      this.applyDefaults();
    });
  },

  applyContent(doc: ContentDoc, fallbackId: string) {
    const segs = doc?.segments || [];
    const sentences = segs.length ? segs : [doc?.text || ''];
    const segAudios = doc?.segments_audio || [];
    const audioUrl = doc?.audio_url || makeTtsUrl(doc?.text);
    this.setData({
      sentences,
      segmentsAudio: segAudios,
      activeIndex: 0,
      contentId: doc?.id || fallbackId,
      activeAnchor: 'sentence-0',
      audioUrl,
      audioAvailable: !!audioUrl,
    });
    this.initAudio();
    this.startTimer();
    track('lesson_start', { contentId: doc?.id || fallbackId });
  },

  applyDefaults() {
    const defaultSentences = ['Hello! How are you?', "I'm fine, thank you.", 'Nice to meet you!'];
    this.setData({
      sentences: defaultSentences,
      activeIndex: 0,
      activeAnchor: 'sentence-0',
      audioUrl: makeTtsUrl(defaultSentences[0]),
    });
    this.initAudio();
    this.startTimer();
  },

  initAudio() {
    if (this.data.audio) return;
    const audio = wx.createInnerAudioContext();
    audio.autoplay = false;

    audio.onEnded(() => {
      this.setData({ isPlaying: false });
      if (this.data.autoNext) this.next();
    });

    audio.onError((err) => {
      console.error('音频错误:', err);
      this.setData({ isPlaying: false });
    });

    if (this.data.audioUrl) {
      audio.src = this.data.audioUrl;
    }

    this.setData({ audio });
  },

  startTimer() {
    if (this.data.timer) return;
    const t = setInterval(() => {
      this.setData({ secs: this.data.secs + 1 });
    }, 1000);
    this.setData({ timer: t });
  },

  stopTimer() {
    if (this.data.timer) {
      clearInterval(this.data.timer);
      this.setData({ timer: null });
    }
  },

  setActive(i: number | WechatMiniprogram.TouchEvent) {
    const index = typeof i === 'object' ? parseInt((i as any).currentTarget.dataset.index) : i;
    const clamped = Math.max(0, Math.min(index, this.data.sentences.length - 1));
    this.setData({ activeIndex: clamped, activeAnchor: `sentence-${clamped}` });

    const a = this.data.audio;
    if (a) {
      const segAudios = this.data.segmentsAudio || [];
      const newSrc = (segAudios.length && segAudios[clamped])
        ? segAudios[clamped]
        : makeTtsUrl(this.data.sentences[clamped]);
      try {
        a.stop();
        a.src = newSrc;
        this.setData({ isPlaying: false, audioUrl: newSrc });
        if (this.data.autoNext) a.play();
      } catch (_) {}
    }

    if (this.data.autoNext) {
      if (this.data.nextTimer) clearTimeout(this.data.nextTimer);
      const nt = setTimeout(() => this.next(), 3000);
      this.setData({ nextTimer: nt });
    }
  },

  prev() {
    this.setActive(this.data.activeIndex - 1);
  },

  next() {
    const i = Math.min(this.data.sentences.length - 1, this.data.activeIndex + 1);
    this.setActive(i);
  },

  toggleAutoNext(e: WechatMiniprogram.SwitchChange) {
    this.setData({ autoNext: e.detail.value });
  },

  togglePlay() {
    const a = this.data.audio;
    if (!a) {
      wx.showToast({ title: '音频未加载', icon: 'none' });
      return;
    }
    if (this.data.isPlaying) {
      try { a.pause(); this.setData({ isPlaying: false }); } catch (_) {}
    } else {
      if (!a.src) {
        wx.showToast({ title: '音频地址未配置', icon: 'none' });
        return;
      }
      try { a.play(); this.setData({ isPlaying: true }); } catch (_) {
        this.setData({ isPlaying: false });
      }
    }
  },

  cycleRate() {
    const rates = [1.0, 1.25, 1.5, 2.0];
    const cur = this.data.audioRate;
    const idx = (rates.indexOf(cur) + 1) % rates.length;
    const next = rates[idx];
    this.setData({ audioRate: next });
    const a = this.data.audio;
    if (a) {
      try { a.playbackRate = next; } catch (_) {}
    }
  },

  finish() {
    if (this._finished) return;
    this._finished = true;
    const secs = this.data.secs || 0;
    if (this.data.nextTimer) clearTimeout(this.data.nextTimer);
    this.stopTimer();

    const savePromise = this.data.contentId
      ? study.saveProgress({ contentId: this.data.contentId, secs, step: 'learning' })
          .then(() => track('lesson_finish', { contentId: this.data.contentId, secs }))
          .catch(() => {})
      : Promise.resolve();

    savePromise.then(() => {
      wx.showToast({ title: '学习完成！', icon: 'success', duration: 1500 });
      setTimeout(() => {
        if (getCurrentPages().length > 1) {
          wx.navigateBack();
        } else {
          wx.reLaunch({ url: '/pages/index/index' });
        }
      }, 1500);
    });
  },
});
