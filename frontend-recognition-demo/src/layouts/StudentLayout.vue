<template>
  <div class="layout">
    <header class="topbar">
      <div class="topbar-left">
        <span class="logo">AI</span>
        <div>
          <div class="platform-name">马原智学 Agent</div>
          <div class="platform-sub">课前预学、课中互动、课后反馈</div>
        </div>
        <el-tag type="info" class="course-tag">{{ info.course }}</el-tag>
        <span class="meta-text">{{ info.semester }}</span>
        <span class="meta-text">{{ info.college }}</span>
      </div>
      <div class="topbar-right">
        <el-icon size="18"><Bell /></el-icon>
        <span class="user-name">{{ info.name }}</span>
        <el-tag size="small">学生端</el-tag>
      </div>
    </header>

    <div class="layout-body">
      <aside class="sidebar">
        <div class="sidebar-title">学生学习空间</div>
        <div class="sidebar-sub">本周思政学习任务总览</div>

        <router-link to="/student/dashboard" class="nav-item">
          <el-icon><HomeFilled /></el-icon>
          <span>学生工作台</span>
        </router-link>
        <router-link to="/student/pre-study" class="nav-item">
          <el-icon><Reading /></el-icon>
          <span>课前学习</span>
        </router-link>
        <router-link to="/student/pre-study-quiz" class="nav-item">
          <el-icon><Edit /></el-icon>
          <span>预习小测</span>
        </router-link>
        <router-link to="/student/class-interaction" class="nav-item">
          <el-icon><Connection /></el-icon>
          <span>课中互动</span>
        </router-link>
        <router-link to="/student/in-class-quiz" class="nav-item">
          <el-icon><Timer /></el-icon>
          <span>随堂测验</span>
        </router-link>
        <router-link to="/student/ai-qa" class="nav-item">
          <el-icon><ChatDotRound /></el-icon>
          <span>学科问答</span>
        </router-link>
        <router-link to="/student/feedback" class="nav-item">
          <el-icon><Checked /></el-icon>
          <span>课后反馈</span>
        </router-link>
        <router-link to="/student/learning-report" class="nav-item">
          <el-icon><TrendCharts /></el-icon>
          <span>学习报告</span>
        </router-link>
        <router-link to="/student/knowledge-graph" class="nav-item">
          <el-icon><Share /></el-icon>
          <span>知识图谱</span>
        </router-link>
        <router-link to="/student/notifications" class="nav-item">
          <el-icon><Bell /></el-icon>
          <span>消息通知</span>
        </router-link>
        <router-link to="/student/profile" class="nav-item">
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </router-link>

        <div class="sidebar-divider"></div>
        <router-link to="/student/pre-study-demo" class="nav-item nav-demo">
          <el-icon><View /></el-icon>
          <span>📖 案例演示</span>
        </router-link>

        <div class="sidebar-notice">
          <div class="notice-title">平台公告</div>
          <div v-for="(n, i) in notifications" :key="i" class="notice-item">· {{ n.content }}</div>
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
import { getStudentShell } from '../api/platform.js'

const info = ref({
  name: '学生',
  course: '马克思主义基本原理',
  semester: '2025-2026-2',
  college: '马克思主义学院'
})
const notifications = ref([])

onMounted(async () => {
  const data = await getStudentShell()
  info.value = data.info
  notifications.value = data.notices
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
.course-tag { margin-left: 8px; }
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
.sidebar-divider { height: 1px; background: var(--line); margin: 6px 8px; }
.nav-demo { font-size: 13px; opacity: 0.85; }
.nav-demo:hover { opacity: 1; background: #fef9e7; }
.sidebar-notice {
  margin-top: auto; padding: 14px; background: var(--soft); border-radius: 12px;
}
.notice-title { font-size: 13px; font-weight: 700; margin-bottom: 6px; }
.notice-item { font-size: 11px; color: var(--muted); line-height: 1.8; }
.main-content { flex: 1; padding: 24px; overflow-y: auto; }
</style>
