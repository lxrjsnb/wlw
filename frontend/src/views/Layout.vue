<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
      <div class="logo">
        <el-icon v-if="!isCollapse" class="logo-icon"><Monitor /></el-icon>
        <span v-if="!isCollapse">IoT监测</span>
        <el-icon v-else class="logo-mini"><Monitor /></el-icon>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item
          v-for="item in menuList"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.meta.icon" /></el-icon>
          <template #title>{{ item.meta.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主体内容 -->
    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute.meta.title">
              {{ currentRoute.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <!-- 告警通知 -->
          <el-badge :value="alarmCount" :hidden="alarmCount === 0" class="alarm-badge">
            <el-icon @click="showAlarmDialog">
              <Bell />
            </el-icon>
          </el-badge>

          <!-- 用户下拉菜单 -->
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar">
                {{ userStore.userInfo?.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <span class="username">{{ userStore.userInfo?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人信息
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区域 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- 告警通知弹窗 -->
    <el-drawer
      v-model="alarmDialogVisible"
      title="告警通知"
      direction="rtl"
      size="400px"
    >
      <AlarmList />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { createAlarmWebSocket } from '@/utils/websocket'
import { ElMessageBox, ElMessage, ElNotification } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const alarmDialogVisible = ref(false)
const alarmCount = ref(0)

// 当前路由
const currentRoute = computed(() => route)

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 菜单列表（排除布局子路由）
const menuList = computed(() => {
  const routes = router.options.routes
  const layout = routes.find(r => r.name === 'Layout')
  return layout?.children.filter(c => !c.path.includes(':')) || []
})

// WebSocket实例
let ws = null

// 初始化WebSocket
onMounted(() => {
  // 连接告警WebSocket
  ws = createAlarmWebSocket()
  ws.connect()

  ws.on('message', (data) => {
    if (data.type === 'alarm') {
      alarmCount.value++
      ElNotification({
        title: '告警通知',
        message: data.data.message,
        type: 'warning',
        duration: 5000
      })
    }
  })
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})

// 显示告警弹窗
function showAlarmDialog() {
  alarmDialogVisible.value = true
}

// 处理下拉菜单命令
function handleCommand(command) {
  switch (command) {
    case 'profile':
      router.push('/settings')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 退出登录
function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await userStore.logout()
    ElMessage.success('退出成功')
    router.push('/login')
  })
}
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: 100%;
  display: flex;
}

.sidebar {
  background: #304156;
  overflow-x: hidden;
  transition: width 0.3s;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-icon {
  width: 32px;
  height: 32px;
  margin-right: 8px;
  font-size: 32px;
  color: white;
}

.logo-mini {
  width: 32px;
  height: 32px;
  font-size: 32px;
  color: white;
}

.sidebar-menu {
  border: none;
  background: transparent;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: white;
  border-bottom: 1px solid #e6e6e6;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  margin-right: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.alarm-badge {
  cursor: pointer;
  font-size: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: 8px;
}

.username {
  font-size: 14px;
}

.main-content {
  flex: 1;
  overflow: auto;
  background: #f0f2f5;
  padding: 20px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
