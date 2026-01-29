<script setup>
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import * as echarts from 'echarts'
import { ChatDotRound, Document, Warning, TrendCharts, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 模拟数据API（后续替换为真实API）
const loading = ref(false)
const lastUpdateTime = ref(new Date().toLocaleString('zh-CN'))

// 话题统计
const topicStats = ref({
  total_topics: 12,
  active_topics: 8,
  paused_topics: 3,
  archived_topics: 1
})

// 帖子统计
const postStats = ref({
  total_posts: 15680,
  today_posts: 1243,
  positive_count: 5420,
  neutral_count: 7230,
  negative_count: 3030,
  avg_sentiment_score: 0.12,
  avg_influence_score: 342.5
})

// 预警统计
const alertStats = ref({
  total_rules: 15,
  active_rules: 12,
  pending_records: 5,
  today_triggered: 18
})

// 热门话题
const hotTopics = ref([
  { id: 1, name: '人工智能发展', post_count: 4520, sentiment_score: 0.35 },
  { id: 2, name: '新能源汽车', post_count: 3890, sentiment_score: 0.42 },
  { id: 3, name: '教育改革', post_count: 2670, sentiment_score: -0.12 },
  { id: 4, name: '医疗健康', post_count: 1980, sentiment_score: 0.28 },
  { id: 5, name: '环保政策', post_count: 1420, sentiment_score: 0.51 }
])

// 最新预警
const recentAlerts = ref([
  { id: 1, topic_name: '教育改革', rule_type: '负面率告警', status: 'pending', triggered_at: '10:30' },
  { id: 2, topic_name: '环保政策', rule_type: '数量告警', status: 'pending', triggered_at: '09:45' },
  { id: 3, topic_name: '人工智能发展', rule_type: '影响力告警', status: 'acknowledged', triggered_at: '08:20' },
  { id: 4, topic_name: '医疗健康', rule_type: '情感告警', status: 'resolved', triggered_at: '07:15' },
  { id: 5, topic_name: '新能源汽车', rule_type: '数量告警', status: 'pending', triggered_at: '06:50' }
])

// 统计卡片配置
const summaryCards = computed(() => [
  {
    title: '监控话题',
    value: topicStats.value.active_topics,
    total: topicStats.value.total_topics,
    icon: ChatDotRound,
    color: '#409EFF',
    trend: `活跃 ${topicStats.value.active_topics}/${topicStats.value.total_topics}`
  },
  {
    title: '今日帖子',
    value: postStats.value.today_posts,
    total: postStats.value.total_posts,
    icon: Document,
    color: '#67C23A',
    trend: `总计 ${formatNumber(postStats.value.total_posts)}`
  },
  {
    title: '待处理预警',
    value: alertStats.value.pending_records,
    total: alertStats.value.today_triggered,
    icon: Warning,
    color: '#E6A23C',
    trend: `今日新增 ${alertStats.value.today_triggered}`
  },
  {
    title: '平均情感分',
    value: postStats.value.avg_sentiment_score.toFixed(2),
    total: 100,
    icon: TrendCharts,
    color: '#F56C6C',
    trend: getSentimentLabel(postStats.value.avg_sentiment_score)
  }
])

function formatNumber(num) {
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

function getSentimentLabel(score) {
  if (score > 0.3) return '正面'
  if (score < -0.3) return '负面'
  return '中性'
}

function getSentimentClass(score) {
  if (score > 0.3) return 'positive'
  if (score < -0.3) return 'negative'
  return 'neutral'
}

// 情感分布饼图
const sentimentDistributionOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left',
    data: ['正面', '中性', '负面']
  },
  series: [
    {
      name: '情感分布',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['60%', '50%'],
      data: [
        { value: postStats.value.positive_count, name: '正面', itemStyle: { color: '#67C23A' } },
        { value: postStats.value.neutral_count, name: '中性', itemStyle: { color: '#909399' } },
        { value: postStats.value.negative_count, name: '负面', itemStyle: { color: '#F56C6C' } }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        show: true,
        formatter: '{b}: {d}%'
      }
    }
  ]
}))

// 平台分布柱状图
const platformDistributionOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'value',
    axisLabel: {
      color: '#606266'
    },
    splitLine: {
      lineStyle: {
        color: '#EBEEF5'
      }
    }
  },
  yAxis: {
    type: 'category',
    data: ['微博', '微信', '抖音', '知乎', '小红书'],
    axisLabel: {
      color: '#606266'
    }
  },
  series: [
    {
      name: '帖子数量',
      type: 'bar',
      data: [
        { value: 4520, itemStyle: { color: '#ff8200' } },
        { value: 3890, itemStyle: { color: '#07c160' } },
        { value: 5670, itemStyle: { color: '#000000' } },
        { value: 2340, itemStyle: { color: '#0084ff' } },
        { value: 1890, itemStyle: { color: '#ff2442' } }
      ],
      itemStyle: {
        borderRadius: [0, 4, 4, 0]
      },
      label: {
        show: true,
        position: 'right',
        color: '#606266'
      }
    }
  ]
}))

