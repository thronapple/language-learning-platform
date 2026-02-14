function todayKey() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}${m}${day}`
}

function loadCounter() {
  try {
    const data = wx.getStorageSync('ad_freq') || {}
    return data
  } catch (e) { return {} }
}

function saveCounter(counter) {
  try { wx.setStorageSync('ad_freq', counter) } catch (e) {}
}

function inc(slot) {
  const key = todayKey()
  const counter = loadCounter()
  const today = counter[key] || {}
  today[slot] = (today[slot] || 0) + 1
  counter[key] = today
  // cleanup old keys (keep 2 days)
  Object.keys(counter).forEach((k) => { if (k !== key) delete counter[k] })
  saveCounter(counter)
}

function count(slot) {
  const key = todayKey()
  const counter = loadCounter()
  const today = counter[key] || {}
  return today[slot] || 0
}

function canShow(slot, dailyLimit) {
  const shown = count(slot)
  return shown < (dailyLimit || 0)
}

module.exports = { canShow, inc, count }

