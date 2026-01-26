<script setup>
import { computed, onMounted, reactive, ref, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts, Download, Calendar, DataLine } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { listDevices } from '../../api/devices'
import { listSensorData, getDeviceStatistics, exportSensorData } from '../../api/sensors'
import { toIsoString } from '../../utils/date'

const loading = ref(false)
const devices = ref([])
const dateRange = ref([])

// 默认选择最近7天
const defaultStartDate = new Date()
defaultStartDate.setDate(defaultStartDate.getDate() - 7)
dateRange.value = [defaultStartDate, new Date()]

const selectedDeviceId = ref('')
const reportType = ref('overview')

// 监听设备变化，自动加载数据
watch(selectedDeviceId, (newDeviceId, oldDeviceId) => {
  // 避免初始化时重复加载
  if (newDeviceId && newDeviceId !== oldDeviceId) {
    console.log('设备切换:', { old: oldDeviceId, new: newDeviceId })
    loadStatistics()
  }
})

// 监听日期范围变化
watch(dateRange, (newRange) => {
  if (newRange && newRange.length === 2 && selectedDeviceId.value) {
    console.log('日期范围变化:', newRange)
    loadStatistics()
  }
})

const statisticsData = ref({
  totalDataPoints: 0,
  avgTemperature: 0,
  avgHumidity: 0,
  avgPM25: 0,
  dataQuality: { good: 0, uncertain: 0, bad: 0 },
})

const trendData = ref([])

async function loadDevices() {
  try {
    const res = await listDevices({ page: 1, page_size: 200 })
    devices.value = res?.items || []
    if (devices.value.length && !selectedDeviceId.value) {
      selectedDeviceId.value = devices.value[0].device_id
    }
  } catch (e) {
    ElMessage.error(e?.message || '加载设备列表失败')
  }
}

async function loadStatistics() {
  const targetDeviceId = selectedDeviceId.value
  if (!targetDeviceId || dateRange.value?.length !== 2) {
    ElMessage.warning('请选择设备和日期范围')
    return
  }

  loading.value = true
  try {
    const startTime = toIsoString(dateRange.value[0])
    const endTime = toIsoString(dateRange.value[1])

    console.log('加载统计数据:', { targetDeviceId, startTime, endTime })

    // 并行获取温度、湿度、PM2.5的统计数据
    const [tempStats, humidityStats, pm25Stats, allData] = await Promise.all([
      getDeviceStatistics(targetDeviceId, {
        sensor_type: 'temperature',
        start_time: startTime,
        end_time: endTime,
      }).catch(e => { console.error('温度统计失败:', e); return null; }),
      getDeviceStatistics(targetDeviceId, {
        sensor_type: 'humidity',
        start_time: startTime,
        end_time: endTime,
      }).catch(e => { console.error('湿度统计失败:', e); return null; }),
      getDeviceStatistics(targetDeviceId, {
        sensor_type: 'pm25',
        start_time: startTime,
        end_time: endTime,
      }).catch(e => { console.error('PM2.5统计失败:', e); return null; }),
      listSensorData({
        device_id: targetDeviceId,
        start_time: startTime,
        end_time: endTime,
        page: 1,
        page_size: 1000,
      }).catch(e => { console.error('列表数据获取失败:', e); return null; }),
    ])

    console.log('API返回:', { tempStats, humidityStats, pm25Stats, allData })

    // 统计数据
    statisticsData.value = {
      totalDataPoints: allData?.total || 0,
      avgTemperature: tempStats?.avg || 0,
      avgHumidity: humidityStats?.avg || 0,
      avgPM25: pm25Stats?.avg || 0,
      dataQuality: { good: 0, uncertain: 0, bad: 0 },
    }

    // 统计数据质量
    if (allData?.items) {
      allData.items.forEach(item => {
        if (item.quality === 'good') statisticsData.value.dataQuality.good++
        else if (item.quality === 'uncertain') statisticsData.value.dataQuality.uncertain++
        else if (item.quality === 'bad') statisticsData.value.dataQuality.bad++
      })
    }

    // 处理趋势数据 - 按日期分组
    trendData.value = processTrendData(allData?.items || [])

    console.log('最终数据:', { statisticsData: statisticsData.value, trendData: trendData.value })
  } catch (e) {
    console.error('加载统计数据失败:', e)
    ElMessage.error(e?.message || '加载统计数据失败')
  } finally {
    loading.value = false
  }
}

