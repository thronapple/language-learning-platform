Component({
  properties: {
    src: String,
    rate: { type: Number, value: 1.0 },
  },
  methods: {
    play() { this.triggerEvent('play') },
    pause() { this.triggerEvent('pause') },
  },
})

