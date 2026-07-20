<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 运行治理 / 数据看板</span></div>
    <div class="page-header">
      <h1>数据看板</h1>
      <el-button @click="refresh">刷新数据</el-button>
    </div>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="4" v-for="m in metrics" :key="m.label">
        <div class="stat-card">
          <div class="muted small">{{ m.label }}</div>
          <div class="stat-num" :style="{ color: m.color }">{{ m.value }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="8">
        <el-card shadow="never" class="card">
          <template #header><strong>用户构成</strong></template>
          <div class="stat-grid">
            <div class="stat-item"><span class="muted">学生</span><strong>{{ data.users?.students || 0 }}</strong></div>
            <div class="stat-item"><span class="muted">教师</span><strong>{{ data.users?.teachers || 0 }}</strong></div>
            <div class="stat-item"><span class="muted">管理员</span><strong>{{ data.users?.admins || 0 }}</strong></div>
            <div class="stat-item"><span class="muted">今日活跃</span><strong>{{ data.users?.activeToday || 0 }}</strong></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="card">
          <template #header><strong>内容治理</strong></template>
          <div class="stat-grid">
            <div class="stat-item"><span class="muted">知识来源</span><strong>{{ data.knowledgeSources?.total || 0 }}</strong><span class="muted small">已审核 {{ data.knowledgeSources?.approved || 0 }}</span></div>
            <div class="stat-item"><span class="muted">AI 审核</span><strong>{{ data.aiReviews?.total || 0 }}</strong><span class="muted small">待审 {{ data.aiReviews?.pending || 0 }}</span></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="card">
          <template #header><strong>教学活动</strong></template>
          <div class="stat-grid">
            <div class="stat-item"><span class="muted">测验提交</span><strong>{{ data.quizzes?.totalSubmissions || 0 }}</strong><span class="muted small">均分 {{ data.quizzes?.avgScore || 0 }}</span></div>
            <div class="stat-item"><span class="muted">AI 对话</span><strong>{{ data.aiChat?.sessions || 0 }} 会话</strong><span class="muted small">{{ data.aiChat?.messages || 0 }} 条消息</span></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getPlatformAnalytics } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const loading = ref(true)
const data = ref({})

const metrics = ref([])

async function refresh() {
  await runPageLoad(loading, async () => {
    const d = await getPlatformAnalytics()
    data.value = d
    metrics.value = [
      { label: '用户总数', value: d.users?.total || 0, color: '#409EFF' },
      { label: '活跃用户(今日)', value: d.users?.activeToday || 0, color: '#67C23A' },
      { label: '总课程数', value: d.courses?.total || 0, color: '#E6A23C' },
      { label: 'AI审核待办', value: d.aiReviews?.pending || 0, color: '#F56C6C' },
      { label: '测验提交', value: d.quizzes?.totalSubmissions || 0, color: '#409EFF' },
      { label: '知识来源', value: d.knowledgeSources?.total || 0, color: '#67C23A' }
    ]
  })
}

onMounted(refresh)
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.muted.small { font-size: 11px; display: block; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card { background: var(--soft); border-radius: 14px; padding: 20px; text-align: center; border: 1px dashed var(--line); }
.stat-num { font-size: 36px; font-weight: 800; margin-top: 4px; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.stat-item { display: flex; flex-direction: column; gap: 4px; }
.stat-item strong { font-size: 24px; font-weight: 800; }
</style>
