<script setup>
import { ref, onMounted, h } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import PaginatedList from '../../components/PaginatedList.vue'
import { getPosts } from '../../api/posts'
import { getActiveTopics } from '../../api/topics'

const topics = ref([])

// 查询参数
const queryParams = ref({
  page: 1,
  page_size: 20,
  topic: '',
  platform: '',
  sentiment: '',
  start_date: '',
  end_date: ''
})

// 列配置
const columns = [
  {
    prop: 'content',
    label: '内容',
    minWidth: 300,
    showOverflowTooltip: true
  },
  {
    prop: 'author',
    label: '作者',
    width: 120
  },
  {
    prop: 'platform_name',
    label: '平台',
    width: 100,
    slot: 'platform'
  },
  {
    prop: 'sentiment',
    label: '情感',
    width: 80,
    slot: 'sentiment'
  },
  {
    prop: 'influence_score',
    label: '影响力',
    width: 100
  },
  {
    prop: 'publish_time_formatted',
    label: '发布时间',
    width: 160
  }
]

// 行操作按钮
function createRowActions(row) {
  return h(
    'el-button',
    {
      link: true,
      type: 'primary',
      size: 'small',
      onClick: () => ElMessage.info('查看详情功能待实现')
    },
    () => '详情'
  )
}

// 工具栏操作
const toolbarActions = [
  {
    label: '查询',
    type: 'primary',
    handler: handleSearch
  },
  {
    label: '重置',
    handler: handleReset
  }
]

// 获取数据的函数
async function fetchPosts(params) {
  return getPosts({ ...queryParams.value, ...params })
}

// 搜索
function handleSearch() {
  queryParams.value.page = 1
}

// 重置
function handleReset() {
  queryParams.value = {
    page: 1,
    page_size: 20,
    topic: '',
    platform: '',
    sentiment: '',
    start_date: '',
    end_date: ''
  }
}

// 获取情感样式
function getSentimentClass(sentiment) {
  return { 'sentiment-tag': true, [sentiment]: true }
}

// 加载话题
async function loadTopics() {
  try {
    const data = await getActiveTopics()
    topics.value = data.results || data
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadTopics)
</script>

<template>
  <div class="page-container grid-bg">
    <div class="page-header">
      <div>
        <h1 class="page-title">帖子列表</h1>
        <p class="page-subtitle">查看和分析社交媒体帖子</p>
      </div>
    </div>

    <!-- 筛选表单 -->
    <div class="card mb-lg">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="话题">
          <el-select v-model="queryParams.topic" placeholder="全部" clearable style="width: 180px">
            <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="情感">
          <el-select v-model="queryParams.sentiment" placeholder="全部" clearable style="width: 120px">
            <el-option label="正面" value="positive" />
            <el-option label="中性" value="neutral" />
            <el-option label="负面" value="negative" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card">
      <PaginatedList
        :fetch-function="fetchPosts"
        :columns="columns"
        :row-actions="createRowActions"
        :initial-query="queryParams"
      >
        <template #platform="{ row }">
          <span :class="['platform-badge', row.platform_name?.toLowerCase()]">
            {{ row.platform_name }}
          </span>
        </template>

        <template #sentiment="{ row }">
          <span :class="getSentimentClass(row.sentiment)">
            {{ row.sentiment_display }}
          </span>
        </template>
      </PaginatedList>
    </div>
  </div>
</template>

<style scoped>
.mb-lg {
  margin-bottom: 20px;
}
</style>
