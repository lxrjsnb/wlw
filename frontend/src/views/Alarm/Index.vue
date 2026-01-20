<template>
  <div class="alarm-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总告警数" :value="stats.total" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="待处理" :value="stats.by_status?.pending" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="严重告警" :value="stats.by_priority?.critical" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="24小时内" :value="stats.recent_24h" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 告警列表 -->
    <el-card class="alarm-card">
      <template #header>
        <div class="card-header">
          <span>告警记录</span>
          <el-button @click="handleQuery">
            <el-icon><Refresh /></el-icon>
            刷新
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
        <el-form-item label="传感器类型">
          <el-input
            v-model="queryParams.sensor_type"
            placeholder="请输入传感器类型"
            clearable
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="queryParams.status"
            placeholder="全部"
            clearable
            @change="handleQuery"
          >
            <el-option label="待处理" value="pending" />
            <el-option label="已确认" value="acknowledged" />
            <el-option label="已解决" value="resolved" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select
            v-model="queryParams.priority"
            placeholder="全部"
            clearable
            @change="handleQuery"
          >
            <el-option label="严重" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">搜索</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="alarmList" stripe>
        <el-table-column prop="device_id_str" label="设备ID" width="120" />
        <el-table-column prop="alarm_rule_name" label="告警规则" width="150" />
        <el-table-column prop="sensor_type_name" label="传感器" width="120" />
        <el-table-column label="当前值/阈值" width="150">
          <template #default="{ row }">
            {{ row.current_value }}{{ row.unit }} / {{ row.threshold_value }}{{ row.unit }}
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">
              {{ row.priority_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="triggered_at" label="触发时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.triggered_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              size="small"
              @click="handleResolve(row, 'acknowledged')"
            >
              确认
            </el-button>
            <el-button
              v-if="row.status !== 'resolved'"
              size="small"
              type="primary"
              @click="handleResolve(row, 'resolved')"
            >
              解决
            </el-button>
            <el-button size="small" @click="handleView(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.page_size"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="handleQuery"
        @current-change="handleQuery"
      />
    </el-card>

    <!-- 告警详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="告警详情" width="600px">
      <el-descriptions v-if="currentAlarm" :column="2" border>
        <el-descriptions-item label="设备ID">
          {{ currentAlarm.device_id_str }}
        </el-descriptions-item>
        <el-descriptions-item label="告警规则">
          {{ currentAlarm.alarm_rule_name }}
        </el-descriptions-item>
        <el-descriptions-item label="传感器">
          {{ currentAlarm.sensor_type_name }}
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-tag :type="getPriorityType(currentAlarm.priority)">
            {{ currentAlarm.priority_display }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="当前值">
          {{ currentAlarm.current_value }}{{ currentAlarm.unit }}
        </el-descriptions-item>
        <el-descriptions-item label="阈值">
          {{ currentAlarm.threshold_value }}{{ currentAlarm.unit }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentAlarm.status)">
            {{ currentAlarm.status_display }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="触发时间">
          {{ formatTime(currentAlarm.triggered_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="告警消息" :span="2">
          {{ currentAlarm.message }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentAlarm.acknowledged_by_name" label="确认人">
          {{ currentAlarm.acknowledged_by_name }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentAlarm.acknowledged_at" label="确认时间">
          {{ formatTime(currentAlarm.acknowledged_at) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentAlarm.resolved_by_name" label="解决人">
          {{ currentAlarm.resolved_by_name }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentAlarm.resolved_at" label="解决时间">
          {{ formatTime(currentAlarm.resolved_at) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentAlarm.resolution_note" label="解决说明" :span="2">
          {{ currentAlarm.resolution_note }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getAlarmRecords, resolveAlarm, getAlarmStats } from '@/api/alarm'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const alarmList = ref([])
const total = ref(0)
const detailDialogVisible = ref(false)
const currentAlarm = ref(null)

const stats = reactive({
  total: 0,
  by_status: {},
  by_priority: {},
  recent_24h: 0
})

const queryParams = reactive({
  page: 1,
  page_size: 20,
  device_id: '',
  sensor_type: '',
  status: '',
  priority: ''
})

// 获取告警列表
async function fetchAlarmList() {
  loading.value = true
  try {
    const res = await getAlarmRecords(queryParams)
    alarmList.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('获取告警列表失败')
  } finally {
    loading.value = false
  }
}

// 获取告警统计
async function fetchAlarmStats() {
  try {
    const res = await getAlarmStats()
    Object.assign(stats, res)
  } catch (error) {
    console.error('获取告警统计失败:', error)
  }
}

// 查询
function handleQuery() {
  queryParams.page = 1
  fetchAlarmList()
}

// 重置
function resetQuery() {
  Object.assign(queryParams, {
    page: 1,
    page_size: 20,
    device_id: '',
    sensor_type: '',
    status: '',
    priority: ''
  })
  fetchAlarmList()
}

// 处理告警
async function handleResolve(row, status) {
  const actionText = status === 'acknowledged' ? '确认' : '解决'

  try {
    await ElMessageBox.confirm(
      `确定要${actionText}该告警吗？`,
      '提示',
      { type: 'warning' }
    )
    await resolveAlarm(row.id, { status })
    ElMessage.success(`${actionText}成功`)
    fetchAlarmList()
    fetchAlarmStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`${actionText}失败`)
    }
  }
}

// 查看详情
function handleView(row) {
  currentAlarm.value = row
  detailDialogVisible.value = true
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

// 获取状态类型
function getStatusType(status) {
  const map = {
    pending: 'danger',
    acknowledged: 'warning',
    resolved: 'success',
    false_positive: 'info'
  }
  return map[status] || 'info'
}

// 格式化时间
function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchAlarmList()
  fetchAlarmStats()
})
</script>

<style scoped>
.alarm-page {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.alarm-card {
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
