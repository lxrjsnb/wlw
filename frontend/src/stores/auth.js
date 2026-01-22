import { defineStore } from 'pinia'
import * as authApi from '../api/auth'

const STORAGE_KEYS = {
  access: 'access_token',
  refresh: 'refresh_token',
  user: 'user',
}

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw)
  } catch {
    return fallback
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem(STORAGE_KEYS.access) || '',
    refreshToken: localStorage.getItem(STORAGE_KEYS.refresh) || '',
    user: readJson(STORAGE_KEYS.user, null),
    ready: true,
  }),
  getters: {
    isAuthenticated: (s) => Boolean(s.accessToken),
    role: (s) => s.user?.role || '',
    username: (s) => s.user?.username || '',
    canManageAlarms: (s) => ['admin', 'operator'].includes(s.user?.role),
    canControlDevice: (s) => ['admin', 'operator'].includes(s.user?.role),
  },
  actions: {
    setSession({ access, refresh, user }) {
      this.accessToken = access || ''
      this.refreshToken = refresh || ''
      this.user = user || null
      if (access) localStorage.setItem(STORAGE_KEYS.access, access)
      if (refresh) localStorage.setItem(STORAGE_KEYS.refresh, refresh)
      if (user) localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user))
    },
    async login({ username, password }) {
      const data = await authApi.login({ username, password })
      this.setSession({ access: data.access, refresh: data.refresh, user: data.user })
      return data
    },
    async fetchMe() {
      const data = await authApi.getCurrentUser()
      this.user = data
      localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(data))
      return data
    },
    async logout() {
      try {
        await authApi.logout()
      } catch {
        // ignore
      }
      this.accessToken = ''
      this.refreshToken = ''
      this.user = null
      localStorage.removeItem(STORAGE_KEYS.access)
      localStorage.removeItem(STORAGE_KEYS.refresh)
      localStorage.removeItem(STORAGE_KEYS.user)
    },
  },
})

