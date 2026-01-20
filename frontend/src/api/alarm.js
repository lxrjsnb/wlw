/**
 * 告警管理API
 * Alarm management API
 */
import request from '@/utils/request'

// 获取告警规则列表
export function getAlarmRules(params) {
  return request({
    url: '/alarms/rules/',
    method: 'get',
    params
  })
}

// 创建告警规则
export function createAlarmRule(data) {
  return request({
    url: '/alarms/rules/create/',
    method: 'post',
    data
  })
}

// 更新告警规则
export function updateAlarmRule(id, data) {
  return request({
    url: `/alarms/rules/${id}/`,
    method: 'put',
    data
  })
}

// 删除告警规则
export function deleteAlarmRule(id) {
  return request({
    url: `/alarms/rules/${id}/`,
    method: 'delete'
  })
}

// 获取告警记录列表
export function getAlarmRecords(params) {
  return request({
    url: '/alarms/records/',
    method: 'get',
    params
  })
}

// 获取告警记录详情
export function getAlarmRecord(id) {
  return request({
    url: `/alarms/records/${id}/`,
    method: 'get'
  })
}

// 处理告警
export function resolveAlarm(id, data) {
  return request({
    url: `/alarms/records/${id}/resolve/`,
    method: 'post',
    data
  })
}

// 获取告警统计
export function getAlarmStats() {
  return request({
    url: '/alarms/stats/',
    method: 'get'
  })
}

// 获取告警通知列表
export function getAlarmNotifications(params) {
  return request({
    url: '/alarms/notifications/',
    method: 'get',
    params
  })
}
