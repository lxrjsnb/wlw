<script setup>
import { ref, computed, onMounted } from 'vue'
import { Avatar, Refresh, TrendCharts } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { getTopics } from '../../api/topics'

const loading = ref(false)
const selectedTopic = ref('')
const sortBy = ref('kol_score') // kol_score, content, network, leadership, sentiment
const topics = ref([])

const kolData = ref({
  ranking: [], // KOL排行
  stats: {
    total: 0,
    initiators: 0,
    spreaders: 0,
    guides: 0,
    comprehensive: 0,
  },
})

const kolTypes = {
  initiator: { label: '发起者', color: '#F56C6C' },
  spreader: { label: '传播者', color: '#409EFF' },
  guide: { label: '引导者', color: '#E6A23C' },
  comprehensive: { label: '综合影响力者', color: '#67C23A' },
}

// 初始化时直接生成模拟数据
const initializeMockData = () => {
  kolData.value = {
    ranking: Array.from({ length: 20 }, (_, i) => {
      const type = ['initiator', 'spreader', 'guide', 'comprehensive'][i % 4]
      return {
        id: i + 1,
        name: `KOL用户${i + 1}`,
        avatar: '',
        kolScore: Math.random() * 40 + 60,
        kolType: type,
        contentInfluence: Math.random() * 100,
        networkInfluence: Math.random() * 100,
        topicLeadership: Math.random() * 100,
        sentimentInfluence: Math.random() * 100,
        followers: Math.floor(Math.random() * 1000000) + 10000,
        posts: Math.floor(Math.random() * 100) + 10,
      }
    }),
    stats: {
      total: 156,
      initiators: 35,
      spreaders: 68,
      guides: 32,
      comprehensive: 21,
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

async function loadKOLData() {
  loading.value = true
  try {
    // 模拟数据生成延迟
    await new Promise(resolve => setTimeout(resolve, 500))

    // TODO: 调用真实API
    // const res = await getKOLRanking({ topic: selectedTopic.value })
    // 模拟数据
    kolData.value = {
      ranking: Array.from({ length: 20 }, (_, i) => {
        const type = ['initiator', 'spreader', 'guide', 'comprehensive'][i % 4]
        return {
          id: i + 1,
          name: `KOL用户${i + 1}`,
          avatar: '',
          kolScore: Math.random() * 40 + 60,
          kolType: type,
          contentInfluence: Math.random() * 100,
          networkInfluence: Math.random() * 100,
          topicLeadership: Math.random() * 100,
          sentimentInfluence: Math.random() * 100,
          followers: Math.floor(Math.random() * 1000000) + 10000,
          posts: Math.floor(Math.random() * 100) + 10,
        }
      }),
      stats: {
        total: 156,
        initiators: 35,
        spreaders: 68,
        guides: 32,
        comprehensive: 21,
      },
    }
  } catch (e) {
    console.error('加载KOL数据失败:', e)
    // 确保数据有默认值
    kolData.value = {
      ranking: [],
      stats: {
        total: 0,
        initiators: 0,
        spreaders: 0,
        guides: 0,
        comprehensive: 0,
      },
    }
  } finally {
    loading.value = false
  }
}

const sortedRanking = computed(() => {
  return [...(kolData.value?.ranking || [])].sort((a, b) => {
    return parseFloat(b[sortBy.value]) - parseFloat(a[sortBy.value])
  })
})

const typeOption = computed(() => {
  const stats = kolData.value?.stats || { initiators: 0, spreaders: 0, guides: 0, comprehensive: 0 }
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, left: 'center' },
    color: Object.values(kolTypes).map(t => t.color),
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      data: [
        { value: stats.initiators, name: kolTypes.initiator.label },
        { value: stats.spreaders, name: kolTypes.spreader.label },
        { value: stats.guides, name: kolTypes.guide.label },
        { value: stats.comprehensive, name: kolTypes.comprehensive.label },
      ],
    }]
  }
})

const radarOption = computed(() => {
  const topKol = sortedRanking.value[0]
  if (!topKol) return {}
  return {
    tooltip: {},
    radar: {
      indicator: [
        { name: '内容影响力', max: 100 },
        { name: '网络影响力', max: 100 },
        { name: '话题引领力', max: 100 },
        { name: '情感影响力', max: 100 },
      ]
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          topKol.contentInfluence,
          topKol.networkInfluence,
          topKol.topicLeadership,
          topKol.sentimentInfluence,
        ],
        name: topKol.name,
        areaStyle: {},
      }]
    }]
  }
})