function processTrendData(items) {
  // 按小时和传感器类型分组
  const hourlyData = {}

  items.forEach(item => {
    const timestamp = new Date(item.timestamp)
    // 格式化为 "2024/1/15 14:00" 格式
    const hourKey = `${timestamp.getFullYear()}/${timestamp.getMonth() + 1}/${timestamp.getDate()} ${String(timestamp.getHours()).padStart(2, '0')}:00`

    if (!hourlyData[hourKey]) {
      hourlyData[hourKey] = { date: hourKey, temperature: [], humidity: [], pm25: [] }
    }
    // API返回的是 sensor_type_code 字段
    if (item.sensor_type_code === 'temperature') {
      hourlyData[hourKey].temperature.push(item.value)
    } else if (item.sensor_type_code === 'humidity') {
      hourlyData[hourKey].humidity.push(item.value)
    } else if (item.sensor_type_code === 'pm25') {
      hourlyData[hourKey].pm25.push(item.value)
    }
  })

  // 计算每小时平均值并排序
  return Object.values(hourlyData)
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .map(hour => ({
      date: hour.date,
      temperature: hour.temperature.length > 0
        ? hour.temperature.reduce((a, b) => a + b, 0) / hour.temperature.length
        : 0,
      humidity: hour.humidity.length > 0
        ? hour.humidity.reduce((a, b) => a + b, 0) / hour.humidity.length
        : 0,
      pm25: hour.pm25.length > 0
        ? hour.pm25.reduce((a, b) => a + b, 0) / hour.pm25.length
        : 0,
    }))
}

const qualityPieOption = computed(() => {
  const q = statisticsData.value.dataQuality
  const total = q.good + q.uncertain + q.bad
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, left: 'center' },
    color: ['#67C23A', '#E6A23C', '#F56C6C'],
    series: [{
      name: '数据质量',
      type: 'pie',
      radius: ['40%', '65%'],
      data: [
        { value: q.good, name: '良好' },
        { value: q.uncertain, name: '不确定' },
        { value: q.bad, name: '差' },
      ],
      label: {
        formatter: params => `${params.name}: ${params.value} (${((params.value / total) * 100).toFixed(1)}%)`
      }
    }]
  }
})

const qualityTableData = computed(() => {
  const q = statisticsData.value.dataQuality
  const total = q.good + q.uncertain + q.bad
  return [
    { name: '良好', value: q.good, percent: total > 0 ? ((q.good / total) * 100).toFixed(1) : '0.0' },
    { name: '不确定', value: q.uncertain, percent: total > 0 ? ((q.uncertain / total) * 100).toFixed(1) : '0.0' },
    { name: '差', value: q.bad, percent: total > 0 ? ((q.bad / total) * 100).toFixed(1) : '0.0' },
  ]
})

const trendLineOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const time = params[0]?.axisValue || ''
      let result = `<div style="margin-bottom: 4px;">${time}</div>`
      params.forEach(param => {
        result += `<div style="display: flex; align-items: center; gap: 8px;">
          <span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; border-radius: 50%;"></span>
          <span>${param.seriesName}:</span>
          <strong>${param.value}</strong>
        </div>`
      })
      return result
    }
  },
  legend: { bottom: 0, left: 'center' },
  grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
  dataZoom: [
    {
      type: 'inside',
      start: 0,
      end: 100,
      minSpan: 10
    },
    {
      type: 'slider',
      start: 0,
      end: 100,
      minSpan: 10,
      height: 20,
      bottom: 50
    }
  ],
  xAxis: {
    type: 'category',
    data: trendData.value.map(d => d.date),
    axisLabel: {
      rotate: 45,
      formatter: (value) => {
        // 只显示日期和小时，如 "1/15 14:00"
        const parts = value.split(' ')
        if (parts.length === 2) {
          const dateParts = parts[0].split('/')
          if (dateParts.length === 3) {
            return `${dateParts[1]}/${dateParts[2]} ${parts[1]}`
          }
        }
        return value
      }
    }
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '温度 (°C)',
      type: 'line',
      data: trendData.value.map(d => d.temperature.toFixed(1)),
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      itemStyle: { color: '#F56C6C' },
      lineStyle: { width: 2 },
    },
    {
      name: '湿度 (%)',
      type: 'line',
      data: trendData.value.map(d => d.humidity.toFixed(1)),
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      itemStyle: { color: '#409EFF' },
      lineStyle: { width: 2 },
    },
    {
      name: 'PM2.5',
      type: 'line',
      data: trendData.value.map(d => d.pm25.toFixed(0)),
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      itemStyle: { color: '#67C23A' },
      lineStyle: { width: 2 },
    },
  ],
}))

async function exportReport() {
  if (!selectedDeviceId.value || dateRange.value?.length !== 2) {
    ElMessage.warning('请选择设备和日期范围')
    return
  }

  loading.value = true
  try {
    const response = await exportSensorData({
      device_id: selectedDeviceId.value,
      start_time: toIsoString(dateRange.value[0]),
      end_time: toIsoString(dateRange.value[1]),
      format: 'excel',
    })

    // http.js 对于 blob 返回整个 response 对象，需要用 response.data 获取 Blob
    const blob = response.data
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // 尝试从响应头获取文件名，如果没有则使用默认文件名
    const contentDisposition = response.headers?.['content-disposition']
    let filename = `数据报表_${selectedDeviceId.value}_${dateRange.value[0].toLocaleDateString()}.xlsx`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '')
        // 处理可能的 UTF-8 编码
        if (filename.startsWith('UTF-8')) {
          filename = decodeURIComponent(filename.split("''")[1])
        }
      }
    }
    link.download = filename

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('报表导出成功')
  } catch (e) {
    console.error('导出失败:', e)
    ElMessage.error(e?.message || '导出失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadDevices()
  // loadStatistics 会在 watch 中自动触发，不需要手动调用
})
</script>

