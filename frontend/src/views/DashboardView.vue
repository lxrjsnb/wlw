<script setup>
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import { Monitor, Warning, CircleCheck, DataLine, TrendCharts, Location, Timer } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getDeviceStats } from '../api/devices'
import { getAlarmStats } from '../api/alarms'
import { listSensorData } from '../api/sensors'

const loading = ref(false)
const deviceStats = ref(null)
const alarmStats = ref(null)
const dataTotal = ref(0)
const recentAlarms = ref([])
const deviceHealthData = ref([])

const summaryCards = computed(() => [
  {
    title: '总设备数',
    value: deviceStats.value?.total ?? '-',
    icon: Monitor,
    color: '#409EFF',
    bg: '#ecf5ff',
    trend: deviceStats.value ? '+2 较上周' : '',
  },
  {
    title: '在线设备',
    value: deviceStats.value?.online ?? '-',
    icon: CircleCheck,
    color: '#67C23A',
    bg: '#f0f9eb',
    trend: deviceStats.value ? `${Math.round((deviceStats.value.online / deviceStats.value.total) * 100)}% 在线率` : '',
  },
  {
    title: '待处理告警',
    value: alarmStats.value?.by_status?.pending ?? '-',
    icon: Warning,
    color: '#F56C6C',
    bg: '#fef0f0',
    trend: alarmStats.value?.recent_24h ? `+${alarmStats.value.recent_24h} 今日新增` : '',
  },
  {
    title: '数据点',
    value: dataTotal.value ? formatNumber(dataTotal.value) : '-',
    icon: DataLine,
    color: '#909399',
    bg: '#f4f4f5',
    trend: '持续增长中',
  },
])

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const deviceStatusOption = computed(() => {
  const s = deviceStats.value
  const data = s
    ? [
        { value: s.online, name: '在线' },
        { value: s.offline, name: '离线' },
        { value: s.error, name: '故障' },
        { value: s.maintenance, name: '维护' },
      ]
    : []
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, left: 'center' },
    series: [
      {
        name: '设备状态',
        type: 'pie',
        radius: ['40%', '65%'],
        label: { formatter: '{b}: {c}' },
        data,
      },
    ],
  }
})

async function load() {
  loading.value = true
  try {
    const [ds, as, sd] = await Promise.all([
      getDeviceStats(),
      getAlarmStats(),
      listSensorData({ page: 1, page_size: 1 }),
    ])
    deviceStats.value = ds
    alarmStats.value = as
    dataTotal.value = sd?.total ?? 0

    // 获取最近告警
    recentAlarms.value = as?.critical_pending?.slice(0, 5) || []

    // 模拟设备健康度数据
    deviceHealthData.value = generateDeviceHealthData()
  } catch (e) {
    ElMessage.error(e?.message || '加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

function generateDeviceHealthData() {
  const locations = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京']
  return locations.map(loc => ({
    name: loc,
    value: Math.floor(Math.random() * 30) + 70,
  })).sort((a, b) => b.value - a.value)
}

const deviceHealthOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'value',
    max: 100,
    axisLabel: { formatter: '{value}%' }
  },
  yAxis: {
    type: 'category',
    data: deviceHealthData.value.map(d => d.name)
  },
  series: [{
    type: 'bar',
    data: deviceHealthData.value.map(d => ({
      value: d.value,
      itemStyle: {
        color: d.value >= 90 ? '#67C23A' : d.value >= 70 ? '#E6A23C' : '#F56C6C'
      }
    })),
    label: {
      show: true,
      position: 'right',
      formatter: '{c}%'
    }
  }]
}))

const alarmPriorityOption = computed(() => {
  const s = alarmStats.value
  const data = s?.by_priority ? [
    { value: s.by_priority.critical || 0, name: '严重' },
    { value: s.by_priority.high || 0, name: '高' },
    { value: s.by_priority.medium || 0, name: '中' },
    { value: s.by_priority.low || 0, name: '低' },
  ] : []
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, left: 'center' },
    color: ['#F56C6C', '#E6A23C', '#409EFF', '#909399'],
    series: [{
      name: '告警优先级',
      type: 'pie',
      radius: ['35%', '60%'],
      data,
      label: { formatter: '{b}: {c}' }
    }]
  }
})

onMounted(load)
</script>

