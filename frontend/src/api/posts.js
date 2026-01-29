/**
 * 帖子相关API
 */
import request from './http'

/**
 * 获取帖子列表
 */
export function getPosts(params) {
  return request({
    url: '/api/v1/posts/',
    method: 'get',
    params
  })
}

/**
 * 获取帖子详情
 */
export function getPost(id) {
  return request({
    url: `/api/v1/posts/${id}/`,
    method: 'get'
  })
}

/**
 * 获取帖子统计
 */
export function getPostStats() {
  return request({
    url: '/api/v1/posts/stats/',
    method: 'get'
  })
}

/**
 * 情感分析
 */
export function analyzeSentiment(data) {
  return request({
    url: '/api/v1/posts/sentiment_analysis/',
    method: 'post',
    data
  })
}

/**
 * 获取热门帖子
 */
export function getHotPosts(params) {
  return request({
    url: '/api/v1/posts/hot/',
    method: 'get',
    params
  })
}

/**
 * 获取正面帖子
 */
export function getPositivePosts(params) {
  return request({
    url: '/api/v1/posts/positive/',
    method: 'get',
    params
  })
}

/**
 * 获取负面帖子
 */
export function getNegativePosts(params) {
  return request({
    url: '/api/v1/posts/negative/',
    method: 'get',
    params
  })
}
