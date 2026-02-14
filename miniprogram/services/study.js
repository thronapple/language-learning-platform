const { request } = require('./request')

function saveProgress(payload) {
  return request('/study/progress', { method: 'POST', data: payload })
}

module.exports = { saveProgress }

