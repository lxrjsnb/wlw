<script setup>
import { h } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import PaginatedList from '../../components/PaginatedList.vue'
import { deleteAlertRule, enableAlertRule, disableAlertRule } from '../../api/alerts'
import { useRouter } from 'vue-router'

const router = useRouter()

// 列配置
const columns = [
  {
    prop: 'topic_name',
    label: '话题',
    width: 150
  },
  {
    prop: 'rule_type_display',
    label: '规则类型',
    width: 120
  },
  {
    prop: 'condition_display',
    label: '条件',
    width: 80
  },
  {
    prop: 'threshold_value',
    label: '阈值',
    width: 100
  },
  {
    prop: 'priority',
    label: '优先级',
    width: 80,
    slot: 'priority'
  },
  {
    prop: 'enabled',
    label: '状态',
    width: 80,
    slot: 'enabled'
  },
  {
    prop: 'cooldown_minutes',
    label: '冷却(分钟)',
    width: 100
  },
  {
    prop: 'description',
    label: '描述',
    minWidth: 200,
    showOverflowTooltip: true
  }
]

// 行操作按钮
function createRowActions(row) {
  return h('div', { class: 'row-actions' }, [
    h(
      'el-button',
      {
        icon: Edit,
        link: true,
        type: 'primary',
        size: 'small',
        onClick: () => router.push(`/alerts/rules/${row.id}/edit`)
      },
      () => '编辑'
    ),
    h(
      'el-button',
      {
        icon: Delete,
        link: true,
        type: 'danger',
        size: 'small',
        onClick: () => handleDelete(row)
      },
      () => '删除'
    )
  ])
}

// 工具栏操作
const toolbarActions = [
  {
    label: '新建规则',
    type: 'primary',
    icon: Plus,
    handler: () => router.push('/alerts/rules/new')
  }
]

// 获取数据的函数
async function fetchAlertRules(params) {
  const { getAlertRules } = await import('../../api/alerts')
  return getAlertRules(params)
}

// 删除处理
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除这条规则吗？', '提示', {
      type: 'warning'
    })
    await deleteAlertRule(row.id)
    ElMessage.success('删除成功')
    return true
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
    return false
  }
}

// 切换启用状态
async function handleToggle(row) {
  try {
    if (row.enabled) {
      await disableAlertRule(row.id)
      ElMessage.success('已禁用')
    } else {
      await enableAlertRule(row.id)
      ElMessage.success('已启用')
    }
    return true
  } catch (e) {
    ElMessage.error('操作失败')
    return false
  }
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
        <h1 class="page-title">预警规则</h1>
        <p class="page-subtitle">配置和管理预警规则</p>
      </div>
    </div>

    <div class="card">
      <PaginatedList
        :fetch-function="fetchAlertRules"
        :columns="columns"
        :row-actions="createRowActions"
        :toolbar-actions="toolbarActions"
      >
        <template #priority="{ row }">
          <span :class="getPriorityClass(row.priority)">
            {{ row.priority_display }}
          </span>
        </template>

        <template #enabled="{ row }">
          <el-switch :model-value="row.enabled" @change="handleToggle(row)" />
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
