<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getPosts } from '../../api/posts'
import { getActiveTopics } from '../../api/topics'

const loading = ref(false)
const posts = ref([])
const total = ref(0)
const topics = ref([])

const queryParams = ref({
  page: 1,
  page_size: 20,
  topic: '',
  platform: '',
  sentiment: '',
  start_date: '',
  end_date: ''
})

async function load() {
  loading.value = true
  try {
    const data = await getPosts(queryParams.value)
    posts.value = data.results || data
    total.value = data.count || posts.value.length
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

function getSentimentClass(sentiment) {
  return { 'sentiment-tag': true, [sentiment]: true }
}

onMounted(() => {
  load()
  loadTopics()
})
</script>

<template>
  <div class="page-container grid-bg">
    <div class="page-header">
      <div>
        <h1 class="page-title">帖子列表</h1>
        <p class="page-subtitle">查看和分析社交媒体帖子</p>
      </div>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <div class="card mb-lg">
      <el-form :inline="true">
        <el-form-item label="话题">
          <el-select v-model="queryParams.topic" placeholder="全部" clearable>
            <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="情感">
          <el-select v-model="queryParams.sentiment" placeholder="全部" clearable>
            <el-option label="正面" value="positive" />
            <el-option label="中性" value="neutral" />
            <el-option label="负面" value="negative" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="queryParams = { page: 1, page_size: 20 }; load()">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card">
      <el-table :data="posts" v-loading="loading" stripe>
        <el-table-column prop="content" label="内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="author" label="作者" width="120" />
        <el-table-column prop="platform_name" label="平台" width="100">
          <template #default="{ row }">
            <span :class="['platform-badge', row.platform_name?.toLowerCase()]">
              {{ row.platform_name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="情感" width="80">
          <template #default="{ row }">
            <span :class="getSentimentClass(row.sentiment)">
              {{ row.sentiment_display }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="influence_score" label="影响力" width="100" />
        <el-table-column prop="publish_time_formatted" label="发布时间" width="160" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          :page-size="queryParams.page_size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="load"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
