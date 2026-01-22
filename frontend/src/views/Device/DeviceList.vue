<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import {
  controlDevice,
  createDevice,
  deleteDevice,
  listDeviceLogs,
  listDevices,
  listSensorTypes,
  updateDevice,
} from '../../api/devices'
import { formatDateTime } from '../../utils/date'

const auth = useAuthStore()

const loading = ref(false)
const devices = ref([])
const page = reactive({ total: 0, page: 1, page_size: 20 })
const filters = reactive({ keyword: '', status: '', sensor_type: '' })

const sensorTypes = ref([])
const sensorTypeOptions = computed(() =>
  sensorTypes.value.map((s) => ({ label: `${s.name} (${s.code})`, value: s.code, id: s.id }))
)
const sensorTypeIdByCode = computed(() => {
  const map = new Map()
  for (const s of sensorTypes.value) map.set(s.code, s.id)
  return map
})

const statusOptions = [
  { label: '在线', value: 'online' },
  { label: '离线', value: 'offline' },
  { label: '故障', value: 'error' },
  { label: '维护中', value: 'maintenance' },
]

async function loadSensorTypes() {
  try {
    const res = await listSensorTypes({ page: 1, page_size: 100 })
    sensorTypes.value = res?.items || []
  } catch {
    sensorTypes.value = []
  }
}

