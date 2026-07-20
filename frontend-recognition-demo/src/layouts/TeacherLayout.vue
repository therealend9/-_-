<template>
  <div class="layout">
    <header class="topbar">
      <div class="topbar-left">
        <span class="logo">AI</span>
        <div>
          <div class="platform-name">马原智学 Agent</div>
          <div class="platform-sub">备课、互动、批改复核闭环</div>
        </div>
        <el-tag type="info">{{ info.course }}</el-tag>
        <span class="meta-text">{{ info.semester }}</span>
        <span class="meta-text">{{ info.college }}</span>
      </div>
      <div class="topbar-right">
        <el-icon size="18"><Bell /></el-icon>
        <span class="user-name">{{ info.name }}</span>
        <el-tag size="small" type="warning">教师端</el-tag>
      </div>
    </header>

    <div class="layout-body">
      <aside class="sidebar">
        <div class="sidebar-title">教师教学空间</div>
        <div class="sidebar-sub">备课、上课、批改闭环</div>

        <router-link to="/teacher/dashboard" class="nav-item">
          <el-icon><HomeFilled /></el-icon>
          <span>教师工作台</span>
        </router-link>
        <router-link to="/teacher/lesson-design" class="nav-item">
          <el-icon><Document /></el-icon>
          <span>AI备课中心</span>
        </router-link>
        <router-link to="/teacher/preclass-analytics" class="nav-item">
          <el-icon><DataAnalysis /></el-icon>
          <span>课前学情</span>
        </router-link>
        <router-link to="/teacher/class-interaction" class="nav-item">
          <el-icon><Connection /></el-icon>
          <span>课堂互动</span>
        </router-link>
        <router-link to="/teacher/live-quiz" class="nav-item">
          <el-icon><EditPen /></el-icon>
          <span>随堂微测</span>
        </router-link>
        <router-link to="/teacher/grading-review" class="nav-item">
          <el-icon><Checked /></el-icon>
          <span>批改复核</span>
        </router-link>
        <router-link to="/teacher/class-report" class="nav-item">
          <el-icon><TrendCharts /></el-icon>
          <span>班级报告</span>
        </router-link>
        <router-link to="/teacher/resource-library" class="nav-item">
          <el-icon><Collection /></el-icon>
          <span>资源案例</span>
        </router-link>

        <div class="sidebar-notice">
          <div class="notice-title">教师提醒</div>
          <div v-for="(r, i) in reminders" :key="i" class="notice-item">· {{ r }}</div>
        </div>
      </aside>

      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getTeacherShell } from '../api/platform.js'

const info = ref({
  name: '教师',
  course: '马克思主义基本原理',
  semester: '2025-2026-2',
  college: '马克思主义学院'
})
const reminders = ref([])

onMounted(async () => {
  const data = await getTeacherShell()
  info.value = data.info
  reminders.value = data.notices
})
</script>

<style scoped>
.layout { height: 100vh; display: flex; flex-direction: column; }
.topbar {
  height: 64px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; background: var(--card); border-bottom: 1px solid var(--line); flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; gap: 10px; }
.logo {
  width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
  background: var(--active); border-radius: 10px; font-weight: 800; font-size: 15px;
}
.platform-name { font-size: 17px; font-weight: 700; }
.platform-sub { font-size: 12px; color: var(--muted); }
.meta-text { font-size: 13px; color: var(--muted); }
.topbar-right { display: flex; align-items: center; gap: 10px; }
.user-name { font-size: 14px; font-weight: 600; }
.layout-body { flex: 1; display: flex; overflow: hidden; }
.sidebar {
  width: 220px; background: var(--card); border-right: 1px solid var(--line);
  padding: 16px; flex-shrink: 0; display: flex; flex-direction: column; gap: 2px;
}
.sidebar-title { font-size: 16px; font-weight: 700; margin-bottom: 2px; }
.sidebar-sub { font-size: 12px; color: var(--muted); margin-bottom: 12px; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-radius: 10px; font-size: 14px; color: var(--ink);
  transition: background 0.15s;
}
.nav-item:hover { background: var(--soft); }
.nav-item.router-link-active { background: var(--active); font-weight: 700; }
.sidebar-notice {
  margin-top: auto; padding: 14px; background: var(--soft); border-radius: 12px;
}
.notice-title { font-size: 13px; font-weight: 700; margin-bottom: 6px; }
.notice-item { font-size: 11px; color: var(--muted); line-height: 1.8; }
.main-content { flex: 1; padding: 24px; overflow-y: auto; }
</style>
