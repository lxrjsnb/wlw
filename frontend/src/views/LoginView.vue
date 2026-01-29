<template>
  <div class="login-page">
    <!-- 背景网格 -->
    <div class="grid-background">
      <div class="grid-line horizontal"></div>
      <div class="grid-line horizontal"></div>
      <div class="grid-line horizontal"></div>
      <div class="grid-line vertical"></div>
      <div class="grid-line vertical"></div>
    </div>

    <!-- 光晕效果 -->
    <div class="glow-effect"></div>

    <!-- 顶部导航 -->
    <header class="login-header">
      <div class="brand">
        <el-icon class="brand-icon" :size="28"><DataLine /></el-icon>
        <span class="brand-name">舆情分析系统</span>
        <span class="brand-dot"></span>
        <span class="brand-version">v2.1</span>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="login-main">
      <!-- 左侧信息区 -->
      <div class="info-section">
        <div class="status-badge">
          <span class="status-dot"></span>
          系统运行中
        </div>

        <h1 class="main-title">
          舆情分析
          <span class="highlight">智能洞察</span>
        </h1>

        <p class="description">
          新一代社交媒体舆情监测平台<br>
          实时监测 · 情感分析 · 趋势预测 · 智能预警
        </p>

        <div class="feature-list">
          <div class="feature-item">
            <el-icon class="feature-icon"><Monitor /></el-icon>
            <div class="feature-text">
              <div class="feature-value">24/7</div>
              <div class="feature-label">实时监控</div>
            </div>
          </div>
          <div class="feature-divider"></div>
          <div class="feature-item">
            <el-icon class="feature-icon"><DataAnalysis /></el-icon>
            <div class="feature-text">
              <div class="feature-value">< 100ms</div>
              <div class="feature-label">响应延迟</div>
            </div>
          </div>
          <div class="feature-divider"></div>
          <div class="feature-item">
            <el-icon class="feature-icon"><Bell /></el-icon>
            <div class="feature-text">
              <div class="feature-value">99.9%</div>
              <div class="feature-label">可用性</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录卡片 -->
      <div class="login-section">
        <div class="login-card">
          <div class="card-header">
            <h2>登录系统</h2>
            <p>请输入您的账号密码</p>
          </div>

          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="rules"
            class="login-form"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <div class="form-footer">
              <el-checkbox v-model="rememberMe">记住密码</el-checkbox>
            </div>

            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              登 录
            </el-button>
          </el-form>
        </div>
      </div>
    </main>

    <!-- 底部信息 -->
    <footer class="login-footer">
      <span>© {{ new Date().getFullYear() }} 舆情分析系统. All rights reserved.</span>
    </footer>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataLine, Monitor, DataAnalysis, Bell, User, Lock
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  // 检查表单引用
  if (!loginFormRef.value) {
    ElMessage.warning('表单未初始化')
    return
  }

  // 基本验证
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  try {
    // 验证表单
    await loginFormRef.value.validate()

    loading.value = true
    await auth.login({ username: loginForm.username, password: loginForm.password })

    ElMessage.success('登录成功')
    const next = route.query.next ? String(route.query.next) : '/'
    router.replace(next)
  } catch (error) {
    console.error('登录失败:', error)

    // 表单验证失败
    if (error === false) {
      return
    }

    // API 请求失败
    if (error?.response?.status === 401) {
      ElMessage.error('用户名或密码错误')
    } else if (error?.response?.status === 404) {
      ElMessage.error('登录接口不存在，请检查后端服务')
    } else if (error?.response?.status === 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else if (error?.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error?.message) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('登录失败，请检查网络连接')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: #030508;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* === 背景网格效果 === */
.grid-background {
  position: absolute;
  inset: 0;
  opacity: 0.3;
  background-image:
    linear-gradient(rgba(0, 195, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 195, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 30s linear infinite;
}

@keyframes gridMove {
  0% { background-position: 0 0; }
  100% { background-position: 50px 50px; }
}

.grid-line {
  position: absolute;
  background: linear-gradient(90deg, transparent, rgba(0, 195, 255, 0.3), transparent);
  height: 1px;
  width: 100%;
  animation: lineScan 8s ease-in-out infinite;
}

.grid-line.horizontal:nth-child(1) { top: 20%; animation-delay: 0s; }
.grid-line.horizontal:nth-child(2) { top: 50%; animation-delay: 2s; }
.grid-line.horizontal:nth-child(3) { top: 80%; animation-delay: 4s; }

.grid-line.vertical {
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, transparent, rgba(0, 195, 255, 0.3), transparent);
  left: 30%;
  animation: lineScanVertical 10s ease-in-out infinite;
}

.grid-line.vertical:nth-child(4) { left: 30%; animation-delay: 0s; }
.grid-line.vertical:nth-child(5) { left: 70%; animation-delay: 5s; }

@keyframes lineScan {
  0%, 100% { opacity: 0; transform: translateX(-100px); }
  50% { opacity: 1; transform: translateX(100px); }
}

@keyframes lineScanVertical {
  0%, 100% { opacity: 0; transform: translateY(-100px); }
  50% { opacity: 1; transform: translateY(100px); }
}

/* === 光晕效果 === */
.glow-effect {
  position: absolute;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(0, 195, 255, 0.15) 0%, transparent 70%);
  top: -200px;
  right: -200px;
  filter: blur(100px);
  animation: glowPulse 6s ease-in-out infinite alternate;
}

@keyframes glowPulse {
  0% { opacity: 0.5; transform: scale(1); }
  100% { opacity: 1; transform: scale(1.2); }
}

/* === 顶部导航 === */
.login-header {
  position: relative;
  z-index: 10;
  padding: 24px 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  color: #00c3ff;
  filter: drop-shadow(0 0 8px rgba(0, 195, 255, 0.5));
}

.brand-name {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
  background: linear-gradient(180deg, #fff 0%, #888 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #00c3ff;
  box-shadow: 0 0 8px rgba(0, 195, 255, 0.8);
}

.brand-version {
  font-size: 11px;
  color: #666;
  font-weight: 500;
  letter-spacing: 1px;
}

/* === 主内容区 === */
.login-main {
  position: relative;
  z-index: 10;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 100px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

/* === 左侧信息区 === */
.info-section {
  flex: 1;
  max-width: 550px;
  animation: slideInLeft 0.8s ease-out;
}

@keyframes slideInLeft {
  0% { opacity: 0; transform: translateX(-40px); }
  100% { opacity: 1; transform: translateX(0); }
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(0, 195, 255, 0.1);
  border: 1px solid rgba(0, 195, 255, 0.3);
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  color: #00c3ff;
  margin-bottom: 32px;
  letter-spacing: 1px;
  backdrop-filter: blur(10px);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00ff88;
  box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.7);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(0, 255, 136, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 136, 0); }
}

.main-title {
  font-size: 52px;
  line-height: 1.2;
  font-weight: 800;
  margin: 0 0 24px;
  letter-spacing: 2px;
  color: #fff;
}

.main-title .highlight {
  display: block;
  background: linear-gradient(135deg, #00c3ff 0%, #0088ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-top: 8px;
}

.description {
  font-size: 15px;
  line-height: 1.8;
  color: #888;
  margin-bottom: 48px;
  letter-spacing: 0.5px;
}

.feature-list {
  display: flex;
  align-items: center;
  gap: 32px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.feature-icon {
  font-size: 24px;
  color: #00c3ff;
  filter: drop-shadow(0 0 6px rgba(0, 195, 255, 0.4));
}

.feature-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.feature-value {
  font-size: 18px;
  font-weight: 700;
  color: #00c3ff;
}

.feature-label {
  font-size: 11px;
  color: #666;
  letter-spacing: 1px;
}

.feature-divider {
  width: 1px;
  height: 40px;
  background: linear-gradient(180deg, transparent, rgba(255, 255, 255, 0.1), transparent);
}

/* === 右侧登录区 === */
.login-section {
  flex: 0 0 400px;
  animation: slideInRight 0.8s ease-out;
}

@keyframes slideInRight {
  0% { opacity: 0; transform: translateX(40px); }
  100% { opacity: 1; transform: translateX(0); }
}

.login-card {
  background: rgba(10, 15, 25, 0.8);
  backdrop-filter: blur(40px);
  padding: 40px;
  border-radius: 16px;
  border: 1px solid rgba(0, 195, 255, 0.15);
  box-shadow: 0 0 60px rgba(0, 195, 255, 0.1);
  transition: all 0.3s ease;
}

.login-card:hover {
  border-color: rgba(0, 195, 255, 0.3);
  box-shadow: 0 0 80px rgba(0, 195, 255, 0.15);
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.card-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
  letter-spacing: 1px;
}

.card-header p {
  font-size: 13px;
  color: #666;
  margin: 0;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: none;
  border-radius: 10px;
  transition: all 0.3s;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 195, 255, 0.3);
  background: rgba(255, 255, 255, 0.05);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #00c3ff;
  background: rgba(0, 195, 255, 0.05);
  box-shadow: 0 0 20px rgba(0, 195, 255, 0.1);
}

.login-form :deep(.el-input__inner) {
  color: #fff;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #555;
}

.login-form :deep(.el-input__prefix-inner > .el-icon) {
  color: #666;
}

.form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.form-footer :deep(.el-checkbox__label) {
  color: #888;
  font-size: 13px;
}

.form-footer :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #00c3ff;
  border-color: #00c3ff;
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #00c3ff 0%, #0088ff 100%);
  border: none;
  letter-spacing: 2px;
  transition: all 0.3s;
  box-shadow: 0 4px 20px rgba(0, 195, 255, 0.3);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(0, 195, 255, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

/* === 底部 === */
.login-footer {
  text-align: center;
  padding: 20px;
  font-size: 12px;
  color: #444;
  position: relative;
  z-index: 10;
  letter-spacing: 1px;
}

/* === 响应式 === */
@media (max-width: 1024px) {
  .login-main {
    flex-direction: column;
    gap: 40px;
    padding: 24px;
  }

  .info-section {
    text-align: center;
    max-width: 100%;
  }

  .feature-list {
    justify-content: center;
    flex-wrap: wrap;
  }

  .login-section {
    width: 100%;
    max-width: 400px;
  }

  .main-title {
    font-size: 36px;
  }
}
</style>
