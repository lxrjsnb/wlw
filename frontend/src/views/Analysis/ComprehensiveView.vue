<script setup>
import { ref, onMounted } from 'vue'
import { Refresh, TrendCharts, User, Warning, Share } from '@element-plus/icons-vue'
import { getTopics } from '../../api/topics'
import {
  getRealtimeHotness,
  getHotnessTrend,
  getKOLRanking,
  detectEmergency,
  getEmergencyHistory,
  getPropagationPaths,
  getKeyNodes,
  getCurrentStage,
  getEvolutionHistory
} from '../../api/analysis'

const loading = ref(false)
const topics = ref([])
const selectedTopic = ref('')

// 热度数据
const hotnessData = ref({
  realtime: [],
  trend: []
})

// KOL数据
const kolData = ref({
  ranking: [],
  summary: {}
})

// 突发事件数据
const emergencyData = ref({
  active: [],
  history: []
})

// 传播数据
const propagationData = ref({
  paths: [],
  keyNodes: []
})

// 演化数据
const evolutionData = ref({
  currentStage: '',
  history: []
})

// 核心指标卡片
const summaryCards = ref([
  { title: '当前热度', value: 0, icon: TrendCharts, color: '#409EFF' },
  { title: '活跃KOL', value: 0, icon: User, color: '#67C23A' },
  { title: '突发事件', value: 0, icon: Warning, color: '#F56C6C' },
  { title: '传播层级', value: 0, icon: Share, color: '#E6A23C' }
])

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

async function load() {
  loading.value = true
  try {
    const params = selectedTopic.value ? { topic: selectedTopic.value } : {}

    // 并行加载所有数据
    const [hotness, kol, emergency, propagation, evolution] = await Promise.all([
      // 热度分析
      Promise.all([
        getRealtimeHotness(params).catch(() => ({ results: [] })),
        getHotnessTrend(params).catch(() => ({ trend: [] }))
      ]),
      // KOL分析
      getKOLRanking(params).catch(() => ({ ranking: [] })),
      // 突发事件
      Promise.all([
        detectEmergency(params).catch(() => ({ results: [] })),
        getEmergencyHistory(params).catch(() => ({ results: [] }))
      ]),
      // 传播分析
      Promise.all([
        getPropagationPaths(params).catch(() => ({ paths: [] })),
        getKeyNodes(params).catch(() => ({ nodes: [] }))
      ]),
      // 演化分析
      Promise.all([
        getCurrentStage(selectedTopic.value).catch(() => ({ stage: 'unknown' })),
        getEvolutionHistory(selectedTopic.value).catch(() => ({ history: [] }))
      ])
    ])

    // 处理热度数据
    hotnessData.value = {
      realtime: hotness[0]?.results || [],
      trend: hotness[1]?.trend || []
    }

    // 处理KOL数据
    kolData.value = {
      ranking: kol?.ranking || [],
      summary: kol?.summary || {}
    }

    // 处理突发事件数据
    emergencyData.value = {
      active: emergency[0]?.results || [],
      history: emergency[1]?.results || []
    }

    // 处理传播数据
    propagationData.value = {
      paths: propagation[0]?.paths || [],
      keyNodes: propagation[1]?.nodes || []
    }

    // 处理演化数据
    evolutionData.value = {
      currentStage: evolution[0]?.stage || '',
      history: evolution[1]?.history || []
    }

    // 更新核心指标卡片
    summaryCards.value = [
      {
        title: '当前热度',
        value: hotnessData.value.realtime[0]?.score || 0,
        icon: TrendCharts,
        color: '#409EFF'
      },
      {
        title: '活跃KOL',
        value: kolData.value.ranking.length || 0,
        icon: User,
        color: '#67C23A'
      },
      {
        title: '突发事件',
        value: emergencyData.value.active.length || 0,
        icon: Warning,
        color: '#F56C6C'
      },
      {
        title: '传播层级',
        value: propagationData.value.paths.length || 0,
        icon: Share,
        color: '#E6A23C'
      }
    ]
  } catch (e) {
    console.error('加载失败:', e)
  } finally {
    loading.value = false
  }
}

// 获取优先级样式
function getPriorityClass(priority) {
  const classes = {
    critical: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'info'
  }
  return classes[priority] || 'info'
}

// 获取阶段标签
function getStageLabel(stage) {
  const labels = {
   潜伏: '潜伏期',
    爆发: '爆发期',
    扩散: '扩散期',
    衰退: '衰退期',
    消亡: '消亡期'
  }
  return labels[stage] || stage
}

