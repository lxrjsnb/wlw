<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { listDevices, listSensorTypes } from '../../api/devices'
import {
  createAlarmRule,
  deleteAlarmRule,
  getAlarmStats,
  listAlarmNotifications,
  listAlarmRecords,
  listAlarmRules,
  updateAlarmRecord,
  resolveAlarmRecord,
  updateAlarmRule,
} from '../../api/alarms'
import { formatDateTime, toIsoString } from '../../utils/date'

const auth = useAuthStore()

const activeTab = ref('records')
const loadingStats = ref(false)
const alarmStats = ref(null)

const devices = ref([])
const sensorTypes = ref([])
const deviceOptions = computed(() =>
  devices.value.map((d) => ({ label: `${d.name} (${d.device_id})`, value: d.device_id, id: d.id }))
)
const deviceIdToPk = computed(() => {
  const m = new Map()
  for (const d of devices.value) m.set(d.device_id, d.id)
  return m
})

const sensorTypeOptions = computed(() =>
  sensorTypes.value.map((s) => ({ label: `${s.name} (${s.code})`, value: s.code, id: s.id }))
)
const sensorCodeToPk = computed(() => {
  const m = new Map()
  for (const s of sensorTypes.value) m.set(s.code, s.id)
  return m
})

async function loadBaseOptions() {
  try {
    const [d, s] = await Promise.all([listDevices({ page: 1, page_size: 300 }), listSensorTypes({ page: 1, page_size: 300 })])
    devices.value = d?.items || []
    sensorTypes.value = s?.items || []
  } catch {
    // ignore
  }
}

async function loadStats() {
  loadingStats.value = true
  try {
    alarmStats.value = await getAlarmStats()
  } catch (e) {
    ElMessage.error(e?.message || '加载告警统计失败')
  } finally {
    loadingStats.value = false
  }
}

// Records
const recordsLoading = ref(false)
const records = ref([])
const recordsPage = reactive({ page: 1, page_size: 20, total: 0 })
const recordFilters = reactive({
  device_id: '',
  status: '',
  priority: '',
  sensor_type: '',
  timeRange: [],
})

async function loadRecords() {
  recordsLoading.value = true
  try {
    const params = {
      page: recordsPage.page,
      page_size: recordsPage.page_size,
      device_id: recordFilters.device_id || undefined,
      status: recordFilters.status || undefined,
      priority: recordFilters.priority || undefined,
      sensor_type: recordFilters.sensor_type || undefined,
    }
    if (recordFilters.timeRange?.length === 2) {
      params.start_time = toIsoString(recordFilters.timeRange[0])
      params.end_time = toIsoString(recordFilters.timeRange[1])
    }
    const res = await listAlarmRecords(params)
    records.value = res?.items || []
    recordsPage.total = res?.total || 0
  } catch (e) {
    ElMessage.error(e?.message || '加载告警记录失败')
  } finally {
    recordsLoading.value = false
  }
}

async function handleRecordAction(row, status) {
  if (!auth.canManageAlarms) return
  try {
    const needNote = status !== 'acknowledged'
    let note = ''
    if (needNote) {
      note = await ElMessageBox.prompt('请输入处理说明（可空）', '处理告警', {
        confirmButtonText: '提交',
        cancelButtonText: '取消',
        inputType: 'textarea',
        inputPlaceholder: '例如：已检查现场，设备恢复正常',
        inputValue: '',
      }).then((r) => r.value)
    }
    if (status === 'acknowledged') {
      await updateAlarmRecord(row.id, { status })
    } else {
      await resolveAlarmRecord(row.id, { status, resolution_note: note })
    }
    ElMessage.success('处理成功')
    await Promise.all([loadRecords(), loadStats()])
  } catch {
    // canceled or failed
  }
}

function priorityTagType(p) {
  if (p === 'critical') return 'danger'
  if (p === 'high') return 'warning'
  if (p === 'medium') return ''
  return 'info'
}

// Rules
const rulesLoading = ref(false)
const rules = ref([])
const rulesPage = reactive({ page: 1, page_size: 20, total: 0 })
const ruleFilters = reactive({ device_id: '', priority: '', enabled: '' })

