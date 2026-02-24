import { request } from '../../services/request';
import { track } from '../../utils/track';

Page({
  data: {
    url: '',
    generating: false as boolean,
  },

  generate() {
    if (this.data.generating) return;
    this.setData({ generating: true });
    request.post<{ url: string }>('/export/longshot', { contentId: 'demo' })
      .then((res) => {
        this.setData({ url: res.url });
        try { track('export_longshot', { ok: true }); } catch (_) {}
        wx.showToast({ title: '已生成', icon: 'success' });
      })
      .catch(() => {
        try { track('export_longshot', { ok: false }); } catch (_) {}
        wx.showToast({ title: '生成失败', icon: 'none' });
      })
      .finally(() => this.setData({ generating: false }));
  },

  save() {
    const url = this.data.url;
    if (!url) return;
    wx.downloadFile({
      url,
      success: (res) => {
        wx.saveImageToPhotosAlbum({
          filePath: res.tempFilePath,
          success: () => wx.showToast({ title: '已保存到相册', icon: 'success' }),
          fail: () => wx.showToast({ title: '保存失败，请检查权限', icon: 'none' }),
        });
      },
    });
  },
});
