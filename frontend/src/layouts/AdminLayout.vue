<template>
  <div class="layout">
    <header class="topbar">
      <div class="topbar-left">
        <span class="logo">AI</span>
        <div>
          <div class="platform-name">马原智学 Agent</div>
          <div class="platform-sub">知识库、审核、日志治理</div>
        </div>
        <el-tag type="info">{{ info.course }}</el-tag>
        <span class="meta-text">{{ info.semester }}</span>
        <span class="meta-text">{{ info.college }}</span>
      </div>
      <div class="topbar-right">
        <el-icon size="18"><Bell /></el-icon>
        <span class="user-name">{{ info.name }}</span>
        <el-tag size="small" type="danger">管理端</el-tag>
      </div>
    </header>

    <div class="layout-body">
      <aside class="sidebar">
        <div class="sidebar-title">平台治理中心</div>
        <div class="sidebar-sub">全校思政教学运行总览</div>

        <router-link to="/admin/dashboard" class="nav-item">
          <el-icon><HomeFilled /></el-icon>
          <span>管理端工作台</span>
        </router-link>
        <router-link to="/admin/user-management" class="nav-item">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </router-link>
        <router-link to="/admin/org-structure" class="nav-item">
          <el-icon><OfficeBuilding /></el-icon>
          <span>组织架构</span>
        </router-link>
        <router-link to="/admin/course-management" class="nav-item">
          <el-icon><School /></el-icon>
          <span>课程班级</span>
        </router-link>
        <router-link to="/admin/knowledge-base" class="nav-item">
          <el-icon><Collection /></el-icon>
          <span>知识库管理</span>
        </router-link>
        <router-link to="/admin/ai-review" class="nav-item">
          <el-icon><Checked /></el-icon>
          <span>AI内容审核</span>
        </router-link>
        <router-link to="/admin/rubrics" class="nav-item">
          <el-icon><DocumentChecked /></el-icon>
          <span>评分量规</span>
        </router-link>
        <router-link to="/admin/assignment-management" class="nav-item">
          <el-icon><Tickets /></el-icon>
          <span>作业小测</span>
        </router-link>
        <router-link to="/admin/analytics" class="nav-item">
          <el-icon><TrendCharts /></el-icon>
          <span>数据统计</span>
        </router-link>
        <router-link to="/admin/audit-log" class="nav-item">
          <el-icon><List /></el-icon>
          <span>日志审计</span>
        </router-link>
        <router-link to="/admin/system-settings" class="nav-item">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </router-link>
        <router-link to="/admin/role-permission" class="nav-item">
          <el-icon><Key /></el-icon>
          <span>角色权限</span>
        </router-link>

        <div class="sidebar-notice">
          <div class="notice-title">治理提醒</div>
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
import { getAdminShell } from '../api/platform.js'

const info = ref({
  name: '平台管理员',
  course: '全校思政课程',
  semester: '2025-2026-2',
  college: '马克思主义学院'
})
const reminders = ref([])

onMounted(async () => {
  const data = await getAdminShell()
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
