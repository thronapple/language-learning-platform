const { request } = require('../services/request')

function track(event, props = {}) {
  try {
    request('/events', { method: 'POST', data: { event, props } })
  } catch (e) {
    // ignore
  }
}

module.exports = { track }
