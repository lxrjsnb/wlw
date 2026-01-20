/**
 * 传感器数据API
 * Sensor data API
 */
import request from '@/utils/request'

// 获取传感器数据列表
export function getSensorDataList(params) {
  return request({
    url: '/sensors/data/',
    method: 'get',
    params
  })
}

// 获取设备最新数据
export function getLatestData(deviceId) {
  return request({
    url: `/sensors/data/latest/${deviceId}/`,
    method: 'get'
  })
}

// 获取数据统计
export function getDataStatistics(deviceId, params) {
  return request({
    url: `/sensors/data/statistics/${deviceId}/`,
    method: 'get',
    params
  })
}

// 获取历史数据
export function getHistoryData(deviceId, params) {
  return request({
    url: `/sensors/data/history/${deviceId}/`,
    method: 'get',
    params
  })
}

// 导出数据
export function exportData(params) {
  return request({
    url: '/sensors/data/export/',
    method: 'get',
    params,
    responseType: 'blob'
  })
}
