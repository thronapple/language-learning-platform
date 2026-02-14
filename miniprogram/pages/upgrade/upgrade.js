const { request } = require('../../services/request')
const { track } = require('../../utils/track')

Page({
  data: { plan: '', price: '', contact: '' },
  onShow() {
    try { track('upgrade_view') } catch (e) {}
  },
  choose(e) { this.setData({ plan: e.currentTarget.dataset.plan, price: e.currentTarget.dataset.price }) },
  onInput(e) { this.setData({ contact: e.detail.value }) },
  submit() {
    const { plan, price, contact } = this.data
    if (!contact) return
    try { track('upgrade_click', { plan, price: Number(price || 0) }) } catch (e) {}
    request('/billing/intent', { method: 'POST', data: { plan, price: Number(price || 0) } })
      .then(() => request('/wishlist', { method: 'POST', data: { contactType: 'wx', contact, plan, price_point: Number(price || 0) } }))
      .then(() => { try { track('wishlist_submit', { contact_type: 'wx' }) } catch (e) {}; wx.showToast({ title: '已提交', icon: 'success' }) })
  },
})
