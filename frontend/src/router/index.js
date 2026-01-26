import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/LoginView.vue'),
        meta: { title: '登录' }
    },
    {
        path: '/',
        component: MainLayout,
        redirect: '/dashboard',
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('../views/DashboardView.vue'),
                meta: { title: '仪表盘', requiresAuth: true }
            },
            {
                path: 'devices',
                name: 'DeviceList',
                component: () => import('../views/Device/DeviceList.vue'),
                meta: { title: '设备管理', requiresAuth: true }
            },
            {
                path: 'data/realtime',
                name: 'RealTimeData',
                component: () => import('../views/data/RealTimeData.vue'),
                meta: { title: '实时监控', requiresAuth: true }
            },
            {
                path: 'alarms',
                name: 'AlarmCenter',
                component: () => import('../views/Alarm/AlarmList.vue'),
                meta: { title: '告警中心', requiresAuth: true }
            },
            {
                path: 'users',
                name: 'UserManagement',
                component: () => import('../views/User/UserManagement.vue'),
                meta: { title: '用户管理', requiresAuth: true, requiresAdmin: true }
            },
            {
                path: 'settings',
                name: 'SystemSettings',
                component: () => import('../views/System/SystemSettings.vue'),
                meta: { title: '系统设置', requiresAuth: true, requiresAdmin: true }
            },
            {
                path: 'reports',
                name: 'DataReport',
                component: () => import('../views/Report/DataReport.vue'),
                meta: { title: '数据报表', requiresAuth: true }
            }
        ]
    },
    {
        path: '/:pathMatch(.*)*',
        redirect: '/dashboard'
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach(async (to, from, next) => {
    document.title = to.meta?.title ? `${to.meta.title} - IoT 监控系统` : 'IoT 监控系统'
    const auth = useAuthStore()

    if (to.path === '/login' && auth.isAuthenticated) {
        next({ path: '/', replace: true })
        return
    }

    if (to.meta.requiresAuth && !auth.isAuthenticated) {
        next({ path: '/login', query: { next: to.fullPath } })
        return
    }

    if (to.meta.requiresAdmin && auth.role !== 'admin') {
        next({ path: '/dashboard' })
        return
    }

    if (auth.isAuthenticated && !auth.user) {
        try {
            await auth.fetchMe()
        } catch {
            await auth.logout()
            next({ path: '/login', query: { next: to.fullPath } })
            return
        }
    }

    next()
})

export default router
