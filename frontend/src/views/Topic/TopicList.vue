<script setup>
import { h } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, View } from '@element-plus/icons-vue'
import PaginatedList from '../../components/PaginatedList.vue'
import { deleteTopic, pauseTopic, activateTopic } from '../../api/topics'

const router = useRouter()

// 列配置
const columns = [
  {
    prop: 'name',
    label: '话题名称',
    minWidth: 150
  },
  {
    prop: 'description',
    label: '描述',
    minWidth: 200,
    showOverflowTooltip: true
  },
  {
    prop: 'keywords',
    label: '关键词',
    minWidth: 150,
    slot: 'keywords'
  },
  {
    prop: 'status',
    label: '状态',
    width: 100,
    slot: 'status'
  },
  {
    prop: 'platform_count',
    label: '平台数',
    width: 80
  },
  {
    prop: 'post_count',
    label: '帖子数',
    width: 80
  }
]

// 行操作按钮
function createRowActions(row) {
  const actions = [
    h(
      'el-button',
      {
        icon: View,
        link: true,
        type: 'primary',
        size: 'small',
        onClick: () => router.push(`/topics/${row.id}`)
      },
      () => '查看'
    ),
    h(
      'el-button',
      {
        icon: Edit,
        link: true,
        type: 'primary',
        size: 'small',
        onClick: () => router.push(`/topics/${row.id}/edit`)
      },
      () => '编辑'
    )
  ]

  // 状态切换按钮
  if (row.status === 'active') {
    actions.push(
      h(
        'el-button',
        {
          link: true,
          type: 'warning',
          size: 'small',
          onClick: () => handlePause(row)
        },
        () => '暂停'
      )
    )
  } else {
    actions.push(
      h(
        'el-button',
        {
          link: true,
          type: 'success',
          size: 'small',
          onClick: () => handleActivate(row)
        },
        () => '激活'
      )
    )
  }

  actions.push(
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
  )

  return h('div', { class: 'row-actions' }, actions)
}

// 工具栏操作
const toolbarActions = [
  {
    label: '新建话题',
    type: 'primary',
    icon: Plus,
    handler: () => router.push('/topics/new')
  }
]

// 获取数据的函数
async function fetchTopics(params) {
  const { getTopics } = await import('../../api/topics')
  return getTopics(params)
}

// 删除处理
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除这个话题吗？', '提示', {
      type: 'warning'
    })
    await deleteTopic(row.id)
    ElMessage.success('删除成功')
    return true // 返回true表示需要刷新
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
    return false
  }
}

// 暂停处理
async function handlePause(row) {
  try {
    await pauseTopic(row.id)
    ElMessage.success('已暂停')
    return true
  } catch (e) {
    ElMessage.error('操作失败')
    return false
  }
}

// 激活处理
async function handleActivate(row) {
  try {
    await activateTopic(row.id)
    ElMessage.success('已激活')
    return true
  } catch (e) {
    ElMessage.error('操作失败')
    return false
  }
}

// 获取状态样式
function getStatusClass(status) {
  return { 'status-badge': true, [status]: true }
}
</script>

<template>
  <div class="page-container grid-bg">
    <div class="page-header">
      <div>
        <h1 class="page-title">话题管理</h1>
        <p class="page-subtitle">管理社交媒体监控话题</p>
      </div>
    </div>

    <div class="card">
      <PaginatedList
        :fetch-function="fetchTopics"
        :columns="columns"
        :row-actions="createRowActions"
        :toolbar-actions="toolbarActions"
      >
        <template #keywords="{ row }">
          <el-tag
            v-for="kw in row.keywords?.slice(0, 3)"
            :key="kw"
            size="small"
            class="mr-sm"
          >
            {{ kw }}
          </el-tag>
        </template>

        <template #status="{ row }">
          <span :class="getStatusClass(row.status)">
            {{ row.status_display || row.status }}
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

.mr-sm {
  margin-right: 4px;
}
</style>