// 7日趋势折线图
const trendOption = computed(() => ({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['帖子数量', '情感分数']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    axisLabel: {
      color: '#606266'
    }
  },
  yAxis: [
    {
      type: 'value',
      name: '帖子数',
      position: 'left',
      axisLabel: {
        color: '#606266'
      },
      splitLine: {
        lineStyle: {
          color: '#EBEEF5'
        }
      }
    },
    {
      type: 'value',
      name: '情感分',
      position: 'right',
      axisLabel: {
        color: '#606266'
      },
      splitLine: {
        show: false
      }
    }
  ],
  series: [
    {
      name: '帖子数量',
      type: 'line',
      data: [820, 932, 901, 934, 1290, 1330, 1243],
      smooth: true,
      itemStyle: {
        color: '#409EFF'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      }
    },
    {
      name: '情感分数',
      type: 'line',
      yAxisIndex: 1,
      data: [0.15, 0.12, 0.18, 0.08, 0.22, 0.25, 0.12],
      smooth: true,
      itemStyle: {
        color: '#67C23A'
      }
    }
  ]
}))

async function load() {
  loading.value = true
  try {
    // TODO: 调用真实API
    // const [ts, ps, als] = await Promise.all([
    //   getTopicStats(),
    //   getPostStats(),
    //   getAlertStats()
    // ])

    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 500))

    lastUpdateTime.value = new Date().toLocaleString('zh-CN')
  } catch (e) {
    ElMessage.error(e?.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

function refresh() {
  load()
}

const getStatusClass = (status) => {
  const classes = {
    pending: 'status-badge pending',
    acknowledged: 'status-badge acknowledged',
    resolved: 'status-badge resolved'
  }
  return classes[status] || ''
}

const getStatusText = (status) => {
  const texts = {
    pending: '待处理',
    acknowledged: '已确认',
    resolved: '已解决'
  }
  return texts[status] || status
}

onMounted(load)
</script>

<template>
  <div class="page-container grid-bg">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">舆情总览</h1>
        <p class="page-subtitle">社交媒体舆情监控与分析平台</p>
      </div>
      <div class="header-actions">
        <span class="update-time">更新时间: {{ lastUpdateTime }}</span>
        <el-button :icon="Refresh" @click="refresh" :loading="loading">刷新</el-button>
      </div>
    </div>

    <!-- 统计卡片区域 -->
    <div class="content-grid content-grid-4 mb-lg">
      <div
        v-for="card in summaryCards"
        :key="card.title"
        class="metric-card"
      >
        <div class="metric-icon" :style="{ backgroundColor: card.color }">
          <el-icon :size="24"><component :is="card.icon" /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-label">{{ card.title }}</div>
          <div class="metric-value">{{ card.value }}</div>
          <div class="metric-trend">{{ card.trend }}</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="content-grid content-grid-3 mb-lg">
      <!-- 情感分布饼图 -->
      <div class="chart-container">
        <div class="chart-header">
          <span class="chart-title">情感分布</span>
        </div>
        <div class="chart-body">
          <VChart :option="sentimentDistributionOption" autoresize v-loading="loading" />
        </div>
      </div>

      <!-- 平台分布柱状图 -->
      <div class="chart-container">
        <div class="chart-header">
          <span class="chart-title">平台分布</span>
        </div>
        <div class="chart-body">
          <VChart :option="platformDistributionOption" autoresize v-loading="loading" />
        </div>
      </div>

      <!-- 7日趋势折线图 -->
      <div class="chart-container">
        <div class="chart-header">
          <span class="chart-title">7日趋势</span>
        </div>
        <div class="chart-body">
          <VChart :option="trendOption" autoresize v-loading="loading" />
        </div>
      </div>
    </div>

    <!-- 数据表格区域 -->
    <div class="content-grid content-grid-2">
      <!-- 热门话题 -->
      <div class="card">
        <div class="card-header">
          <span>热门话题</span>
          <el-button type="primary" link @click="$router.push('/topics')">
            查看全部
          </el-button>
        </div>
        <el-table :data="hotTopics" size="small" v-loading="loading">
          <el-table-column prop="name" label="话题名称" min-width="120" />
          <el-table-column prop="post_count" label="帖子数" min-width="100">
            <template #default="{ row }">{{ formatNumber(row.post_count) }}</template>
          </el-table-column>
          <el-table-column label="情感倾向" min-width="100">
            <template #default="{ row }">
              <span :class="['sentiment-tag', getSentimentClass(row.sentiment_score)]">
                {{ getSentimentLabel(row.sentiment_score) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="sentiment_score" label="情感分数" min-width="100">
            <template #default="{ row }">{{ row.sentiment_score.toFixed(2) }}</template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 最新预警 -->
      <div class="card">
        <div class="card-header">
          <span>最新预警</span>
          <el-button type="primary" link @click="$router.push('/alerts')">
            查看全部
          </el-button>
        </div>
        <el-table :data="recentAlerts" size="small" v-loading="loading">
          <el-table-column prop="topic_name" label="话题" min-width="100" />
          <el-table-column prop="rule_type" label="规则类型" min-width="100" />
          <el-table-column label="状态" min-width="80">
            <template #default="{ row }">
              <span :class="getStatusClass(row.status)">
                {{ getStatusText(row.status) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="triggered_at" label="触发时间" min-width="80" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  min-height: 100vh;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.update-time {
  font-size: 13px;
  color: var(--text-secondary);
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
  margin-bottom: 4px;
}

.metric-trend {
  font-size: 12px;
  color: var(--text-secondary);
}

.chart-container {
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-body {
  height: 280px;
}

.card {
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-lighter);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.sentiment-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.sentiment-tag.positive {
  background-color: rgba(103, 194, 58, 0.1);
  color: var(--sentiment-positive);
}

.sentiment-tag.neutral {
  background-color: rgba(144, 147, 153, 0.1);
  color: var(--sentiment-neutral);
}

.sentiment-tag.negative {
  background-color: rgba(245, 108, 108, 0.1);
  color: var(--sentiment-negative);
}
</style>
