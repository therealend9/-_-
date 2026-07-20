<template>
  <div>
    <div class="breadcrumb"><span class="muted">学生端 / 学生工作台</span></div>

    <!-- 案例演示入口 -->
    <div class="demo-banner" @click="openDemo">
      <span class="demo-banner-text">📐 查看「学生工作台」静态设计 Demo →</span>
    </div>

    <!-- ===== 当前课程横幅 ===== -->
    <div class="course-banner">
      <div class="cb-left">
        <div class="cb-badge">当前课程</div>
        <h1 class="cb-title">{{ currentCourse.chapter }}</h1>
        <div class="cb-meta">{{ currentCourse.name }} · {{ currentCourse.teacher }} · {{ currentCourse.className }}</div>
        <div class="cb-progress">
          <span class="cb-progress-label">学习进度</span>
          <el-progress :percentage="currentCourse.progress" :stroke-width="6" :show-text="false" color="#3a7bd5" style="width:160px" />
          <span class="cb-progress-pct">{{ currentCourse.progress }}%</span>
        </div>
      </div>
      <div class="cb-actions">
        <el-button size="large" type="primary" @click="router.push('/student/pre-study')">进入课前学习</el-button>
        <el-button size="large" @click="router.push('/student/pre-study-quiz')">预习小测</el-button>
      </div>
    </div>

    <!-- ===== 四大模块快捷入口 ===== -->
    <div class="module-grid">
      <div
        v-for="m in modules" :key="m.key"
        class="module-card"
        @click="router.push(m.route)"
      >
        <div class="mc-icon">
          <el-icon size="22"><component :is="m.icon" /></el-icon>
        </div>
        <div class="mc-body">
          <div class="mc-top">
            <strong class="mc-label">{{ m.label }}</strong>
            <el-tag v-if="m.status" size="small" :type="m.statusType || 'info'" effect="plain">{{ m.status }}</el-tag>
          </div>
          <div class="mc-desc">{{ m.desc }}</div>
        </div>
        <el-icon size="16" class="mc-arrow"><ArrowRight /></el-icon>
      </div>
    </div>

    <!-- ===== 统计卡片 ===== -->
    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :span="6" v-for="stat in summaryStats" :key="stat.label">
        <div class="stat-card">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-num" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="stat-desc">{{ stat.desc }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- ===== 最近动态 ===== -->
      <el-col :span="14">
        <el-card shadow="never" class="side-card">
          <template #header><strong>最近动态</strong></template>
          <div v-for="(item, i) in recentActivity" :key="i" class="activity-row">
            <span class="act-dot" :class="'act-dot--' + item.type"></span>
            <div class="act-body">
              <div class="act-title">{{ item.title }}</div>
              <div class="act-desc">{{ item.desc }}</div>
            </div>
            <span class="act-time">{{ item.time }}</span>
          </div>
        </el-card>
      </el-col>

      <!-- ===== 课后反馈 + 更多入口 ===== -->
      <el-col :span="10">
        <el-card shadow="never" class="side-card">
          <template #header>
            <div class="card-head-row">
              <strong>课后反馈</strong>
              <el-button text type="primary" size="small" @click="router.push('/student/feedback')">查看全部</el-button>
            </div>
          </template>
          <div v-for="fb in recentFeedbacks" :key="fb.id" class="fb-row" @click="router.push(`/student/feedback/${fb.id}`)">
            <span class="fb-score-dot" :class="{ 'fb-score-dot--high': fb.score >= 85 }">{{ fb.score }}</span>
            <span class="fb-chapter">{{ fb.chapter }}</span>
            <span class="fb-date">{{ fb.date }}</span>
          </div>
        </el-card>

        <el-card shadow="never" class="side-card" style="margin-top: 16px">
          <template #header><strong>更多入口</strong></template>
          <div class="extra-grid">
            <div class="extra-item" @click="router.push('/student/ai-qa')">
              <el-icon size="18"><ChatDotRound /></el-icon>
              <span>AI 问答</span>
            </div>
            <div class="extra-item" @click="router.push('/student/knowledge-graph')">
              <el-icon size="18"><Connection /></el-icon>
              <span>知识图谱</span>
            </div>
            <div class="extra-item" @click="router.push('/student/learning-report')">
              <el-icon size="18"><DataAnalysis /></el-icon>
              <span>学习报告</span>
            </div>
            <div class="extra-item" @click="router.push('/student/notifications')">
              <el-icon size="18"><Bell /></el-icon>
              <span>消息通知</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight, Bell, ChatDotRound, ChatLineRound, Connection,
  DataAnalysis, Edit, Reading, Timer
} from '@element-plus/icons-vue'
import { getStudentDashboard } from '../../api/student.js'

const router = useRouter()
const currentCourse = ref({ name: '马克思主义基本原理', chapter: '加载中…', teacher: '', className: '', progress: 0 })

function openDemo() {
  window.open(`${import.meta.env.BASE_URL}学生工作台-静态demo.html`, '_blank')
}
const modules = ref([])
const summaryStats = ref([])
const recentActivity = ref([])
const recentFeedbacks = ref([])

onMounted(async () => {
  try {
    const data = await getStudentDashboard()
    currentCourse.value = data.currentCourse || currentCourse.value
    modules.value = data.modules || []
    summaryStats.value = data.summaryStats || []
    recentActivity.value = data.recentActivity || []
    recentFeedbacks.value = data.recentFeedbacks || []
  } catch (e) {
    console.error('加载工作台失败', e)
  }
})
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }

