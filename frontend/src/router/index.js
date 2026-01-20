/**
 * 路由配置
 * Router configuration
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard/Index.vue'),
        meta: { title: '仪表盘', icon: 'DataAnalysis' }
      },
      {
        path: 'devices',
        name: 'DeviceList',
        component: () => import('@/views/Device/Index.vue'),
        meta: { title: '设备管理', icon: 'Monitor' }
      },
      {
        path: 'devices/:id',
        name: 'DeviceDetail',
        component: () => import('@/views/Device/Detail.vue'),
        meta: { title: '设备详情', icon: 'Monitor' }
      },
      {
        path: 'monitor/realtime',
        name: 'RealtimeMonitor',
        component: () => import('@/views/Monitor/Realtime.vue'),
        meta: { title: '实时监控', icon: 'Connection' }
      },
      {
        path: 'monitor/history',
        name: 'HistoryMonitor',
        component: () => import('@/views/Monitor/History.vue'),
        meta: { title: '历史数据', icon: 'TrendCharts' }
      },
      {
        path: 'alarms',
        name: 'AlarmList',
        component: () => import('@/views/Alarm/Index.vue'),
        meta: { title: '告警管理', icon: 'Warning' }
      },
      {
        path: 'alarms/rules',
        name: 'AlarmRules',
        component: () => import('@/views/Alarm/Rules.vue'),
        meta: { title: '告警规则', icon: 'Setting' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings/Index.vue'),
        meta: { title: '系统设置', icon: 'Tools' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/404.vue'),
    meta: { title: '404', requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 设置页面标题
  document.title = to.meta.title
    ? `${to.meta.title} - ${import.meta.env.VITE_APP_TITLE}`
    : import.meta.env.VITE_APP_TITLE

  // 检查是否需要认证
  if (to.meta.requiresAuth !== false) {
    if (!userStore.token) {
      ElMessage.warning('请先登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
  }

  // 如果已登录且访问登录页，重定向到首页
  if (to.path === '/login' && userStore.token) {
    next({ path: '/' })
    return
  }

  next()
})

export default router
