const { request } = require('./request')

function add(item) {
  return request('/vocab', { method: 'POST', data: item })
}

function list(params = {}) {
  return request('/vocab', { method: 'GET', data: params })
}

function remove(word) {
  return request(`/vocab/${encodeURIComponent(word)}`, { method: 'DELETE' })
}

function review(word, rating) {
  return request('/vocab/review', { method: 'POST', data: { word, rating } })
}

function due(params = {}) {
  return request('/vocab/due', { method: 'GET', data: params })
}

module.exports = { add, list, remove, review, due }
