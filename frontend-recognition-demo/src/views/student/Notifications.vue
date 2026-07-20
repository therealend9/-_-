<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">学生端 / 消息通知 / 通知中心</span></div>
    <div class="page-header">
      <h1>消息通知</h1>
      <el-button size="small" @click="markAll">全部已读</el-button>
    </div>

    <el-tabs v-model="activeTab" style="margin-top: 16px">
      <el-tab-pane label="全部消息" name="all" />
      <el-tab-pane label="课程通知" name="course" />
      <el-tab-pane label="作业反馈" name="feedback" />
      <el-tab-pane label="系统通知" name="system" />
    </el-tabs>

    <div v-for="msg in filteredMessages" :key="msg.id" style="margin-bottom: 12px">
      <el-card shadow="never" class="card" :class="{ unread: !msg.isRead }" @click="msg.targetRoute && $router.push(msg.targetRoute)">
        <div style="display: flex; align-items: flex-start; gap: 14px">
          <div class="dot" v-if="!msg.isRead"></div>
          <div style="flex: 1">
            <div style="display: flex; justify-content: space-between">
              <strong>{{ msg.title }}</strong>
              <span class="muted small">{{ formatTime(msg.createdAt) }}</span>
            </div>
            <p class="muted" style="margin-top: 6px; line-height: 1.6">{{ msg.content }}</p>
          </div>
        </div>
      </el-card>
    </div>

    <div v-if="!filteredMessages.length" class="muted" style="text-align: center; padding: 40px">暂无通知</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getStudentNotifications, markAllNotificationsRead } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const activeTab = ref('all')
const loading = ref(true)
const messages = ref([])

const filteredMessages = computed(() => {
  if (activeTab.value === 'all') return messages.value
  return messages.value.filter(item => item.category === activeTab.value)
})

function formatTime(t) {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diff = now - d
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

async function markAll() {
  try {
    await markAllNotificationsRead()
    messages.value.forEach(m => m.isRead = true)
    ElMessage.success('已全部标记为已读')
  } catch (e) { ElMessage.error('操作失败') }
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getStudentNotifications()
  messages.value = (data.messages || []).map(m => ({
    ...m,
    isRead: m.isRead !== undefined ? m.isRead : !m.read,
    createdAt: m.createdAt || m.time || ''
  }))
}))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); cursor: pointer; }
.card.unread { background: #fafaf7; border-color: #606060; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: #409EFF; margin-top: 6px; flex-shrink: 0; }
</style>
