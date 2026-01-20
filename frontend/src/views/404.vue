<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面不存在</p>
    <el-button type="primary" @click="goHome">返回首页</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}
</script>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.not-found h1 {
  font-size: 120px;
  color: #409eff;
  margin: 0;
}

.not-found p {
  font-size: 24px;
  color: #999;
  margin: 20px 0 40px;
}
</style>
