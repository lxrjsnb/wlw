<template>
  <div class="alarm-rules-page">
    <el-card class="rules-card">
      <template #header>
        <div class="card-header">
          <span>告警规则</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加规则
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="设备">
          <el-input
            v-model="queryParams.device_id"
            placeholder="请输入设备ID"
            clearable
          />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-select
            v-model="queryParams.enabled"
            placeholder="全部"
            clearable
            @change="handleQuery"
          >
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">搜索</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="rulesList" stripe>
        <el-table-column prop="name" label="规则名称" width="200" />
        <el-table-column prop="device_name" label="设备" width="150" />
        <el-table-column prop="sensor_type_name" label="传感器" width="120" />
        <el-table-column label="条件" width="150">
          <template #default="{ row }">
            {{ getConditionText(row.condition) }}
            {{ row.threshold_max !== null ? row.threshold_max : row.threshold_min }}
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">
              {{ row.priority_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="启用" width="80">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="delay_minutes" label="延迟(分钟)" width="120" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="ruleFormRef"
        :model="ruleForm"
        :rules="ruleRules"
        label-width="120px"
      >
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="ruleForm.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="设备" prop="device">
          <el-select
            v-model="ruleForm.device"
            placeholder="请选择设备"
            style="width: 100%"
          >
            <el-option
              v-for="device in deviceList"
              :key="device.device_id"
              :label="`${device.name} (${device.device_id})`"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="传感器类型" prop="sensor_type">
          <el-select
            v-model="ruleForm.sensor_type"
            placeholder="请选择传感器类型"
            style="width: 100%"
          >
            <el-option
              v-for="sensor in sensorTypes"
              :key="sensor.id"
              :label="`${sensor.name} (${sensor.unit})`"
              :value="sensor.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="条件" prop="condition">
          <el-select v-model="ruleForm.condition" placeholder="请选择条件">
            <el-option label="大于" value="greater_than" />
            <el-option label="小于" value="less_than" />
            <el-option label="区间内" value="between" />
            <el-option label="区间外" value="outside" />
          </el-select>
        </el-form-item>
        <el-form-item
          v-if="ruleForm.condition === 'greater_than'"
          label="阈值"
          prop="threshold_max"
        >
          <el-input-number
            v-model="ruleForm.threshold_max"
            :precision="2"
            :step="0.1"
          />
        </el-form-item>
        <el-form-item
          v-if="ruleForm.condition === 'less_than'"
          label="阈值"
          prop="threshold_min"
        >
          <el-input-number
            v-model="ruleForm.threshold_min"
            :precision="2"
            :step="0.1"
          />
        </el-form-item>
        <el-form-item
          v-if="ruleForm.condition === 'between' || ruleForm.condition === 'outside'"
          label="最小值"
          prop="threshold_min"
        >
          <el-input-number
            v-model="ruleForm.threshold_min"
            :precision="2"
            :step="0.1"
          />
        </el-form-item>
        <el-form-item
          v-if="ruleForm.condition === 'between' || ruleForm.condition === 'outside'"
          label="最大值"
          prop="threshold_max"
        >
          <el-input-number
            v-model="ruleForm.threshold_max"
            :precision="2"
            :step="0.1"
          />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="ruleForm.priority" placeholder="请选择优先级">
            <el-option label="严重" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="延迟告警(分钟)" prop="delay_minutes">
          <el-input-number v-model="ruleForm.delay_minutes" :min="0" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="ruleForm.enabled" />
        </el-form-item>
        <el-form-item label="发送通知">
          <el-switch v-model="ruleForm.notification_enabled" />
        </el-form-item>
        <el-form-item label="告警恢复通知">
          <el-switch v-model="ruleForm.recovery_enabled" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="ruleForm.description"
            type="textarea"
            placeholder="请输入描述"
          />
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
import { getAlarmRules, createAlarmRule, updateAlarmRule, deleteAlarmRule } from '@/api/alarm'
import { getDeviceList, getSensorTypes } from '@/api/device'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const rulesList = ref([])
const deviceList = ref([])
const sensorTypes = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('添加规则')
const ruleFormRef = ref(null)

const queryParams = reactive({
  device_id: '',
  enabled: ''
})

const ruleForm = reactive({
  name: '',
  device: null,
  sensor_type: null,
  condition: 'greater_than',
  threshold_min: null,
  threshold_max: null,
  priority: 'medium',
  delay_minutes: 0,
  enabled: true,
  notification_enabled: true,
  recovery_enabled: true,
  description: ''
})

const ruleRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  device: [{ required: true, message: '请选择设备', trigger: 'change' }],
  sensor_type: [{ required: true, message: '请选择传感器类型', trigger: 'change' }],
  condition: [{ required: true, message: '请选择条件', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }]
}

// 获取告警规则列表
async function fetchRulesList() {
  loading.value = true
  try {
    const res = await getAlarmRules(queryParams)
    rulesList.value = res.items || []
  } catch (error) {
    ElMessage.error('获取告警规则列表失败')
  } finally {
    loading.value = false
  }
}

// 获取设备列表
async function fetchDeviceList() {
  try {
    const res = await getDeviceList({ page_size: 100 })
    deviceList.value = res.items || []
  } catch (error) {
    console.error('获取设备列表失败:', error)
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
  fetchRulesList()
}

// 重置
function resetQuery() {
  Object.assign(queryParams, {
    device_id: '',
    enabled: ''
  })
  fetchRulesList()
}

// 添加规则
function showAddDialog() {
  dialogTitle.value = '添加规则'
  dialogVisible.value = true
}

// 编辑规则
function handleEdit(row) {
  dialogTitle.value = '编辑规则'
  Object.assign(ruleForm, {
    name: row.name,
    device: row.device,
    sensor_type: row.sensor_type,
    condition: row.condition,
    threshold_min: row.threshold_min,
    threshold_max: row.threshold_max,
    priority: row.priority,
    delay_minutes: row.delay_minutes,
    enabled: row.enabled,
    notification_enabled: row.notification_enabled,
    recovery_enabled: row.recovery_enabled,
    description: row.description
  })
  dialogVisible.value = true
}

// 删除规则
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除规则 ${row.name} 吗？`, '提示', {
      type: 'warning'
    })
    await deleteAlarmRule(row.id)
    ElMessage.success('删除成功')
    fetchRulesList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
async function handleSubmit() {
  if (!ruleFormRef.value) return

  await ruleFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (dialogTitle.value === '添加规则') {
          await createAlarmRule(ruleForm)
          ElMessage.success('添加成功')
        } else {
          await updateAlarmRule(ruleForm.device, ruleForm)
          ElMessage.success('更新成功')
        }
        dialogVisible.value = false
        fetchRulesList()
      } catch (error) {
        ElMessage.error(dialogTitle.value === '添加规则' ? '添加失败' : '更新失败')
      }
    }
  })
}

// 重置表单
function resetForm() {
  ruleFormRef.value?.resetFields()
  Object.assign(ruleForm, {
    name: '',
    device: null,
    sensor_type: null,
    condition: 'greater_than',
    threshold_min: null,
    threshold_max: null,
    priority: 'medium',
    delay_minutes: 0,
    enabled: true,
    notification_enabled: true,
    recovery_enabled: true,
    description: ''
  })
}

// 获取条件文本
function getConditionText(condition) {
  const map = {
    greater_than: '>',
    less_than: '<',
    between: '介于',
    outside: '不在区间'
  }
  return map[condition] || condition
}

// 获取优先级类型
function getPriorityType(priority) {
  const map = {
    critical: 'danger',
    high: 'warning',
    medium: 'primary',
    low: 'info'
  }
  return map[priority] || 'info'
}

onMounted(() => {
  fetchRulesList()
  fetchDeviceList()
  fetchSensorTypes()
})
</script>

<style scoped>
.alarm-rules-page {
  padding: 0;
}

.rules-card {
  min-height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}
</style>