onMounted(() => {
  loadTopics()
  load()
})
</script>

<template>
  <div class="page-container grid-bg">
    <div class="page-header">
      <div>
        <h1 class="page-title">综合分析</h1>
        <p class="page-subtitle">热度、KOL、突发事件、传播与演化综合分析</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedTopic" placeholder="选择话题" style="width: 200px; margin-right: 12px" @change="load">
          <el-option label="全部话题" value="" />
          <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="content-grid content-grid-4 mb-lg">
      <div v-for="card in summaryCards" :key="card.title" class="metric-card">
        <div class="metric-icon" :style="{ backgroundColor: card.color }">
          <el-icon :size="24"><component :is="card.icon" /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-label">{{ card.title }}</div>
          <div class="metric-value">{{ card.value }}</div>
        </div>
      </div>
    </div>

    <div class="content-grid content-grid-2 mb-lg">
      <!-- 热度排行榜 -->
      <div class="card">
        <div class="card-header">
          <span>热度排行榜</span>
        </div>
        <el-table :data="hotnessData.realtime.slice(0, 10)" size="small" v-loading="loading" max-height="300">
          <el-table-column type="index" label="排名" width="60" />
          <el-table-column prop="content" label="内容" min-width="150" show-overflow-tooltip />
          <el-table-column prop="author" label="作者" width="100" />
          <el-table-column prop="score" label="热度值" width="80">
            <template #default="{ row }">{{ row.score?.toFixed(0) || 0 }}</template>
          </el-table-column>
        </el-table>
      </div>

      <!-- KOL排行榜 -->
      <div class="card">
        <div class="card-header">
          <span>KOL排行</span>
        </div>
        <el-table :data="kolData.ranking.slice(0, 10)" size="small" v-loading="loading" max-height="300">
          <el-table-column type="index" label="排名" width="60" />
          <el-table-column prop="author" label="KOL" width="120" />
          <el-table-column prop="total_posts" label="帖子数" width="80" />
          <el-table-column prop="avg_influence" label="影响力" width="80">
            <template #default="{ row }">{{ row.avg_influence?.toFixed(1) || 0 }}</template>
          </el-table-column>
          <el-table-column prop="followers" label="粉丝数" width="80">
            <template #default="{ row }">{{ row.followers || 0 }}</template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div class="content-grid content-grid-2 mb-lg">
      <!-- 突发事件列表 -->
      <div class="card">
        <div class="card-header">
          <span>突发事件列表</span>
        </div>
        <el-table :data="emergencyData.active.slice(0, 10)" size="small" v-loading="loading" max-height="300">
          <el-table-column prop="detected_at" label="时间" width="100">
            <template #default="{ row }">
              {{ new Date(row.detected_at).toLocaleDateString('zh-CN') }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="getPriorityClass(row.severity)" size="small">
                {{ row.severity }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80" />
        </el-table>
      </div>

      <!-- 传播关键节点 -->
      <div class="card">
        <div class="card-header">
          <span>传播关键节点</span>
        </div>
        <el-table :data="propagationData.keyNodes.slice(0, 10)" size="small" v-loading="loading" max-height="300">
          <el-table-column prop="author" label="节点" width="120" />
          <el-table-column prop="role" label="角色" width="100" />
          <el-table-column prop="reach" label="触达数" width="80" />
          <el-table-column prop="influence_score" label="影响力" width="80">
            <template #default="{ row }">{{ row.influence_score?.toFixed(1) || 0 }}</template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 舆情演化阶段 -->
    <div class="card">
      <div class="card-header">
        <span>舆情演化阶段</span>
      </div>
      <el-table :data="evolutionData.history" size="small" v-loading="loading">
        <el-table-column prop="stage" label="阶段" width="100">
          <template #default="{ row }">{{ getStageLabel(row.stage) }}</template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="120">
          <template #default="{ row }">
            {{ new Date(row.start_time).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column prop="duration_hours" label="持续时长(小时)" width="120" />
        <el-table-column prop="post_count" label="帖子数" width="100" />
        <el-table-column prop="peak_influence" label="峰值影响力" width="120" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.metric-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.metric-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.metric-content {
  flex: 1;
}

.metric-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.mb-lg {
  margin-bottom: 20px;
}

.content-grid {
  display: grid;
  gap: 20px;
}

.content-grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.content-grid-4 {
  grid-template-columns: repeat(4, 1fr);
}

@media (max-width: 1200px) {
  .content-grid-4 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .content-grid-2,
  .content-grid-4 {
    grid-template-columns: 1fr;
  }
}
</style>
