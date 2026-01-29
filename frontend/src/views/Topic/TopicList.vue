<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, View, Refresh } from '@element-plus/icons-vue'
import { getTopics, deleteTopic, pauseTopic, activateTopic } from '../../api/topics'

const loading = ref(false)
const topics = ref([])
const total = ref(0)

const queryParams = ref({
  page: 1,
  page_size: 20,
  status: '',
  search: ''
})

async function load() {
  loading.value = true
  try {
    const data = await getTopics(queryParams.value)
    topics.value = data.results || data
    total.value = data.count || topics.value.length
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除这个话题吗？', '提示', {
      type: 'warning'
    })
    await deleteTopic(row.id)
    ElMessage.success('删除成功')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function handlePause(row) {
  try {
    await pauseTopic(row.id)
    ElMessage.success('已暂停')
    load()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function handleActivate(row) {
  try {
    await activateTopic(row.id)
    ElMessage.success('已激活')
    load()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function getStatusClass(status) {
  return { 'status-badge': true, [status]: true }
}

onMounted(load)
</script>

<template>
  <div class="page-container grid-bg">
    <div class="page-header">
      <div>
        <h1 class="page-title">话题管理</h1>
        <p class="page-subtitle">管理社交媒体监控话题</p>
      </div>
      <el-button :icon="Plus" type="primary">新建话题</el-button>
    </div>

    <div class="card">
      <el-table :data="topics" v-loading="loading" stripe>
        <el-table-column prop="name" label="话题名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="关键词" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="kw in row.keywords?.slice(0, 3)" :key="kw" size="small" class="mr-sm">
              {{ kw }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span :class="getStatusClass(row.status)">
              {{ row.status_display || row.status }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="platform_count" label="平台数" width="80" />
        <el-table-column prop="post_count" label="帖子数" width="80" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button :icon="View" link type="primary" size="small">查看</el-button>
            <el-button :icon="Edit" link type="primary" size="small">编辑</el-button>
            <el-button v-if="row.status === 'active'" link type="warning" size="small" @click="handlePause(row)">暂停</el-button>
            <el-button v-else link type="success" size="small" @click="handleActivate(row)">激活</el-button>
            <el-button :icon="Delete" link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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
.mr-sm {
  margin-right: 4px;
}
</style>
