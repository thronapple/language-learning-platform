import { request } from '../../services/request';
import { track } from '../../utils/track';

Page({
  data: {
    text: '',
    importing: false as boolean,
  },

  onInput(e: WechatMiniprogram.Input) {
    this.setData({ text: e.detail.value });
  },

  doImport() {
    const payload = this.data.text.trim();
    if (!payload || this.data.importing) return;
    this.setData({ importing: true });
    const type = payload.startsWith('http') ? 'url' : 'text';
    try { track('import_try', { type }); } catch (_) {}
    request.post<{ id?: string }>('/import', { type, payload })
      .then((res) => {
        try { track('import_success', { type }); } catch (_) {}
        wx.showToast({ title: '导入成功', icon: 'success' });
        this.setData({ text: '' });
        if (res && res.id) {
          wx.navigateTo({ url: `/pages/study/study?id=${encodeURIComponent(res.id)}` });
        }
      })
      .catch(() => {
        try { track('import_fail', { type }); } catch (_) {}
        wx.showToast({ title: '导入失败，请改用文本导入', icon: 'none' });
      })
      .finally(() => this.setData({ importing: false }));
  },
});