async function loadRules() {
  rulesLoading.value = true
  try {
    const res = await listAlarmRules({
      page: rulesPage.page,
      page_size: rulesPage.page_size,
      device_id: ruleFilters.device_id || undefined,
      priority: ruleFilters.priority || undefined,
      enabled: ruleFilters.enabled || undefined,
    })
    rules.value = res?.items || []
    rulesPage.total = res?.total || 0
  } catch (e) {
    ElMessage.error(e?.message || '加载告警规则失败')
  } finally {
    rulesLoading.value = false
  }
}

const ruleDialogVisible = ref(false)
const ruleDialogMode = ref('create') // create | edit
const ruleSaving = ref(false)
const editingRuleId = ref(null)
const ruleForm = reactive({
  name: '',
  description: '',
  device_id: '',
  sensor_code: '',
  rule_type: 'threshold',
  condition: 'greater_than',
  threshold_min: null,
  threshold_max: null,
  priority: 'medium',
  enabled: true,
  notification_enabled: true,
  delay_minutes: 0,
  recovery_enabled: true,
})

function openCreateRule() {
  ruleDialogMode.value = 'create'
  editingRuleId.value = null
  Object.assign(ruleForm, {
    name: '',
    description: '',
    device_id: devices.value[0]?.device_id || '',
    sensor_code: '',
    rule_type: 'threshold',
    condition: 'greater_than',
    threshold_min: null,
    threshold_max: null,
    priority: 'medium',
    enabled: true,
    notification_enabled: true,
    delay_minutes: 0,
    recovery_enabled: true,
  })
  ruleDialogVisible.value = true
}

function openEditRule(row) {
  ruleDialogMode.value = 'edit'
  editingRuleId.value = row.id
  Object.assign(ruleForm, {
    name: row.name,
    description: row.description || '',
    device_id: row.device ? devices.value.find((d) => d.id === row.device)?.device_id || '' : '',
    sensor_code: row.sensor_type ? sensorTypes.value.find((s) => s.id === row.sensor_type)?.code || '' : '',
    rule_type: row.rule_type,
    condition: row.condition,
    threshold_min: row.threshold_min,
    threshold_max: row.threshold_max,
    priority: row.priority,
    enabled: row.enabled,
    notification_enabled: row.notification_enabled,
    delay_minutes: row.delay_minutes,
    recovery_enabled: row.recovery_enabled,
  })
  ruleDialogVisible.value = true
}

async function submitRule() {
  if (!ruleForm.name || !ruleForm.device_id) {
    ElMessage.warning('请填写规则名称并选择设备')
    return
  }
  ruleSaving.value = true
  try {
    let threshold_min = ruleForm.threshold_min
    let threshold_max = ruleForm.threshold_max
    if (ruleForm.condition === 'less_than' && threshold_min != null && threshold_max == null) {
      threshold_max = threshold_min
    }
    const payload = {
      name: ruleForm.name,
      description: ruleForm.description || '',
      device: deviceIdToPk.value.get(ruleForm.device_id),
      sensor_type: ruleForm.sensor_code ? sensorCodeToPk.value.get(ruleForm.sensor_code) : null,
      rule_type: ruleForm.rule_type,
      condition: ruleForm.condition,
      threshold_min,
      threshold_max,
      priority: ruleForm.priority,
      enabled: ruleForm.enabled,
      notification_enabled: ruleForm.notification_enabled,
      delay_minutes: ruleForm.delay_minutes,
      recovery_enabled: ruleForm.recovery_enabled,
    }
    if (!payload.device) throw new Error('设备不存在或未加载')

    if (ruleDialogMode.value === 'create') {
      await createAlarmRule(payload)
      ElMessage.success('规则创建成功')
    } else {
      await updateAlarmRule(editingRuleId.value, payload)
      ElMessage.success('规则更新成功')
    }
    ruleDialogVisible.value = false
    await loadRules()
  } catch (e) {
    ElMessage.error(e?.payload?.message || e?.message || '保存失败')
  } finally {
    ruleSaving.value = false
  }
}

