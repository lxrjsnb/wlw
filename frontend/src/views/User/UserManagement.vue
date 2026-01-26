<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { User, Lock, Delete, Edit, Plus } from '@element-plus/icons-vue'
import { formatDateTime } from '../../utils/date'

const auth = useAuthStore()

const loading = ref(false)
const users = ref([])
const page = reactive({ total: 0, page: 1, page_size: 20 })
const filters = reactive({ keyword: '', role: '', department: '' })

const roleOptions = [
  { label: '管理员', value: 'admin' },
  { label: '操作员', value: 'operator' },
  { label: '查看者', value: 'viewer' },
]

const departmentOptions = [
  '技术部',
  '运维部',
  '监控部',
  '管理部',
]

async function loadUsers() {
  loading.value = true
  try {
    // TODO: 从 API 加载用户列表
    // const res = await listUsers({
    //   page: page.page,
    //   page_size: page.page_size,
    //   keyword: filters.keyword || undefined,
    //   role: filters.role || undefined,
    //   department: filters.department || undefined,
    // })
    // users.value = res?.items || []
    // page.total = res?.total || 0

    // 模拟数据
    users.value = [
      {
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        role: 'admin',
        department: '技术部',
        phone: '13800138001',
        is_active: true,
        last_login: '2024-01-20 10:30:00',
        date_joined: '2024-01-01 09:00:00',
      },
      {
        id: 2,
        username: 'operator1',
        email: 'operator1@example.com',
        role: 'operator',
        department: '运维部',
        phone: '13800138002',
        is_active: true,
        last_login: '2024-01-20 09:15:00',
        date_joined: '2024-01-05 14:20:00',
      },
      {
        id: 3,
        username: 'operator2',
        email: 'operator2@example.com',
        role: 'operator',
        department: '运维部',
        phone: '13800138003',
        is_active: true,
        last_login: '2024-01-19 16:45:00',
        date_joined: '2024-01-08 11:30:00',
      },
      {
        id: 4,
        username: 'viewer1',
        email: 'viewer1@example.com',
        role: 'viewer',
        department: '监控部',
        phone: '13800138004',
        is_active: true,
        last_login: '2024-01-20 08:00:00',
        date_joined: '2024-01-10 15:40:00',
      },
      {
        id: 5,
        username: 'viewer2',
        email: 'viewer2@example.com',
        role: 'viewer',
        department: '监控部',
        phone: '13800138005',
        is_active: false,
        last_login: '2024-01-15 12:20:00',
        date_joined: '2024-01-12 10:10:00',
      },
    ]
    page.total = 5
  } catch (e) {
    ElMessage.error(e?.message || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.role = ''
  filters.department = ''
  page.page = 1
  loadUsers()
}

// 创建/编辑用户对话框
const dialogVisible = ref(false)
const dialogMode = ref('create') // create | edit
const saving = ref(false)
const editingUserId = ref(null)
const userForm = reactive({
  username: '',
  email: '',
  password: '',
  role: 'viewer',
  department: '',
  phone: '',
  is_active: true,
})

function openCreate() {
  dialogMode.value = 'create'
  editingUserId.value = null
  Object.assign(userForm, {
    username: '',
    email: '',
    password: '',
    role: 'viewer',
    department: '',
    phone: '',
    is_active: true,
  })
  dialogVisible.value = true
}

function openEdit(row) {
  dialogMode.value = 'edit'
  editingUserId.value = row.id
  Object.assign(userForm, {
    username: row.username,
    email: row.email,
    password: '',
    role: row.role,
    department: row.department,
    phone: row.phone,
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function submitUser() {
  if (!userForm.username || !userForm.email) {
    ElMessage.warning('请填写用户名和邮箱')
    return
  }
  if (dialogMode.value === 'create' && !userForm.password) {
    ElMessage.warning('请设置初始密码')
    return
  }

  saving.value = true
  try {
    // TODO: 调用 API 创建/更新用户
    await new Promise(resolve => setTimeout(resolve, 500))

    if (dialogMode.value === 'create') {
      ElMessage.success('用户创建成功')
    } else {
      ElMessage.success('用户更新成功')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (e) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除用户「${row.username}」？此操作不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    // TODO: 调用 API 删除用户
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('已删除')
    await loadUsers()
  } catch {
    // cancelled
  }
}

// 修改密码对话框
const passwordDialogVisible = ref(false)
const passwordForm = reactive({
  userId: null,
  username: '',
  newPassword: '',
  confirmPassword: '',
})

function openChangePassword(row) {
  passwordForm.userId = row.id
  passwordForm.username = row.username
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordDialogVisible.value = true
}

async function submitChangePassword() {
  if (!passwordForm.newPassword) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (passwordForm.newPassword.length < 6) {
    ElMessage.warning('密码长度不能少于6位')
    return
  }

  saving.value = true
  try {
    // TODO: 调用 API 修改密码
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('密码修改成功')
    passwordDialogVisible.value = false
  } catch (e) {
    ElMessage.error(e?.message || '修改失败')
  } finally {
    saving.value = false
  }
}

function roleTagType(role) {
  if (role === 'admin') return 'danger'
  if (role === 'operator') return 'warning'
  return 'info'
}

function roleText(role) {
  const map = { admin: '管理员', operator: '操作员', viewer: '查看者' }
  return map[role] || role
}

onMounted(loadUsers)
</script>

<template>
  <div class="user-management">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </div>
          <div class="actions">
            <el-button type="primary" :icon="Plus" @click="openCreate" v-if="auth.is_admin">
              添加用户
            </el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="filters" @submit.prevent>
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="用户名/邮箱"
            clearable
            @change="loadUsers"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="filters.role" placeholder="全部" clearable style="width: 140px" @change="loadUsers">
            <el-option v-for="o in roleOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="filters.department" placeholder="全部" clearable style="width: 160px" @change="loadUsers">
            <el-option v-for="d in departmentOptions" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadUsers">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="users" style="width: 100%">
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="角色" width="110">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)">{{ roleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部门" min-width="120" />
        <el-table-column prop="phone" label="手机号" min-width="130" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.last_login) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Lock" @click="openChangePassword(row)" v-if="auth.is_admin">
              改密
            </el-button>
            <el-button size="small" :icon="Edit" @click="openEdit(row)" v-if="auth.is_admin">
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              :icon="Delete"
              @click="confirmDelete(row)"
              v-if="auth.is_admin && row.username !== 'admin'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          background
          layout="total, prev, pager, next, sizes"
          :total="page.total"
          :current-page="page.page"
          :page-size="page.page_size"
          :page-sizes="[10, 20, 50, 100]"
          @update:current-page="
            (p) => {
              page.page = p
              loadUsers()
            }
          "
          @update:page-size="
            (s) => {
              page.page_size = s
              page.page = 1
              loadUsers()
            }
          "
        />
      </div>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '添加用户' : '编辑用户'"
      width="600px"
    >
      <el-form label-width="90px">
        <el-form-item label="用户名">
          <el-input v-model="userForm.username" placeholder="输入用户名" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" type="email" placeholder="输入邮箱地址" />
        </el-form-item>
        <el-form-item label="密码" v-if="dialogMode === 'create'">
          <el-input v-model="userForm.password" type="password" placeholder="设置初始密码" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.role" style="width: 100%">
            <el-option v-for="o in roleOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="userForm.department" placeholder="选择部门" style="width: 100%">
            <el-option v-for="d in departmentOptions" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="userForm.phone" placeholder="输入手机号" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="userForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitUser">保存</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码对话框 -->
    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="500px">
      <el-form label-width="90px">
        <el-form-item label="用户">
          <el-input :model-value="passwordForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.newPassword" type="password" placeholder="输入新密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitChangePassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.user-management {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.filters {
  margin-bottom: 12px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