function getKOLTypeInfo(type) {
  return kolTypes[type] || kolTypes.spreader
}

function formatFollowers(count) {
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + 'w'
  }
  return count.toString()
}

async function handleRefresh() {
  await loadKOLData()
}

onMounted(async () => {
  await loadTopics()
  await loadKOLData()
})
</script>

<template>
  <div class="kol-view">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title">
            <el-icon><Avatar /></el-icon>
            <span>KOL画像分析</span>
          </div>
          <el-button :icon="Refresh" @click="handleRefresh" :loading="loading">刷新</el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filters">
        <el-form :inline="true">
          <el-form-item label="话题">
            <el-select v-model="selectedTopic" placeholder="选择话题" @change="loadKOLData">
              <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="排序方式">
            <el-select v-model="sortBy" @change="loadKOLData">
              <el-option label="综合得分" value="kol_score" />
              <el-option label="内容影响力" value="contentInfluence" />
              <el-option label="网络影响力" value="networkInfluence" />
              <el-option label="话题引领力" value="topicLeadership" />
              <el-option label="情感影响力" value="sentimentInfluence" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- Loading -->
      <div v-if="loading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="30"><Avatar /></el-icon>
        <p style="margin-top: 10px;">加载中...</p>
      </div>

      <!-- KOL分类统计 -->
      <el-row :gutter="20" v-show="!loading">
        <el-col :span="12">
          <el-card shadow="hover" header="KOL类型分布">
            <div class="chart-container-small">
              <VChart class="chart" :option="typeOption" autoresize />
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" header="Top KOL 能力雷达图">
            <div class="chart-container-small">
              <VChart class="chart" :option="radarOption" autoresize />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- KOL排行榜 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="KOL影响力排行 Top 20">
            <el-table :data="sortedRanking" size="small" max-height="600">
              <el-table-column label="排名" type="index" width="60" />
              <el-table-column label="KOL" width="180">
                <template #default="{ row }">
                  <div style="display: flex; align-items: center; gap: 10px;">
                    <el-avatar :size="40" :icon="Avatar" />
                    <div>
                      <div style="font-weight: 600;">{{ row.name }}</div>
                      <div style="font-size: 12px; color: #909399;">粉丝: {{ formatFollowers(row.followers) }}</div>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :style="{ backgroundColor: getKOLTypeInfo(row.kolType).color, border: 'none' }">
                    {{ getKOLTypeInfo(row.kolType).label }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="kolScore" label="综合得分" width="100" sortable align="center">
                <template #default="{ row }">
                  <el-tag type="success">{{ row.kolScore }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="内容影响力" width="120" sortable align="center">
                <template #default="{ row }">
                  <el-progress :percentage="parseFloat(row.contentInfluence)" :show-text="false" />
                  <span style="font-size: 12px;">{{ row.contentInfluence }}</span>
                </template>
              </el-table-column>
              <el-table-column label="网络影响力" width="120" sortable align="center">
                <template #default="{ row }">
                  <el-progress :percentage="parseFloat(row.networkInfluence)" :show-text="false" />
                  <span style="font-size: 12px;">{{ row.networkInfluence }}</span>
                </template>
              </el-table-column>
              <el-table-column label="话题引领力" width="120" sortable align="center">
                <template #default="{ row }">
                  <el-progress :percentage="parseFloat(row.topicLeadership)" :show-text="false" />
                  <span style="font-size: 12px;">{{ row.topicLeadership }}</span>
                </template>
              </el-table-column>
              <el-table-column label="情感影响力" width="120" sortable align="center">
                <template #default="{ row }">
                  <el-progress :percentage="parseFloat(row.sentimentInfluence)" :show-text="false" />
                  <span style="font-size: 12px;">{{ row.sentimentInfluence }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="posts" label="帖子数" width="80" align="center" />
              <el-table-column label="操作" width="100">
                <template #default>
                  <el-button type="primary" link size="small">详情</el-button>
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
.kol-view {
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

.chart-container-small {
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>