<template>
  <div class="data-report">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title">
            <el-icon><DataLine /></el-icon>
            <span>数据统计报表</span>
          </div>
          <div class="actions">
            <el-button type="primary" :icon="Download" @click="exportReport" :loading="loading">
              导出报表
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filters">
        <el-form :inline="true" @submit.prevent>
          <el-form-item label="设备">
            <el-select v-model="selectedDeviceId" placeholder="选择设备" filterable>
              <el-option
                v-for="d in devices"
                :key="d.device_id"
                :label="`${d.name} (${d.device_id})`"
                :value="d.device_id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="日期范围">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="到"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadStatistics" :loading="loading">查询</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Loading提示 -->
      <div v-if="loading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="30"><DataLine /></el-icon>
        <p style="margin-top: 10px;">加载中...</p>
      </div>

      <!-- 统计概览 -->
      <div class="statistics-overview" v-show="!loading">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #ecf5ff; color: #409EFF">
                <el-icon><DataLine /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">数据点总数</div>
                <div class="stat-value">{{ statisticsData.totalDataPoints.toLocaleString() }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #fef0f0; color: #F56C6C">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">平均温度</div>
                <div class="stat-value">{{ typeof statisticsData.avgTemperature === 'number' ? statisticsData.avgTemperature.toFixed(1) : statisticsData.avgTemperature }}°C</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #f0f9eb; color: #67C23A">
                <el-icon><Calendar /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">平均湿度</div>
                <div class="stat-value">{{ typeof statisticsData.avgHumidity === 'number' ? statisticsData.avgHumidity.toFixed(1) : statisticsData.avgHumidity }}%</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #f4f4f5; color: #909399">
                <el-icon><DataLine /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">平均PM2.5</div>
                <div class="stat-value">{{ typeof statisticsData.avgPM25 === 'number' ? statisticsData.avgPM25.toFixed(1) : statisticsData.avgPM25 }}μg/m³</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 图表区域 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="12">
          <el-card shadow="hover" header="数据质量分布">
            <div class="chart-container">
              <VChart
                v-if="trendData.length"
                class="chart"
                :option="qualityPieOption"
                :key="'pie-' + selectedDeviceId"
                autoresize
              />
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" header="数据质量详情">
            <el-table :data="qualityTableData" size="small">
              <el-table-column prop="name" label="质量等级" />
              <el-table-column prop="value" label="数据点" align="right" />
              <el-table-column label="占比" align="right">
                <template #default="{ row }">
                  <el-progress
                    :percentage="parseFloat(row.percent)"
                    :color="row.name === '良好' ? '#67C23A' : row.name === '不确定' ? '#E6A23C' : '#F56C6C'"
                  />
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <!-- 趋势图 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="数据趋势">
            <div class="chart-container">
              <VChart
                v-if="trendData.length"
                class="chart-large"
                :option="trendLineOption"
                :key="'trend-' + selectedDeviceId"
                autoresize
              />
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 详细数据表格 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="每日数据汇总">
            <el-table :data="trendData" size="small">
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column label="温度" width="120">
                <template #default="{ row }">
                  <span v-if="row.temperature > 0" :style="{ color: row.temperature > 28 ? '#F56C6C' : row.temperature < 18 ? '#409EFF' : '' }">
                    {{ row.temperature.toFixed(1) }}°C
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="湿度" width="120">
                <template #default="{ row }">
                  <span v-if="row.humidity > 0" :style="{ color: row.humidity > 70 ? '#E6A23C' : '' }">
                    {{ row.humidity.toFixed(1) }}%
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="PM2.5" width="120">
                <template #default="{ row }">
                  <el-tag v-if="row.pm25 > 0" :type="row.pm25 <= 35 ? 'success' : row.pm25 <= 75 ? 'warning' : 'danger'">
                    {{ row.pm25.toFixed(0) }}μg/m³
                  </el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="空气质量评估">
                <template #default="{ row }">
                  <span v-if="row.pm25 <= 35 && row.pm25 > 0" style="color: #67C23A">优</span>
                  <span v-else-if="row.pm25 <= 75 && row.pm25 > 0" style="color: #E6A23C">良</span>
                  <span v-else-if="row.pm25 > 75" style="color: #F56C6C">差</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped>
.data-report {
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
  margin-bottom: 20px;
}

.statistics-overview {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 16px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.mt-20 {
  margin-top: 20px;
}

.chart-container {
  height: 350px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart {
  width: 100%;
  height: 300px;
}

.chart-large {
  width: 100%;
  height: 350px;
}
</style>
