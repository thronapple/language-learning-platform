const { request } = require('../../services/request')
const { track } = require('../../utils/track')

Page({
  data: { url: '' },
  generate() {
    request('/export/longshot', { method: 'POST', data: { contentId: 'demo' } })
      .then((res) => {
        this.setData({ url: res.url })
        try { track('export_longshot', { ok: true }) } catch (e) {}
        wx.showToast({ title: '已生成', icon: 'success' })
      })
      .catch(() => {
        try { track('export_longshot', { ok: false }) } catch (e) {}
      })
  },
  save() {
    const url = this.data.url
    if (!url) return
    wx.downloadFile({
      url,
      success: (res) => {
        const path = res.tempFilePath
        wx.saveImageToPhotosAlbum({
          filePath: path,
          success: () => wx.showToast({ title: '已保存到相册', icon: 'success' }),
          fail: () => wx.showToast({ title: '保存失败，请检查权限', icon: 'none' }),
          complete: () => { try { track('export_save', { ok: true }) } catch (e) {} },
        })
      },
      fail: () => { try { track('export_save', { ok: false }) } catch (e) {} },
    })
  },
})