async function loadDevices() {
  loading.value = true
  try {
    const res = await listDevices({
      page: page.page,
      page_size: page.page_size,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      sensor_type: filters.sensor_type || undefined,
    })
    devices.value = res?.items || []
    page.total = res?.total || 0
  } catch (e) {
    ElMessage.error(e?.message || '加载设备列表失败')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.status = ''
  filters.sensor_type = ''
  page.page = 1
  loadDevices()
}

// Create/Edit dialog
const dialogVisible = ref(false)
const dialogMode = ref('create') // create | edit
const saving = ref(false)
const editingDeviceId = ref('')
const form = reactive({
  device_id: '',
  name: '',
  location: '',
  description: '',
  status: 'offline',
  ip_address: '',
  firmware_version: '',
  battery_level: null,
  sensor_type_codes: [],
})

function openCreate() {
  dialogMode.value = 'create'
  editingDeviceId.value = ''
  Object.assign(form, {
    device_id: '',
    name: '',
    location: '',
    description: '',
    status: 'offline',
    ip_address: '',
    firmware_version: '',
    battery_level: null,
    sensor_type_codes: [],
  })
  dialogVisible.value = true
}

function openEdit(row) {
  dialogMode.value = 'edit'
  editingDeviceId.value = row.device_id
  Object.assign(form, {
    device_id: row.device_id,
    name: row.name,
    location: row.location || '',
    description: row.description || '',
    status: row.status,
    ip_address: row.ip_address || '',
    firmware_version: row.firmware_version || '',
    battery_level: row.battery_level ?? null,
    sensor_type_codes: (row.sensor_types_info || []).map((s) => s.code),
  })
  dialogVisible.value = true
}

async function submit() {
  if (!form.name || (dialogMode.value === 'create' && !form.device_id)) {
    ElMessage.warning('请填写设备ID与名称')
    return
  }
  saving.value = true
  try {
    const sensor_type_ids = form.sensor_type_codes
      .map((code) => sensorTypeIdByCode.value.get(code))
      .filter(Boolean)
    const payload = {
      name: form.name,
      location: form.location || '',
      description: form.description || '',
      status: form.status,
      ip_address: form.ip_address || null,
      firmware_version: form.firmware_version || '',
      battery_level: form.battery_level,
      sensor_type_ids,
    }

    if (dialogMode.value === 'create') {
      await createDevice({ ...payload, device_id: form.device_id })
      ElMessage.success('设备创建成功')
    } else {
      await updateDevice(editingDeviceId.value, payload)
      ElMessage.success('设备更新成功')
    }
    dialogVisible.value = false
    await loadDevices()
  } catch (e) {
    ElMessage.error(e?.payload?.message || e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除设备「${row.name}」(${row.device_id})？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteDevice(row.device_id)
    ElMessage.success('已删除')
    await loadDevices()
  } catch {
    // cancelled
  }
}

// Logs drawer
const logsVisible = ref(false)
const logsLoading = ref(false)
const logs = ref([])
const logsPage = reactive({ page: 1, page_size: 10, total: 0 })
const logFilters = reactive({ log_type: '' })
const currentLogDevice = ref(null)

async function openLogs(row) {
  currentLogDevice.value = row
  logsPage.page = 1
  logFilters.log_type = ''
  logsVisible.value = true
  await loadLogs()
}

async function loadLogs() {
  if (!currentLogDevice.value) return
  logsLoading.value = true
  try {
    const res = await listDeviceLogs(currentLogDevice.value.device_id, {
      page: logsPage.page,
      page_size: logsPage.page_size,
      log_type: logFilters.log_type || undefined,
    })
    logs.value = res?.items || []
    logsPage.total = res?.total || 0
  } catch (e) {
    ElMessage.error(e?.message || '加载日志失败')
  } finally {
    logsLoading.value = false
  }
}

// Control dialog
const controlVisible = ref(false)
const controlling = ref(false)
const controlTarget = ref(null)
const controlForm = reactive({ command: 'restart', parametersText: '' })
const commandOptions = ['start', 'stop', 'restart', 'configure', 'calibrate']

function openControl(row) {
  controlTarget.value = row
  controlForm.command = 'restart'
  controlForm.parametersText = ''
  controlVisible.value = true
}

async function submitControl() {
  if (!controlTarget.value) return
  controlling.value = true
  try {
    let parameters = undefined
    if (controlForm.parametersText?.trim()) {
      parameters = JSON.parse(controlForm.parametersText)
    }
    await controlDevice(controlTarget.value.device_id, {
      command: controlForm.command,
      parameters,
    })
    ElMessage.success('控制命令已发送')
    controlVisible.value = false
  } catch (e) {
    const msg = e?.payload?.message || e?.message || '发送失败'
    ElMessage.error(msg)
  } finally {
    controlling.value = false
  }
}

function statusTagType(status) {
  if (status === 'online') return 'success'
  if (status === 'offline') return 'info'
  if (status === 'maintenance') return 'warning'
  if (status === 'error') return 'danger'
  return ''
}

onMounted(async () => {
  await loadSensorTypes()
  await loadDevices()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <div class="title">设备管理</div>
        <div class="actions">
          <el-button type="primary" :disabled="auth.role === 'viewer'" @click="openCreate">添加设备</el-button>
        </div>
      </div>
    </template>

    <el-form :inline="true" class="filters" @submit.prevent>
      <el-form-item label="关键词">
        <el-input v-model="filters.keyword" placeholder="设备ID/名称/位置" clearable @change="loadDevices" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.status" placeholder="全部" clearable style="width: 140px" @change="loadDevices">
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="传感器">
        <el-select
          v-model="filters.sensor_type"
          placeholder="全部"
          clearable
          filterable
          style="width: 220px"
          @change="loadDevices"
        >
          <el-option v-for="o in sensorTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadDevices">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="devices" style="width: 100%">
      <el-table-column prop="device_id" label="设备ID" min-width="140" />
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="location" label="位置" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="owner_name" label="所有者" min-width="110" />
      <el-table-column prop="ip_address" label="IP" min-width="120" />
      <el-table-column label="电量" width="90">
        <template #default="{ row }">{{ row.battery_level ?? '-' }}%</template>
      </el-table-column>
      <el-table-column label="最后心跳" min-width="170">
        <template #default="{ row }">{{ formatDateTime(row.last_heartbeat) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openLogs(row)">日志</el-button>
          <el-button
            size="small"
            type="primary"
            :disabled="!auth.canControlDevice || !row.is_online"
            @click="openControl(row)"
          >
            控制
          </el-button>
          <el-button size="small" :disabled="auth.role === 'viewer'" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" :disabled="auth.role === 'viewer'" @click="confirmDelete(row)">
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
            loadDevices()
          }
        "
        @update:page-size="
          (s) => {
            page.page_size = s
            page.page = 1
            loadDevices()
          }
        "
      />
    </div>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '添加设备' : '编辑设备'" width="680px">
    <el-form label-width="100px">
      <el-form-item label="设备ID" v-if="dialogMode === 'create'">
        <el-input v-model="form.device_id" placeholder="如: device-001" />
      </el-form-item>
      <el-form-item label="名称">
        <el-input v-model="form.name" placeholder="设备名称" />
      </el-form-item>
      <el-form-item label="位置">
        <el-input v-model="form.location" placeholder="安装位置" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="form.status" style="width: 180px">
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="IP地址">
        <el-input v-model="form.ip_address" placeholder="可选" />
      </el-form-item>
      <el-form-item label="固件版本">
        <el-input v-model="form.firmware_version" placeholder="可选" />
      </el-form-item>
      <el-form-item label="电量">
        <el-input-number v-model="form.battery_level" :min="0" :max="100" :step="1" />
      </el-form-item>
      <el-form-item label="传感器类型">
        <el-select v-model="form.sensor_type_codes" multiple filterable clearable style="width: 100%">
          <el-option v-for="o in sensorTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="可选" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
    </template>
  </el-dialog>

  <el-drawer v-model="logsVisible" :title="currentLogDevice ? `设备日志 - ${currentLogDevice.name}` : '设备日志'" size="55%">
    <div style="padding: 0 12px 12px 12px">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="类型">
          <el-select v-model="logFilters.log_type" placeholder="全部" clearable style="width: 160px" @change="loadLogs">
            <el-option label="状态变更" value="status" />
            <el-option label="控制操作" value="control" />
            <el-option label="错误" value="error" />
            <el-option label="信息" value="info" />
          </el-select>
        </el-form-item>
      </el-form>

      <el-table v-loading="logsLoading" :data="logs" size="small" style="width: 100%">
        <el-table-column prop="log_type" label="类型" width="100" />
        <el-table-column prop="message" label="内容" min-width="220" show-overflow-tooltip />
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="logsPage.total"
          :current-page="logsPage.page"
          :page-size="logsPage.page_size"
          @update:current-page="
            (p) => {
              logsPage.page = p
              loadLogs()
            }
          "
        />
      </div>
    </div>
  </el-drawer>

  <el-dialog v-model="controlVisible" title="远程控制" width="560px">
    <el-alert
      v-if="controlTarget && !controlTarget.is_online"
      type="warning"
      title="设备离线，无法控制"
      :closable="false"
      style="margin-bottom: 12px"
    />
    <el-form label-width="90px">
      <el-form-item label="设备">
        <el-input :model-value="controlTarget ? `${controlTarget.name} (${controlTarget.device_id})` : ''" disabled />
      </el-form-item>
      <el-form-item label="命令">
        <el-select v-model="controlForm.command" style="width: 200px">
          <el-option v-for="c in commandOptions" :key="c" :label="c" :value="c" />
        </el-select>
      </el-form-item>
      <el-form-item label="参数(JSON)">
        <el-input
          v-model="controlForm.parametersText"
          type="textarea"
          :rows="4"
          placeholder='可选，例如: {"mode":"eco"}'
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="controlVisible = false">取消</el-button>
      <el-button
        type="primary"
        :loading="controlling"
        :disabled="!controlTarget?.is_online || !auth.canControlDevice"
        @click="submitControl"
      >
        发送
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-weight: 600;
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
