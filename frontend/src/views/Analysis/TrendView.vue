<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getTopics } from '../../api/topics'
import { getTrendAnalysis, getPlatformCompare, getInfluenceRanking } from '../../api/analysis'
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

// 趋势图表配置
const trendOption = computed(() => {
  const dates = trendData.value?.dates?.map(d => {
    const date = new Date(d)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }) || []
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
    const params = selectedTopic.value ? { topic: selectedTopic.value } : {}

    // 并行加载所有数据
    const [trend, platform, ranking] = await Promise.all([
      getTrendAnalysis(params),
      getPlatformCompare(params),
      getInfluenceRanking(params)
    ])

    // 处理趋势数据
    if (trend) {
      trendData.value = {
        dates: trend.dates || [],
        post_counts: trend.post_counts || [],
        sentiment_scores: trend.sentiment_scores || [],
        influence_scores: trend.influence_scores || []
      }
    }

    // 处理平台数据
    if (platform) {
      platformData.value = {
        platforms: platform.platforms || [],
        post_counts: platform.post_counts || [],
        sentiment_scores: platform.sentiment_scores || [],
        engagement_rates: platform.engagement_rates || []
      }
    }

    // 处理排行数据
    if (ranking) {
      rankingData.value = {
        top_posts: ranking.top_posts || [],
        top_authors: ranking.top_authors || []
      }
    }
  } catch (e) {
    console.error('加载失败:', e)
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
        <el-select v-model="selectedTopic" placeholder="选择话题" style="width: 200px; margin-right: 12px" @change="load">
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
          <el-table-column prop="influence_score" label="影响力" width="80">
            <template #default="{ row }">{{ row.influence_score?.toFixed(1) || 0 }}</template>
          </el-table-column>
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
</style>
