Component({
  properties: {
    icon: { type: String, value: '😵' },
    title: { type: String, value: '加载失败' },
    desc: { type: String, value: '请检查网络后重试' },
  },
  methods: {
    onRetry() {
      this.triggerEvent('retry')
    },
  },
})
