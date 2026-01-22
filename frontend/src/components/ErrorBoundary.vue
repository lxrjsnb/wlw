<script setup>
import { onErrorCaptured, ref } from 'vue'

const props = defineProps({
  title: { type: String, default: '页面渲染失败' },
})

const error = ref(null)

function reset() {
  error.value = null
}

function onReload() {
  window.location.reload()
}

// Capture errors from children and render fallback UI instead of a blank screen
// Returning false prevents the error from propagating further.
onErrorCaptured((err) => {
  error.value = err
  return false
})
</script>

<template>
  <div v-if="error" class="boundary">
    <el-result icon="error" :title="props.title" sub-title="请打开控制台查看具体报错信息">
      <template #extra>
        <el-button @click="reset">重试渲染</el-button>
        <el-button type="primary" @click="onReload">刷新页面</el-button>
      </template>
    </el-result>
    <el-card class="error-card" shadow="never">
      <pre class="error-text">{{ String(error?.stack || error?.message || error) }}</pre>
    </el-card>
  </div>
  <slot v-else />
</template>

<style scoped>
.boundary {
  padding: 24px 12px;
}

.error-card {
  margin-top: 12px;
}

.error-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: #606266;
}
</style>
