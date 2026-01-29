/**
 * 话题相关API
 */
import request from './http'

/**
 * 获取话题列表
 */
export function getTopics(params) {
  return request({
    url: '/api/v1/topics/',
    method: 'get',
    params
  })
}

/**
 * 获取话题详情
 */
export function getTopic(id) {
  return request({
    url: `/api/v1/topics/${id}/`,
    method: 'get'
  })
}

/**
 * 创建话题
 */
export function createTopic(data) {
  return request({
    url: '/api/v1/topics/',
    method: 'post',
    data
  })
}

/**
 * 更新话题
 */
export function updateTopic(id, data) {
  return request({
    url: `/api/v1/topics/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除话题
 */
export function deleteTopic(id) {
  return request({
    url: `/api/v1/topics/${id}/`,
    method: 'delete'
  })
}

/**
 * 获取话题统计
 */
export function getTopicStats() {
  return request({
    url: '/api/v1/topics/stats/',
    method: 'get'
  })
}

/**
 * 暂停话题
 */
export function pauseTopic(id) {
  return request({
    url: `/api/v1/topics/${id}/pause/`,
    method: 'post'
  })
}

/**
 * 激活话题
 */
export function activateTopic(id) {
  return request({
    url: `/api/v1/topics/${id}/activate/`,
    method: 'post'
  })
}

/**
 * 获取活跃话题列表
 */
export function getActiveTopics() {
  return request({
    url: '/api/v1/topics/active/',
    method: 'get'
  })
}

/**
 * 获取平台列表
 */
export function getPlatforms() {
  return request({
    url: '/api/v1/topics/platforms/',
    method: 'get'
  })
}
