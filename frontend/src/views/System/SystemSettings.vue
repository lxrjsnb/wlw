<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Setting, Notification, DocumentDelete, InfoFilled,
  Bell, Switch, DataLine
} from '@element-plus/icons-vue'

const activeTab = ref('general')
const loading = ref(false)

// 通用设置
const generalSettings = reactive({
  systemName: '舆情分析系统',
  timezone: 'Asia/Shanghai',
  language: 'zh-CN',
  dataRetentionDays: 90,
  maxUploadSize: 10,
})

// 通知设置
const notificationSettings = reactive({
  emailEnabled: true,
  smsEnabled: false,
  websocketEnabled: true,
  emailSmtpHost: 'smtp.example.com',
  emailSmtpPort: 587,
  emailFrom: 'noreply@example.com',
  notificationBatchSize: 10,
  notificationInterval: 5,
})

// 数据保留策略
const retentionSettings = reactive({
  postDataRetention: 90,
  alertDataRetention: 365,
  logDataRetention: 30,
  autoCleanupEnabled: true,
  cleanupTime: '02:00',
  cleanupFrequency: 'daily',
})

// 系统信息
const systemInfo = ref({
  version: 'v1.0.0',
  buildTime: '2025-01-29 10:30:00',
  djangoVersion: '4.2.0',
  pythonVersion: '3.11.0',
  database: 'MySQL 8.0',
  redis: 'Connected',
  celery: 'Running',
  lastBackup: '2025-01-29 03:00:00',
})

