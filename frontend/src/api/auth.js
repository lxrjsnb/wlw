/**
 * 认证相关API
 * Authentication API
 */
import request from '@/utils/request'

// 用户登录
export function login(data) {
  return request({
    url: '/auth/login/',
    method: 'post',
    data
  })
}

// 用户登出
export function logout() {
  return request({
    url: '/auth/logout/',
    method: 'post'
  })
}

// 刷新Token
export function refreshToken(data) {
  return request({
    url: '/auth/refresh/',
    method: 'post',
    data
  })
}

// 获取当前用户信息
export function getUserInfo() {
  return request({
    url: '/auth/user/',
    method: 'get'
  })
}

// 修改密码
export function changePassword(data) {
  return request({
    url: '/auth/change-password/',
    method: 'post',
    data
  })
}

// 用户注册
export function register(data) {
  return request({
    url: '/auth/register/',
    method: 'post',
    data
  })
}
