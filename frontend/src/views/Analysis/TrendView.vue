<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getTopics } from '../../api/topics'
import VChart from 'vue-echarts'

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

// 初始化时直接生成模拟数据
const initializeMockData = () => {
  // 生成过去7天的日期
  const dates = []
  const postCounts = []
  const sentimentScores = []
  const influenceScores = []

  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(`${date.getMonth() + 1}/${date.getDate()}`)
    postCounts.push(Math.floor(Math.random() * 500) + 100)
    sentimentScores.push(Math.random() * 2 - 1)
    influenceScores.push(Math.random() * 100)
  }

  trendData.value = {
    dates,
    post_counts: postCounts,
    sentiment_scores: sentimentScores,
    influence_scores: influenceScores
  }

  platformData.value = {
    platforms: ['微博', '微信', '抖音', '知乎', 'B站'],
    post_counts: [Math.floor(Math.random() * 1000) + 200, Math.floor(Math.random() * 500) + 100, Math.floor(Math.random() * 800) + 150, Math.floor(Math.random() * 300) + 50, Math.floor(Math.random() * 400) + 80],
    sentiment_scores: [Math.random(), Math.random(), Math.random(), Math.random(), Math.random()],
    engagement_rates: [Math.random() * 10 + 2, Math.random() * 5 + 1, Math.random() * 15 + 3, Math.random() * 8 + 2, Math.random() * 12 + 2]
  }

  rankingData.value = {
    top_posts: Array.from({ length: 10 }, (_, i) => ({
      content: `这是第 ${i + 1} 条热门帖子的内容摘要，展示了用户的观点和讨论...`,
      author: `用户${Math.floor(Math.random() * 10000)}`,
      influence_score: Math.random() * 100
    })),
    top_authors: Array.from({ length: 10 }, (_, i) => ({
      author: `KOL作者${i + 1}`,
      total_posts: Math.floor(Math.random() * 100) + 10,
      avg_influence: Math.random() * 100
    }))
  }
}

// 立即初始化数据
initializeMockData()

// 趋势图表配置
const trendOption = computed(() => {
  const dates = trendData.value?.dates || []
  const post_counts = trendData.value?.post_counts || []
  const sentiment_scores = trendData.value?.sentiment_scores || []
  const influence_scores = trendData.value?.influence_scores || []

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['帖子数', '情感分数', '影响力'] },
    xAxis: {
      type: 'category',
      data: dates,
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
        data: post_counts,
        smooth: true,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '情感分数',
        type: 'line',
        yAxisIndex: 1,
        data: sentiment_scores,
        smooth: true,
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '影响力',
        type: 'line',
        yAxisIndex: 1,
        data: influence_scores,
        smooth: true,
        itemStyle: { color: '#E6A23C' }
      }
    ]
  }
})

// 平台对比图表配置
const platformOption = computed(() => {
  const platforms = platformData.value?.platforms || []
  const post_counts = platformData.value?.post_counts || []

  return {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: platforms,
      axisLabel: { color: '#606266' }
    },
    yAxis: { type: 'value', axisLabel: { color: '#606266' } },
    series: [
      {
        name: '帖子数',
        type: 'bar',
        data: post_counts,
        itemStyle: { color: '#409EFF' }
      }
    ]
  }
})

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
    // 模拟数据生成
    await new Promise(resolve => setTimeout(resolve, 500))

    // 生成过去7天的日期
    const dates = []
    const postCounts = []
    const sentimentScores = []
    const influenceScores = []

    for (let i = 6; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      dates.push(`${date.getMonth() + 1}/${date.getDate()}`)
      postCounts.push(Math.floor(Math.random() * 500) + 100)
      sentimentScores.push(Math.random() * 2 - 1)
      influenceScores.push(Math.random() * 100)
    }

    trendData.value = {
      dates,
      post_counts: postCounts,
      sentiment_scores: sentimentScores,
      influence_scores: influenceScores
    }

    platformData.value = {
      platforms: ['微博', '微信', '抖音', '知乎', 'B站'],
      post_counts: [Math.floor(Math.random() * 1000) + 200, Math.floor(Math.random() * 500) + 100, Math.floor(Math.random() * 800) + 150, Math.floor(Math.random() * 300) + 50, Math.floor(Math.random() * 400) + 80],
      sentiment_scores: [Math.random(), Math.random(), Math.random(), Math.random(), Math.random()],
      engagement_rates: [Math.random() * 10 + 2, Math.random() * 5 + 1, Math.random() * 15 + 3, Math.random() * 8 + 2, Math.random() * 12 + 2]
    }

    rankingData.value = {
      top_posts: Array.from({ length: 10 }, (_, i) => ({
        content: `这是第 ${i + 1} 条热门帖子的内容摘要，展示了用户的观点和讨论...`,
        author: `用户${Math.floor(Math.random() * 10000)}`,
        influence_score: Math.random() * 100
      })),
      top_authors: Array.from({ length: 10 }, (_, i) => ({
        author: `KOL作者${i + 1}`,
        total_posts: Math.floor(Math.random() * 100) + 10,
        avg_influence: Math.random() * 100
      }))
    }
  } finally {
    loading.value = false
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
