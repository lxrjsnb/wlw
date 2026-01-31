<script setup>
import { ref, computed, onMounted } from 'vue'
import { Compass, Refresh, TrendCharts } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { getTopics } from '../../api/topics'

const loading = ref(false)
const selectedTopic = ref('')
const topics = ref([])

const evolutionData = ref({
  currentStage: '',
  stageHistory: [],
  metrics: [],
  predictions: {},
})

const stageConfig = {
  latent: { label: '潜伏期', color: '#909399', icon: '🌱', desc: '少量帖子、情感中性、关注低' },
  germination: { label: '萌发期', color: '#409EFF', icon: '🌿', desc: '帖子增长>20%、出现KOL' },
  explosion: { label: '爆发期', color: '#F56C6C', icon: '🔥', desc: '帖子>均值×3、情感极化、跨平台' },
  diffusion: { label: '扩散期', color: '#E6A23C', icon: '📈', desc: '增长放缓、传播加深' },
  decline: { label: '衰退期', color: '#67C23A', icon: '📉', desc: '连续下降、热度降低' },
  death: { label: '消亡期', color: '#C0C4CC', icon: '💀', desc: '偶发帖子、基本无互动' },
}

// 初始化时直接生成模拟数据
const initializeMockData = () => {
  const stages = Object.keys(stageConfig)
  evolutionData.value = {
    currentStage: stages[2], // 模拟在爆发期
    stageHistory: stages.slice(0, 3).map((stage, i) => ({
      stage,
      startedAt: new Date(Date.now() - (3 - i) * 86400000).toLocaleDateString(),
      duration: i === 2 ? null : Math.floor(Math.random() * 48) + 24,
      peakHotness: Math.floor(Math.random() * 50) + 50,
      postCount: Math.floor(Math.random() * 1000) + 100,
    })),
    metrics: Array.from({ length: 7 }, (_, i) => ({
      date: `1/${i + 1}`,
      postCount: Math.floor(Math.random() * 500) + 100,
      hotness: Math.floor(Math.random() * 60) + 40,
      sentiment: Math.random() * 2 - 1,
    })),
    predictions: {
      nextStage: stages[3],
      duration: Math.floor(Math.random() * 48) + 24,
      confidence: Math.random() * 0.3 + 0.6,
    },
  }
}

// 立即初始化数据
initializeMockData()

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

async function loadEvolutionData() {
  loading.value = true
  try {
    // 模拟数据生成延迟
    await new Promise(resolve => setTimeout(resolve, 500))

    // TODO: 调用真实API
    // const res = await getCurrentStage(selectedTopic.value)
    // 模拟数据
    const stages = Object.keys(stageConfig)
    evolutionData.value = {
      currentStage: stages[2], // 模拟在爆发期
      stageHistory: stages.slice(0, 3).map((stage, i) => ({
        stage,
        startedAt: new Date(Date.now() - (3 - i) * 86400000).toLocaleDateString(),
        duration: i === 2 ? null : Math.floor(Math.random() * 48) + 24,
        peakHotness: Math.floor(Math.random() * 50) + 50,
        postCount: Math.floor(Math.random() * 1000) + 100,
      })),
      metrics: Array.from({ length: 7 }, (_, i) => ({
        date: `1/${i + 1}`,
        postCount: Math.floor(Math.random() * 500) + 100,
        hotness: Math.floor(Math.random() * 60) + 40,
        sentiment: Math.random() * 2 - 1,
      })),
      predictions: {
        nextStage: stages[3],
        duration: Math.floor(Math.random() * 48) + 24,
        confidence: Math.random() * 0.3 + 0.6,
      },
    }
  } catch (e) {
    console.error('加载演化数据失败:', e)
    // 确保数据有默认值
    evolutionData.value = {
      currentStage: 'latent',
      stageHistory: [],
      metrics: [],
      predictions: {
        nextStage: 'germination',
        duration: 24,
        confidence: '0.60',
      },
    }
  } finally {
    loading.value = false
  }
}

const currentStageInfo = computed(() => {
  if (!evolutionData.value) {
    return stageConfig.latent
  }
  return stageConfig[evolutionData.value.currentStage] || stageConfig.latent
})

const stageTimelineOption = computed(() => {
  // 直接返回固定的配置
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['1/25', '1/26', '1/27'],
    },
    yAxis: { type: 'value', name: '帖子数' },
    series: [{
      type: 'bar',
      data: [150, 200, 180],
      itemStyle: { color: '#409EFF' }
    }]
  }
})

const metricsOption = computed(() => {
  // 直接返回固定的配置
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, left: 'center' },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['1/25', '1/26', '1/27', '1/28', '1/29', '1/30', '1/31'],
    },
    yAxis: [
      { type: 'value', name: '帖子数', position: 'left' },
      { type: 'value', name: '热度', position: 'right' },
    ],
    series: [
      {
        name: '帖子数',
        type: 'bar',
        data: [120, 200, 150, 180, 220, 160, 140],
        itemStyle: { color: '#409EFF' },
      },
      {
        name: '热度',
        type: 'line',
        yAxisIndex: 1,
        data: [45, 52, 48, 55, 50, 47, 43],
        smooth: true,
        itemStyle: { color: '#E6A23C' },
      },
    ],
  }
})

