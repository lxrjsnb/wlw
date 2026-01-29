<script setup>
import { ref, computed, onMounted } from 'vue'
import { TrendCharts, Calendar, ChatDotRound, Bell, Download } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { getTopics } from '../../api/topics'
import { getPosts } from '../../api/posts'
import { getAlertRecords } from '../../api/alerts'

const loading = ref(false)
const dateRange = ref([])

// 默认选择最近30天
const defaultStartDate = new Date()
defaultStartDate.setDate(defaultStartDate.getDate() - 30)
dateRange.value = [defaultStartDate, new Date()]

const selectedTopic = ref('')
const topics = ref([])

const reportData = ref({
  totalPosts: 0,
  positivePosts: 0,
  negativePosts: 0,
  neutralPosts: 0,
  totalAlerts: 0,
  avgSentiment: 0,
  platformDistribution: [],
  sentimentTrend: [],
  topKeywords: [],
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

async function loadReportData() {
  loading.value = true
  try {
    // 并行获取数据
    const [postsRes, alertsRes] = await Promise.all([
      getPosts({
        topic: selectedTopic.value,
        page: 1,
        page_size: 1000,
      }).catch(e => {
        console.error('加载帖子失败:', e)
        return { results: [], items: [], count: 0, total: 0 }
      }),
      getAlertRecords({
        page: 1,
        page_size: 100,
      }).catch(e => {
        console.error('加载预警失败:', e)
        return { results: [], items: [], count: 0, total: 0 }
      }),
    ])

    const posts = postsRes.results || postsRes.items || []
    const alerts = alertsRes.results || alertsRes.items || []

    // 统计数据
    const positive = posts.filter(p => p.sentiment === 'positive').length
    const negative = posts.filter(p => p.sentiment === 'negative').length
    const neutral = posts.filter(p => p.sentiment === 'neutral').length

    // 计算平均情感得分
    const sentimentScores = posts.filter(p => p.sentiment_score !== null).map(p => p.sentiment_score || 0)
    const avgScore = sentimentScores.length > 0
      ? sentimentScores.reduce((a, b) => a + b, 0) / sentimentScores.length
      : 0

    // 平台分布
    const platformCounts = {}
    posts.forEach(p => {
      const platform = p.platform || 'unknown'
      platformCounts[platform] = (platformCounts[platform] || 0) + 1
    })

    // 情感趋势（按天统计）
    const trendMap = {}
    posts.forEach(p => {
      if (p.published_at) {
        const date = new Date(p.published_at).toLocaleDateString('zh-CN')
        if (!trendMap[date]) {
          trendMap[date] = { positive: 0, negative: 0, neutral: 0 }
        }
        if (trendMap[date][p.sentiment] !== undefined) {
          trendMap[date][p.sentiment]++
        }
      }
    })

    // Top关键词（简单模拟）
    const keywordCounts = {}
    posts.forEach(p => {
      if (p.content) {
        const words = p.content.split(/\s+/).filter(w => w.length > 1)
        words.forEach(w => {
          keywordCounts[w] = (keywordCounts[w] || 0) + 1
        })
      }
    })
    const topKeywords = Object.entries(keywordCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([word, count]) => ({ word, count }))

    reportData.value = {
      totalPosts: postsRes.count || postsRes.total || 0,
      positivePosts: positive,
      negativePosts: negative,
      neutralPosts: neutral,
      totalAlerts: alertsRes.count || alertsRes.total || 0,
      avgSentiment: avgScore,
      platformDistribution: Object.entries(platformCounts).map(([name, value]) => ({ name, value })),
      sentimentTrend: Object.entries(trendMap)
        .map(([date, data]) => ({ date, ...data }))
        .sort((a, b) => new Date(a.date) - new Date(b.date)),
      topKeywords,
    }
  } catch (e) {
    console.error('加载报表数据失败:', e)
  } finally {
    loading.value = false
  }
}

// 情感分布饼图配置
const sentimentPieOption = computed(() => {
  const { positivePosts, negativePosts, neutralPosts } = reportData.value
  const total = positivePosts + negativePosts + neutralPosts
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, left: 'center' },
    color: ['#67C23A', '#F56C6C', '#909399'],
    series: [{
      name: '情感分布',
      type: 'pie',
      radius: ['40%', '65%'],
      data: [
        { value: positivePosts, name: '正面' },
        { value: negativePosts, name: '负面' },
        { value: neutralPosts, name: '中性' },
      ],
      label: {
        formatter: params => `${params.name}: ${params.value} (${total > 0 ? ((params.value / total) * 100).toFixed(1) : 0}%)`
      }
    }]
  }
})

