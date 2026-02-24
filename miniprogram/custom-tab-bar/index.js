Component({
  data: {
    selected: 0,
    list: [
      { pagePath: '/pages/index/index', text: '首页', icon: '🏠', iconSelected: '🏠' },
      { pagePath: '/pages/vocab/vocab', text: '词汇', icon: '📖', iconSelected: '📖' },
      { pagePath: '/pages/mine/mine', text: '我的', icon: '👤', iconSelected: '👤' },
    ],
  },
  methods: {
    switchTab(e) {
      const idx = e.currentTarget.dataset.index
      const item = this.data.list[idx]
      wx.switchTab({ url: item.pagePath })
    },
  },
})
