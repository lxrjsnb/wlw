<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts, Download, Calendar, DataLine } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { listDevices } from '../../api/devices'
import { listSensorData } from '../../api/sensors'
import { formatDateTime, toIsoString } from '../../utils/date'

const loading = ref(false)
const devices = ref([])
const dateRange = ref([])

// 默认选择最近7天
const defaultStartDate = new Date()
defaultStartDate.setDate(defaultStartDate.getDate() - 7)
dateRange.value = [defaultStartDate, new Date()]

const selectedDeviceId = ref('')
const reportType = ref('overview')

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
  if (!selectedDeviceId.value || dateRange.value?.length !== 2) return

  loading.value = true
  try {
    // TODO: 调用统计 API
    // const res = await getStatistics({
    //   device_id: selectedDeviceId.value,
    //   start_time: toIsoString(dateRange.value[0]),
    //   end_time: toIsoString(dateRange.value[1]),
    // })
    // statisticsData.value = res

    // 模拟数据
    statisticsData.value = {
      totalDataPoints: 15623,
      avgTemperature: 24.5,
      avgHumidity: 58.3,
      avgPM25: 42.8,
      dataQuality: { good: 14890, uncertain: 521, bad: 212 },
    }

    // 模拟趋势数据
    trendData.value = generateTrendData()
  } catch (e) {
    ElMessage.error(e?.message || '加载统计数据失败')
  } finally {
    loading.value = false
  }
}

function generateTrendData() {
  const data = []
  const startDate = dateRange.value[0]
  for (let i = 0; i < 7; i++) {
    const date = new Date(startDate)
    date.setDate(date.getDate() + i)
    data.push({
      date: date.toLocaleDateString('zh-CN'),
      temperature: 22 + Math.random() * 5,
      humidity: 50 + Math.random() * 20,
      pm25: 30 + Math.random() * 40,
    })
  }
  return data
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

const trendLineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0, left: 'center' },
  grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
  xAxis: {
    type: 'category',
    data: trendData.value.map(d => d.date),
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '温度 (°C)',
      type: 'line',
      data: trendData.value.map(d => d.temperature.toFixed(1)),
      smooth: true,
      itemStyle: { color: '#F56C6C' },
    },
    {
      name: '湿度 (%)',
      type: 'line',
      data: trendData.value.map(d => d.humidity.toFixed(1)),
      smooth: true,
      itemStyle: { color: '#409EFF' },
    },
    {
      name: 'PM2.5',
      type: 'line',
      data: trendData.value.map(d => d.pm25.toFixed(0)),
      smooth: true,
      itemStyle: { color: '#67C23A' },
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
    // TODO: 调用导出 API
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('报表导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadDevices()
  await loadStatistics()
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
            <el-select v-model="selectedDeviceId" placeholder="选择设备" filterable @change="loadStatistics">
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
              @change="loadStatistics"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadStatistics">查询</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 统计概览 -->
      <div class="statistics-overview">
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
                <div class="stat-value">{{ statisticsData.avgTemperature }}°C</div>
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
                <div class="stat-value">{{ statisticsData.avgHumidity }}%</div>
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
                <div class="stat-value">{{ statisticsData.avgPM25 }}μg/m³</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 图表区域 -->
      <el-row :gutter="20" class="mt-20">
        <el-col :span="12">
          <el-card shadow="hover" header="数据质量分布">
            <div class="chart-container">
              <VChart v-if="!loading" class="chart" :option="qualityPieOption" autoresize />
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" header="数据质量详情">
            <el-table :data="[
              { name: '良好', value: statisticsData.dataQuality.good, percent: ((statisticsData.dataQuality.good / (statisticsData.dataQuality.good + statisticsData.dataQuality.uncertain + statisticsData.dataQuality.bad)) * 100).toFixed(1) },
              { name: '不确定', value: statisticsData.dataQuality.uncertain, percent: ((statisticsData.dataQuality.uncertain / (statisticsData.dataQuality.good + statisticsData.dataQuality.uncertain + statisticsData.dataQuality.bad)) * 100).toFixed(1) },
              { name: '差', value: statisticsData.dataQuality.bad, percent: ((statisticsData.dataQuality.bad / (statisticsData.dataQuality.good + statisticsData.dataQuality.uncertain + statisticsData.dataQuality.bad)) * 100).toFixed(1) },
            ]" size="small">
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
      <el-row :gutter="20" class="mt-20">
        <el-col :span="24">
          <el-card shadow="hover" header="数据趋势">
            <div class="chart-container">
              <VChart v-if="!loading && trendData.length" class="chart-large" :option="trendLineOption" autoresize />
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 详细数据表格 -->
      <el-row :gutter="20" class="mt-20">
        <el-col :span="24">
          <el-card shadow="hover" header="每日数据汇总">
            <el-table :data="trendData" size="small">
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column label="温度" width="120">
                <template #default="{ row }">
                  <span :style="{ color: row.temperature > 28 ? '#F56C6C' : row.temperature < 18 ? '#409EFF' : '' }">
                    {{ row.temperature.toFixed(1) }}°C
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="湿度" width="120">
                <template #default="{ row }">
                  <span :style="{ color: row.humidity > 70 ? '#E6A23C' : '' }">
                    {{ row.humidity.toFixed(1) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="PM2.5" width="120">
                <template #default="{ row }">
                  <el-tag :type="row.pm25 <= 35 ? 'success' : row.pm25 <= 75 ? 'warning' : 'danger'">
                    {{ row.pm25.toFixed(0) }}μg/m³
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="空气质量评估">
                <template #default="{ row }">
                  <span v-if="row.pm25 <= 35" style="color: #67C23A">优</span>
                  <span v-else-if="row.pm25 <= 75" style="color: #E6A23C">良</span>
                  <span v-else style="color: #F56C6C">差</span>
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
