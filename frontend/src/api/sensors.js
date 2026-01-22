import { http } from './http'

export function listSensorData(params) {
  return http.get('/api/v1/sensors/data/', { params })
}

export function getLatestDeviceData(deviceId) {
  return http.get(`/api/v1/sensors/data/latest/${encodeURIComponent(deviceId)}/`)
}

export function getDeviceHistory(deviceId, params) {
  return http.get(`/api/v1/sensors/data/history/${encodeURIComponent(deviceId)}/`, { params })
}

export function getDeviceStatistics(deviceId, params) {
  return http.get(`/api/v1/sensors/data/statistics/${encodeURIComponent(deviceId)}/`, { params })
}

export async function exportSensorData(params) {
  return http.get('/api/v1/sensors/data/export/', {
    params,
    responseType: 'blob',
  })
}