<template>
  <div class="dashboard-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in summaryCards" :key="card.title">
        <el-card shadow="hover" class="summary-card">
          <div class="card-content">
            <div class="card-icon" :style="{ color: card.color, backgroundColor: card.bg }">
              <el-icon><component :is="card.icon" /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-value">{{ card.value }}</div>
              <div class="card-title">{{ card.title }}</div>
              <div class="card-trend" v-if="card.trend">{{ card.trend }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="mt-20">
      <!-- 设备状态分布 -->
      <el-col :span="8">
        <el-card shadow="hover" header="设备状态分布" :body-style="{ padding: '12px 16px' }">
          <div class="chart-placeholder" v-loading="loading">
            <VChart v-if="deviceStats" class="chart" :option="deviceStatusOption" autoresize />
            <el-empty v-else description="暂无数据" />
          </div>
        </el-card>
      </el-col>

      <!-- 设备健康度排行 -->
      <el-col :span="8">
        <el-card shadow="hover" header="设备健康度排行" :body-style="{ padding: '12px 16px' }">
          <div class="chart-placeholder" v-loading="loading">
            <VChart v-if="deviceHealthData.length" class="chart" :option="deviceHealthOption" autoresize />
            <el-empty v-else description="暂无数据" />
          </div>
        </el-card>
      </el-col>

      <!-- 告警优先级分布 -->
      <el-col :span="8">
        <el-card shadow="hover" header="告警优先级分布" :body-style="{ padding: '12px 16px' }">
          <div class="chart-placeholder" v-loading="loading">
            <VChart v-if="alarmStats" class="chart" :option="alarmPriorityOption" autoresize />
            <el-empty v-else description="暂无数据" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格区域 -->
    <el-row :gutter="20" class="mt-20">
      <!-- 最近告警 -->
      <el-col :span="12">
        <el-card shadow="hover" header="最近严重告警" :body-style="{ padding: '12px 12px' }">
          <el-table
            v-loading="loading"
            :data="recentAlarms"
            size="small"
            style="width: 100%"
            max-height="300"
          >
            <el-table-column prop="device_name" label="设备" min-width="100" />
            <el-table-column prop="sensor_type_name" label="传感器" min-width="100" />
            <el-table-column label="当前值" min-width="90">
              <template #default="{ row }">{{ row.current_value }} {{ row.unit }}</template>
            </el-table-column>
            <el-table-column prop="triggered_at" label="触发时间" min-width="150" />
          </el-table>
        </el-card>
      </el-col>

      <!-- 快捷操作 -->
      <el-col :span="12">
        <el-card shadow="hover" header="快捷操作" :body-style="{ padding: '20px' }">
          <div class="quick-actions">
            <el-button type="primary" :icon="Location" @click="$router.push('/devices')">
              查看设备
            </el-button>
            <el-button type="warning" :icon="Warning" @click="$router.push('/alarms')">
              处理告警
            </el-button>
            <el-button type="success" :icon="TrendCharts" @click="$router.push('/data/realtime')">
              实时监控
            </el-button>
            <el-button type="info" :icon="Timer" @click="$router.push('/reports')">
              数据报表
            </el-button>
          </div>

          <el-divider />

          <div class="system-status">
            <h4>系统状态</h4>
            <el-space direction="vertical" :size="8" style="width: 100%">
              <div class="status-item">
                <span>数据库连接</span>
                <el-tag type="success" size="small">正常</el-tag>
              </div>
              <div class="status-item">
                <span>MQTT服务</span>
                <el-tag type="success" size="small">运行中</el-tag>
              </div>
              <div class="status-item">
                <span>WebSocket服务</span>
                <el-tag type="success" size="small">在线</el-tag>
              </div>
              <div class="status-item">
                <span>数据采集</span>
                <el-tag type="success" size="small">活跃</el-tag>
              </div>
            </el-space>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.mt-20 {
  margin-top: 20px;
}

.summary-card {
  border: none;
  transition: transform 0.3s;
}

.summary-card:hover {
  transform: translateY(-4px);
}

.card-content {
  display: flex;
  align-items: center;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 16px;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.card-title {
  font-size: 14px;
  color: #909399;
}

.card-trend {
  font-size: 12px;
  color: #67C23A;
  margin-top: 4px;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f9fafc;
  border-radius: 4px;
}

.chart {
  width: 100%;
  height: 300px;
}

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.system-status h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-item:last-child {
  border-bottom: none;
}
</style>
