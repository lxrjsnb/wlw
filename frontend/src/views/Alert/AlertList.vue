<script setup>
import { ref, h } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Check, CircleClose } from '@element-plus/icons-vue'
import PaginatedList from '../../components/PaginatedList.vue'
import { getAlertRecords, acknowledgeAlert, resolveAlert } from '../../api/alerts'

const selectedIds = ref([])

// 查询参数
const queryParams = ref({
  page: 1,
  page_size: 20,
  status: '',
  topic: ''
})

// 列配置
const columns = [
  {
    prop: 'topic_name',
    label: '话题',
    width: 120
  },
  {
    prop: 'rule_type_display',
    label: '规则类型',
    width: 120
  },
  {
    prop: 'priority',
    label: '优先级',
    width: 80,
    slot: 'priority'
  },
  {
    prop: 'message',
    label: '消息',
    minWidth: 200,
    showOverflowTooltip: true
  },
  {
    prop: 'current_value',
    label: '当前值',
    width: 100
  },
  {
    prop: 'threshold_value',
    label: '阈值',
    width: 80
  },
  {
    prop: 'status',
    label: '状态',
    width: 80,
    slot: 'status'
  },
  {
    prop: 'triggered_at_formatted',
    label: '触发时间',
    width: 120
  }
]

// 行操作按钮
function createRowActions(row) {
  const actions = []

  if (row.status === 'pending') {
    actions.push(
      h(
        'el-button',
        {
          icon: Check,
          link: true,
          type: 'primary',
          size: 'small',
          onClick: () => handleAcknowledge(row)
        },
        () => '确认'
      )
    )
  }

  if (row.status !== 'resolved') {
    actions.push(
      h(
        'el-button',
        {
          icon: CircleClose,
          link: true,
          type: 'success',
          size: 'small',
          onClick: () => handleResolve(row)
        },
        () => '解决'
      )
    )
  }

  return h('div', { class: 'row-actions' }, actions)
}

// 获取数据的函数
async function fetchAlerts(params) {
  return getAlertRecords({ ...queryParams.value, ...params })
}

// 确认处理
async function handleAcknowledge(row) {
  try {
    await acknowledgeAlert(row.id)
    ElMessage.success('已确认')
    return true
  } catch (e) {
    ElMessage.error('操作失败')
    return false
  }
}

// 解决处理
async function handleResolve(row) {
  try {
    const result = await ElMessageBox.prompt('请输入处理说明', '解决预警', {
      inputPattern: /.+/,
      inputErrorMessage: '请输入处理说明'
    })
    await resolveAlert(row.id, { resolution_note: result.value })
    ElMessage.success('已解决')
    return true
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败')
    }
    return false
  }
}

// 选择变化
function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.id)
}

// 获取状态样式
function getStatusClass(status) {
  return { 'status-badge': true, [status]: true }
}

// 获取优先级样式
function getPriorityClass(priority) {
  return { 'priority-badge': true, [priority]: true }
}
</script>

<template>
  <div class="page-container grid-bg">
    <div class="page-header">
      <div>
        <h1 class="page-title">预警中心</h1>
        <p class="page-subtitle">查看和处理系统预警</p>
      </div>
    </div>

    <div class="card">
      <PaginatedList
        :fetch-function="fetchAlerts"
        :columns="columns"
        :row-actions="createRowActions"
        :selection="true"
        @selection-change="handleSelectionChange"
      >
        <template #priority="{ row }">
          <span :class="['priority-badge', row.priority]">
            {{ row.priority_display }}
          </span>
        </template>

        <template #status="{ row }">
          <span :class="getStatusClass(row.status)">
            {{ row.status_display }}
          </span>
        </template>
      </PaginatedList>
    </div>
  </div>
</template>

<style scoped>
.row-actions {
  display: flex;
  gap: 4px;
}
</style>
