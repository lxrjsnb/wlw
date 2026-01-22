import { http } from './http'

export function getAlarmStats() {
  return http.get('/api/v1/alarms/stats/')
}

export function listAlarmRecords(params) {
  return http.get('/api/v1/alarms/records/', { params })
}

export function updateAlarmRecord(recordId, payload) {
  return http.patch(`/api/v1/alarms/records/${recordId}/`, payload)
}

export function resolveAlarmRecord(recordId, payload) {
  return http.post(`/api/v1/alarms/records/${recordId}/resolve/`, payload)
}

export function listAlarmRules(params) {
  return http.get('/api/v1/alarms/rules/', { params })
}

export function createAlarmRule(payload) {
  return http.post('/api/v1/alarms/rules/create/', payload)
}

export function updateAlarmRule(ruleId, payload) {
  return http.put(`/api/v1/alarms/rules/${ruleId}/`, payload)
}

export function deleteAlarmRule(ruleId) {
  return http.delete(`/api/v1/alarms/rules/${ruleId}/`)
}

export function listAlarmNotifications(params) {
  return http.get('/api/v1/alarms/notifications/', { params })
}
