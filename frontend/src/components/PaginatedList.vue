<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  // API获取函数
  fetchFunction: {
    type: Function,
    required: true
  },
  // 列配置
  columns: {
    type: Array,
    default: () => []
  },
  // 初始查询参数
  initialQuery: {
    type: Object,
    default: () => ({})
  },
  // 行操作按钮生成函数
  rowActions: {
    type: Function,
    default: null
  },
  // 工具栏操作按钮
  toolbarActions: {
    type: Array,
    default: () => []
  },
  // 是否支持多选
  selection: {
    type: Boolean,
    default: false
  },
  // 卡片标题
  title: {
    type: String,
    default: ''
  },
  // 是否显示卡片头部
  showHeader: {
    type: Boolean,
    default: true
  },
  // 是否显示边框
  border: {
    type: Boolean,
    default: false
  },
  // 斑马纹
  stripe: {
    type: Boolean,
    default: true
  },
  // 自定义空状态文本
  emptyText: {
    type: String,
    default: '暂无数据'
  }
})

const emit = defineEmits([
  'selection-change',
  'row-click',
  'loaded',
  'refresh'
])

// 状态管理
const loading = ref(false)
const data = ref([])
const total = ref(0)
const selectedIds = ref([])
const selectedRows = ref([])

// 查询参数
const queryParams = ref({
  page: 1,
  page_size: 20,
  ...props.initialQuery
})

// 监听初始查询参数变化
watch(() => props.initialQuery, (newQuery) => {
  queryParams.value = {
    ...queryParams.value,
    ...newQuery
  }
  load()
}, { deep: true })

// 加载数据
async function load() {
  loading.value = true
  try {
    const response = await props.fetchFunction(queryParams.value)
    data.value = response.results || response || []
    total.value = response.count || data.value.length
    emit('loaded', data.value)
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error(error?.message || '加载数据失败')
    data.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 刷新数据
function refresh() {
  queryParams.value.page = 1
  load()
  emit('refresh')
}

// 页码变化
function handlePageChange(page) {
  queryParams.value.page = page
  load()
}

// 每页数量变化
function handleSizeChange(size) {
  queryParams.value.page_size = size
  queryParams.value.page = 1
  load()
}

// 选择变化
function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.id)
  selectedRows.value = selection
  emit('selection-change', selection, selectedIds.value)
}

// 行点击
function handleRowClick(row) {
  emit('row-click', row)
}

// 暴露方法给父组件
defineExpose({
  load,
  refresh,
  getSelectedIds: () => selectedIds.value,
  getSelectedRows: () => selectedRows.value,
  clearSelection: () => {
    selectedIds.value = []
    selectedRows.value = []
  }
})

onMounted(load)
</script>

<template>
  <div class="paginated-list">
    <!-- 工具栏 -->
    <div v-if="toolbarActions.length > 0" class="toolbar mb-sm">
      <el-button
        v-for="action in toolbarActions"
        :key="action.label"
        :type="action.type || 'default'"
        :icon="action.icon"
        :disabled="action.disabled"
        :loading="action.loading"
        @click="action.handler"
      >
        {{ action.label }}
      </el-button>
      <div style="flex: 1"></div>
      <el-button :icon="Refresh" @click="refresh" :loading="loading">刷新</el-button>
    </div>

    <!-- 表格 -->
    <el-table
      :data="data"
      v-loading="loading"
      :border="border"
      :stripe="stripe"
      @selection-change="selection ? handleSelectionChange : undefined"
      @row-click="handleRowClick"
    >
      <!-- 多选列 -->
      <el-table-column v-if="selection" type="selection" width="55" />

      <!-- 动态列 -->
      <template v-for="col in columns" :key="col.prop">
        <el-table-column
          :prop="col.prop"
          :label="col.label"
          :width="col.width"
          :min-width="col.minWidth"
          :fixed="col.fixed"
          :show-overflow-tooltip="col.showOverflowTooltip !== false"
          :align="col.align || 'left'"
          :formatter="col.formatter"
        >
          <template v-if="col.slot" #default="{ row, column, $index }">
            <slot :name="col.slot" :row="row" :column="column" :index="$index"></slot>
          </template>
          <template v-else-if="col.render" #default="{ row, column, $index }">
            <component :is="col.render(row, column, $index)" />
          </template>
          <template v-else-if="col.tag" #default="{ row }">
            <el-tag
              v-if="Array.isArray(row[col.prop])"
              v-for="(item, idx) in row[col.prop]"
              :key="idx"
              :type="col.tagType || ''"
              size="small"
              class="mr-sm"
            >
              {{ item }}
            </el-tag>
            <el-tag v-else :type="col.tagType || ''" size="small">
              {{ row[col.prop] }}
            </el-tag>
          </template>
        </el-table-column>
      </template>

      <!-- 操作列 -->
      <el-table-column
        v-if="rowActions"
        label="操作"
        :width="120"
        :fixed="'right'"
      >
        <template #default="{ row, column, $index }">
          <component :is="rowActions(row, column, $index)" />
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div v-if="total > 0" class="pagination-container">
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && data.length === 0" class="empty-state">
      <el-empty :description="emptyText" />
    </div>
  </div>
</template>

<style scoped>
.paginated-list {
  width: 100%;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar > *:not(:first-child):not(:last-child) {
  margin-right: 8px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.empty-state {
  padding: 40px 0;
}

.mr-sm {
  margin-right: 4px;
}

.mb-sm {
  margin-bottom: 12px;
}
</style>
