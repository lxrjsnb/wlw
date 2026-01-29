<script setup>
import { ref, computed, onMounted } from 'vue'
import { Share, Refresh, User } from '@element-plus/icons-vue'
import { getTopics } from '../../api/topics'

const loading = ref(false)
const selectedTopic = ref('')
const topics = ref([])

const propagationData = ref({
  paths: [], // 传播路径
  keyNodes: [], // 关键节点
  pattern: '', // 传播模式
  stats: {
    depth: 0,
    breadth: 0,
    speed: 0,
    coverage: 0,
  },
})

const propagationPatterns = {
  star: { label: '星型传播', color: '#F56C6C', desc: '单中心多点辐射' },
  chain: { label: '链式传播', color: '#409EFF', desc: '节点形成长链' },
  viral: { label: '病毒式传播', color: '#E6A23C', desc: '指数级增长' },
  community: { label: '社区传播', color: '#67C23A', desc: '多子群独立传播' },
}

async function loadTopics() {
  try {
    const res = await getTopics({ page: 1, page_size: 100 })
    topics.value = res?.results || res?.items || []
    if (topics.value.length && !selectedTopic.value) {
      selectedTopic.value = topics.value[0].id
    }
  } catch (e) {
    console.error('加载话题失败:', e)
  }
}

async function loadPropagationData() {
  loading.value = true
  try {
    // TODO: 调用真实API
    // const res = await getPropagationPaths({ topic: selectedTopic.value })
    // 模拟数据
    propagationData.value = {
      paths: Array.from({ length: 5 }, (_, i) => ({
        id: i + 1,
        sourcePost: `源头帖子 ${i + 1}`,
        depth: Math.floor(Math.random() * 5) + 1,
        breadth: Math.floor(Math.random() * 100) + 10,
        nodes: Math.floor(Math.random() * 200) + 20,
      })),
      keyNodes: Array.from({ length: 10 }, (_, i) => ({
        id: i + 1,
        name: `KOL用户${i + 1}`,
        followers: Math.floor(Math.random() * 100000) + 10000,
        centrality: (Math.random()).toFixed(3),
        influence: Math.floor(Math.random() * 100),
        type: ['发起者', '传播者', '引导者'][Math.floor(Math.random() * 3)],
      })),
      pattern: Object.keys(propagationPatterns)[Math.floor(Math.random() * 4)],
      stats: {
        depth: Math.floor(Math.random() * 5) + 1,
        breadth: Math.floor(Math.random() * 100) + 10,
        speed: (Math.random() * 1000 + 100).toFixed(0),
        coverage: (Math.random() * 50 + 30).toFixed(1),
      },
    }
  } catch (e) {
    console.error('加载传播数据失败:', e)
  } finally {
    loading.value = false
  }
}

const patternOption = computed(() => {
  const pattern = propagationPatterns[propagationData.value.pattern]
  return {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: 100, name: pattern.label, itemStyle: { color: pattern.color } },
      ],
      label: {
        show: true,
        formatter: `{b}\n{c}`,
        fontSize: 16,
      }
    }]
  }
})

const centralityOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
  xAxis: { type: 'value', max: 1 },
  yAxis: {
    type: 'category',
    data: propagationData.value.keyNodes.slice(0, 5).map(n => n.name).reverse(),
  },
  series: [{
    type: 'bar',
    data: propagationData.value.keyNodes.slice(0, 5).map(n => n.centrality).reverse(),
    itemStyle: { color: '#409EFF' },
    label: { show: true, position: 'right' }
  }]
}))

async function handleRefresh() {
  await loadPropagationData()
}

onMounted(async () => {
  await loadTopics()
  await loadPropagationData()
})
</script>

<template>
  <div class="propagation-view">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title">
            <el-icon><Share /></el-icon>
            <span>传播分析</span>
          </div>
          <el-button :icon="Refresh" @click="handleRefresh" :loading="loading">刷新</el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filters">
        <el-form :inline="true">
          <el-form-item label="话题">
            <el-select v-model="selectedTopic" placeholder="选择话题" @change="loadPropagationData">
              <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- Loading -->
      <div v-if="loading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="30"><Share /></el-icon>
        <p style="margin-top: 10px;">加载中...</p>
      </div>

      <!-- 传播统计概览 -->
      <el-row :gutter="20" v-show="!loading">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ propagationData.stats.depth }}</div>
            <div class="stat-label">传播深度</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ propagationData.stats.breadth }}</div>
            <div class="stat-label">传播广度</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ propagationData.stats.speed }}</div>
            <div class="stat-label">传播速度</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ propagationData.stats.coverage }}%</div>
            <div class="stat-label">覆盖率</div>
          </div>
        </el-col>
      </el-row>

      <!-- 传播模式和关键节点 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="12">
          <el-card shadow="hover" header="传播模式识别">
            <div class="chart-container-small">
              <VChart class="chart" :option="patternOption" autoresize />
            </div>
            <el-divider />
            <div class="pattern-desc">
              <el-tag :style="{ backgroundColor: propagationPatterns[propagationData.pattern].color, border: 'none' }" size="large">
                {{ propagationPatterns[propagationData.pattern].label }}
              </el-tag>
              <p class="desc">{{ propagationPatterns[propagationData.pattern].desc }}</p>
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" header="关键节点中心性 Top 5">
            <div class="chart-container-small">
              <VChart class="chart" :option="centralityOption" autoresize />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 关键传播节点排行 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="关键传播节点 Top 10">
            <el-table :data="propagationData.value.keyNodes" size="small">
              <el-table-column label="排名" type="index" width="60" />
              <el-table-column prop="name" label="用户名称" width="120">
                <template #default="{ row }">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <el-avatar :size="32" :icon="User" />
                    <span>{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="type" label="节点类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.type === '发起者' ? 'danger' : row.type === '引导者' ? 'warning' : 'primary'" size="small">
                    {{ row.type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="followers" label="粉丝数" width="100" align="right">
                <template #default="{ row }">
                  {{ (row.followers / 10000).toFixed(1) }}w
                </template>
              </el-table-column>
              <el-table-column prop="centrality" label="中心性" width="100" align="right">
                <template #default="{ row }">
                  <el-progress :percentage="row.centrality * 100" :show-text="false" />
                </template>
              </el-table-column>
              <el-table-column prop="influence" label="影响力" width="100" align="right">
                <template #default="{ row }">
                  <el-tag :type="row.influence > 70 ? 'danger' : row.influence > 40 ? 'warning' : 'info'">
                    {{ row.influence }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <!-- 传播路径列表 -->
      <el-row :gutter="20" class="mt-20" v-show="!loading">
        <el-col :span="24">
          <el-card shadow="hover" header="传播路径列表">
            <el-table :data="propagationData.value.paths" size="small">
              <el-table-column label="ID" prop="id" width="60" />
              <el-table-column prop="sourcePost" label="源头帖子" min-width="200" show-overflow-tooltip />
              <el-table-column prop="depth" label="传播深度" width="100" align="center" />
              <el-table-column prop="breadth" label="传播广度" width="100" align="center" />
              <el-table-column prop="nodes" label="节点数" width="100" align="center" />
              <el-table-column label="操作" width="100">
                <template #default>
                  <el-button type="primary" link size="small">查看详情</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped>
.propagation-view {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.filters {
  margin-bottom: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.chart-container-small {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart {
  width: 100%;
  height: 100%;
}

.pattern-desc {
  text-align: center;
  padding: 10px 0;
}

.pattern-desc .desc {
  margin: 10px 0 0 0;
  color: #606266;
}
</style>
