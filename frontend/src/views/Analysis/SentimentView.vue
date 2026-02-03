<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getTopics } from '../../api/topics'
import { getKeywordCloud, getSentimentTimeline, getMultilevelSentiment } from '../../api/analysis'

const loading = ref(false)
const topics = ref([])
const selectedTopic = ref('')

const keywordData = ref([])
const sentimentTimeline = ref({
  dates: [],
  positive: [],
  neutral: [],
  negative: []
})

const sentimentSummary = ref({
  positive_count: 0,
  neutral_count: 0,
  negative_count: 0,
  positive_ratio: 0,
  neutral_ratio: 0,
  negative_ratio: 0
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
    const [keywords, timeline, multilevel] = await Promise.all([
      getKeywordCloud(params),
      getSentimentTimeline(params),
      getMultilevelSentiment(params)
    ])

    // 处理关键词数据
    if (keywords) {
      keywordData.value = keywords.keywords || []
    }

    // 处理情感时间线数据
    if (timeline) {
      sentimentTimeline.value = {
        dates: timeline.dates || [],
        positive: timeline.positive || [],
        neutral: timeline.neutral || [],
        negative: timeline.negative || []
      }
    }

    // 处理情感统计摘要
    if (multilevel) {
      sentimentSummary.value = {
        positive_count: multilevel.positive_count || 0,
        neutral_count: multilevel.neutral_count || 0,
        negative_count: multilevel.negative_count || 0,
        positive_ratio: multilevel.positive_ratio || 0,
        neutral_ratio: multilevel.neutral_ratio || 0,
        negative_ratio: multilevel.negative_ratio || 0
      }
    }
  } catch (e) {
    console.error('加载失败:', e)
  } finally {
    loading.value = false
  }
}

// 获取情感标签
function getSentimentLabel(score) {
  if (score > 0.3) return '正面'
  if (score < -0.3) return '负面'
  return '中性'
}

// 获取情感样式
function getSentimentClass(score) {
  if (score > 0.3) return 'positive'
  if (score < -0.3) return 'negative'
  return 'neutral'
}

// 获取总数
const getTotalSentiment = computed(() => {
  return sentimentSummary.value.positive_count +
         sentimentSummary.value.neutral_count +
         sentimentSummary.value.negative_count
})

onMounted(() => {
  loadTopics()
  load()
})
</script>

<template>
  <div class="page-container grid-bg">
    <div class="page-header">
      <div>
        <h1 class="page-title">情感分析</h1>
        <p class="page-subtitle">分析帖子的情感倾向和关键词</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedTopic" placeholder="选择话题" style="width: 200px; margin-right: 12px" @change="load">
          <el-option label="全部话题" value="" />
          <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </div>
    </div>

    <div class="content-grid content-grid-2">
      <!-- 关键词云 -->
      <div class="chart-container">
        <div class="chart-header">
          <span class="chart-title">关键词云</span>
        </div>
        <div class="chart-body" v-loading="loading">
          <div v-if="keywordData.length" class="keyword-cloud">
            <el-tag
              v-for="kw in keywordData"
              :key="kw.name"
              :size="kw.value > 50 ? 'large' : kw.value > 20 ? 'default' : 'small'"
              class="keyword-tag"
              :type="kw.value > 50 ? 'danger' : kw.value > 20 ? 'warning' : 'info'"
            >
              {{ kw.name }} ({{ kw.value }})
            </el-tag>
          </div>
          <el-empty v-else description="暂无数据" />
        </div>
      </div>

      <!-- 情感统计 -->
      <div class="card">
        <div class="card-header">
          <span>情感分布</span>
        </div>
        <div v-loading="loading">
          <div class="sentiment-summary">
            <div class="sentiment-item positive">
              <div class="label">正面</div>
              <div class="value">{{ sentimentSummary.positive_count }}</div>
              <div class="ratio">{{ (sentimentSummary.positive_ratio * 100).toFixed(1) }}%</div>
            </div>
            <div class="sentiment-item neutral">
              <div class="label">中性</div>
              <div class="value">{{ sentimentSummary.neutral_count }}</div>
              <div class="ratio">{{ (sentimentSummary.neutral_ratio * 100).toFixed(1) }}%</div>
            </div>
            <div class="sentiment-item negative">
              <div class="label">负面</div>
              <div class="value">{{ sentimentSummary.negative_count }}</div>
              <div class="ratio">{{ (sentimentSummary.negative_ratio * 100).toFixed(1) }}%</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 情感趋势 -->
    <div class="card">
      <div class="card-header">
        <span>情感趋势</span>
      </div>
      <div v-loading="loading">
        <el-table :data="sentimentTimeline.dates.map((d, i) => ({
          date: d,
          positive: sentimentTimeline.positive[i] || 0,
          neutral: sentimentTimeline.neutral[i] || 0,
          negative: sentimentTimeline.negative[i] || 0,
          total: (sentimentTimeline.positive[i] || 0) + (sentimentTimeline.neutral[i] || 0) + (sentimentTimeline.negative[i] || 0)
        }))" size="small">
          <el-table-column prop="date" label="日期" width="120">
            <template #default="{ row }">
              {{ new Date(row.date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) }}
            </template>
          </el-table-column>
          <el-table-column prop="positive" label="正面" width="100">
            <template #default="{ row }">{{ row.positive }}</template>
          </el-table-column>
          <el-table-column prop="neutral" label="中性" width="100">
            <template #default="{ row }">{{ row.neutral }}</template>
          </el-table-column>
          <el-table-column prop="negative" label="负面" width="100">
            <template #default="{ row }">{{ row.negative }}</template>
          </el-table-column>
          <el-table-column prop="total" label="总计" width="100">
            <template #default="{ row }">{{ row.total }}</template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
}

.keyword-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.keyword-tag {
  font-size: 14px;
  cursor: pointer;
  transition: transform 0.2s;
}

.keyword-tag:hover {
  transform: scale(1.1);
}

.sentiment-summary {
  display: flex;
  justify-content: space-around;
  padding: 40px 20px;
}

.sentiment-item {
  text-align: center;
}

.sentiment-item .label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.sentiment-item .value {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 4px;
}

.sentiment-item .ratio {
  font-size: 12px;
  color: var(--text-secondary);
}

.sentiment-item.positive .value { color: var(--sentiment-positive); }
.sentiment-item.neutral .value { color: var(--sentiment-neutral); }
.sentiment-item.negative .value { color: var(--sentiment-negative); }

.content-grid {
  display: grid;
  gap: 20px;
}

.content-grid-2 {
  grid-template-columns: repeat(2, 1fr);
}
</style>
