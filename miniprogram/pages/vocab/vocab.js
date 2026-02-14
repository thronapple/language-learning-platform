const vocab = require('../../services/vocab')
const { track } = require('../../utils/track')

Page({
  data: { items: [], allItems: [], word: '', onlyDue: true },
  onShow() {
    this.load()
  },
  load() {
    if (this.data.onlyDue) {
      const before = new Date().toISOString()
      vocab.due({ before }).then((res) => {
        const allItems = res.items || []
        this.setData({ allItems })
        this.applyFilter()
      })
    } else {
      vocab.list().then((res) => {
        const allItems = res.items || []
        this.setData({ allItems })
        this.applyFilter()
      })
    }
  },
  toggleDue(e) {
    this.setData({ onlyDue: e.detail.value })
    this.load()
  },
  onInput(e) { this.setData({ word: e.detail.value }); this.applyFilter() },
  add() {
    if (!this.data.word) return
    const w = this.data.word
    vocab.add({ word: w }).then(() => { track('vocab_add', { word: w }); this.load() })
  },
  onRate(e) {
    const rating = e.detail.value
    const word = (e.currentTarget.dataset && e.currentTarget.dataset.word) || ''
    const targetWord = word || (this.data.items[0] && this.data.items[0].word)
    if (!targetWord) return
    vocab.review(targetWord, rating).then(() => { track('vocab_review', { word: targetWord, rating }); this.load() })
  },
  remove(e) {
    const w = (e.currentTarget.dataset && e.currentTarget.dataset.word) || ''
    if (!w) return
    vocab.remove(w).then(() => { track('vocab_remove', { word: w }); this.load() })
  },
  applyFilter() {
    const q = (this.data.word || '').trim().toLowerCase()
    if (!q) {
      this.setData({ items: this.data.allItems })
      return
    }
    const filtered = (this.data.allItems || []).filter((it) =>
      (it.word || '').toLowerCase().indexOf(q) >= 0
    )
    this.setData({ items: filtered })
  },
})
