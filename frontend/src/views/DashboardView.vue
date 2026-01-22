<script setup>
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import { Monitor, Warning, CircleCheck, DataLine } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getDeviceStats } from '../api/devices'
import { getAlarmStats } from '../api/alarms'
import { listSensorData } from '../api/sensors'

const loading = ref(false)
const deviceStats = ref(null)
const alarmStats = ref(null)
const dataTotal = ref(0)

const summaryCards = computed(() => [
  {
    title: '总设备数',
    value: deviceStats.value?.total ?? '-',
    icon: Monitor,
    color: '#409EFF',
    bg: '#ecf5ff',
  },
  {
    title: '在线设备',
    value: deviceStats.value?.online ?? '-',
    icon: CircleCheck,
    color: '#67C23A',
    bg: '#f0f9eb',
  },
  {
    title: '待处理告警',
    value: alarmStats.value?.by_status?.pending ?? '-',
    icon: Warning,
    color: '#F56C6C',
    bg: '#fef0f0',
  },
  {
    title: '数据点',
    value: dataTotal.value || '-',
    icon: DataLine,
    color: '#909399',
    bg: '#f4f4f5',
  },
])

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
  } catch (e) {
    ElMessage.error(e?.message || '加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="dashboard-container">
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
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="16">
        <el-card shadow="hover" header="设备状态分布" :body-style="{ padding: '12px 16px' }">
          <div class="chart-placeholder" v-loading="loading">
            <VChart v-if="deviceStats" class="chart" :option="deviceStatusOption" autoresize />
            <el-empty v-else description="暂无数据" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" header="待处理严重告警" :body-style="{ padding: '12px 12px' }">
          <el-table
            v-loading="loading"
            :data="alarmStats?.critical_pending || []"
            size="small"
            style="width: 100%"
            height="320"
          >
            <el-table-column prop="device_name" label="设备" min-width="90" />
            <el-table-column prop="sensor_type_name" label="传感器" min-width="90" />
            <el-table-column label="当前值" min-width="90">
              <template #default="{ row }">{{ row.current_value }} {{ row.unit }}</template>
            </el-table-column>
            <el-table-column prop="triggered_at" label="时间" min-width="120" />
          </el-table>
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
</style>
