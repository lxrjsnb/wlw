<template>
  <div class="realtime-monitor-page">
    <!-- 设备选择 -->
    <el-card class="selector-card">
      <el-form :inline="true">
        <el-form-item label="选择设备">
          <el-select
            v-model="selectedDeviceId"
            placeholder="请选择设备"
            style="width: 300px"
            @change="handleDeviceChange"
          >
            <el-option
              v-for="device in deviceList"
              :key="device.device_id"
              :label="`${device.name} (${device.device_id})`"
              :value="device.device_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="传感器类型">
          <el-select
            v-model="selectedSensorType"
            placeholder="全部"
            clearable
            @change="handleSensorChange"
          >
            <el-option
              v-for="sensor in sensorTypes"
              :key="sensor.code"
              :label="`${sensor.name} (${sensor.unit})`"
              :value="sensor.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-switch
            v-model="autoScroll"
            active-text="自动滚动"
            inactive-text="固定显示"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 实时数据卡片 -->
    <el-row :gutter="20" class="data-cards">
      <el-col :span="6" v-for="item in realtimeData" :key="item.sensor_type_code">
        <el-card shadow="hover">
          <div class="data-card-content">
            <div class="card-header">
              <el-icon :size="24" :color="item.color || '#409eff'">
                <component :is="getIcon(item.sensor_type_code)" />
              </el-icon>
              <span class="card-title">{{ item.sensor_type_name }}</span>
            </div>
            <div class="card-value">
              {{ Number(item.value).toFixed(item.precision || 1) }}
              <span class="card-unit">{{ item.unit }}</span>
            </div>
            <div class="card-time">{{ formatTime(item.timestamp) }}</div>
            <div class="card-status">
              <el-tag :type="item.quality === 'good' ? 'success' : 'warning'" size="small">
                {{ item.quality === 'good' ? '良好' : '不确定' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时图表 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>实时趋势图</span>
          <div>
            <el-button size="small" @click="clearChartData">清空</el-button>
            <el-button size="small" @click="refreshData">刷新</el-button>
          </div>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <template #header>
        <span>数据记录</span>
      </template>
      <el-table :data="dataTable" stripe max-height="400">
        <el-table-column prop="sensor_type_name" label="传感器类型" width="150" />
        <el-table-column prop="value" label="数值" width="120">
          <template #default="{ row }">
            {{ Number(row.value).toFixed(row.precision || 1) }} {{ row.unit }}
          </template>
        </el-table-column>
        <el-table-column prop="quality" label="质量" width="100">
          <template #default="{ row }">
            <el-tag :type="row.quality === 'good' ? 'success' : 'warning'" size="small">
              {{ row.quality === 'good' ? '良好' : '不确定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDeviceList, getLatestData, getSensorTypes } from '@/api/device'
import { createRealtimeWebSocket } from '@/utils/websocket'
import { ElMessage } from 'element-plus'

// 设备列表
const deviceList = ref([])
const sensorTypes = ref([])
const selectedDeviceId = ref('')
const selectedSensorType = ref('')
const autoScroll = ref(true)
const realtimeData = ref([])
const dataTable = ref([])

// 图表相关
const chartRef = ref(null)
let chart = null
const chartData = reactive({
  timestamps: [],
  values: {}
})

// WebSocket实例
let ws = null

// 获取设备列表
async function fetchDeviceList() {
  try {
    const res = await getDeviceList({ page_size: 100 })
    deviceList.value = res.items || []
    if (deviceList.value.length > 0) {
      selectedDeviceId.value = deviceList.value[0].device_id
      handleDeviceChange()
    }
  } catch (error) {
    ElMessage.error('获取设备列表失败')
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

// 设备变更
async function handleDeviceChange() {
  if (!selectedDeviceId.value) return

  // 关闭旧连接
  if (ws) {
    ws.close()
  }

  // 获取最新数据
  await fetchLatestData()

  // 初始化WebSocket
  initWebSocket()
}

// 传感器类型变更
function handleSensorChange() {
  updateChartData()
}

// 获取最新数据
async function fetchLatestData() {
  try {
    const res = await getLatestData(selectedDeviceId.value)
    realtimeData.value = res.data || []
    dataTable.value = res.data || []
    updateChartData()
  } catch (error) {
    console.error('获取最新数据失败:', error)
  }
}

// 初始化WebSocket
function initWebSocket() {
  ws = createRealtimeWebSocket(selectedDeviceId.value)
  ws.connect()

  ws.on('message', (data) => {
    if (data.type === 'sensor_data') {
      handleSensorData(data.data)
    }
  })
}

// 处理传感器数据
function handleSensorData(data) {
  const timestamp = new Date(data.timestamp)
  const timeStr = timestamp.toLocaleTimeString('zh-CN')

  // 更新实时数据
  if (data.sensors) {
    Object.keys(data.sensors).forEach(code => {
      const existing = realtimeData.value.find(d => d.sensor_type_code === code)
      if (existing) {
        existing.value = data.sensors[code]
        existing.timestamp = timestamp
      }
    })
  }

  // 更新图表数据
  if (!chartData.timestamps.includes(timeStr)) {
    chartData.timestamps.push(timeStr)

    // 限制数据点数量
    if (chartData.timestamps.length > 100) {
      chartData.timestamps.shift()
    }
  }

  // 更新图表
  updateChart()
}

// 更新图表数据
function updateChartData() {
  if (!selectedSensorType.value) {
    // 显示所有传感器
    realtimeData.value.forEach(item => {
      if (!chartData.values[item.sensor_type_code]) {
        chartData.values[item.sensor_type_code] = []
      }
      chartData.values[item.sensor_type_code].push(Number(item.value))

      // 限制数据点数量
      if (chartData.values[item.sensor_type_code].length > chartData.timestamps.length) {
        chartData.values[item.sensor_type_code].shift()
      }
    })
  } else {
    // 只显示选中的传感器
    const item = realtimeData.value.find(d => d.sensor_type_code === selectedSensorType.value)
    if (item) {
      if (!chartData.values[item.sensor_type_code]) {
        chartData.values[item.sensor_type_code] = []
      }
      chartData.values[item.sensor_type_code].push(Number(item.value))

      // 限制数据点数量
      if (chartData.values[item.sensor_type_code].length > chartData.timestamps.length) {
        chartData.values[item.sensor_type_code].shift()
      }
    }
  }

  updateChart()
}

// 初始化图表
async function initChart() {
  await nextTick()
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)
  updateChart()

  // 响应式
  window.addEventListener('resize', () => {
    chart?.resize()
  })
}

// 更新图表
function updateChart() {
  if (!chart) return

  // 准备系列数据
  const series = []
  const sensors = selectedSensorType.value
    ? realtimeData.value.filter(d => d.sensor_type_code === selectedSensorType.value)
    : realtimeData.value

  sensors.forEach(sensor => {
    series.push({
      name: sensor.sensor_type_name,
      type: 'line',
      smooth: true,
      data: chartData.values[sensor.sensor_type_code] || [],
      itemStyle: {
        color: sensor.color || '#409eff'
      }
    })
  })

  const option = {
    title: {
      text: '实时数据趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: chartData.timestamps
    },
    yAxis: {
      type: 'value'
    },
    series
  }

  chart.setOption(option)

  // 自动滚动
  if (autoScroll.value) {
    chart.dispatchAction({
      type: 'dataZoom',
      start: Math.max(0, 100 - (100 / Math.max(1, chartData.timestamps.length)) * 10),
      end: 100
    })
  }
}

// 清空图表数据
function clearChartData() {
  chartData.timestamps = []
  chartData.values = {}
  updateChart()
}

// 刷新数据
function refreshData() {
  fetchLatestData()
}

// 获取图标
function getIcon(code) {
  const iconMap = {
    temperature: 'Sunny',
    humidity: 'Cloudy',
    pm25: 'WindPower',
    co2: 'Cpu',
    light: 'Sunny'
  }
  return iconMap[code] || 'DataLine'
}

// 格式化时间
function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchDeviceList()
  fetchSensorTypes()
  initChart()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  if (chart) {
    chart.dispose()
  }
  window.removeEventListener('resize', () => {
    chart?.resize()
  })
})
</script>

<style scoped>
.realtime-monitor-page {
  padding: 0;
}

.selector-card {
  margin-bottom: 20px;
}

.data-cards {
  margin-bottom: 20px;
}

.data-card-content {
  text-align: center;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 14px;
  color: #909399;
  margin-left: 8px;
}

.card-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.card-unit {
  font-size: 14px;
  color: #909399;
}

.card-time {
  font-size: 12px;
  color: #c0c4cc;
  margin-bottom: 8px;
}

.card-status {
  display: flex;
  justify-content: center;
}

.chart-card,
.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 400px;
}
</style>
