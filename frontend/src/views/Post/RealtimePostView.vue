<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Connection } from '@element-plus/icons-vue'
import { getPosts } from '../../api/posts'
import { getActiveTopics } from '../../api/topics'

const loading = ref(false)
const posts = ref([])
const topics = ref([])
const selectedTopic = ref('')
const isConnected = ref(false)
const ws = ref(null)

async function load() {
  loading.value = true
  try {
    const params = {
      page: 1,
      page_size: 50,
      topic: selectedTopic.value
    }
    const data = await getPosts(params)
    posts.value = data.results || data
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

function connectWebSocket() {
  if (ws.value) {
    ws.value.close()
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_WS_HOST || 'localhost:8001'
  const wsUrl = `${protocol}//${host}/ws/posts/`

  ws.value = new WebSocket(wsUrl)

  ws.value.onopen = () => {
    isConnected.value = true
    ElMessage.success('WebSocket已连接')

    // 订阅话题
    if (selectedTopic.value) {
      ws.value.send(JSON.stringify({
        type: 'subscribe_topic',
        topic_id: selectedTopic.value
      }))
    }
  }

  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'new_post') {
      posts.value.unshift(data.data)
      if (posts.value.length > 50) {
        posts.value.pop()
      }
    }
  }

  ws.value.onclose = () => {
    isConnected.value = false
    // 自动重连
    setTimeout(connectWebSocket, 3000)
  }

  ws.value.onerror = () => {
    isConnected.value = false
  }
}

function disconnectWebSocket() {
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
  isConnected.value = false
}

onMounted(() => {
  loadTopics()
  load()
  connectWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<template>
  <div class="page-container grid-bg">
    <div class="page-header">
      <div>
        <h1 class="page-title">实时监控</h1>
        <p class="page-subtitle">实时查看社交媒体帖子流</p>
      </div>
      <div class="header-actions">
        <el-select
          v-model="selectedTopic"
          placeholder="选择话题"
          style="width: 200px; margin-right: 12px"
          @change="load"
        >
          <el-option label="全部话题" value="" />
          <el-option v-for="t in topics" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button
          :icon="Connection"
          :type="isConnected ? 'success' : 'danger'"
          @click="isConnected ? disconnectWebSocket() : connectWebSocket()"
        >
          {{ isConnected ? '已连接' : '连接' }}
        </el-button>
      </div>
    </div>

    <div class="card">
      <el-scrollbar height="calc(100vh - 240px)">
        <div v-loading="loading && !posts.length">
          <div v-for="post in posts" :key="post.id" class="post-item">
            <div class="post-header">
              <div class="post-author">
                <span class="platform-badge" :class="post.platform_name?.toLowerCase()">
                  {{ post.platform_name }}
                </span>
                <span class="author-name">{{ post.author }}</span>
              </div>
              <div class="post-meta">
                <span class="post-time">{{ post.publish_time_formatted }}</span>
                <span :class="['sentiment-tag', post.sentiment]">
                  {{ post.sentiment_display }}
                </span>
              </div>
            </div>
            <div class="post-content">
              {{ post.content }}
            </div>
            <div class="post-stats">
              <span>👍 {{ post.likes }}</span>
              <span>💬 {{ post.comments }}</span>
              <span>🔄 {{ post.shares }}</span>
              <span>👁️ {{ post.views }}</span>
              <span class="influence">影响力: {{ post.influence_score?.toFixed(0) }}</span>
            </div>
          </div>

          <div v-if="!posts.length" class="empty-state">
            <div class="empty-state-icon">📭</div>
            <div class="empty-state-text">暂无帖子数据</div>
          </div>
        </div>
      </el-scrollbar>
    </div>
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
}

.post-item {
  padding: 16px;
  border-bottom: 1px solid var(--border-lighter);
  transition: background-color 0.2s;
}

.post-item:hover {
  background-color: var(--bg-hover);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.post-author {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-name {
  font-weight: 600;
  color: var(--text-primary);
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.post-time {
  font-size: 13px;
  color: var(--text-secondary);
}

.post-content {
  margin-bottom: 12px;
  color: var(--text-regular);
  line-height: 1.6;
}

.post-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
}

.influence {
  margin-left: auto;
  font-weight: 600;
  color: var(--primary-color);
}
</style>
