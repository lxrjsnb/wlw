<template>
  <div class="history-monitor-page">
    <!-- 查询条件 -->
    <el-card class="query-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="设备">
          <el-select
            v-model="queryParams.device_id"
            placeholder="请选择设备"
            style="width: 200px"
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
            v-model="queryParams.sensor_type"
            placeholder="请选择传感器类型"
            clearable
          >
            <el-option
              v-for="sensor in sensorTypes"
              :key="sensor.code"
              :label="`${sensor.name} (${sensor.unit})`"
              :value="sensor.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-radio-group v-model="timeRange" @change="handleTimeRangeChange">
            <el-radio-button :label="1">1小时</el-radio-button>
            <el-radio-button :label="6">6小时</el-radio-button>
            <el-radio-button :label="24">24小时</el-radio-button>
            <el-radio-button :label="168">7天</el-radio-button>
            <el-radio-button :value="custom">自定义</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="timeRange === 'custom'">
          <el-date-picker
            v-model="customDateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleExport">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 图表 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>历史数据趋势</span>
          <div>
            <el-button size="small" @click="refreshChart">刷新</el-button>
          </div>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>

    <!-- 数据统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="数据点数" :value="statistics.count" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="最小值" :value="statistics.min" :precision="2" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="最大值" :value="statistics.max" :precision="2" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="平均值" :value="statistics.avg" :precision="2" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>数据明细</span>
          <el-tag type="info">共 {{ total }} 条记录</el-tag>
        </div>
      </template>
      <el-table v-loading="loading" :data="tableData" stripe max-height="400">
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDeviceList, getSensorTypes } from '@/api/device'
import { getHistoryData, getDataStatistics, exportData } from '@/api/sensor'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

// 设备列表
const deviceList = ref([])
const sensorTypes = ref([])

// 查询参数
const timeRange = ref(24)
const customDateRange = ref([])
const queryParams = reactive({
  device_id: '',
  sensor_type: '',
  hours: 24,
  start_time: '',
  end_time: '',
  page: 1,
  page_size: 20
})

// 数据
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const statistics = reactive({
  count: 0,
  min: 0,
  max: 0,
  avg: 0
})

// 图表
const chartRef = ref(null)
let chart = null

// 获取设备列表
async function fetchDeviceList() {
  try {
    const res = await getDeviceList({ page_size: 100 })
    deviceList.value = res.items || []
    if (deviceList.value.length > 0) {
      queryParams.device_id = deviceList.value[0].device_id
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

// 时间范围变更
function handleTimeRangeChange() {
  if (timeRange.value !== 'custom') {
    queryParams.hours = timeRange.value
    queryParams.start_time = ''
    queryParams.end_time = ''
  }
}

// 查询
async function handleQuery() {
  if (timeRange.value === 'custom' && customDateRange.value.length === 2) {
    queryParams.start_time = customDateRange.value[0]
    queryParams.end_time = customDateRange.value[1]
  } else {
    queryParams.hours = timeRange.value
    queryParams.start_time = ''
    queryParams.end_time = ''
  }

  await Promise.all([
    fetchHistoryData(),
    fetchStatistics()
  ])
}

// 获取历史数据
async function fetchHistoryData() {
  loading.value = true
  try {
    const res = await getHistoryData(queryParams.device_id, queryParams)
    tableData.value = res.data || []
    total.value = res.count || 0

    // 更新图表
    updateChartData()
  } catch (error) {
    ElMessage.error('获取历史数据失败')
  } finally {
    loading.value = false
  }
}

// 获取统计数据
async function fetchStatistics() {
  if (!queryParams.device_id || !queryParams.sensor_type) {
    return
  }

  try {
    const res = await getDataStatistics(queryParams.device_id, queryParams)
    Object.assign(statistics, res)
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 更新图表数据
function updateChartData() {
  if (!chart) return

  // 按传感器类型分组
  const groupedData = {}
  tableData.value.forEach(item => {
    if (!groupedData[item.sensor_type_code]) {
      groupedData[item.sensor_type_code] = {
        name: item.sensor_type_name,
        timestamps: [],
        values: [],
        color: item.color || '#409eff'
      }
    }
    groupedData[item.sensor_type_code].timestamps.push(
      dayjs(item.timestamp).format('HH:mm:ss')
    )
    groupedData[item.sensor_type_code].values.push(Number(item.value))
  })

  // 准备系列
  const series = Object.values(groupedData).map(item => ({
    name: item.name,
    type: 'line',
    smooth: true,
    data: item.values,
    itemStyle: {
      color: item.color
    }
  }))

  const timestamps = Object.values(groupedData)[0]?.timestamps || []

  const option = {
    title: {
      text: '历史数据趋势',
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
      data: timestamps
    },
    yAxis: {
      type: 'value'
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100
      }
    ],
    series
  }

  chart.setOption(option)
}

// 初始化图表
async function initChart() {
  await nextTick()
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)

  window.addEventListener('resize', () => {
    chart?.resize()
  })
}

// 刷新图表
function refreshChart() {
  handleQuery()
}

// 导出数据
async function handleExport() {
  try {
    const blob = await exportData(queryParams)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `sensor_data_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 格式化时间
function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(async () => {
  await fetchDeviceList()
  await fetchSensorTypes()
  initChart()
  handleQuery()
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
  }
  window.removeEventListener('resize', () => {
    chart?.resize()
  })
})
</script>

<style scoped>
.history-monitor-page {
  padding: 0;
}

.query-card {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.stats-row {
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

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