async function loadSettings() {
  loading.value = true
  try {
    // TODO: 从 API 加载设置
    // const response = await getSystemSettings()
    // Object.assign(generalSettings, response.general)
    // Object.assign(notificationSettings, response.notification)
    // Object.assign(retentionSettings, response.retention)
  } catch (e) {
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

async function saveGeneralSettings() {
  loading.value = true
  try {
    // TODO: 调用 API 保存设置
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

async function saveNotificationSettings() {
  loading.value = true
  try {
    // TODO: 调用 API 保存设置
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

async function saveRetentionSettings() {
  loading.value = true
  try {
    // TODO: 调用 API 保存设置
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

async function testNotification() {
  loading.value = true
  try {
    // TODO: 调用 API 发送测试通知
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('测试通知已发送')
  } catch (e) {
    ElMessage.error('发送失败')
  } finally {
    loading.value = false
  }
}

async function cleanupOldData() {
  loading.value = true
  try {
    // TODO: 调用 API 清理旧数据
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('数据清理完成')
  } catch (e) {
    ElMessage.error('清理失败')
  } finally {
    loading.value = false
  }
}

async function backupDatabase() {
  loading.value = true
  try {
    // TODO: 调用 API 备份数据库
    await new Promise(resolve => setTimeout(resolve, 3000))
    ElMessage.success('数据库备份完成')
    systemInfo.value.lastBackup = new Date().toLocaleString('zh-CN')
  } catch (e) {
    ElMessage.error('备份失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadSettings)
</script>

<template>
  <div class="system-settings">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="title">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="settings-tabs">
        <!-- 通用设置 -->
        <el-tab-pane label="通用设置" name="general">
          <div class="tab-content">
            <el-form label-width="140px" style="max-width: 600px">
              <el-form-item label="系统名称">
                <el-input v-model="generalSettings.systemName" placeholder="输入系统名称" />
              </el-form-item>

              <el-form-item label="时区">
                <el-select v-model="generalSettings.timezone" style="width: 100%">
                  <el-option label="亚洲/上海 (GMT+8)" value="Asia/Shanghai" />
                  <el-option label="亚洲/东京 (GMT+9)" value="Asia/Tokyo" />
                  <el-option label="欧洲/伦敦 (GMT+0)" value="Europe/London" />
                  <el-option label="美国/纽约 (GMT-5)" value="America/New_York" />
                </el-select>
              </el-form-item>

              <el-form-item label="语言">
                <el-select v-model="generalSettings.language" style="width: 100%">
                  <el-option label="简体中文" value="zh-CN" />
                  <el-option label="English" value="en-US" />
                  <el-option label="日本語" value="ja-JP" />
                </el-select>
              </el-form-item>

              <el-form-item label="数据保留天数">
                <el-input-number
                  v-model="generalSettings.dataRetentionDays"
                  :min="7"
                  :max="365"
                  :step="1"
                />
                <span class="form-tip">舆情数据保留天数，超过此天数的数据将被归档</span>
              </el-form-item>

              <el-form-item label="最大上传大小">
                <el-input-number
                  v-model="generalSettings.maxUploadSize"
                  :min="1"
                  :max="100"
                  :step="1"
                />
                <span class="form-tip">MB</span>
              </el-form-item>

              <el-form-item>
                <el-button type="primary" :loading="loading" @click="saveGeneralSettings">
                  保存设置
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 通知设置 -->
        <el-tab-pane name="notification">
          <template #label>
            <span><el-icon><Notification /></el-icon> 通知设置</span>
          </template>
          <div class="tab-content">
            <el-form label-width="160px" style="max-width: 700px">
              <div class="setting-section">
                <h4>通知方式</h4>
                <el-form-item label="启用邮件通知">
                  <el-switch v-model="notificationSettings.emailEnabled" />
                  <span class="form-tip">通过邮件发送告警通知</span>
                </el-form-item>

                <el-form-item label="启用短信通知">
                  <el-switch v-model="notificationSettings.smsEnabled" />
                  <span class="form-tip">通过短信发送紧急告警通知</span>
                </el-form-item>

                <el-form-item label="启用WebSocket推送">
                  <el-switch v-model="notificationSettings.websocketEnabled" />
                  <span class="form-tip">实时推送告警到前端</span>
                </el-form-item>
              </div>

              <el-divider />

              <div class="setting-section">
                <h4>邮件服务器配置</h4>
                <el-form-item label="SMTP服务器">
                  <el-input v-model="notificationSettings.emailSmtpHost" placeholder="smtp.example.com" />
                </el-form-item>

                <el-form-item label="SMTP端口">
                  <el-input-number v-model="notificationSettings.emailSmtpPort" :min="1" :max="65535" />
                </el-form-item>

                <el-form-item label="发件人邮箱">
                  <el-input v-model="notificationSettings.emailFrom" placeholder="noreply@example.com" />
                </el-form-item>

                <el-form-item>
                  <el-button @click="testNotification" :loading="loading">
                    <el-icon><Bell /></el-icon>
                    发送测试通知
                  </el-button>
                </el-form-item>
              </div>

              <el-divider />

              <div class="setting-section">
                <h4>通知策略</h4>
                <el-form-item label="批量发送数量">
                  <el-input-number v-model="notificationSettings.notificationBatchSize" :min="1" :max="100" />
                  <span class="form-tip">批量发送的通知数量</span>
                </el-form-item>

                <el-form-item label="发送间隔(分钟)">
                  <el-input-number v-model="notificationSettings.notificationInterval" :min="1" :max="60" />
                  <span class="form-tip">通知发送的时间间隔</span>
                </el-form-item>
              </div>

              <el-form-item>
                <el-button type="primary" :loading="loading" @click="saveNotificationSettings">
                  保存设置
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 数据管理 -->
        <el-tab-pane name="data">
          <template #label>
            <span><el-icon><DataLine /></el-icon> 数据管理</span>
          </template>
          <div class="tab-content">
            <el-form label-width="160px" style="max-width: 600px">
              <div class="setting-section">
                <h4>数据保留策略</h4>
                <el-form-item label="帖子数据保留">
                  <el-input-number
                    v-model="retentionSettings.postDataRetention"
                    :min="7"
                    :max="365"
                  />
                  <span class="form-tip">天</span>
                </el-form-item>

                <el-form-item label="预警数据保留">
                  <el-input-number
                    v-model="retentionSettings.alertDataRetention"
                    :min="30"
                    :max="1095"
                  />
                  <span class="form-tip">天</span>
                </el-form-item>

                <el-form-item label="日志数据保留">
                  <el-input-number
                    v-model="retentionSettings.logDataRetention"
                    :min="7"
                    :max="180"
                  />
                  <span class="form-tip">天</span>
                </el-form-item>

                <el-form-item label="启用自动清理">
                  <el-switch v-model="retentionSettings.autoCleanupEnabled" />
                </el-form-item>

                <el-form-item label="清理时间">
                  <el-time-picker
                    v-model="retentionSettings.cleanupTime"
                    format="HH:mm"
                    value-format="HH:mm"
                  />
                </el-form-item>

                <el-form-item label="清理频率">
                  <el-select v-model="retentionSettings.cleanupFrequency">
                    <el-option label="每天" value="daily" />
                    <el-option label="每周" value="weekly" />
                    <el-option label="每月" value="monthly" />
                  </el-select>
                </el-form-item>

                <el-form-item>
                  <el-button type="danger" :loading="loading" @click="cleanupOldData">
                    <el-icon><DocumentDelete /></el-icon>
                    立即清理旧数据
                  </el-button>
                  <span class="form-tip">将根据保留策略清理过期数据</span>
                </el-form-item>
              </div>

              <el-divider />

              <div class="setting-section">
                <h4>数据备份</h4>
                <el-form-item label="最后备份时间">
                  <span>{{ systemInfo.lastBackup }}</span>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" :loading="loading" @click="backupDatabase">
                    <el-icon><Switch /></el-icon>
                    立即备份数据库
                  </el-button>
                </el-form-item>
              </div>

              <el-form-item>
                <el-button type="primary" :loading="loading" @click="saveRetentionSettings">
                  保存设置
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 系统信息 -->
        <el-tab-pane name="info">
          <template #label>
            <span><el-icon><InfoFilled /></el-icon> 系统信息</span>
          </template>
          <div class="tab-content">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="系统版本">
                {{ systemInfo.version }}
              </el-descriptions-item>
              <el-descriptions-item label="构建时间">
                {{ systemInfo.buildTime }}
              </el-descriptions-item>
              <el-descriptions-item label="Django版本">
                {{ systemInfo.djangoVersion }}
              </el-descriptions-item>
              <el-descriptions-item label="Python版本">
                {{ systemInfo.pythonVersion }}
              </el-descriptions-item>
              <el-descriptions-item label="数据库">
                <el-tag type="success">{{ systemInfo.database }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="Redis">
                <el-tag type="success">{{ systemInfo.redis }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="Celery任务">
                <el-tag type="success">{{ systemInfo.celery }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="最后备份">
                {{ systemInfo.lastBackup }}
              </el-descriptions-item>
            </el-descriptions>

            <el-divider />

            <div class="system-stats">
              <h4>系统统计</h4>
              <el-row :gutter="20">
                <el-col :span="6">
                  <div class="stat-box">
                    <div class="stat-value">25</div>
                    <div class="stat-label">监测话题</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-box">
                    <div class="stat-value">12K</div>
                    <div class="stat-label">帖子数量</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-box">
                    <div class="stat-value">89</div>
                    <div class="stat-label">预警规则</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-box">
                    <div class="stat-value">5</div>
                    <div class="stat-label">用户数量</div>
                  </div>
                </el-col>
              </el-row>
            </div>

            <el-divider />

            <div class="license-info">
              <h4>许可证信息</h4>
              <p>版权所有 © 2025 舆情分析系统</p>
              <p>本软件采用 MIT 许可证</p>
              <el-link type="primary" href="https://github.com" target="_blank">
                <el-icon><Link /></el-icon>
                查看源代码
              </el-link>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.system-settings {
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

.settings-tabs {
  margin-top: -20px;
}

.tab-content {
  padding: 20px 0;
}

.setting-section {
  margin-bottom: 20px;
}

.setting-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.system-stats {
  margin: 20px 0;
}

.system-stats h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
}

.stat-box {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.license-info {
  margin-top: 20px;
}

.license-info h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
}

.license-info p {
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
}
</style>
