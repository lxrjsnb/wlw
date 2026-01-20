/**
 * Axios请求封装
 * Axios request interceptor and wrapper
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    const token = userStore.token

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const { code, message, data } = response.data

    // 请求成功
    if (code === 0 || code === undefined) {
      return data
    }

    // 业务错误
    ElMessage.error(message || '请求失败')
    return Promise.reject(new Error(message || '请求失败'))
  },
  error => {
    console.error('Response error:', error)

    if (error.response) {
      const { status, data } = error.response

      // 401 未授权 - 跳转登录
      if (status === 401) {
        const userStore = useUserStore()
        userStore.logout()
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
        return Promise.reject(error)
      }

      // 403 禁止访问
      if (status === 403) {
        ElMessage.error(data.message || '无权访问')
        return Promise.reject(error)
      }

      // 404 资源不存在
      if (status === 404) {
        ElMessage.error(data.message || '请求的资源不存在')
        return Promise.reject(error)
      }

      // 500 服务器错误
      if (status === 500) {
        ElMessage.error(data.message || '服务器错误')
        return Promise.reject(error)
      }

      // 其他错误
      ElMessage.error(data.message || error.message || '请求失败')
    } else if (error.message.includes('timeout')) {
      ElMessage.error('请求超时，请重试')
    } else if (error.message.includes('Network')) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error(error.message || '请求失败')
    }

    return Promise.reject(error)
  }
)

export default request
