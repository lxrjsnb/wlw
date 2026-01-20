/**
 * 设备管理API
 * Device management API
 */
import request from '@/utils/request'

// 获取设备列表
export function getDeviceList(params) {
  return request({
    url: '/devices/',
    method: 'get',
    params
  })
}

// 获取设备详情
export function getDeviceDetail(deviceId) {
  return request({
    url: `/devices/${deviceId}/`,
    method: 'get'
  })
}

// 创建设备
export function createDevice(data) {
  return request({
    url: '/devices/',
    method: 'post',
    data
  })
}

// 更新设备
export function updateDevice(deviceId, data) {
  return request({
    url: `/devices/${deviceId}/`,
    method: 'put',
    data
  })
}

// 删除设备
export function deleteDevice(deviceId) {
  return request({
    url: `/devices/${deviceId}/`,
    method: 'delete'
  })
}

// 控制设备
export function controlDevice(deviceId, data) {
  return request({
    url: `/devices/control/${deviceId}/`,
    method: 'post',
    data
  })
}

// 获取设备日志
export function getDeviceLogs(deviceId, params) {
  return request({
    url: `/devices/logs/${deviceId}/`,
    method: 'get',
    params
  })
}

// 获取设备统计
export function getDeviceStats() {
  return request({
    url: '/devices/stats/',
    method: 'get'
  })
}

// 获取传感器类型列表
export function getSensorTypes(params) {
  return request({
    url: '/devices/sensor-types/',
    method: 'get',
    params
  })
}
