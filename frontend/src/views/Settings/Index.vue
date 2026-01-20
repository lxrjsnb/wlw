<template>
  <div class="settings-page">
    <el-card class="settings-card">
      <template #header>系统设置</template>

      <el-tabs v-model="activeTab">
        <!-- 个人信息 -->
        <el-tab-pane label="个人信息" name="profile">
          <el-form :model="userForm" label-width="120px" style="max-width: 600px">
            <el-form-item label="用户名">
              <el-input v-model="userForm.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="userForm.email" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="userForm.phone" />
            </el-form-item>
            <el-form-item label="角色">
              <el-tag>{{ getRoleText(userForm.role) }}</el-tag>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveProfile">保存</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 修改密码 -->
        <el-tab-pane label="修改密码" name="password">
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="120px"
            style="max-width: 600px"
          >
            <el-form-item label="旧密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认新密码" prop="new_password_confirm">
              <el-input
                v-model="passwordForm.new_password_confirm"
                type="password"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 系统信息 -->
        <el-tab-pane label="系统信息" name="system">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="系统名称">
              物联网环境监测系统
            </el-descriptions-item>
            <el-descriptions-item label="系统版本">
              v1.0.0
            </el-descriptions-item>
            <el-descriptions-item label="前端版本">
              {{ frontendVersion }}
            </el-descriptions-item>
            <el-descriptions-item label="后端API">
              {{ backendApi }}
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { changePassword } from '@/api/auth'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const activeTab = ref('profile')
const passwordFormRef = ref(null)

const userForm = reactive({
  username: '',
  email: '',
  phone: '',
  role: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  new_password_confirm: ''
})

const passwordRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  new_password_confirm: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const frontendVersion = 'v1.0.0'
const backendApi = import.meta.env.VITE_API_BASE_URL

// 初始化用户信息
function initUserInfo() {
  if (userStore.userInfo) {
    Object.assign(userForm, {
      username: userStore.userInfo.username,
      email: userStore.userInfo.email || '',
      phone: userStore.userInfo.phone || '',
      role: userStore.userInfo.role
    })
  }
}

// 保存个人信息
function handleSaveProfile() {
  ElMessage.success('个人信息保存成功')
  // TODO: 调用API保存个人信息
}

// 修改密码
async function handleChangePassword() {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await changePassword({
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password,
          new_password_confirm: passwordForm.new_password_confirm
        })
        ElMessage.success('密码修改成功，请重新登录')
        passwordFormRef.value.resetFields()
      } catch (error) {
        ElMessage.error('密码修改失败')
      }
    }
  })
}

// 获取角色文本
function getRoleText(role) {
  const map = {
    admin: '管理员',
    operator: '操作员',
    viewer: '查看者'
  }
  return map[role] || role
}

onMounted(() => {
  initUserInfo()
})
</script>

<style scoped>
.settings-page {
  padding: 0;
}

.settings-card {
  max-width: 1000px;
}
</style>
