import { http } from './http'

export function login({ username, password }) {
  return http.post('/api/v1/auth/login/', { username, password })
}

export function logout() {
  return http.post('/api/v1/auth/logout/')
}

export function getCurrentUser() {
  return http.get('/api/v1/auth/user/')
}

