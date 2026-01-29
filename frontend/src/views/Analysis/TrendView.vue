<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getTrendAnalysis, getPlatformCompare, getInfluenceRanking } from '../../api/analysis'
import { getActiveTopics } from '../../api/topics'
import VChart from 'vue-echarts'
import * as echarts from 'echarts'

const loading = ref(false)
const topics = ref([])
const selectedTopic = ref('')

const trendData = ref({
  dates: [],
  post_counts: [],
  sentiment_scores: [],
  influence_scores: []
})

const platformData = ref({
  platforms: [],
  post_counts: [],
  sentiment_scores: [],
  engagement_rates: []
})

const rankingData = ref({
  top_posts: [],
  top_authors: []
})

// 趋势图表配置
const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['帖子数', '情感分数', '影响力'] },
  xAxis: {
    type: 'category',
    data: trendData.value.dates,
    axisLabel: { color: '#606266' }
  },
  yAxis: [
    { type: 'value', name: '帖子数', position: 'left' },
    { type: 'value', name: '分数', position: 'right' }
  ],
  series: [
    {
      name: '帖子数',
      type: 'line',
      data: trendData.value.post_counts,
      smooth: true,
      itemStyle: { color: '#409EFF' }
    },
    {
      name: '情感分数',
      type: 'line',
      yAxisIndex: 1,
      data: trendData.value.sentiment_scores,
      smooth: true,
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '影响力',
      type: 'line',
      yAxisIndex: 1,
      data: trendData.value.influence_scores,
      smooth: true,
      itemStyle: { color: '#E6A23C' }
    }
  ]
}))

// 平台对比图表配置
const platformOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: platformData.value.platforms,
    axisLabel: { color: '#606266' }
  },
  yAxis: { type: 'value', axisLabel: { color: '#606266' } },
  series: [
    {
      name: '帖子数',
      type: 'bar',
      data: platformData.value.post_counts,
      itemStyle: { color: '#409EFF' }
    }
  ]
}))

async function load() {
  loading.value = true
  try {
    const params = selectedTopic.value ? { topic_id: selectedTopic.value } : {}

    const [trend, platform, ranking] = await Promise.all([
      getTrendAnalysis(params),
      getPlatformCompare(params),
      getInfluenceRanking(params)
    ])

    trendData.value = trend
    platformData.value = platform
    rankingData.value = ranking

  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadTopics() {
  try {
    const data = await getActiveTopics()
    topics.value = data.results || data
  } catch (e) {
    console.error(e)
  }
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
        <h1 class="page-title">趋势分析</h1>
        <p class="page-subtitle">分析帖子的数量、情感和影响力趋势</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedTopic" placeholder="选择话题" style="width: 200px; margin-right: 12px">
          <el-option label="全部话题" value="" />
          <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <!-- 趋势图表 -->
    <div class="chart-container mb-lg">
      <div class="chart-header">
        <span class="chart-title">7日趋势</span>
      </div>
      <div class="chart-body">
        <VChart :option="trendOption" autoresize v-loading="loading" />
      </div>
    </div>

    <div class="content-grid content-grid-2">
      <!-- 平台对比 -->
      <div class="chart-container">
        <div class="chart-header">
          <span class="chart-title">平台对比</span>
        </div>
        <div class="chart-body">
          <VChart :option="platformOption" autoresize v-loading="loading" />
        </div>
      </div>

      <!-- 热门帖子 -->
      <div class="card">
        <div class="card-header">
          <span>热门帖子</span>
        </div>
        <el-table :data="rankingData.top_posts?.slice(0, 5)" size="small" v-loading="loading" max-height="280">
          <el-table-column prop="content" label="内容" min-width="150" show-overflow-tooltip />
          <el-table-column prop="author" label="作者" width="100" />
          <el-table-column prop="influence_score" label="影响力" width="80" />
        </el-table>
      </div>
    </div>

    <!-- 热门作者 -->
    <div class="card">
      <div class="card-header">
        <span>热门作者</span>
      </div>
      <el-table :data="rankingData.top_authors?.slice(0, 10)" size="small" v-loading="loading">
        <el-table-column prop="author" label="作者" width="150" />
        <el-table-column prop="total_posts" label="帖子数" width="100" />
        <el-table-column prop="avg_influence" label="平均影响力" width="120">
          <template #default="{ row }">{{ row.avg_influence?.toFixed(1) || 0 }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
}
</style>
