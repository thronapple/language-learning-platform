const { request } = require('./request')

function list(params = {}) {
  return request('/content', { method: 'GET', data: params })
}

function get(id) {
  return request(`/content/${id}`)
}

module.exports = { list, get }

