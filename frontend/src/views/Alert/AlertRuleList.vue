<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Refresh } from '@element-plus/icons-vue'
import { getAlertRules, deleteAlertRule, enableAlertRule, disableAlertRule } from '../../api/alerts'

const loading = ref(false)
const rules = ref([])
const total = ref(0)

const queryParams = ref({
  page: 1,
  page_size: 20
})

async function load() {
  loading.value = true
  try {
    const data = await getAlertRules(queryParams.value)
    rules.value = data.results || data
    total.value = data.count || rules.value.length
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除这条规则吗？', '提示', {
      type: 'warning'
    })
    await deleteAlertRule(row.id)
    ElMessage.success('删除成功')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function handleToggle(row) {
  try {
    if (row.enabled) {
      await disableAlertRule(row.id)
      ElMessage.success('已禁用')
    } else {
      await enableAlertRule(row.id)
      ElMessage.success('已启用')
    }
    load()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function getPriorityClass(priority) {
  return { 'priority-badge': true, [priority]: true }
}

onMounted(load)
</script>

<template>
  <div class="page-container grid-bg">
    <div class="page-header">
      <div>
        <h1 class="page-title">预警规则</h1>
        <p class="page-subtitle">配置和管理预警规则</p>
      </div>
      <el-button :icon="Plus" type="primary">新建规则</el-button>
    </div>

    <div class="card">
      <el-table :data="rules" v-loading="loading" stripe>
        <el-table-column prop="topic_name" label="话题" width="150" />
        <el-table-column prop="rule_type_display" label="规则类型" width="120" />
        <el-table-column prop="condition_display" label="条件" width="80" />
        <el-table-column prop="threshold_value" label="阈值" width="100" />
        <el-table-column label="优先级" width="80">
          <template #default="{ row }">
            <span :class="getPriorityClass(row.priority)">
              {{ row.priority_display }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="cooldown_minutes" label="冷却(分钟)" width="100" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button :icon="Edit" link type="primary" size="small">编辑</el-button>
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
</style>
