const { track } = require('../../utils/track')
const { canShow, inc } = require('../../utils/adfreq')

Component({
  properties: {
    slot: { type: String, value: 'result' },
    daily: { type: Number, value: 3 },
  },
  data: { visible: false },
  lifetimes: {
    attached() {
      const s = this.properties.slot || 'result'
      const limit = this.properties.daily || 0
      if (limit > 0 && canShow(s, limit)) {
        this.setData({ visible: true })
        try { track('ad_impression', { slot: s }) } catch (e) {}
        try { inc(s) } catch (e) {}
      }
    },
  },
  methods: {
    onClick() {
      const s = this.properties.slot || 'result'
      try { track('ad_click', { slot: s }) } catch (e) {}
    },
  },
})

