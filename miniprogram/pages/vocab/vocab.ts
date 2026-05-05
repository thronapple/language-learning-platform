import * as vocab from '../../services/vocab';
import { track } from '../../utils/track';

interface VocabItem {
  word: string;
  meaning?: string;
  phonetic?: string;
  example?: string;
  level?: string;
  category?: string;
  nextReview?: string;
}

Page({
  data: {
    items: [] as VocabItem[],
    allItems: [] as VocabItem[],
    activeIndex: 0,
    activeItem: null as VocabItem | null,
    word: '',
    onlyDue: false,
    loading: true,
    loadError: false,
    revealed: false,
    reviewedCount: 0,
    rememberedCount: 8,
    fuzzyCount: 3,
    forgottenCount: 1,
    showMeaning: {} as Record<string, boolean>,
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 });
    }
    this.load();
  },

  goHome() {
    wx.switchTab({ url: '/pages/index/index' });
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
    this.setData({ onlyDue: e.detail.value, activeIndex: 0, revealed: false });
    this.load();
  },

  setFilter(e: WechatMiniprogram.TouchEvent) {
    const raw = e.currentTarget.dataset.onlyDue;
    const onlyDue = raw === true || raw === 'true';
    if (onlyDue === this.data.onlyDue) return;
    this.setData({ onlyDue, activeIndex: 0, revealed: false });
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
      const nextData: Record<string, number> = {
        reviewedCount: this.data.reviewedCount + 1,
      };
      if (rating === 'again') nextData.forgottenCount = this.data.forgottenCount + 1;
      if (rating === 'hard') nextData.fuzzyCount = this.data.fuzzyCount + 1;
      if (rating === 'good' || rating === 'easy') nextData.rememberedCount = this.data.rememberedCount + 1;
      this.setData(nextData);
      wx.showToast({ title: rating === 'easy' ? '太棒了！' : '继续加油', icon: 'success', duration: 800 });
      this.nextCard();
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
      this.syncActiveItem();
      return;
    }
    const filtered = this.data.allItems.filter((it) =>
      (it.word || '').toLowerCase().indexOf(q) >= 0
    );
    this.setData({ items: filtered });
    this.syncActiveItem();
  },

  syncActiveItem() {
    const { items, activeIndex } = this.data;
    if (!items.length) {
      this.setData({ activeItem: null, activeIndex: 0, revealed: false });
      return;
    }
    const nextIndex = Math.min(activeIndex, items.length - 1);
    this.setData({
      activeIndex: nextIndex,
      activeItem: items[nextIndex],
      revealed: false,
    });
  },

  revealAnswer() {
    this.setData({ revealed: true });
  },

  nextCard() {
    const { items, activeIndex } = this.data;
    if (!items.length) return;
    const nextIndex = activeIndex >= items.length - 1 ? 0 : activeIndex + 1;
    this.setData({
      activeIndex: nextIndex,
      activeItem: items[nextIndex],
      revealed: false,
    });
  },
});
