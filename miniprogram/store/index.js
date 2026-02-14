const store = {
  state: {
    user: null,
    plan: null,
    todayStats: null,
  },
  set(key, value) {
    this.state[key] = value
  },
  get(key) {
    return this.state[key]
  },
}

module.exports = store