// 情感趋势图配置
const sentimentTrendOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
  },
  legend: { bottom: 0, left: 'center' },
  grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
  xAxis: {
    type: 'category',
    data: reportData.value.sentimentTrend.map(d => d.date),
    axisLabel: { rotate: 45 }
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '正面',
      type: 'line',
      data: reportData.value.sentimentTrend.map(d => d.positive),
      smooth: true,
      itemStyle: { color: '#67C23A' },
    },
    {
      name: '负面',
      type: 'line',
      data: reportData.value.sentimentTrend.map(d => d.negative),
      smooth: true,
      itemStyle: { color: '#F56C6C' },
    },
    {
      name: '中性',
      type: 'line',
      data: reportData.value.sentimentTrend.map(d => d.neutral),
      smooth: true,
      itemStyle: { color: '#909399' },
    },
  ],
}))

// 平台分布图配置
const platformOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, left: 'center' },
  series: [{
    type: 'pie',
    radius: '60%',
    data: reportData.value.platformDistribution,
  }]
}))

// 关键词柱状图
const keywordsOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
  xAxis: {
    type: 'value',
  },
  yAxis: {
    type: 'category',
    data: reportData.value.topKeywords.map(k => k.word).reverse(),
  },
  series: [{
    type: 'bar',
    data: reportData.value.topKeywords.map(k => k.count).reverse(),
    itemStyle: { color: '#409EFF' },
  }],
}))

async function exportReport() {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    // TODO: 实现真实的导出功能
    console.log('导出报表:', reportData.value)
  } catch (e) {
    console.error('导出失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadTopics()
  await loadReportData()
})
</script>

<template>
  <div class="data-report">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title">
            <el-icon><TrendCharts /></el-icon>
            <span>舆情数据报表</span>
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
          <el-form-item label="话题">
            <el-select v-model="selectedTopic" placeholder="选择话题" @change="loadReportData">
              <el-option
                v-for="t in topics"
                :key="t.id"
                :label="t.name"
                :value="t.id"
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
              @change="loadReportData"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadReportData" :loading="loading">查询</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Loading提示 -->
      <div v-if="loading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="30"><TrendCharts /></el-icon>
        <p style="margin-top: 10px;">加载中...</p>
      </div>

      <!-- 统计概览 -->
      <div class="statistics-overview" v-show="!loading">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #ecf5ff; color: #409EFF">
                <el-icon><ChatDotRound /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">帖子总数</div>
                <div class="stat-value">{{ reportData.totalPosts.toLocaleString() }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #f0f9eb; color: #67C23A">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">正面情感</div>
                <div class="stat-value">{{ reportData.positivePosts.toLocaleString() }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #fef0f0; color: #F56C6C">
                <el-icon><Bell /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">预警数量</div>
                <div class="stat-value">{{ reportData.totalAlerts.toLocaleString() }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: #f4f4f5; color: #909399">
                <el-icon><Calendar /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-label">平均情感得分</div>
                <div class="stat-value">{{ reportData.avgSentiment.toFixed(2) }}</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 图表区域 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="12">
          <el-card shadow="hover" header="情感分布">
            <div class="chart-container">
              <VChart
                v-if="reportData.totalPosts > 0"
                class="chart"
                :option="sentimentPieOption"
                autoresize
              />
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" header="平台分布">
            <div class="chart-container">
              <VChart
                v-if="reportData.platformDistribution.length > 0"
                class="chart"
                :option="platformOption"
                autoresize
              />
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 趋势图 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="情感趋势">
            <div class="chart-container-large">
              <VChart
                v-if="reportData.sentimentTrend.length > 0"
                class="chart-large"
                :option="sentimentTrendOption"
                autoresize
              />
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 关键词 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="热门关键词">
            <div class="chart-container-large">
              <VChart
                v-if="reportData.topKeywords.length > 0"
                class="chart-large"
                :option="keywordsOption"
                autoresize
              />
              <el-empty v-else description="暂无数据" />
            </div>
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

.chart-container-large {
  height: 400px;
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