async function confirmDeleteRule(row) {
  try {
    await ElMessageBox.confirm(`确认删除规则「${row.name}」？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteAlarmRule(row.id)
    ElMessage.success('已删除')
    await loadRules()
  } catch {
    // canceled
  }
}

// Notifications
const notifLoading = ref(false)
const notifications = ref([])
const notifPage = reactive({ page: 1, page_size: 20, total: 0 })
const notifFilters = reactive({ status: '', notification_type: '' })

async function loadNotifications() {
  notifLoading.value = true
  try {
    const res = await listAlarmNotifications({
      page: notifPage.page,
      page_size: notifPage.page_size,
      status: notifFilters.status || undefined,
      notification_type: notifFilters.notification_type || undefined,
    })
    notifications.value = res?.items || []
    notifPage.total = res?.total || 0
  } catch (e) {
    ElMessage.error(e?.message || '加载通知失败')
  } finally {
    notifLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadBaseOptions(), loadStats()])
  await Promise.all([loadRecords(), loadRules(), loadNotifications()])
})
</script>

<template>
  <div class="alarm-page">
    <el-row :gutter="12" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" v-loading="loadingStats">
          <div class="stat">
            <div class="stat-title">总告警</div>
            <div class="stat-value">{{ alarmStats?.total ?? '-' }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" v-loading="loadingStats">
          <div class="stat">
            <div class="stat-title">待处理</div>
            <div class="stat-value danger">{{ alarmStats?.by_status?.pending ?? '-' }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" v-loading="loadingStats">
          <div class="stat">
            <div class="stat-title">24小时新增</div>
            <div class="stat-value">{{ alarmStats?.recent_24h ?? '-' }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" v-loading="loadingStats">
          <div class="stat">
            <div class="stat-title">严重待处理</div>
            <div class="stat-value danger">{{ alarmStats?.by_priority?.critical ?? '-' }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="header">
          <div class="title">告警中心</div>
          <div class="header-actions">
            <el-button size="small" @click="loadStats">刷新统计</el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="告警记录" name="records">
          <el-form :inline="true" class="filters" @submit.prevent>
            <el-form-item label="设备">
              <el-select v-model="recordFilters.device_id" clearable filterable placeholder="全部" style="width: 240px">
                <el-option v-for="o in deviceOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="recordFilters.status" clearable placeholder="全部" style="width: 140px">
                <el-option label="待处理" value="pending" />
                <el-option label="已确认" value="acknowledged" />
                <el-option label="已解决" value="resolved" />
                <el-option label="误报" value="false_positive" />
              </el-select>
            </el-form-item>
            <el-form-item label="优先级">
              <el-select v-model="recordFilters.priority" clearable placeholder="全部" style="width: 140px">
                <el-option label="严重" value="critical" />
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
            </el-form-item>
            <el-form-item label="传感器">
              <el-select v-model="recordFilters.sensor_type" clearable filterable placeholder="全部" style="width: 220px">
                <el-option v-for="o in sensorTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="时间">
              <el-date-picker
                v-model="recordFilters.timeRange"
                type="datetimerange"
                range-separator="到"
                start-placeholder="开始"
                end-placeholder="结束"
                style="width: 320px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="recordsPage.page = 1; loadRecords()">查询</el-button>
            </el-form-item>
          </el-form>

          <el-table v-loading="recordsLoading" :data="records" style="width: 100%">
            <el-table-column prop="triggered_at" label="时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.triggered_at) }}</template>
            </el-table-column>
            <el-table-column prop="device_name" label="设备" min-width="140" />
            <el-table-column prop="alarm_rule_name" label="规则" min-width="140" show-overflow-tooltip />
            <el-table-column prop="sensor_type_name" label="传感器" min-width="120" />
            <el-table-column label="当前/阈值" min-width="140">
              <template #default="{ row }">{{ row.current_value }} / {{ row.threshold_value }} {{ row.unit }}</template>
            </el-table-column>
            <el-table-column label="优先级" width="110">
              <template #default="{ row }">
                <el-tag size="small" :type="priorityTagType(row.priority)">{{ row.priority }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="130">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'pending' ? 'danger' : row.status === 'acknowledged' ? 'warning' : 'success'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  :disabled="!auth.canManageAlarms || row.status !== 'pending'"
                  @click="handleRecordAction(row, 'acknowledged')"
                >
                  确认
                </el-button>
                <el-button
                  size="small"
                  type="primary"
                  :disabled="!auth.canManageAlarms || (row.status !== 'pending' && row.status !== 'acknowledged')"
                  @click="handleRecordAction(row, 'resolved')"
                >
                  解决
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  :disabled="!auth.canManageAlarms || (row.status !== 'pending' && row.status !== 'acknowledged')"
                  @click="handleRecordAction(row, 'false_positive')"
                >
                  误报
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pager">
            <el-pagination
              background
              layout="total, prev, pager, next, sizes"
              :total="recordsPage.total"
              :current-page="recordsPage.page"
              :page-size="recordsPage.page_size"
              :page-sizes="[10, 20, 50, 100]"
              @update:current-page="
                (p) => {
                  recordsPage.page = p
                  loadRecords()
                }
              "
              @update:page-size="
                (s) => {
                  recordsPage.page_size = s
                  recordsPage.page = 1
                  loadRecords()
                }
              "
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="告警规则" name="rules">
          <div class="rules-toolbar">
            <el-form :inline="true" class="filters" @submit.prevent>
              <el-form-item label="设备">
                <el-select v-model="ruleFilters.device_id" clearable filterable placeholder="全部" style="width: 240px">
                  <el-option v-for="o in deviceOptions" :key="o.value" :label="o.label" :value="o.value" />
                </el-select>
              </el-form-item>
              <el-form-item label="优先级">
                <el-select v-model="ruleFilters.priority" clearable placeholder="全部" style="width: 140px">
                  <el-option label="严重" value="critical" />
                  <el-option label="高" value="high" />
                  <el-option label="中" value="medium" />
                  <el-option label="低" value="low" />
                </el-select>
              </el-form-item>
              <el-form-item label="启用">
                <el-select v-model="ruleFilters.enabled" clearable placeholder="全部" style="width: 140px">
                  <el-option label="启用" value="true" />
                  <el-option label="停用" value="false" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="rulesPage.page = 1; loadRules()">查询</el-button>
                <el-button type="primary" plain :disabled="!auth.canManageAlarms" @click="openCreateRule">新建规则</el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-table v-loading="rulesLoading" :data="rules" style="width: 100%">
            <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="device_name" label="设备" min-width="140" />
            <el-table-column prop="sensor_type_name" label="传感器" min-width="140" />
            <el-table-column prop="condition" label="条件" width="120" />
            <el-table-column label="阈值" min-width="140">
              <template #default="{ row }">
                <span v-if="row.threshold_min !== null && row.threshold_min !== undefined">{{ row.threshold_min }}</span>
                <span v-if="row.threshold_min !== null && row.threshold_min !== undefined && (row.threshold_max !== null && row.threshold_max !== undefined)"> ~ </span>
                <span v-if="row.threshold_max !== null && row.threshold_max !== undefined">{{ row.threshold_max }}</span>
                <span v-if="row.sensor_type_unit"> {{ row.sensor_type_unit }}</span>
              </template>
            </el-table-column>
            <el-table-column label="优先级" width="110">
              <template #default="{ row }"><el-tag size="small" :type="priorityTagType(row.priority)">{{ row.priority }}</el-tag></template>
            </el-table-column>
            <el-table-column label="启用" width="90">
              <template #default="{ row }"><el-switch :model-value="row.enabled" disabled /></template>
            </el-table-column>
            <el-table-column label="操作" width="190" fixed="right">
              <template #default="{ row }">
                <el-button size="small" :disabled="!auth.canManageAlarms" @click="openEditRule(row)">编辑</el-button>
                <el-button size="small" type="danger" :disabled="!auth.canManageAlarms" @click="confirmDeleteRule(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pager">
            <el-pagination
              background
              layout="total, prev, pager, next, sizes"
              :total="rulesPage.total"
              :current-page="rulesPage.page"
              :page-size="rulesPage.page_size"
              :page-sizes="[10, 20, 50, 100]"
              @update:current-page="
                (p) => {
                  rulesPage.page = p
                  loadRules()
                }
              "
              @update:page-size="
                (s) => {
                  rulesPage.page_size = s
                  rulesPage.page = 1
                  loadRules()
                }
              "
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="通知记录" name="notifications">
          <el-form :inline="true" class="filters" @submit.prevent>
            <el-form-item label="状态">
              <el-select v-model="notifFilters.status" clearable placeholder="全部" style="width: 160px">
                <el-option label="待发送" value="pending" />
                <el-option label="已发送" value="sent" />
                <el-option label="失败" value="failed" />
              </el-select>
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="notifFilters.notification_type" clearable placeholder="全部" style="width: 160px">
                <el-option label="WebSocket" value="websocket" />
                <el-option label="邮件" value="email" />
                <el-option label="短信" value="sms" />
                <el-option label="微信" value="wechat" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="notifPage.page = 1; loadNotifications()">查询</el-button>
            </el-form-item>
          </el-form>

          <el-table v-loading="notifLoading" :data="notifications" style="width: 100%">
            <el-table-column prop="alarm_device_name" label="设备" min-width="140" />
            <el-table-column prop="notification_type" label="类型" width="120" />
            <el-table-column prop="recipient" label="接收人" min-width="160" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="120" />
            <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip />
            <el-table-column label="创建时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <div class="pager">
            <el-pagination
              background
              layout="total, prev, pager, next, sizes"
              :total="notifPage.total"
              :current-page="notifPage.page"
              :page-size="notifPage.page_size"
              :page-sizes="[10, 20, 50, 100]"
              @update:current-page="
                (p) => {
                  notifPage.page = p
                  loadNotifications()
                }
              "
              @update:page-size="
                (s) => {
                  notifPage.page_size = s
                  notifPage.page = 1
                  loadNotifications()
                }
              "
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>

  <el-dialog v-model="ruleDialogVisible" :title="ruleDialogMode === 'create' ? '新建告警规则' : '编辑告警规则'" width="720px">
    <el-form label-width="110px">
      <el-form-item label="规则名称">
        <el-input v-model="ruleForm.name" placeholder="如：温度过高告警" />
      </el-form-item>
      <el-form-item label="设备">
        <el-select v-model="ruleForm.device_id" filterable placeholder="请选择" style="width: 100%">
          <el-option v-for="o in deviceOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="传感器(可选)">
        <el-select v-model="ruleForm.sensor_code" filterable clearable placeholder="可不选" style="width: 100%">
          <el-option v-for="o in sensorTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="条件">
        <el-select v-model="ruleForm.condition" style="width: 220px">
          <el-option label="大于" value="greater_than" />
          <el-option label="小于" value="less_than" />
          <el-option label="等于" value="equal" />
          <el-option label="区间内" value="between" />
          <el-option label="区间外" value="outside" />
        </el-select>
      </el-form-item>
      <el-form-item label="最小阈值" v-if="['between', 'outside', 'less_than'].includes(ruleForm.condition)">
        <el-input-number v-model="ruleForm.threshold_min" :step="0.1" style="width: 220px" />
      </el-form-item>
      <el-form-item label="最大阈值" v-if="['greater_than', 'between', 'outside', 'equal', 'less_than'].includes(ruleForm.condition)">
        <el-input-number v-model="ruleForm.threshold_max" :step="0.1" style="width: 220px" />
      </el-form-item>
      <el-form-item label="优先级">
        <el-select v-model="ruleForm.priority" style="width: 220px">
          <el-option label="严重" value="critical" />
          <el-option label="高" value="high" />
          <el-option label="中" value="medium" />
          <el-option label="低" value="low" />
        </el-select>
      </el-form-item>
      <el-form-item label="启用">
        <el-switch v-model="ruleForm.enabled" />
      </el-form-item>
      <el-form-item label="发送通知">
        <el-switch v-model="ruleForm.notification_enabled" />
      </el-form-item>
      <el-form-item label="延迟(分钟)">
        <el-input-number v-model="ruleForm.delay_minutes" :min="0" :max="1440" :step="1" />
      </el-form-item>
      <el-form-item label="恢复通知">
        <el-switch v-model="ruleForm.recovery_enabled" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="ruleForm.description" type="textarea" :rows="3" placeholder="可选" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="ruleDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="ruleSaving" :disabled="!auth.canManageAlarms" @click="submitRule">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.alarm-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-row .stat {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-title {
  color: #909399;
  font-size: 12px;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
}

.danger {
  color: #f56c6c;
}

.header {
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
