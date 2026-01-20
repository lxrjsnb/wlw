<template>
  <div class="device-detail-page">
    <!-- 返回按钮 -->
    <el-button @click="goBack" class="back-btn">
      <el-icon><Back /></el-icon>
      返回设备列表
    </el-button>

    <!-- 设备基本信息 -->
    <el-card class="info-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>设备详情 - {{ deviceInfo?.name }}</span>
          <el-tag :type="getStatusType(deviceInfo?.status)">
            {{ getStatusText(deviceInfo?.status) }}
          </el-tag>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="设备ID">{{ deviceInfo?.device_id }}</el-descriptions-item>
        <el-descriptions-item label="设备名称">{{ deviceInfo?.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(deviceInfo?.status)">
            {{ getStatusText(deviceInfo?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="安装位置">{{ deviceInfo?.location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ deviceInfo?.ip_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="固件版本">{{ deviceInfo?.firmware_version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="所有者">{{ deviceInfo?.owner_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="电池电量">
          {{ deviceInfo?.battery_level ? `${deviceInfo.battery_level}%` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="最后心跳">
          {{ formatTime(deviceInfo?.last_heartbeat) }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="3">
          {{ deviceInfo?.description || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 传感器类型 -->
      <div class="sensors-section">
        <h4>支持的传感器</h4>
        <el-tag
          v-for="sensor in deviceInfo?.sensor_types_info"
          :key="sensor.id"
          class="sensor-tag"
        >
          {{ sensor.name }} ({{ sensor.unit }})
        </el-tag>
      </div>
    </el-card>

    <!-- 实时数据 -->
    <el-card class="data-card" v-loading="dataLoading">
      <template #header>
        <div class="card-header">
          <span>实时数据</span>
          <el-button size="small" @click="fetchLatestData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="8" v-for="data in sensorData" :key="data.id">
          <div class="data-item">
            <div class="data-icon">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="data-content">
              <div class="data-title">{{ data.sensor_type_name }}</div>
              <div class="data-value">
                {{ Number(data.value).toFixed(data.precision || 1) }}{{ data.unit }}
              </div>
              <div class="data-time">{{ formatTime(data.timestamp) }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-empty v-if="!sensorData.length" description="暂无数据" />
    </el-card>

    <!-- 设备日志 -->
    <el-card class="log-card">
      <template #header>
        <span>设备日志</span>
      </template>

      <el-table :data="logs" stripe max-height="300">
        <el-table-column prop="log_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getLogTypeColor(row.log_type)">
              {{ row.log_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDeviceDetail, getLatestData, getDeviceLogs } from '@/api/device'
import { createRealtimeWebSocket } from '@/utils/websocket'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const dataLoading = ref(false)
const deviceInfo = ref(null)
const sensorData = ref([])
const logs = ref([])

// WebSocket实例
let ws = null

// 获取设备详情
async function fetchDeviceDetail() {
  loading.value = true
  try {
    const deviceId = route.params.id
    deviceInfo.value = await getDeviceDetail(deviceId)
  } catch (error) {
    ElMessage.error('获取设备详情失败')
  } finally {
    loading.value = false
  }
}

// 获取最新数据
async function fetchLatestData() {
  dataLoading.value = true
  try {
    const deviceId = route.params.id
    const res = await getLatestData(deviceId)
    sensorData.value = res.data || []
  } catch (error) {
    console.error('获取最新数据失败:', error)
  } finally {
    dataLoading.value = false
  }
}

// 获取设备日志
async function fetchDeviceLogs() {
  try {
    const deviceId = route.params.id
    const res = await getDeviceLogs(deviceId)
    logs.value = res.items || []
  } catch (error) {
    console.error('获取设备日志失败:', error)
  }
}

// 初始化WebSocket
function initWebSocket() {
  const deviceId = route.params.id
  ws = createRealtimeWebSocket(deviceId)
  ws.connect()

  ws.on('message', (data) => {
    if (data.type === 'sensor_data') {
      // 更新实时数据
      fetchLatestData()
    }
  })
}

// 返回上一页
function goBack() {
  router.back()
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

// 获取日志类型颜色
function getLogTypeColor(type) {
  const map = {
    status: 'info',
    control: 'warning',
    error: 'danger',
    info: 'success'
  }
  return map[type] || 'info'
}

// 格式化时间
function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchDeviceDetail()
  fetchLatestData()
  fetchDeviceLogs()
  initWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.device-detail-page {
  padding: 0;
}

.back-btn {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-card,
.data-card,
.log-card {
  margin-bottom: 20px;
}

.sensors-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.sensors-section h4 {
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.sensor-tag {
  margin-right: 10px;
  margin-bottom: 10px;
}

.data-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 10px;
}

.data-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #409eff;
  border-radius: 4px;
  color: white;
  font-size: 24px;
  margin-right: 12px;
}

.data-content {
  flex: 1;
}

.data-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.data-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.data-time {
  font-size: 12px;
  color: #c0c4cc;
}
</style>
