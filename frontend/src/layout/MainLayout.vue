<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ChatDotRound, Document, DataLine, Bell, Setting, Fold, Expand, User, UserFilled, TrendCharts, FolderOpened, Files, Sunny, Share, Warning, Avatar, Compass } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import ErrorBoundary from '../components/ErrorBoundary.vue'

const router = useRouter()
const route = useRoute()
const isCollapse = ref(false)
const auth = useAuthStore()

const activeMenu = computed(() => route.path)

const displayName = computed(() => auth.user?.username || '未登录')

const handleCommand = async (command) => {
  if (command === 'logout') {
    await auth.logout()
    router.push('/login')
    return
  }
  if (command === 'profile') {
    router.push('/dashboard')
  }
}

const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

const handleMenuSelect = (key) => {
  console.log('Menu selected:', key)
  router.push(key)
}

// 根据用户角色显示不同的菜单
const menuItems = computed(() => {
  const items = [
    { path: '/dashboard', icon: TrendCharts, title: '舆情总览' },
    { path: '/topics', icon: FolderOpened, title: '话题管理' },
    { path: '/posts', icon: Document, title: '帖子列表' },
    { path: '/posts/realtime', icon: DataLine, title: '实时监控' },
    // 深度分析分组
    { type: 'group', title: '深度分析' },
    { path: '/analysis/sentiment', icon: ChatDotRound, title: '情感分析' },
    { path: '/analysis/trend', icon: TrendCharts, title: '趋势分析' },
    { path: '/analysis/hotness', icon: Sunny, title: '热度分析' },
    { path: '/analysis/propagation', icon: Share, title: '传播分析' },
    { path: '/analysis/emergency', icon: Warning, title: '突发事件' },
    { path: '/analysis/kol', icon: Avatar, title: 'KOL画像' },
    { path: '/analysis/evolution', icon: Compass, title: '舆情演化' },
    { path: '/alerts', icon: Bell, title: '预警中心' },
    { path: '/alerts/rules', icon: Setting, title: '预警规则' },
  ]

  // 所有用户都可以访问数据报表
  items.push({ path: '/reports', icon: Files, title: '数据报表' })

  // 仅管理员可见的菜单
  if (auth.role === 'admin') {
    items.push({ path: '/users', icon: UserFilled, title: '用户管理' })
    items.push({ path: '/settings', icon: Setting, title: '系统设置' })
  }

  return items
})
</script>

<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '240px'" class="aside">
      <div class="logo-container">
        <img src="/vite.svg" alt="Logo" class="logo" />
        <h1 v-show="!isCollapse" class="title">舆情分析系统</h1>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        :collapse="isCollapse"
        background-color="transparent"
        text-color="#475569"
        active-text-color="#ffffff"
        router
        @select="handleMenuSelect"
      >
        <template v-for="item in menuItems" :key="item.path || item.title">
          <!-- 分组标题 -->
          <el-menu-item-group v-if="item.type === 'group' && !isCollapse" :title="item.title">
          </el-menu-item-group>
          <!-- 普通菜单项 -->
          <el-menu-item v-else-if="item.path" :index="item.path">
            <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="trigger" @click="toggleSidebar">
            <Expand v-if="isCollapse" />
            <Fold v-else />
          </el-icon>
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="el-dropdown-link user-profile">
              <el-avatar :size="32" :icon="User" />
              <span class="username">{{ displayName }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main grid-bg">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <ErrorBoundary>
              <component :is="Component" />
            </ErrorBoundary>
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-container {
  height: 100vh;
}

.aside {
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
  border-right: 1px solid #E2E8F0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.03);
  transition: width 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
  overflow: hidden;
  padding: 0 10px;
}

.logo {
  height: 32px;
  width: 32px;
}

.title {
  margin-left: 12px;
  color: #FFFFFF;
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
}

.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #E2E8F0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
}

.trigger {
  font-size: 20px;
  cursor: pointer;
  margin-right: 20px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-profile {
  display: flex;
  align-items: center;
  cursor: pointer;
  outline: none;
}

.username {
  margin-left: 8px;
  font-size: 14px;
  color: #606266;
}

.main {
  background-color: #F8FAFC;
  padding: 24px;
}

/* New fade-slide transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
