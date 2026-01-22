<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listDevices, listSensorTypes } from '../../api/devices'
import { exportSensorData, getDeviceHistory, getLatestDeviceData, listSensorData } from '../../api/sensors'
import { downloadBlob } from '../../utils/download'
import { formatDateTime, toIsoString } from '../../utils/date'
import TimeSeriesChart from '../../components/TimeSeriesChart.vue'

const loading = ref(false)
const devices = ref([])
const sensorTypes = ref([])
const selectedDeviceId = ref('')
const latest = ref([])

const polling = ref(true)
const pollSeconds = ref(10)
let timer = null

const historyLoading = ref(false)
const historyPoints = ref([])
const selectedSensorCode = ref('')

const tableLoading = ref(false)
const tableRows = ref([])
const tablePage = reactive({ page: 1, page_size: 20, total: 0 })
const timeRange = ref([])

const sensorTypeByCode = computed(() => {
  const m = new Map()
  for (const s of sensorTypes.value) m.set(s.code, s)
  return m
})

const sensorOptions = computed(() =>
  latest.value.map((d) => ({
    label: `${d.sensor_type_name} (${d.sensor_type_code})`,
    value: d.sensor_type_code,
    unit: d.unit,
  }))
)

const currentUnit = computed(() => sensorTypeByCode.value.get(selectedSensorCode.value)?.unit || '')

function qualityTagType(q) {
  if (q === 'good') return 'success'
  if (q === 'uncertain') return 'warning'
  if (q === 'bad') return 'danger'
  return 'info'
}

async function loadDevices() {
  try {
    const res = await listDevices({ page: 1, page_size: 200 })
    devices.value = res?.items || []
    if (!selectedDeviceId.value && devices.value.length) {
      selectedDeviceId.value = devices.value[0].device_id
    }
  } catch (e) {
    ElMessage.error(e?.message || '加载设备列表失败')
  }
}

async function loadSensorTypes() {
  try {
    const res = await listSensorTypes({ page: 1, page_size: 200 })
    sensorTypes.value = res?.items || []
  } catch {
    sensorTypes.value = []
  }
}

async function loadLatest() {
  if (!selectedDeviceId.value) return
  loading.value = true
  try {
    const res = await getLatestDeviceData(selectedDeviceId.value)
    latest.value = res?.data || []
    if (!selectedSensorCode.value && latest.value.length) {
      selectedSensorCode.value = latest.value[0].sensor_type_code
    }
  } catch (e) {
    ElMessage.error(e?.message || '加载最新数据失败')
  } finally {
    loading.value = false
  }
}

async function loadHistory() {
  if (!selectedDeviceId.value) return
  historyLoading.value = true
  try {
    const res = await getDeviceHistory(selectedDeviceId.value, {
      sensor_type: selectedSensorCode.value || undefined,
      hours: 24,
    })
    historyPoints.value = res?.data || []
  } catch (e) {
    ElMessage.error(e?.message || '加载历史数据失败')
  } finally {
    historyLoading.value = false
  }
}

async function loadTable() {
  if (!selectedDeviceId.value) return
  tableLoading.value = true
  try {
    const params = {
      page: tablePage.page,
      page_size: tablePage.page_size,
      device_id: selectedDeviceId.value,
      sensor_type: selectedSensorCode.value || undefined,
    }
    if (timeRange.value?.length === 2) {
      params.start_time = toIsoString(timeRange.value[0])
      params.end_time = toIsoString(timeRange.value[1])
    }
    const res = await listSensorData(params)
    tableRows.value = res?.items || []
    tablePage.total = res?.total || 0
  } catch (e) {
    ElMessage.error(e?.message || '加载数据列表失败')
  } finally {
    tableLoading.value = false
  }
}

async function exportCsv() {
  if (!selectedDeviceId.value) return
  try {
    const params = {
      device_id: selectedDeviceId.value,
      sensor_type: selectedSensorCode.value || undefined,
      format: 'csv',
    }
    if (timeRange.value?.length === 2) {
      params.start_time = toIsoString(timeRange.value[0])
      params.end_time = toIsoString(timeRange.value[1])
    }
    const res = await exportSensorData(params)
    const filename = `sensor_data_${selectedDeviceId.value}_${selectedSensorCode.value || 'all'}.csv`
    downloadBlob(res.data, filename)
  } catch (e) {
    ElMessage.error(e?.message || '导出失败')
  }
}

function startTimer() {
  stopTimer()
  timer = window.setInterval(() => {
    if (!polling.value) return
    loadLatest()
  }, Math.max(2, Number(pollSeconds.value)) * 1000)
}

