import { request } from '../../services/request';
import { track } from '../../utils/track';

Page({
  data: {
    plan: '',
    price: '',
    contact: '',
    submitting: false as boolean,
  },

  onShow() {
    try { track('upgrade_view'); } catch (_) {}
  },

  choose(e: WechatMiniprogram.TouchEvent) {
    this.setData({
      plan: e.currentTarget.dataset.plan as string,
      price: e.currentTarget.dataset.price as string,
    });
  },

  onInput(e: WechatMiniprogram.Input) {
    this.setData({ contact: e.detail.value });
  },

  submit() {
    const { plan, price, contact } = this.data;
    if (!contact || this.data.submitting) return;
    this.setData({ submitting: true });
    try { track('upgrade_click', { plan, price: Number(price || 0) }); } catch (_) {}
    request.post('/billing/intent', { plan, price: Number(price || 0) })
      .then(() => request.post('/wishlist', {
        contactType: 'wx', contact, plan, price_point: Number(price || 0),
      }))
      .then(() => {
        try { track('wishlist_submit', { contact_type: 'wx' }); } catch (_) {}
        wx.showToast({ title: '已提交，感谢支持！', icon: 'success' });
        this.setData({ contact: '' });
      })
      .catch(() => wx.showToast({ title: '提交失败', icon: 'none' }))
      .finally(() => this.setData({ submitting: false }));
  },
});
