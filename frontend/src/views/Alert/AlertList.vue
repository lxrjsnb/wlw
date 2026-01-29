<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Check, CircleClose } from '@element-plus/icons-vue'
import { getAlertRecords, acknowledgeAlert, resolveAlert } from '../../api/alerts'

const loading = ref(false)
const alerts = ref([])
const total = ref(0)
const selectedIds = ref([])

const queryParams = ref({
  page: 1,
  page_size: 20,
  status: '',
  topic: ''
})

async function load() {
  loading.value = true
  try {
    const data = await getAlertRecords(queryParams.value)
    alerts.value = data.results || data
    total.value = data.count || alerts.value.length
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleAcknowledge(row) {
  try {
    await acknowledgeAlert(row.id)
    ElMessage.success('已确认')
    load()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function handleResolve(row) {
  try {
    await ElMessageBox.prompt('请输入处理说明', '解决预警', {
      inputPattern: /.+/,
      inputErrorMessage: '请输入处理说明'
    })
    await resolveAlert(row.id, { resolution_note: row.resolution_note })
    ElMessage.success('已解决')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.id)
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
        <h1 class="page-title">预警中心</h1>
        <p class="page-subtitle">查看和处理系统预警</p>
      </div>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <div class="card">
      <el-table
        :data="alerts"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="topic_name" label="话题" width="120" />
        <el-table-column prop="rule_type_display" label="规则类型" width="120" />
        <el-table-column prop="priority_display" label="优先级" width="80">
          <template #default="{ row }">
            <span :class="['priority-badge', row.priority]">
              {{ row.priority_display }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="current_value" label="当前值" width="100" />
        <el-table-column prop="threshold_value" label="阈值" width="80" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <span :class="getStatusClass(row.status)">
              {{ row.status_display }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="triggered_at_formatted" label="触发时间" width="120" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              :icon="Check"
              link
              type="primary"
              size="small"
              @click="handleAcknowledge(row)"
            >
              确认
            </el-button>
            <el-button
              v-if="row.status !== 'resolved'"
              :icon="CircleClose"
              link
              type="success"
              size="small"
              @click="handleResolve(row)"
            >
              解决
            </el-button>
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
