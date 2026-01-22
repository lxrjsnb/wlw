import axios from 'axios'

function getAccessToken() {
  return localStorage.getItem('access_token') || ''
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 20000,
})

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    if (response.config.responseType === 'blob') return response
    const payload = response.data
    if (payload && typeof payload === 'object' && 'code' in payload) {
      if (payload.code !== 0) {
        const error = new Error(payload.message || '请求失败')
        error.code = payload.code
        error.payload = payload
        throw error
      }
      return payload.data
    }
    return payload
  },
  (error) => {
    const status = error?.response?.status
    if (status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    }
    throw error
  }
)

