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
                meta: { title: '舆情总览', requiresAuth: true }
            },
            {
                path: 'topics',
                name: 'TopicList',
                component: () => import('../views/Topic/TopicList.vue'),
                meta: { title: '话题管理', requiresAuth: true }
            },
            {
                path: 'posts',
                name: 'PostList',
                component: () => import('../views/Post/PostList.vue'),
                meta: { title: '帖子列表', requiresAuth: true }
            },
            {
                path: 'posts/realtime',
                name: 'RealtimePostView',
                component: () => import('../views/Post/RealtimePostView.vue'),
                meta: { title: '实时监控', requiresAuth: true }
            },
            {
                path: 'analysis/sentiment',
                name: 'SentimentView',
                component: () => import('../views/Analysis/SentimentView.vue'),
                meta: { title: '情感分析', requiresAuth: true }
            },
            {
                path: 'analysis/trend',
                name: 'TrendView',
                component: () => import('../views/Analysis/TrendView.vue'),
                meta: { title: '趋势分析', requiresAuth: true }
            },
            {
                path: 'analysis/hotness',
                name: 'HotnessAnalysis',
                component: () => import('../views/Analysis/HotnessView.vue'),
                meta: { title: '热度分析', requiresAuth: true }
            },
            {
                path: 'analysis/propagation',
                name: 'PropagationAnalysis',
                component: () => import('../views/Analysis/PropagationView.vue'),
                meta: { title: '传播分析', requiresAuth: true }
            },
            {
                path: 'analysis/emergency',
                name: 'EmergencyAnalysis',
                component: () => import('../views/Analysis/EmergencyView.vue'),
                meta: { title: '突发事件', requiresAuth: true }
            },
            {
                path: 'analysis/kol',
                name: 'KOLAnalysis',
                component: () => import('../views/Analysis/KOLView.vue'),
                meta: { title: 'KOL画像', requiresAuth: true }
            },
            {
                path: 'analysis/evolution',
                name: 'EvolutionAnalysis',
                component: () => import('../views/Analysis/EvolutionView.vue'),
                meta: { title: '舆情演化', requiresAuth: true }
            },
            {
                path: 'alerts',
                name: 'AlertList',
                component: () => import('../views/Alert/AlertList.vue'),
                meta: { title: '预警中心', requiresAuth: true }
            },
            {
                path: 'alerts/rules',
                name: 'AlertRuleList',
                component: () => import('../views/Alert/AlertRuleList.vue'),
                meta: { title: '预警规则', requiresAuth: true }
            },
            {
                path: 'reports',
                name: 'DataReport',
                component: () => import('../views/Report/DataReport.vue'),
                meta: { title: '数据报表', requiresAuth: true }
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
    document.title = to.meta?.title ? `${to.meta.title} - 舆情分析系统` : '舆情分析系统'
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
