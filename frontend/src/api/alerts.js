/**
 * 预警相关API
 */
import request from './http'
import { createAPI } from './factory'

// 使用工厂模式创建API (可选使用)
export const alertRulesAPI = createAPI('/api/v1/alerts/rules')
export const alertRecordsAPI = createAPI('/api/v1/alerts/records')

/**
 * 获取预警规则列表
 */
export function getAlertRules(params) {
  return request({
    url: '/api/v1/alerts/rules/',
    method: 'get',
    params
  })
}

/**
 * 获取预警规则详情
 */
export function getAlertRule(id) {
  return request({
    url: `/api/v1/alerts/rules/${id}/`,
    method: 'get'
  })
}

/**
 * 创建预警规则
 */
export function createAlertRule(data) {
  return request({
    url: '/api/v1/alerts/rules/',
    method: 'post',
    data
  })
}

/**
 * 更新预警规则
 */
export function updateAlertRule(id, data) {
  return request({
    url: `/api/v1/alerts/rules/${id}/`,
    method: 'put',
    data
  })
}

/**
 * 删除预警规则
 */
export function deleteAlertRule(id) {
  return request({
    url: `/api/v1/alerts/rules/${id}/`,
    method: 'delete'
  })
}

/**
 * 启用预警规则
 */
export function enableAlertRule(id) {
  return request({
    url: `/api/v1/alerts/rules/${id}/enable/`,
    method: 'post'
  })
}

/**
 * 禁用预警规则
 */
export function disableAlertRule(id) {
  return request({
    url: `/api/v1/alerts/rules/${id}/disable/`,
    method: 'post'
  })
}

/**
 * 获取预警记录列表
 */
export function getAlertRecords(params) {
  return request({
    url: '/api/v1/alerts/records/',
    method: 'get',
    params
  })
}

/**
 * 获取预警记录详情
 */
export function getAlertRecord(id) {
  return request({
    url: `/api/v1/alerts/records/${id}/`,
    method: 'get'
  })
}

/**
 * 确认预警
 */
export function acknowledgeAlert(id) {
  return request({
    url: `/api/v1/alerts/records/${id}/acknowledge/`,
    method: 'post'
  })
}

/**
 * 解决预警
 */
export function resolveAlert(id, data) {
  return request({
    url: `/api/v1/alerts/records/${id}/resolve/`,
    method: 'post',
    data
  })
}

/**
 * 获取待处理预警
 */
export function getPendingAlerts(params) {
  return request({
    url: '/api/v1/alerts/records/pending/',
    method: 'get',
    params
  })
}

/**
 * 获取预警统计
 */
export function getAlertStats() {
  return request({
    url: '/api/v1/alerts/records/stats/',
    method: 'get'
  })
}

/**
 * 批量确认预警
 */
export function batchAcknowledgeAlerts(data) {
  return request({
    url: '/api/v1/alerts/records/batch_acknowledge/',
    method: 'post',
    data
  })
}

/**
 * 批量解决预警
 */
export function batchResolveAlerts(data) {
  return request({
    url: '/api/v1/alerts/records/batch_resolve/',
    method: 'post',
    data
  })
}

/**
 * 获取最新预警
 */
export function getRecentAlerts(params = {}) {
  return request({
    url: '/api/v1/alerts/records/recent/',
    method: 'get',
    params
  })
}
