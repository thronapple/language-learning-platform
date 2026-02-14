const { track } = require('../../utils/track')
const { canShow, inc } = require('../../utils/adfreq')

Component({
  properties: {
    slot: { type: String, value: 'finish' },
    daily: { type: Number, value: 2 },
  },
  data: { visible: false },
  methods: {
    maybeShow() {
      const s = this.properties.slot || 'finish'
      const limit = this.properties.daily || 0
      if (limit > 0 && canShow(s, limit)) {
        this.setData({ visible: true })
        try { track('ad_impression', { slot: s }) } catch (e) {}
        try { inc(s) } catch (e) {}
      }
    },
    close() { this.setData({ visible: false }) },
    onClick() {
      const s = this.properties.slot || 'finish'
      try { track('ad_click', { slot: s }) } catch (e) {}
      this.setData({ visible: false })
    },
  },
})

