<template>
  <div class="device-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="设备总数" :value="stats.total">
            <template #suffix>台</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="在线设备" :value="stats.online">
            <template #suffix>台</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="离线设备" :value="stats.offline">
            <template #suffix>台</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="在线率" :value="stats.online_rate">
            <template #suffix>%</template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设备列表 -->
    <el-card class="device-card">
      <template #header>
        <div class="card-header">
          <span>设备列表</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加设备
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="设备ID">
          <el-input
            v-model="queryParams.keyword"
            placeholder="请输入设备ID或名称"
            clearable
            @clear="handleQuery"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="queryParams.status"
            placeholder="全部"
            clearable
            @change="handleQuery"
          >
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="故障" value="error" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">搜索</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="deviceList" stripe>
        <el-table-column prop="device_id" label="设备ID" width="150" />
        <el-table-column prop="name" label="设备名称" width="200" />
        <el-table-column prop="location" label="安装位置" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner_name" label="所有者" width="120" />
        <el-table-column prop="last_heartbeat" label="最后心跳" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_heartbeat) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="handleQuery"
        @current-change="handleQuery"
      />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="deviceFormRef"
        :model="deviceForm"
        :rules="deviceRules"
        label-width="120px"
      >
        <el-form-item label="设备ID" prop="device_id">
          <el-input
            v-model="deviceForm.device_id"
            placeholder="请输入设备ID"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="deviceForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="安装位置" prop="location">
          <el-input v-model="deviceForm.location" placeholder="请输入安装位置" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="deviceForm.description"
            type="textarea"
            placeholder="请输入描述"
          />
        </el-form-item>
        <el-form-item label="IP地址">
          <el-input v-model="deviceForm.ip_address" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="固件版本">
          <el-input v-model="deviceForm.firmware_version" placeholder="请输入固件版本" />
        </el-form-item>
        <el-form-item label="传感器类型">
          <el-select
            v-model="deviceForm.sensor_type_ids"
            multiple
            placeholder="请选择传感器类型"
            style="width: 100%"
          >
            <el-option
              v-for="item in sensorTypes"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getDeviceList, deleteDevice, getDeviceStats, getSensorTypes, createDevice, updateDevice } from '@/api/device'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const deviceList = ref([])
const sensorTypes = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const dialogTitle = ref('添加设备')
const isEdit = ref(false)
const deviceFormRef = ref(null)

const stats = reactive({
  total: 0,
  online: 0,
  offline: 0,
  online_rate: 0
})

const queryParams = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  status: ''
})

const deviceForm = reactive({
  device_id: '',
  name: '',
  location: '',
  description: '',
  ip_address: '',
  firmware_version: '',
  sensor_type_ids: []
})

const deviceRules = {
  device_id: [{ required: true, message: '请输入设备ID', trigger: 'blur' }],
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }]
}

// 获取设备列表
async function fetchDeviceList() {
  loading.value = true
  try {
    const res = await getDeviceList(queryParams)
    deviceList.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

// 获取设备统计
async function fetchDeviceStats() {
  try {
    const res = await getDeviceStats()
    Object.assign(stats, res)
  } catch (error) {
    console.error('获取设备统计失败:', error)
  }
}

// 获取传感器类型
async function fetchSensorTypes() {
  try {
    const res = await getSensorTypes()
    sensorTypes.value = res.items || []
  } catch (error) {
    console.error('获取传感器类型失败:', error)
  }
}

// 查询
function handleQuery() {
  queryParams.page = 1
  fetchDeviceList()
}

// 重置
function resetQuery() {
  Object.assign(queryParams, {
    page: 1,
    page_size: 20,
    keyword: '',
    status: ''
  })
  fetchDeviceList()
}

// 添加设备
function showAddDialog() {
  dialogTitle.value = '添加设备'
  isEdit.value = false
  dialogVisible.value = true
}

// 编辑设备
function handleEdit(row) {
  dialogTitle.value = '编辑设备'
  isEdit.value = true
  Object.assign(deviceForm, {
    device_id: row.device_id,
    name: row.name,
    location: row.location,
    description: row.description,
    ip_address: row.ip_address,
    firmware_version: row.firmware_version,
    sensor_type_ids: row.sensor_types_info?.map(s => s.id) || []
  })
  dialogVisible.value = true
}

// 查看设备详情
function handleView(row) {
  router.push(`/devices/${row.device_id}`)
}

// 删除设备
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除设备 ${row.name} 吗？`, '提示', {
      type: 'warning'
    })
    await deleteDevice(row.device_id)
    ElMessage.success('删除成功')
    fetchDeviceList()
    fetchDeviceStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
async function handleSubmit() {
  if (!deviceFormRef.value) return

  await deviceFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (isEdit.value) {
          await updateDevice(deviceForm.device_id, deviceForm)
          ElMessage.success('更新成功')
        } else {
          await createDevice(deviceForm)
          ElMessage.success('添加成功')
        }
        dialogVisible.value = false
        fetchDeviceList()
        fetchDeviceStats()
      } catch (error) {
        ElMessage.error(isEdit.value ? '更新失败' : '添加失败')
      }
    }
  })
}

// 重置表单
function resetForm() {
  deviceFormRef.value?.resetFields()
  Object.assign(deviceForm, {
    device_id: '',
    name: '',
    location: '',
    description: '',
    ip_address: '',
    firmware_version: '',
    sensor_type_ids: []
  })
}

// 获取状态类型
function getStatusType(status) {
  const map = {
    online: 'success',
    offline: 'info',
    error: 'danger',
    maintenance: 'warning'
  }
  return map[status] || 'info'
}

// 获取状态文本
function getStatusText(status) {
  const map = {
    online: '在线',
    offline: '离线',
    error: '故障',
    maintenance: '维护中'
  }
  return map[status] || status
}

// 格式化时间
function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchDeviceList()
  fetchDeviceStats()
  fetchSensorTypes()
})
</script>

<style scoped>
.device-page {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.device-card {
  min-height: calc(100% - 200px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
