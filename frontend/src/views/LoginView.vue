<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login({ username: form.username, password: form.password })
    ElMessage.success('登录成功')
    const next = route.query.next ? String(route.query.next) : '/'
    router.replace(next)
  } catch (e) {
    const msg =
      e?.response?.data?.message ||
      e?.payload?.message ||
      e?.message ||
      '登录失败，请检查账号密码'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-content">
      <div class="left-panel">
        <div class="brand">
          <h1>IoT 监控系统</h1>
          <p>新一代环境监测平台</p>
        </div>
        <div class="illustration">
          <!-- Add SVG or Image here -->
        </div>
      </div>
      
      <div class="right-panel">
        <div class="login-box">
          <h2>欢迎回来</h2>
          <p class="subtitle">请登录您的账户</p>
          
          <el-form :model="form" class="login-form">
            <el-form-item>
              <el-input 
                v-model="form.username" 
                placeholder="用户名" 
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            
            <el-form-item>
              <el-input 
                v-model="form.password" 
                placeholder="密码" 
                type="password" 
                size="large"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            
            <el-button 
              type="primary" 
              class="login-btn" 
              size="large" 
              :loading="loading"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2b32b2 0%, #1488cc 100%);
}

.login-content {
  width: 900px;
  height: 550px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 15px 35px rgba(0,0,0,0.2);
  display: flex;
  overflow: hidden;
}

.left-panel {
  flex: 1;
  background: linear-gradient(135deg, #3a7bd5 0%, #3a6073 100%);
  padding: 40px;
  display: flex;
  flex-direction: column;
  color: #fff;
  position: relative;
}

.brand h1 {
  font-size: 36px;
  font-weight: 700;
  margin: 0;
}

.brand p {
  opacity: 0.8;
  margin-top: 10px;
  font-size: 16px;
}

.right-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.login-box {
  width: 100%;
  max-width: 320px;
}

.login-box h2 {
  font-size: 28px;
  color: #333;
  margin-bottom: 8px;
}

.subtitle {
  color: #666;
  margin-bottom: 30px;
}

.login-btn {
  width: 100%;
  margin-top: 10px;
  font-weight: 600;
}
</style>
