import { http } from './http'

export function listSensorTypes(params) {
  return http.get('/api/v1/devices/sensor-types/', { params })
}

export function getDeviceStats() {
  return http.get('/api/v1/devices/stats/')
}

export function listDevices(params) {
  return http.get('/api/v1/devices/', { params })
}

export function createDevice(payload) {
  return http.post('/api/v1/devices/', payload)
}

export function getDevice(deviceId) {
  return http.get(`/api/v1/devices/${encodeURIComponent(deviceId)}/`)
}

export function updateDevice(deviceId, payload) {
  return http.put(`/api/v1/devices/${encodeURIComponent(deviceId)}/`, payload)
}

export function deleteDevice(deviceId) {
  return http.delete(`/api/v1/devices/${encodeURIComponent(deviceId)}/`)
}

export function controlDevice(deviceId, payload) {
  return http.post(`/api/v1/devices/control/${encodeURIComponent(deviceId)}/`, payload)
}

export function listDeviceLogs(deviceId, params) {
  return http.get(`/api/v1/devices/logs/${encodeURIComponent(deviceId)}/`, { params })
}

