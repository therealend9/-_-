<template>
  <div>
    <div class="breadcrumb"><span class="muted">教师端 / 教学工作台</span></div>

    <div class="demo-banner" @click="openDemo">
      <span class="demo-banner-text">📐 查看「教师工作台」静态设计 Demo →</span>
    </div>

    <!-- ===== 当前课程横幅 ===== -->
    <div class="course-banner">
      <div class="cb-left">
        <div class="cb-badge">今日课程</div>
        <h1 class="cb-title">{{ currentCourse.chapter }}</h1>
        <div class="cb-meta">{{ currentCourse.name }} · {{ currentCourse.className }} · {{ currentCourse.time }} 上课</div>
        <div class="cb-progress">
          <span class="cb-progress-label">备课进度</span>
          <el-progress :percentage="currentCourse.progress" :stroke-width="6" :show-text="false" color="#3a7bd5" style="width:160px" />
          <span class="cb-progress-pct">{{ currentCourse.progress }}%</span>
        </div>
      </div>
      <div class="cb-actions">
        <el-button size="large" type="primary" @click="router.push('/teacher/lesson-design')">进入备课</el-button>
        <el-button size="large" @click="router.push('/teacher/class-interaction')">开始上课</el-button>
      </div>
    </div>

    <!-- ===== 四大模块 ===== -->
    <div class="module-grid">
      <div v-for="m in modules" :key="m.key" class="module-card" @click="router.push(m.route)">
        <div class="mc-icon"><el-icon size="22"><component :is="m.icon" /></el-icon></div>
        <div class="mc-body">
          <div class="mc-top">
            <strong class="mc-label">{{ m.label }}</strong>
            <el-tag size="small" :type="m.statusType" effect="plain">{{ m.status }}</el-tag>
          </div>
          <div class="mc-desc">{{ m.desc }}</div>
        </div>
        <el-icon size="16" class="mc-arrow"><ArrowRight /></el-icon>
      </div>
    </div>

    <!-- ===== 统计 ===== -->
    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
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

      <!-- ===== 快捷入口 + 状态 ===== -->
      <el-col :span="10">
        <el-card shadow="never" class="side-card">
          <template #header><strong>快捷入口</strong></template>
          <div class="quick-grid">
            <div v-for="q in quickActions" :key="q.label" class="quick-item" @click="router.push(q.route)">
              <strong>{{ q.label }}</strong>
              <span class="muted small">{{ q.desc }}</span>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="side-card" style="margin-top: 16px" v-for="col in stateCols" :key="col.title">
          <template #header><strong>{{ col.title }}</strong></template>
          <div v-for="(item, i) in col.items" :key="i" class="state-item">{{ item }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, ChatLineRound, Checked, DataAnalysis, Edit } from '@element-plus/icons-vue'
import { getTeacherDashboard } from '../../api/teacher.js'

const router = useRouter()
const currentCourse = ref({ name: '马克思主义基本原理', chapter: '加载中…', className: '', time: '', progress: 0 })

function openDemo() {
  window.open(`${import.meta.env.BASE_URL}教师工作台-静态demo.html`, '_blank')
}
const modules = ref([])
const stats = ref([])
const recentActivity = ref([])
const quickActions = ref([])
const stateCols = ref([])

onMounted(async () => {
  try {
    const data = await getTeacherDashboard()
    currentCourse.value = data.currentCourse || currentCourse.value
    modules.value = data.modules || []
    stats.value = data.stats || []
    recentActivity.value = data.recentActivity || []
    quickActions.value = data.quickActions || []
    stateCols.value = data.stateCols || []
  } catch (e) { console.error('加载工作台失败', e) }
})
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.muted.small { font-size: 12px; }

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
.cb-meta { font-size: 13px; color: var(--muted); margin-bottom: 14px; }
.cb-progress { display: flex; align-items: center; gap: 10px; }
.cb-progress-label { font-size: 12px; color: var(--muted); }
.cb-progress-pct { font-size: 13px; font-weight: 700; }
.cb-actions { display: flex; flex-direction: column; gap: 10px; flex-shrink: 0; }

/* ===== 四模块 ===== */
.module-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 4px; }
.module-card {
  display: flex; align-items: center; gap: 14px;
  background: var(--card); border: 1px solid var(--line); border-left: 3px solid transparent;
  border-radius: 14px; padding: 18px 20px; cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
}
.module-card:nth-child(1) { border-left-color: #67c23a; }
.module-card:nth-child(2) { border-left-color: #409EFF; }
.module-card:nth-child(3) { border-left-color: #e6a23c; }
.module-card:nth-child(4) { border-left-color: #F56C6C; }
.module-card:hover { border-color: #909090; box-shadow: var(--shadow-md); transform: translateY(-2px); }
.mc-icon {
  width: 44px; height: 44px; border-radius: 12px;
  background: var(--soft); display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; color: var(--primary);
  transition: background var(--duration-fast);
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

/* ===== 统计 ===== */
.stat-card {
  background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 18px 20px; text-align: center;
  transition: box-shadow var(--duration-fast);
}
.stat-card:hover { box-shadow: var(--shadow-sm); }
.stat-label { font-size: 12px; color: var(--muted); }
.stat-num { font-size: 28px; font-weight: 800; margin: 6px 0; }
.stat-desc { font-size: 12px; color: var(--muted); }

/* ===== 侧栏 ===== */
.side-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }

/* 动态 */
.activity-row {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px 0; border-bottom: 1px dashed var(--line);
}
.activity-row:last-child { border-bottom: none; padding-bottom: 0; }
.act-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.act-dot--ai      { background: #3a7bd5; }
.act-dot--student { background: #67c23a; }
.act-dot--warn    { background: #F56C6C; }
.act-dot--system  { background: #909399; }
.act-body { flex: 1; min-width: 0; }
.act-title { font-size: 13px; font-weight: 700; }
.act-desc { font-size: 12px; color: var(--muted); margin-top: 2px; }
.act-time { font-size: 11px; color: var(--muted); flex-shrink: 0; }

/* 快捷入口 */
.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.quick-item {
  padding: 12px 14px; border-radius: 10px; cursor: pointer;
  transition: background var(--duration-fast);
}
.quick-item:hover { background: var(--soft); }
.quick-item strong { font-size: 13px; display: block; margin-bottom: 2px; }

/* 状态 */
.state-item {
  font-size: 13px; color: #4d4d4d; padding: 6px 0;
  border-bottom: 1px dashed var(--line);
}
.state-item:last-child { border-bottom: none; }
</style>
