<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 首页 / 平台工作台</span></div>
    <div class="page-header">
      <h1>管理端工作台</h1>
      <div class="header-actions">
        <el-button>查看平台概览</el-button>
        <el-button type="primary">导出运行日报</el-button>
      </div>
    </div>
    <p class="page-desc">把管理首页收成待处理队列、治理入口和运行状态三部分，先分流再深处理</p>

    <!-- 待处理 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header><strong>今天先处理什么</strong></template>
          <div class="hero-box">
            <div class="hero-label">管理端入口页 / 队列优先</div>
            <div class="hero-title">先看待处理队列，再决定进入教学治理、内容治理还是运行治理</div>
            <p class="hero-desc">首页只回答两件事：今天哪里有问题、下一步该进哪个处理台。</p>
            <div class="hero-actions">
              <el-button type="primary">处理待审核</el-button>
              <el-button>进入治理入口</el-button>
            </div>
          </div>
          <el-row :gutter="16" style="margin-top: 16px">
            <el-col :span="12" v-for="s in statusCards" :key="s.label">
              <div class="status-card">
                <div class="status-label">{{ s.label }}</div>
                <div class="status-value">{{ s.value }}</div>
                <div class="status-desc">{{ s.desc }}</div>
                <el-tag size="small" :type="s.tagType">{{ s.tag }}</el-tag>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>进入治理页面</strong></template>
          <div class="entry-item" v-for="e in entries" :key="e.title" @click="e.route && $router.push(e.route)" style="cursor: pointer">
            <div>
              <strong>{{ e.title }}</strong>
              <div class="muted small">{{ e.desc }}</div>
            </div>
            <el-tag size="small" type="info">{{ e.tag }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 待处理队列 + 最近状态 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header><strong>今日待处理队列</strong></template>
          <div v-for="(q, i) in adminQueue" :key="i" style="margin-bottom: 14px">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <strong style="font-size: 14px">{{ q.title }}</strong>
              <el-tag size="small" :color="q.color" style="color: #fff; border: none">{{ q.level }}</el-tag>
            </div>
            <div class="muted" style="font-size: 12px; margin-top: 2px">{{ q.count }} 条待处理</div>
            <el-divider v-if="i < adminQueue.length - 1" style="margin: 10px 0" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>平台核心指标</strong></template>
          <div class="stat-row">
            <div class="stat-card" v-for="stat in coreStats" :key="stat.label">
              <div class="muted">{{ stat.label }}</div>
              <div class="stat-num" :style="{ color: stat.color }">{{ stat.value }}</div>
              <div class="muted small">{{ stat.desc }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getAdminDashboard } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const loading = ref(true)
const adminQueue = ref([])
const statusCards = ref([])
const entries = ref([])
const coreStats = ref([])

onMounted(() => runPageLoad(loading, async () => {
  const data = await getAdminDashboard()
  adminQueue.value = data.adminQueue || []
  statusCards.value = data.statusCards || []
  entries.value = data.entries || []
  coreStats.value = data.coreStats || []
}))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.hero-box { background: var(--active); border-radius: 14px; padding: 20px 24px; border: 1px solid #606060; }
.hero-label { font-size: 12px; color: var(--muted); font-weight: 700; }
.hero-title { font-size: 19px; font-weight: 800; margin: 8px 0; }
.hero-desc { font-size: 13px; color: var(--muted); margin-bottom: 14px; }
.hero-actions { display: flex; gap: 10px; }
.status-card { background: var(--soft); border-radius: 12px; padding: 14px 16px; border: 1px dashed var(--line); }
.status-label { font-size: 14px; font-weight: 600; color: var(--muted); }
.status-value { font-size: 22px; font-weight: 800; margin: 4px 0; }
.status-desc { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
.entry-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px dashed var(--line); }
.entry-item:last-child { border-bottom: none; }
.stat-row { display: flex; gap: 16px; }
.stat-card {
  flex: 1; background: var(--soft); border-radius: 14px;
  padding: 18px 20px; border: 1px dashed var(--line);
}
.stat-num { font-size: 28px; font-weight: 700; margin: 4px 0; }
</style>