async function handleRefresh() {
  await loadEvolutionData()
}

onMounted(async () => {
  await loadTopics()
  await loadEvolutionData()
})
</script>

<template>
  <div class="evolution-view">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title">
            <el-icon><Compass /></el-icon>
            <span>舆情演化分析</span>
          </div>
          <el-button :icon="Refresh" @click="handleRefresh" :loading="loading">刷新</el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filters">
        <el-form :inline="true">
          <el-form-item label="话题">
            <el-select v-model="selectedTopic" placeholder="选择话题" @change="loadEvolutionData">
              <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- Loading -->
      <div v-if="loading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="30"><Compass /></el-icon>
        <p style="margin-top: 10px;">加载中...</p>
      </div>

      <!-- 当前阶段展示 -->
      <el-row :gutter="20" v-show="!loading">
        <el-col :span="24">
          <div class="current-stage-banner" :style="{ borderLeftColor: currentStageInfo.color }">
            <div class="stage-icon">{{ currentStageInfo.icon }}</div>
            <div class="stage-info">
              <div class="stage-title">{{ currentStageInfo.label }}</div>
              <div class="stage-desc">{{ currentStageInfo.desc }}</div>
            </div>
            <div class="stage-prediction">
              <div class="prediction-label">预测下一阶段</div>
              <div class="prediction-value">
                {{ stageConfig[evolutionData.predictions.nextStage]?.label }}
              </div>
              <div class="prediction-confidence">
                置信度: {{ (evolutionData.predictions.confidence * 100).toFixed(0) }}%
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 演化时间线和指标 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="12">
          <el-card shadow="hover" header="演化阶段时间线">
            <div class="chart-container">
              <VChart class="chart" :option="stageTimelineOption" autoresize />
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" header="关键指标趋势">
            <div class="chart-container">
              <VChart class="chart" :option="metricsOption" autoresize />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 阶段历史记录 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="演化历史记录">
            <el-timeline>
              <el-timeline-item
                v-for="(record, index) in (evolutionData.value?.stageHistory || [])"
                :key="index"
                :timestamp="record.startedAt"
                placement="top"
                :color="stageConfig[record.stage]?.color"
              >
                <el-card>
                  <div class="history-item">
                    <el-tag :style="{ backgroundColor: stageConfig[record.stage]?.color, border: 'none', color: 'white' }" size="large">
                      {{ stageConfig[record.stage]?.icon }} {{ stageConfig[record.stage]?.label }}
                    </el-tag>
                    <div class="history-stats">
                      <span>持续时间: {{ record.duration }}h</span>
                      <el-divider direction="vertical" />
                      <span>峰值热度: {{ record.peakHotness }}</span>
                      <el-divider direction="vertical" />
                      <span>帖子数: {{ record.postCount }}</span>
                    </div>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>

      <!-- 阶段特征对比 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="各阶段特征对比">
            <el-table :data="Object.entries(stageConfig).map(([key, val]) => ({ key, ...val }))" size="small">
              <el-table-column label="阶段" width="100">
                <template #default="{ row }">
                  {{ row.icon }} {{ row.label }}
                </template>
              </el-table-column>
              <el-table-column prop="desc" label="特征描述" min-width="300" />
              <el-table-column label="典型指标" width="300">
                <template #default="{ row }">
                  <el-tag size="small" v-if="row.key === 'latent'">帖子 < 均值×1.2</el-tag>
                  <el-tag size="small" v-else-if="row.key === 'germination'">增长率 > 20%</el-tag>
                  <el-tag size="small" v-else-if="row.key === 'explosion'">帖子 > 均值×3</el-tag>
                  <el-tag size="small" v-else-if="row.key === 'diffusion'">增长放缓</el-tag>
                  <el-tag size="small" v-else-if="row.key === 'decline'">连续3h下降</el-tag>
                  <el-tag size="small" v-else>帖子 < 峰值×0.1</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="建议策略" width="200">
                <template #default="{ row }">
                  <span v-if="row.key === 'latent'">持续监测</span>
                  <span v-else-if="row.key === 'germination'">加强关注</span>
                  <span v-else-if="row.key === 'explosion'">快速响应</span>
                  <span v-else-if="row.key === 'diffusion'">跟踪分析</span>
                  <span v-else-if="row.key === 'decline'">总结报告</span>
                  <span v-else>归档处理</span>
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
.evolution-view {
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

.current-stage-banner {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-left: 6px solid;
  border-radius: 8px;
}

.stage-icon {
  font-size: 48px;
}

.stage-info {
  flex: 1;
}

.stage-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stage-desc {
  font-size: 14px;
  color: #606266;
}

.stage-prediction {
  text-align: center;
  padding: 16px;
  background: white;
  border-radius: 8px;
  min-width: 150px;
}

.prediction-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.prediction-value {
  font-size: 18px;
  font-weight: 600;
  color: #409EFF;
  margin-bottom: 4px;
}

.prediction-confidence {
  font-size: 12px;
  color: #67C23A;
}

.chart-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart {
  width: 100%;
  height: 100%;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.history-stats {
  font-size: 14px;
  color: #606266;
}
</style>
