/**
 * 用户状态管理
 * User state management with Pinia
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login, logout, getUserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const userInfo = ref(null)
  const roles = ref([])

  // 登录
  async function loginAction(loginData) {
    try {
      const response = await login(loginData)
      token.value = response.access
      userInfo.value = response.user
      roles.value = [response.user.role]

      // 存储token到localStorage
      localStorage.setItem('access_token', response.access)
      if (response.refresh) {
        localStorage.setItem('refresh_token', response.refresh)
      }

      return response
    } catch (error) {
      throw error
    }
  }

  // 登出
  async function logoutAction() {
    try {
      await logout()
    } finally {
      // 清除本地存储
      token.value = ''
      userInfo.value = null
      roles.value = []
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  // 获取用户信息
  async function fetchUserInfo() {
    try {
      const response = await getUserInfo()
      userInfo.value = response
      roles.value = [response.role]
      return response
    } catch (error) {
      throw error
    }
  }

  // 初始化用户信息
  async function initUser() {
    if (token.value && !userInfo.value) {
      try {
        await fetchUserInfo()
      } catch (error) {
        // Token无效，清除
        token.value = ''
        localStorage.removeItem('access_token')
      }
    }
  }

  // 判断是否有权限
  function hasRole(role) {
    return roles.value.includes(role)
  }

  // 判断是否为管理员
  function isAdmin() {
    return hasRole('admin')
  }

  // 判断是否为操作员或管理员
  function isOperator() {
    return hasRole('admin') || hasRole('operator')
  }

  return {
    token,
    userInfo,
    roles,
    loginAction,
    logout: logoutAction,
    fetchUserInfo,
    initUser,
    hasRole,
    isAdmin,
    isOperator
  }
})
