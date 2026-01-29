<script setup>
import { ref, onMounted } from 'vue'
import { Warning, Refresh, View } from '@element-plus/icons-vue'
import { getTopics } from '../../api/topics'

const loading = ref(false)
const selectedTopic = ref('')
const topics = ref([])

const emergencyData = ref({
  active: [], // 活跃事件
  history: [], // 历史事件
  stats: {
    total: 0,
    active: 0,
    resolved: 0,
    falsePositive: 0,
  },
})

const severityLevels = {
  level_1: { label: '紧急', color: '#F56C6C', icon: '⚠️' },
  level_2: { label: '重要', color: '#E6A23C', icon: '⚡' },
  level_3: { label: '一般', color: '#409EFF', icon: 'ℹ️' },
}

const eventTypes = {
  volume: '数量突发',
  sentiment: '情感突发',
  speed: '速度突发',
  multi: '综合异常',
}

async function loadTopics() {
  try {
    const res = await getTopics({ page: 1, page_size: 100 })
    topics.value = res?.results || res?.items || []
    if (topics.value.length && !selectedTopic.value) {
      selectedTopic.value = topics.value[0].id
    }
  } catch (e) {
    console.error('加载话题失败:', e)
  }
}

async function loadEmergencyData() {
  loading.value = true
  try {
    // TODO: 调用真实API
    // const res = await detectEmergency({ topic: selectedTopic.value })
    // 模拟数据
    emergencyData.value = {
      active: Array.from({ length: 3 }, (_, i) => ({
        id: i + 1,
        topic: `测试话题${i + 1}`,
        eventType: ['volume', 'sentiment', 'speed', 'multi'][i % 4],
        severity: ['level_1', 'level_2', 'level_3'][i % 3],
        detectedAt: new Date().toLocaleString(),
        status: 'active',
        metrics: {
          postCount: Math.floor(Math.random() * 1000) + 500,
          sentimentChange: (Math.random() * 30 + 10).toFixed(1),
          hotness: Math.floor(Math.random() * 50) + 50,
        },
      })),
      history: Array.from({ length: 5 }, (_, i) => ({
        id: i + 10,
        topic: `历史事件${i + 1}`,
        eventType: 'volume',
        severity: 'level_2',
        detectedAt: new Date(Date.now() - (i + 1) * 3600000).toLocaleString(),
        status: ['resolved', 'false_positive'][i % 2],
      })),
      stats: {
        total: 23,
        active: 3,
        resolved: 18,
        falsePositive: 2,
      },
    }
  } catch (e) {
    console.error('加载突发事件数据失败:', e)
  } finally {
    loading.value = false
  }
}

function getSeverityInfo(level) {
  return severityLevels[level] || severityLevels.level_3
}

function getEventTypeName(type) {
  return eventTypes[type] || type
}

async function handleResolve(event) {
  // TODO: 调用API解决事件
  console.log('解决事件:', event)
}

async function handleMarkFalsePositive(event) {
  // TODO: 调用API标记误报
  console.log('标记误报:', event)
}

async function handleRefresh() {
  await loadEmergencyData()
}

onMounted(async () => {
  await loadTopics()
  await loadEmergencyData()
})
</script>

<template>
  <div class="emergency-view">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title">
            <el-icon><Warning /></el-icon>
            <span>突发事件检测</span>
          </div>
          <el-button :icon="Refresh" @click="handleRefresh" :loading="loading">刷新</el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filters">
        <el-form :inline="true">
          <el-form-item label="话题">
            <el-select v-model="selectedTopic" placeholder="选择话题" @change="loadEmergencyData">
              <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- Loading -->
      <div v-if="loading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="30"><Warning /></el-icon>
        <p style="margin-top: 10px;">加载中...</p>
      </div>

      <!-- 统计概览 -->
      <el-row :gutter="20" v-show="!loading">
        <el-col :span="6">
          <div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div class="stat-value">{{ emergencyData.stats.total }}</div>
            <div class="stat-label">总事件数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="stat-value">{{ emergencyData.stats.active }}</div>
            <div class="stat-label">活跃事件</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <div class="stat-value">{{ emergencyData.stats.resolved }}</div>
            <div class="stat-label">已解决</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <div class="stat-value">{{ emergencyData.stats.falsePositive }}</div>
            <div class="stat-label">误报</div>
          </div>
        </el-col>
      </el-row>

      <!-- 活跃突发事件 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover">
            <template #header>
              <span>活跃突发事件 ({{ emergencyData.value.active.length }})</span>
            </template>
            <el-table :data="emergencyData.value.active" size="small" row-class-name="emergency-row">
              <el-table-column label="级别" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.severity === 'level_1' ? 'danger' : row.severity === 'level_2' ? 'warning' : 'info'" size="large">
                    {{ getSeverityInfo(row.severity).icon }} {{ getSeverityInfo(row.severity).label }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="topic" label="话题" width="150" />
              <el-table-column label="事件类型" width="100">
                <template #default="{ row }">
                  <el-tag>{{ getEventTypeName(row.eventType) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="异常指标" width="300">
                <template #default="{ row }">
                  <div v-if="row.metrics">
                    <el-tag size="small" type="danger" v-if="row.metrics.postCount">
                      帖子数: {{ row.metrics.postCount }}
                    </el-tag>
                    <el-tag size="small" type="warning" v-if="row.metrics.sentimentChange">
                      情感变化: +{{ row.metrics.sentimentChange }}%
                    </el-tag>
                    <el-tag size="small" type="info" v-if="row.metrics.hotness">
                      热度: {{ row.metrics.hotness }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="detectedAt" label="检测时间" width="180" />
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button type="primary" link :icon="View" size="small">详情</el-button>
                  <el-button type="success" link size="small" @click="handleResolve(row)">解决</el-button>
                  <el-button type="info" link size="small" @click="handleMarkFalsePositive(row)">误报</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <!-- 历史事件 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="历史事件">
            <el-table :data="emergencyData.value.history" size="small">
              <el-table-column label="级别" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.severity === 'level_1' ? 'danger' : row.severity === 'level_2' ? 'warning' : 'info'">
                    {{ getSeverityInfo(row.severity).label }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="topic" label="话题" width="150" />
              <el-table-column label="事件类型" width="100">
                <template #default="{ row }">
                  <el-tag>{{ getEventTypeName(row.eventType) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="detectedAt" label="检测时间" width="180" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'resolved' ? 'success' : 'info'" size="small">
                    {{ row.status === 'resolved' ? '已解决' : '误报' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default>
                  <el-button type="primary" link size="small">查看</el-button>
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
.emergency-view {
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

.mt-20 {
  margin-top: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

:deep(.emergency-row) {
  background-color: #fef0f0;
}
</style>
