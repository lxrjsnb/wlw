<script setup>
import { ref, computed, onMounted } from 'vue'
import { Sunny, TrendCharts, Refresh } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { getTopics } from '../../api/topics'

const loading = ref(false)
const selectedTopic = ref('')
const timeRange = ref('7d') // 7d, 30d
const topics = ref([])

const hotnessData = ref({
  realtime: [], // 实时热度排行
  trend: [], // 热度趋势
  distribution: { explosive: 0, hot: 0, warm: 0, cold: 0 }, // 等级分布
  fastest: [], // 变化最快
})

// 热度等级配置
const hotnessLevels = {
  explosive: { label: '爆燃性热点', color: '#F56C6C', min: 90 },
  hot: { label: '热点', color: '#E6A23C', min: 70 },
  warm: { label: '温热', color: '#409EFF', min: 50 },
  cold: { label: '冷门', color: '#909399', min: 30 },
  frozen: { label: '冰点', color: '#C0C4CC', min: 0 },
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

async function loadHotnessData() {
  loading.value = true
  try {
    // TODO: 调用真实API
    // const res = await getRealtimeHotness({ topic: selectedTopic.value })
    // 模拟数据
    hotnessData.value = {
      realtime: Array.from({ length: 20 }, (_, i) => ({
        id: i + 1,
        title: `热门帖子 ${i + 1}`,
        author: `用户${i + 1}`,
        hotness: Math.floor(Math.random() * 100),
        level: getHotnessLevel(Math.floor(Math.random() * 100)),
        likes: Math.floor(Math.random() * 10000),
        comments: Math.floor(Math.random() * 1000),
        shares: Math.floor(Math.random() * 5000),
      })),
      trend: generateTrendData(),
      distribution: {
        explosive: Math.floor(Math.random() * 10),
        hot: Math.floor(Math.random() * 20) + 10,
        warm: Math.floor(Math.random() * 30) + 20,
        cold: Math.floor(Math.random() * 40) + 30,
      },
      fastest: Array.from({ length: 10 }, (_, i) => ({
        id: i + 1,
        title: `快速上升帖子 ${i + 1}`,
        change: (Math.random() * 50 + 10).toFixed(1),
      })),
    }
  } catch (e) {
    console.error('加载热度数据失败:', e)
  } finally {
    loading.value = false
  }
}

function getHotnessLevel(score) {
  if (score >= 90) return 'explosive'
  if (score >= 70) return 'hot'
  if (score >= 50) return 'warm'
  if (score >= 30) return 'cold'
  return 'frozen'
}

function generateTrendData() {
  const days = timeRange.value === '7d' ? 7 : 30
  return Array.from({ length: days }, (_, i) => ({
    date: `1/${i + 1}`,
    avgHotness: Math.floor(Math.random() * 60 + 40),
    postCount: Math.floor(Math.random() * 500 + 100),
  }))
}

const hotnessTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0, left: 'center' },
  grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
  xAxis: {
    type: 'category',
    data: hotnessData.value.trend.map(d => d.date),
  },
  yAxis: [
    { type: 'value', name: '平均热度', position: 'left' },
    { type: 'value', name: '帖子数', position: 'right' }
  ],
  series: [
    {
      name: '平均热度',
      type: 'line',
      data: hotnessData.value.trend.map(d => d.avgHotness),
      smooth: true,
      itemStyle: { color: '#E6A23C' },
    },
    {
      name: '帖子数',
      type: 'bar',
      yAxisIndex: 1,
      data: hotnessData.value.trend.map(d => d.postCount),
      itemStyle: { color: '#409EFF' },
    },
  ],
}))

const distributionOption = computed(() => {
  const dist = hotnessData.value.distribution
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, left: 'center' },
    color: Object.values(hotnessLevels).map(l => l.color),
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      data: [
        { value: dist.explosive, name: hotnessLevels.explosive.label },
        { value: dist.hot, name: hotnessLevels.hot.label },
        { value: dist.warm, name: hotnessLevels.warm.label },
        { value: dist.cold, name: hotnessLevels.cold.label },
      ],
      label: {
        formatter: params => `${params.name}: ${params.value}`
      }
    }]
  }
})

async function handleRefresh() {
  await loadHotnessData()
}

onMounted(async () => {
  await loadTopics()
  await loadHotnessData()
})
</script>

<template>
  <div class="hotness-view">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title">
            <el-icon><Sunny /></el-icon>
            <span>热度分析</span>
          </div>
          <el-button :icon="Refresh" @click="handleRefresh" :loading="loading">刷新</el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filters">
        <el-form :inline="true">
          <el-form-item label="话题">
            <el-select v-model="selectedTopic" placeholder="选择话题" @change="loadHotnessData">
              <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-radio-group v-model="timeRange" @change="loadHotnessData">
              <el-radio-button label="7d">近7天</el-radio-button>
              <el-radio-button label="30d">近30天</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <!-- Loading -->
      <div v-if="loading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="30"><Sunny /></el-icon>
        <p style="margin-top: 10px;">加载中...</p>
      </div>

      <!-- 热度等级分布 -->
      <el-row :gutter="20" v-show="!loading">
        <el-col :span="12">
          <el-card shadow="hover" header="热度等级分布">
            <div class="chart-container">
              <VChart class="chart" :option="distributionOption" autoresize />
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" header="热度趋势">
            <div class="chart-container">
              <VChart class="chart" :option="hotnessTrendOption" autoresize />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 实时热度排行 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="14">
          <el-card shadow="hover" header="实时热度排行 Top 20">
            <el-table :data="hotnessData.realtime" size="small" max-height="500">
              <el-table-column label="排名" type="index" width="60" />
              <el-table-column prop="title" label="帖子标题" min-width="200" show-overflow-tooltip />
              <el-table-column prop="author" label="作者" width="100" />
              <el-table-column label="热度" width="120">
                <template #default="{ row }">
                  <el-tag :type="row.level === 'explosive' ? 'danger' : row.level === 'hot' ? 'warning' : 'info'">
                    {{ row.hotness }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="likes" label="点赞" width="80" align="right" />
              <el-table-column prop="comments" label="评论" width="80" align="right" />
              <el-table-column prop="shares" label="转发" width="80" align="right" />
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="10">
          <el-card shadow="hover" header="热度上升最快">
            <el-table :data="hotnessData.fastest" size="small">
              <el-table-column label="排名" type="index" width="60" />
              <el-table-column prop="title" label="帖子" min-width="150" show-overflow-tooltip />
              <el-table-column label="涨幅" width="80" align="right">
                <template #default="{ row }">
                  <span style="color: #F56C6C;">+{{ row.change }}%</span>
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
.hotness-view {
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
</style>