function stopTimer() {
  if (timer) window.clearInterval(timer)
  timer = null
}

watch([selectedDeviceId], async () => {
  selectedSensorCode.value = ''
  tablePage.page = 1
  await loadLatest()
  await loadHistory()
  await loadTable()
})

watch([selectedSensorCode], async () => {
  tablePage.page = 1
  await loadHistory()
  await loadTable()
})

watch([polling, pollSeconds], startTimer)

onMounted(async () => {
  await Promise.all([loadDevices(), loadSensorTypes()])
  await loadLatest()
  await loadHistory()
  await loadTable()
  startTimer()
})

onUnmounted(stopTimer)
</script>

<template>
  <el-card shadow="never" header="实时监控">
    <div class="toolbar">
      <div class="left">
        <el-select v-model="selectedDeviceId" placeholder="选择设备" filterable style="width: 260px">
          <el-option v-for="d in devices" :key="d.device_id" :label="`${d.name} (${d.device_id})`" :value="d.device_id" />
        </el-select>
        <el-select v-model="selectedSensorCode" placeholder="选择传感器" filterable clearable style="width: 260px">
          <el-option v-for="o in sensorOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </div>
      <div class="right">
        <el-date-picker
          v-model="timeRange"
          type="datetimerange"
          range-separator="到"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          style="width: 340px"
          @change="loadTable"
        />
        <el-button @click="exportCsv">导出CSV</el-button>
        <el-switch v-model="polling" inline-prompt active-text="轮询" inactive-text="暂停" />
        <el-input-number v-model="pollSeconds" :min="2" :max="60" :step="1" controls-position="right" />
      </div>
    </div>

    <el-row :gutter="12" class="cards">
      <el-col :span="6" v-for="item in latest" :key="item.sensor_type_code">
        <el-card shadow="hover" :body-style="{ padding: '12px' }">
          <div class="metric">
            <div class="metric-title">
              <span>{{ item.sensor_type_name }}</span>
              <el-tag size="small" :type="qualityTagType(item.quality)">{{ item.quality }}</el-tag>
            </div>
            <div class="metric-value">{{ item.value }} <span class="unit">{{ item.unit }}</span></div>
            <div class="metric-time">更新时间：{{ formatDateTime(item.timestamp) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="chart-card" :body-style="{ padding: '12px 16px' }">
      <template #header>
        <div class="chart-header">
          <span>最近24小时趋势</span>
          <el-button size="small" @click="loadHistory">刷新</el-button>
        </div>
      </template>
      <div v-loading="historyLoading">
        <TimeSeriesChart
          v-if="historyPoints.length"
          :title="selectedSensorCode ? selectedSensorCode : '全部传感器'"
          :unit="currentUnit"
          :points="historyPoints"
        />
        <el-empty v-else description="暂无历史数据" />
      </div>
    </el-card>

    <el-card shadow="never" class="table-card" :body-style="{ padding: '12px 16px' }">
      <template #header>
        <div class="chart-header">
          <span>数据列表</span>
          <el-button size="small" @click="loadTable">刷新</el-button>
        </div>
      </template>
      <el-table v-loading="tableLoading" :data="tableRows" size="small" style="width: 100%">
        <el-table-column prop="device_name" label="设备" min-width="120" />
        <el-table-column prop="sensor_type_name" label="传感器" min-width="120" />
        <el-table-column label="数值" width="120">
          <template #default="{ row }">{{ row.value }} {{ row.unit }}</template>
        </el-table-column>
        <el-table-column prop="quality" label="质量" width="110">
          <template #default="{ row }"><el-tag size="small" :type="qualityTagType(row.quality)">{{ row.quality }}</el-tag></template>
        </el-table-column>
        <el-table-column label="时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.timestamp) }}</template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          background
          layout="total, prev, pager, next, sizes"
          :total="tablePage.total"
          :current-page="tablePage.page"
          :page-size="tablePage.page_size"
          :page-sizes="[10, 20, 50, 100]"
          @update:current-page="
            (p) => {
              tablePage.page = p
              loadTable()
            }
          "
          @update:page-size="
            (s) => {
              tablePage.page_size = s
              tablePage.page = 1
              loadTable()
            }
          "
        />
      </div>
    </el-card>
  </el-card>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.left,
.right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.cards {
  margin-bottom: 12px;
}

.metric-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #606266;
  font-size: 13px;
}

.metric-value {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
  margin-top: 6px;
}

.unit {
  font-size: 12px;
  font-weight: 400;
  color: #909399;
  margin-left: 4px;
}

.metric-time {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

.chart-card,
.table-card {
  margin-top: 12px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
