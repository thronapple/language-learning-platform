const { request } = require('./request')

function me(code) {
  return request('/auth/me', { method: 'POST', data: { code } })
}

module.exports = { me }

