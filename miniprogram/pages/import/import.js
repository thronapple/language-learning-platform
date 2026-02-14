const { request } = require('../../services/request')
const { track } = require('../../utils/track')

Page({
  data: { text: '' },
  onInput(e) { this.setData({ text: e.detail.value }) },
  doImport() {
    const payload = this.data.text.trim()
    if (!payload) return
    const type = payload.startsWith('http') ? 'url' : 'text'
    try { track('import_try', { type }) } catch (e) {}
    request('/import', { method: 'POST', data: { type, payload } })
      .then((res) => {
        try { track('import_success', { type }) } catch (e) {}
        wx.showToast({ title: '导入成功', icon: 'success' })
        if (res && res.id) {
          wx.navigateTo({ url: `/pages/study/study?id=${encodeURIComponent(res.id)}` })
        }
      })
      .catch(() => {
        try { track('import_fail', { type }) } catch (e) {}
        wx.showToast({ title: '导入失败，请改用文本导入', icon: 'none' })
      })
  },
})
