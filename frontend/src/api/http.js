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

  // 开发模式下打印请求信息
  if (import.meta.env.DEV) {
    console.log('🔵 API 请求:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      data: config.data,
      headers: config.headers
    })
  }

  return config
})

http.interceptors.response.use(
  (response) => {
    // 开发模式下打印响应信息
    if (import.meta.env.DEV) {
      console.log('🟢 API 响应:', {
        url: response.config.url,
        status: response.status,
        data: response.data
      })
    }

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
    const config = error?.config

    // 开发模式下打印错误信息
    if (import.meta.env.DEV) {
      console.error('🔴 API 错误:', {
        url: config?.url,
        status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        message: error?.message
      })
    }

    // 401 错误处理
    if (status === 401) {
      // 如果是登录接口，不清除 token（因为登录时本来就没有 token）
      if (!config?.url?.includes('/auth/login/')) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
      }
    }
    throw error
  }
)

