<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getKeywordCloud, getSentimentTimeline } from '../../api/analysis'
import { getActiveTopics } from '../../api/topics'

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

async function load() {
  loading.value = true
  try {
    const params = selectedTopic.value ? { topic_id: selectedTopic.value } : {}

    // 加载关键词云
    const keywords = await getKeywordCloud(params)
    keywordData.value = keywords.keywords || []

    // 加载情感时间线
    const timeline = await getSentimentTimeline(params)
    sentimentTimeline.value = timeline

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
        <h1 class="page-title">情感分析</h1>
        <p class="page-subtitle">分析帖子的情感倾向和关键词</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedTopic" placeholder="选择话题" style="width: 200px; margin-right: 12px">
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
              :size="Math.floor(kw.value / 10) > 3 ? 'large' : 'default'"
              class="keyword-tag"
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
              <div class="value">{{ sentimentTimeline.positive?.reduce((a, b) => a + b, 0) || 0 }}</div>
            </div>
            <div class="sentiment-item neutral">
              <div class="label">中性</div>
              <div class="value">{{ sentimentTimeline.neutral?.reduce((a, b) => a + b, 0) || 0 }}</div>
            </div>
            <div class="sentiment-item negative">
              <div class="label">负面</div>
              <div class="value">{{ sentimentTimeline.negative?.reduce((a, b) => a + b, 0) || 0 }}</div>
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
          positive: sentimentTimeline.positive[i],
          neutral: sentimentTimeline.neutral[i],
          negative: sentimentTimeline.negative[i]
        }))" size="small">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="positive" label="正面" width="100">
            <template #default="{ row }">{{ row.positive || 0 }}</template>
          </el-table-column>
          <el-table-column prop="neutral" label="中性" width="100">
            <template #default="{ row }">{{ row.neutral || 0 }}</template>
          </el-table-column>
          <el-table-column prop="negative" label="负面" width="100">
            <template #default="{ row }">{{ row.negative || 0 }}</template>
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
}

.sentiment-item.positive .value { color: var(--sentiment-positive); }
.sentiment-item.neutral .value { color: var(--sentiment-neutral); }
.sentiment-item.negative .value { color: var(--sentiment-negative); }
</style>
