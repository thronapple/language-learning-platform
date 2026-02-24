import * as vocab from '../../services/vocab';
import { track } from '../../utils/track';

interface VocabItem {
  word: string;
  meaning?: string;
  nextReview?: string;
}

Page({
  data: {
    items: [] as VocabItem[],
    allItems: [] as VocabItem[],
    word: '',
    onlyDue: false,
    loading: true,
    loadError: false,
    showMeaning: {} as Record<string, boolean>,
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 });
    }
    this.load();
  },

  load() {
    this.setData({ loading: true, loadError: false });
    const promise = this.data.onlyDue
      ? vocab.due({ before: new Date().toISOString() })
      : vocab.list();
    promise
      .then((res: any) => {
        const allItems: VocabItem[] = res.items || [];
        this.setData({ allItems });
        this.applyFilter();
      })
      .catch(() => this.setData({ loadError: true }))
      .finally(() => this.setData({ loading: false }));
  },

  toggleDue(e: WechatMiniprogram.SwitchChange) {
    this.setData({ onlyDue: e.detail.value });
    this.load();
  },

  onInput(e: WechatMiniprogram.Input) {
    this.setData({ word: e.detail.value });
    this.applyFilter();
  },

  add() {
    const w = this.data.word.trim();
    if (!w) return;
    vocab.add({ word: w }).then(() => {
      try { track('vocab_add', { word: w }); } catch (_) {}
      this.setData({ word: '' });
      this.load();
      wx.showToast({ title: '已添加', icon: 'success' });
    });
  },

  toggleMeaning(e: WechatMiniprogram.TouchEvent) {
    const word = e.currentTarget.dataset.word as string;
    const showMeaning = { ...this.data.showMeaning };
    showMeaning[word] = !showMeaning[word];
    this.setData({ showMeaning });
  },

  onRate(e: WechatMiniprogram.TouchEvent) {
    const { rating, word } = e.currentTarget.dataset as { rating: string; word: string };
    if (!word || !rating) return;
    vocab.review(word, rating).then(() => {
      try { track('vocab_review', { word, rating }); } catch (_) {}
      wx.showToast({ title: rating === 'easy' ? '太棒了！' : '继续加油', icon: 'success', duration: 800 });
      this.load();
    });
  },

  remove(e: WechatMiniprogram.TouchEvent) {
    const w = e.currentTarget.dataset.word as string;
    if (!w) return;
    wx.showModal({
      title: '确认移除',
      content: `确定要移除"${w}"吗？`,
      success: (res) => {
        if (res.confirm) {
          vocab.remove(w).then(() => {
            try { track('vocab_remove', { word: w }); } catch (_) {}
            this.load();
          });
        }
      },
    });
  },

  applyFilter() {
    const q = (this.data.word || '').trim().toLowerCase();
    if (!q) {
      this.setData({ items: this.data.allItems });
      return;
    }
    const filtered = this.data.allItems.filter((it) =>
      (it.word || '').toLowerCase().indexOf(q) >= 0
    );
    this.setData({ items: filtered });
  },
});
