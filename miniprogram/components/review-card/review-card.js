Component({
  properties: {
    word: String,
    meaning: String,
  },
  methods: {
    again() { this.triggerEvent('rate', { value: 'again' }) },
    hard() { this.triggerEvent('rate', { value: 'hard' }) },
    good() { this.triggerEvent('rate', { value: 'good' }) },
    easy() { this.triggerEvent('rate', { value: 'easy' }) },
  },
})

