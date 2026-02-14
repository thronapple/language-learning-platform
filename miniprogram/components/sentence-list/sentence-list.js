Component({
  properties: {
    segments: { type: Array, value: [] },
    activeIndex: { type: Number, value: 0 },
  },
  methods: {
    scrollTo(index) { this.setData({ activeIndex: index }) },
  },
})