/* 案例演示入口 */
.demo-banner {
  display: flex; align-items: center; gap: 10px;
  background: #fef9e7; border: 1px solid #f5dab1; border-radius: 10px;
  padding: 10px 16px; margin-bottom: 16px; cursor: pointer; font-size: 13px;
  transition: background var(--duration-fast) var(--ease-out);
}
.demo-banner:hover { background: #fdf3d0; }
.demo-banner-text { font-weight: 600; color: #b88230; }

/* ===== 课程横幅 ===== */
.course-banner {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 24px;
  background: var(--card); border: 1px solid var(--line); border-left: 4px solid var(--primary);
  border-radius: 18px; padding: 28px 32px; margin-bottom: 20px;
  transition: box-shadow var(--duration-normal) var(--ease-out);
}
.course-banner:hover { box-shadow: var(--shadow-md); }
.cb-left { flex: 1; min-width: 0; }
.cb-badge {
  display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: 1px;
  color: var(--primary); background: var(--primary-soft);
  padding: 3px 12px; border-radius: 12px; margin-bottom: 10px;
}
.cb-title { font-size: 22px; font-weight: 800; letter-spacing: -0.3px; margin-bottom: 6px; }
.cb-meta { font-size: 13px; color: var(--muted); margin-bottom: 12px; }
.cb-progress { display: flex; align-items: center; gap: 10px; }
.cb-progress-label { font-size: 12px; color: var(--muted); }
.cb-progress-pct { font-size: 13px; font-weight: 700; }
.cb-actions { display: flex; flex-direction: column; gap: 10px; flex-shrink: 0; }

/* ===== 四大模块卡片 ===== */
.module-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
}
.module-card {
  display: flex; align-items: center; gap: 14px;
  background: var(--card); border: 1px solid var(--line);
  border-left: 3px solid transparent;
  border-radius: 14px; padding: 18px 20px; cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-normal) var(--ease-out),
              transform var(--duration-normal) var(--ease-out);
}
.module-card:nth-child(1) { border-left-color: #3a7bd5; }
.module-card:nth-child(2) { border-left-color: #e6a23c; }
.module-card:nth-child(3) { border-left-color: #67c23a; }
.module-card:nth-child(4) { border-left-color: #909399; }
.module-card:hover {
  border-color: #909090; box-shadow: var(--shadow-md); transform: translateY(-2px);
}
.mc-icon {
  width: 44px; height: 44px; border-radius: 12px;
  background: var(--soft); display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; color: var(--primary);
  transition: background var(--duration-fast) var(--ease-out);
}
.module-card:hover .mc-icon { background: var(--primary-soft); }
.mc-body { flex: 1; min-width: 0; }
.mc-top { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.mc-label { font-size: 14px; font-weight: 700; }
.mc-desc { font-size: 12px; color: var(--muted); line-height: 1.5; }
.mc-arrow {
  color: var(--muted); flex-shrink: 0;
  transition: transform var(--duration-fast) var(--ease-out);
}
.module-card:hover .mc-arrow { transform: translateX(2px); color: var(--ink); }

/* ===== 统计卡片 ===== */
.stat-card {
  background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 18px 20px; text-align: center;
  transition: box-shadow var(--duration-fast) var(--ease-out);
}
.stat-card:hover { box-shadow: var(--shadow-sm); }
.stat-label { font-size: 12px; color: var(--muted); }
.stat-num { font-size: 28px; font-weight: 800; margin: 6px 0; }
.stat-desc { font-size: 12px; color: var(--muted); }

/* ===== 侧栏卡片 ===== */
.side-card {
  border-radius: 14px; border: 1px solid var(--line); background: var(--card);
}
.card-head-row { display: flex; justify-content: space-between; align-items: center; }

/* 动态 */
.activity-row {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px 0; border-bottom: 1px dashed var(--line);
}
.activity-row:last-child { border-bottom: none; padding-bottom: 0; }
.act-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px;
}
.act-dot--quiz     { background: #3a7bd5; }
.act-dot--feedback { background: #67c23a; }
.act-dot--comment  { background: #e6a23c; }
.act-dot--system   { background: #909399; }
.act-body { flex: 1; min-width: 0; }
.act-title { font-size: 13px; font-weight: 700; }
.act-desc { font-size: 12px; color: var(--muted); margin-top: 2px; }
.act-time { font-size: 11px; color: var(--muted); flex-shrink: 0; }

/* 反馈快捷入口 */
.fb-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px dashed var(--line);
  cursor: pointer; font-size: 13px;
  transition: background var(--duration-fast);
}
.fb-row:last-child { border-bottom: none; padding-bottom: 0; }
.fb-row:hover { background: var(--soft); margin: 0 -12px; padding-left: 12px; padding-right: 12px; border-radius: 8px; }
.fb-score-dot {
  width: 34px; height: 34px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800; background: var(--soft);
}
.fb-score-dot--high { background: var(--success-soft); color: var(--success); }
.fb-chapter { flex: 1; font-weight: 600; }
.fb-date { font-size: 11px; color: var(--muted); }

/* 更多入口 */
.extra-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.extra-item {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; border-radius: 10px; cursor: pointer;
  font-size: 13px; color: #4d4d4d;
  transition: background var(--duration-fast) var(--ease-out);
}
.extra-item:hover { background: var(--soft); }
.extra-item .el-icon { color: var(--muted); }
</style>
