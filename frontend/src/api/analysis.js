/**
 * 分析相关API
 */
import request from './http'

/**
 * 获取关键词云
 */
export function getKeywordCloud(params) {
  return request({
    url: '/api/v1/analysis/keyword_cloud/',
    method: 'get',
    params
  })
}

/**
 * 获取趋势分析
 */
export function getTrendAnalysis(params) {
  return request({
    url: '/api/v1/analysis/trend/',
    method: 'get',
    params
  })
}

/**
 * 获取影响力排行
 */
export function getInfluenceRanking(params) {
  return request({
    url: '/api/v1/analysis/influence_ranking/',
    method: 'get',
    params
  })
}

/**
 * 获取平台对比
 */
export function getPlatformCompare(params) {
  return request({
    url: '/api/v1/analysis/platform_compare/',
    method: 'get',
    params
  })
}

/**
 * 获取情感时间线
 */
export function getSentimentTimeline(params) {
  return request({
    url: '/api/v1/analysis/sentiment_timeline/',
    method: 'get',
    params
  })
}

/**
 * 获取分析日志
 */
export function getAnalysisLogs(params) {
  return request({
    url: '/api/v1/analysis/logs/',
    method: 'get',
    params
  })
}

// ==================== 热度分析 ====================

/**
 * 获取实时热度排行
 */
export function getRealtimeHotness(params) {
  return request({
    url: '/api/v1/analysis/hotness/realtime/',
    method: 'get',
    params
  })
}

/**
 * 获取热度趋势
 */
export function getHotnessTrend(params) {
  return request({
    url: '/api/v1/analysis/hotness/trend/',
    method: 'get',
    params
  })
}

/**
 * 获取热度等级分布
 */
export function getHotnessDistribution(params) {
  return request({
    url: '/api/v1/analysis/hotness/distribution/',
    method: 'get',
    params
  })
}

// ==================== 传播分析 ====================

/**
 * 获取传播路径
 */
export function getPropagationPaths(params) {
  return request({
    url: '/api/v1/analysis/propagation/paths/',
    method: 'get',
    params
  })
}

/**
 * 获取关键传播节点
 */
export function getKeyNodes(params) {
  return request({
    url: '/api/v1/analysis/propagation/key_nodes/',
    method: 'get',
    params
  })
}

/**
 * 获取传播模式
 */
export function getPropagationPattern(params) {
  return request({
    url: '/api/v1/analysis/propagation/pattern/',
    method: 'get',
    params
  })
}

// ==================== 突发事件 ====================

/**
 * 检测突发事件
 */
export function detectEmergency(params) {
  return request({
    url: '/api/v1/analysis/emergency/detect/',
    method: 'get',
    params
  })
}

/**
 * 获取突发事件历史
 */
export function getEmergencyHistory(params) {
  return request({
    url: '/api/v1/analysis/emergency/history/',
    method: 'get',
    params
  })
}

/**
 * 解决突发事件
 */
export function resolveEmergency(id, data) {
  return request({
    url: `/api/v1/analysis/emergency/${id}/resolve/`,
    method: 'post',
    data
  })
}

/**
 * 标记误报
 */
export function markEmergencyFalsePositive(id) {
  return request({
    url: `/api/v1/analysis/emergency/${id}/false_positive/`,
    method: 'post'
  })
}

// ==================== KOL分析 ====================

/**
 * 获取KOL排行
 */
export function getKOLRanking(params) {
  return request({
    url: '/api/v1/analysis/kol/ranking/',
    method: 'get',
    params
  })
}

/**
 * 获取KOL画像
 */
export function getKOLProfile(author, topic) {
  return request({
    url: `/api/v1/analysis/kol/profile/${author}/`,
    method: 'get',
    params: { topic }
  })
}

/**
 * KOL分类
 */
export function classifyKOLs(params) {
  return request({
    url: '/api/v1/analysis/kol/classify/',
    method: 'get',
    params
  })
}

// ==================== 舆情演化 ====================

/**
 * 获取当前演化阶段
 */
export function getCurrentStage(topicId) {
  return request({
    url: '/api/v1/analysis/evolution/current_stage/',
    method: 'get',
    params: { topic: topicId }
  })
}

/**
 * 获取演化历史
 */
export function getEvolutionHistory(topicId) {
  return request({
    url: '/api/v1/analysis/evolution/history/',
    method: 'get',
    params: { topic: topicId }
  })
}

/**
 * 预测下一阶段
 */
export function predictStage(topicId) {
  return request({
    url: '/api/v1/analysis/evolution/predict/',
    method: 'get',
    params: { topic: topicId }
  })
}

// ==================== 多层次情感分析 ====================

/**
 * 获取多层次情感分析
 */
export function getMultilevelSentiment(params) {
  return request({
    url: '/api/v1/analysis/sentiment/multilevel/',
    method: 'get',
    params
  })
}

/**
 * 获取情感强度分布
 */
export function getSentimentIntensity(params) {
  return request({
    url: '/api/v1/analysis/sentiment/intensity/',
    method: 'get',
    params
  })
}

/**
 * 获取情感演化
 */
export function getSentimentEvolution(params) {
  return request({
    url: '/api/v1/analysis/sentiment/evolution/',
    method: 'get',
    params
  })
}
