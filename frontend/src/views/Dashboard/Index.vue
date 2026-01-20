<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="设备总数" :value="stats.deviceCount">
            <template #suffix>台</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="在线设备" :value="stats.onlineDevice">
            <template #suffix>台</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="待处理告警" :value="stats.pendingAlarms">
            <template #suffix>条</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="今日数据" :value="stats.todayData">
            <template #suffix>条</template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <!-- 设备状态分布 -->
      <el-col :span="12">
        <el-card>
          <template #header>设备状态分布</template>
          <div ref="deviceStatusChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 告警趋势 -->
      <el-col :span="12">
        <el-card>
          <template #header>告警趋势（近7天）</template>
          <div ref="alarmTrendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <!-- 传感器数据趋势 -->
      <el-col :span="24">
        <el-card>
          <template #header>传感器数据趋势（近24小时）</template>
          <div ref="sensorTrendChartRef" class="chart-container-large"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近告警和设备列表 -->
    <el-row :gutter="20" class="list-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近告警</span>
              <el-link type="primary" @click="goToAlarms">查看全部</el-link>
            </div>
          </template>
          <el-table :data="recentAlarms" stripe max-height="300">
            <el-table-column prop="device_name" label="设备" width="100" />
            <el-table-column prop="sensor_type_name" label="传感器" width="100" />
            <el-table-column prop="message" label="消息" show-overflow-tooltip />
            <el-table-column prop="triggered_at" label="时间" width="150">
              <template #default="{ row }">
                {{ formatTime(row.triggered_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>设备列表</span>
              <el-link type="primary" @click="goToDevices">查看全部</el-link>
            </div>
          </template>
          <el-table :data="recentDevices" stripe max-height="300">
            <el-table-column prop="device_id" label="设备ID" width="100" />
            <el-table-column prop="name" label="设备名称" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getDeviceList, getDeviceStats } from '@/api/device'
import { getAlarmRecords, getAlarmStats } from '@/api/alarm'
import { getSensorTypes } from '@/api/device'
import { getHistoryData } from '@/api/sensor'
import dayjs from 'dayjs'

const router = useRouter()

// 统计数据
const stats = reactive({
  deviceCount: 0,
  onlineDevice: 0,
  pendingAlarms: 0,
  todayData: 0
})

// 列表数据
const recentAlarms = ref([])
const recentDevices = ref([])

// 图表引用
const deviceStatusChartRef = ref(null)
const alarmTrendChartRef = ref(null)
const sensorTrendChartRef = ref(null)

// 图表实例
let deviceStatusChart = null
let alarmTrendChart = null
let sensorTrendChart = null

// 获取统计数据
async function fetchStats() {
  try {
    const [deviceStats, alarmStats] = await Promise.all([
      getDeviceStats(),
      getAlarmStats()
    ])

    stats.deviceCount = deviceStats.total
    stats.onlineDevice = deviceStats.online
    stats.pendingAlarms = alarmStats.by_status?.pending || 0
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 获取最近告警
async function fetchRecentAlarms() {
  try {
    const res = await getAlarmRecords({
      page: 1,
      page_size: 5,
      status: 'pending'
    })
    recentAlarms.value = res.items || []
  } catch (error) {
    console.error('获取最近告警失败:', error)
  }
}

// 获取最近设备
async function fetchRecentDevices() {
  try {
    const res = await getDeviceList({
      page: 1,
      page_size: 5
    })
    recentDevices.value = res.items || []
  } catch (error) {
    console.error('获取设备列表失败:', error)
  }
}

// 初始化设备状态图表
function initDeviceStatusChart() {
  if (!deviceStatusChartRef.value) return

  deviceStatusChart = echarts.init(deviceStatusChartRef.value)

  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '设备状态',
        type: 'pie',
        radius: '50%',
        data: [
          { value: stats.onlineDevice, name: '在线' },
          { value: stats.deviceCount - stats.onlineDevice, name: '离线' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  deviceStatusChart.setOption(option)
}

// 初始化告警趋势图表
function initAlarmTrendChart() {
  if (!alarmTrendChartRef.value) return

  alarmTrendChart = echarts.init(alarmTrendChartRef.value)

  // 生成最近7天的日期
  const dates = []
  for (let i = 6; i >= 0; i--) {
    dates.push(dayjs().subtract(i, 'day').format('MM-DD'))
  }

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '告警数量',
        type: 'bar',
        data: [5, 8, 3, 12, 6, 9, 4],
        itemStyle: {
          color: '#f56c6c'
        }
      }
    ]
  }

  alarmTrendChart.setOption(option)
}

// 初始化传感器趋势图表
function initSensorTrendChart() {
  if (!sensorTrendChartRef.value) return

  sensorTrendChart = echarts.init(sensorTrendChartRef.value)

  // 生成最近24小时的时间点
  const timestamps = []
  for (let i = 23; i >= 0; i--) {
    timestamps.push(dayjs().subtract(i, 'hour').format('HH:mm'))
  }

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['温度', '湿度', 'PM2.5']
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timestamps
    },
    yAxis: {
      type: 'value'
    },
    dataZoom: [
      {
        type: 'inside',
        start: 50,
        end: 100
      },
      {
        type: 'slider',
        start: 50,
        end: 100
      }
    ],
    series: [
      {
        name: '温度',
        type: 'line',
        smooth: true,
        data: Array.from({ length: 24 }, () => Math.random() * 10 + 20)
      },
      {
        name: '湿度',
        type: 'line',
        smooth: true,
        data: Array.from({ length: 24 }, () => Math.random() * 20 + 50)
      },
      {
        name: 'PM2.5',
        type: 'line',
        smooth: true,
        data: Array.from({ length: 24 }, () => Math.random() * 50 + 20)
      }
    ]
  }

  sensorTrendChart.setOption(option)
}

// 跳转到告警页面
function goToAlarms() {
  router.push('/alarms')
}

// 跳转到设备页面
function goToDevices() {
  router.push('/devices')
}

// 获取状态类型
function getStatusType(status) {
  const map = {
    online: 'success',
    offline: 'info',
    error: 'danger'
  }
  return map[status] || 'info'
}

// 获取状态文本
function getStatusText(status) {
  const map = {
    online: '在线',
    offline: '离线',
    error: '故障'
  }
  return map[status] || status
}

// 格式化时间
function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(async () => {
  await fetchStats()
  await fetchRecentAlarms()
  await fetchRecentDevices()

  initDeviceStatusChart()
  initAlarmTrendChart()
  initSensorTrendChart()

  window.addEventListener('resize', () => {
    deviceStatusChart?.resize()
    alarmTrendChart?.resize()
    sensorTrendChart?.resize()
  })
})

onUnmounted(() => {
  deviceStatusChart?.dispose()
  alarmTrendChart?.dispose()
  sensorTrendChart?.dispose()
  window.removeEventListener('resize', () => {
    deviceStatusChart?.resize()
    alarmTrendChart?.resize()
    sensorTrendChart?.resize()
  })
})
</script>

<style scoped>
.dashboard-page {
  padding: 0;
}

.stats-row,
.charts-row,
.list-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
}

.chart-container-large {
  height: 400px;
}
</style>
