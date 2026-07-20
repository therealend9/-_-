<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">学生端 / 课前学习 / 章节列表</span></div>
    <div class="page-header">
      <h1>课前学习中心</h1>
      <div class="header-actions">
        <el-button @click="$router.push('/student/ai-qa')">
          <el-icon><ChatDotRound /></el-icon>向 AI 提问
        </el-button>
        <el-button type="primary" @click="$router.push('/student/pre-study-quiz')">
          <el-icon><Edit /></el-icon>进入预习小测
        </el-button>
      </div>
    </div>
    <p class="page-desc">围绕《马克思主义基本原理》共 {{ overview.totalChapters }} 章完成导学、概念预习、小测和课前问题提交</p>

    <!-- 案例演示入口 -->
    <div class="demo-banner" @click="$router.push('/student/pre-study-demo')">
      <span class="demo-banner-icon">📖</span>
      <span class="demo-banner-text">查看"课前学习"模块的完整实现案例演示 →</span>
    </div>

    <!-- 学习概览统计 -->
    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#f0f9eb;color:#67C23A">
            <el-icon size="22"><Checked /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.completedChapters }}/{{ overview.totalChapters }}</div>
            <div class="stat-label">已完成章节</div>
            <div class="stat-sub">{{ overview.inProgressChapters }} 章进行中</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#ecf5ff;color:#409EFF">
            <el-icon size="22"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.progressPercent }}%</div>
            <div class="stat-label">整体完成进度</div>
            <el-progress :percentage="overview.progressPercent" :show-text="false" :stroke-width="6" style="margin-top:6px" />
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fdf6ec;color:#E6A23C">
            <el-icon size="22"><Timer /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview.totalStudyMinutes }} 分钟</div>
            <div class="stat-label">预计总学习时长</div>
            <div class="stat-sub">{{ overview.completedTasks }}/{{ overview.totalTasks }} 个任务已完成</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fef0f0;color:#F56C6C">
            <el-icon size="22"><AlarmClock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ countdownText }}</div>
            <div class="stat-label">下次小测截止</div>
            <div class="stat-sub">{{ overview.nextQuizDeadline }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 左侧：章节列表 -->
      <el-col :span="16">
        <div class="section-title-row">
          <strong>课程章节</strong>
          <el-tag size="small" type="info">{{ overview.totalChapters }} 章</el-tag>
        </div>

        <div
          v-for="chapter in chapters"
          :key="chapter.id"
          class="chapter-card"
          :class="{ 'chapter-completed': chapter.status === '已完成', 'chapter-active': chapter.status === '进行中' }"
          @click="$router.push(`/student/pre-study/${chapter.id}`)"
        >
          <div class="chapter-order">
            <span class="order-num">{{ chapter.chapterOrder }}</span>
          </div>
          <div class="chapter-body">
            <div class="chapter-top">
              <strong class="chapter-title">{{ chapter.title }}</strong>
              <el-tag
                size="small"
                :type="chapter.statusType"
                :effect="chapter.status === '进行中' ? 'dark' : 'light'"
              >
                {{ chapter.status }}
              </el-tag>
            </div>
            <div class="chapter-question">
              <el-icon size="14"><QuestionFilled /></el-icon>
              {{ chapter.coreQuestion }}
            </div>
            <div class="chapter-meta">
              <span><el-icon size="13"><Timer /></el-icon> {{ chapter.estimatedMinutes }} 分钟</span>
              <span><el-icon size="13"><Calendar /></el-icon> 截止 {{ chapter.deadline }}</span>
              <span><el-icon size="13"><Document /></el-icon> {{ chapter.completedTasks }}/{{ chapter.totalTasks }} 项任务</span>
            </div>
            <div class="chapter-progress">
              <el-progress
                :percentage="Math.round((chapter.completedTasks / chapter.totalTasks) * 100)"
                :stroke-width="4"
                :show-text="false"
                :color="chapter.status === '已完成' ? '#67C23A' : chapter.status === '进行中' ? '#409EFF' : '#c9c9c9'"
              />
            </div>
          </div>
          <div class="chapter-arrow">
            <el-icon size="18"><ArrowRight /></el-icon>
          </div>
        </div>
      </el-col>

      <!-- 右侧：任务清单 + 快捷入口 -->
      <el-col :span="8">
        <el-card shadow="never" class="side-card">
          <template #header>
            <div class="card-header-row">
              <strong>待完成预习任务</strong>
              <el-tag size="small" type="warning">{{ pendingTaskCount }} 项</el-tag>
            </div>
          </template>
          <div v-if="pendingTasks.length === 0" class="empty-hint">
            <el-empty description="全部完成，太棒了！" :image-size="80" />
          </div>
          <div v-else v-for="task in pendingTasks" :key="`${task.chapterId}-${task.title}`" class="task-row">
            <div class="task-dot" :class="{ done: task.status === '已完成' }"></div>
            <div class="task-info">
              <div class="task-title">{{ task.title }}</div>
              <div class="task-sub">{{ task.chapterTitle }} · {{ task.desc }}</div>
            </div>
            <el-tag size="small" :type="task.statusType">{{ task.status }}</el-tag>
          </div>
        </el-card>

        <el-card shadow="never" class="side-card" style="margin-top: 16px">
          <template #header><strong>快捷入口</strong></template>
          <div
            v-for="action in quickActions"
            :key="action.route"
            class="quick-entry"
            @click="$router.push(action.route)"
          >
            <div class="entry-icon">
              <el-icon size="18"><component :is="action.icon" /></el-icon>
            </div>
            <div class="entry-info">
              <strong>{{ action.label }}</strong>
              <span class="muted small">{{ action.desc }}</span>
            </div>
            <el-icon size="16"><ArrowRight /></el-icon>
          </div>
        </el-card>

        <!-- 学习小贴士 -->
        <div class="tip-card">
          <div class="tip-icon">💡</div>
          <div class="tip-text">
            <strong>学习建议</strong>
            <p>先阅读导学了解章节框架，再记忆核心概念，最后通过小测检验理解。遇到困惑可以随时向 AI 学伴提问。</p>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AlarmClock, ArrowRight, Calendar, ChatDotRound, Checked, Document,
  Edit, QuestionFilled, Timer, TrendCharts
} from '@element-plus/icons-vue'
import { getPreStudyContent } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const chapters = ref([])
const overview = ref({
  totalChapters: 0, completedChapters: 0, inProgressChapters: 0,
  progressPercent: 0, totalTasks: 0, completedTasks: 0,
  totalStudyMinutes: 0, nextQuizDeadline: ''
})
const tasks = ref([])
const quickActions = ref([])
const now = ref(Date.now())

// 倒计时文本
const countdownText = computed(() => {
  const deadline = new Date('2026-07-18T22:00:00')
  const diff = deadline - now.value
  if (diff <= 0) return '已截止'
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  return `${days} 天 ${hours} 小时`
})

// 待完成任务
const pendingTasks = computed(() => tasks.value.filter(t => t.status !== '已完成'))
const pendingTaskCount = computed(() => pendingTasks.value.length)

// 每秒更新倒计时
let timer = null
onMounted(() => {
  runPageLoad(loading, async () => {
    const data = await getPreStudyContent()
    chapters.value = data.chapters || []
    overview.value = data.overview || overview.value
    tasks.value = data.tasks || []
    quickActions.value = data.quickActions || []
  })
  timer = setInterval(() => { now.value = Date.now() }, 1000)
})
onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; max-width: 65ch; }

/* 案例演示入口 */
.demo-banner {
  margin-top: 14px; display: flex; align-items: center; gap: 10px;
  background: #fef9e7; border: 1px solid #f5dab1; border-radius: 10px;
  padding: 10px 16px; cursor: pointer; font-size: 13px;
  transition: background var(--duration-fast) var(--ease-out);
}
.demo-banner:hover { background: #fdf3d0; }
.demo-banner-icon { font-size: 18px; }
.demo-banner-text { font-weight: 600; color: #b88230; }

/* 统计卡片 */
.stat-card {
  display: flex; align-items: center; gap: 14px;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 16px 18px;
  transition: box-shadow var(--duration-fast) var(--ease-out),
              transform var(--duration-fast) var(--ease-out);
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.stat-icon {
  width: 46px; height: 46px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: transform var(--duration-fast) var(--ease-out);
}
.stat-card:hover .stat-icon { transform: scale(1.05); }
.stat-info { flex: 1; min-width: 0; }
.stat-value { font-size: 22px; font-weight: 800; line-height: 1.2; letter-spacing: -0.3px; }
.stat-label { font-size: 12px; color: var(--muted); margin-top: 2px; }
.stat-sub { font-size: 11px; color: var(--muted); margin-top: 2px; }

/* 章节列表 */
.section-title-row {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 12px; font-size: 16px;
}

.chapter-card {
  display: flex; align-items: center; gap: 16px;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 18px 20px;
  margin-bottom: 10px; cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-normal) var(--ease-out),
              transform var(--duration-normal) var(--ease-out);
}
.chapter-card:hover {
  border-color: #909090;
  box-shadow: var(--shadow-md);
  transform: translateX(3px);
}
.chapter-card.chapter-completed { border-left: 4px solid var(--success); }
.chapter-card.chapter-active { border-left: 4px solid var(--primary); }

.chapter-order {
  width: 42px; height: 42px; border-radius: 12px;
  background: var(--soft); display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; font-variant-numeric: tabular-nums;
  transition: background var(--duration-fast) var(--ease-out);
}
.chapter-completed .chapter-order { background: var(--success-soft); color: var(--success); }
.chapter-active .chapter-order { background: var(--primary-soft); color: var(--primary); }
.order-num { font-size: 17px; font-weight: 800; }

.chapter-body { flex: 1; min-width: 0; }
.chapter-top { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.chapter-title { font-size: 15px; font-weight: 700; letter-spacing: -0.2px; }
.chapter-question {
  font-size: 13px; color: var(--muted);
  display: flex; align-items: flex-start; gap: 6px;
  margin-bottom: 8px; line-height: 1.55;
}
.chapter-question .el-icon { color: var(--primary); flex-shrink: 0; margin-top: 2px; }
.chapter-meta {
  display: flex; gap: 16px; flex-wrap: wrap;
  font-size: 12px; color: var(--muted);
  margin-bottom: 8px;
}
.chapter-meta span { display: flex; align-items: center; gap: 4px; }
.chapter-progress { width: 100%; }
.chapter-arrow {
  color: var(--muted); flex-shrink: 0;
  transition: transform var(--duration-fast) var(--ease-out), color var(--duration-fast);
}
.chapter-card:hover .chapter-arrow { transform: translateX(3px); color: var(--ink); }

/* 右侧卡片 */
.side-card {
  border-radius: 14px; border: 1px solid var(--line);
  background: var(--card); overflow: hidden;
}
.card-header-row { display: flex; justify-content: space-between; align-items: center; }

.task-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px dashed var(--line);
  transition: background var(--duration-fast) var(--ease-out);
}
.task-row:hover { background: var(--soft); margin: 0 -12px; padding-left: 12px; padding-right: 12px; border-radius: 8px; }
.task-row:last-child { border-bottom: none; }
.task-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--muted); flex-shrink: 0;
  transition: background var(--duration-fast) var(--ease-out);
}
.task-dot.done { background: var(--success); }
.task-info { flex: 1; min-width: 0; }
.task-title { font-size: 13px; font-weight: 600; }
.task-sub { font-size: 11px; color: var(--muted); margin-top: 2px; }

.empty-hint { text-align: center; padding: 20px 0; }

/* 快捷入口 */
.quick-entry {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; border-radius: 10px;
  margin-bottom: 2px; cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out),
              transform var(--duration-fast) var(--ease-out);
}
.quick-entry:hover { background: var(--soft); transform: translateX(2px); }
.quick-entry:last-child { margin-bottom: 0; }
.entry-icon {
  width: 38px; height: 38px; border-radius: 10px;
  background: var(--active); display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: background var(--duration-fast) var(--ease-out);
}
.quick-entry:hover .entry-icon { background: var(--primary-soft); }
.entry-info { flex: 1; min-width: 0; }
.entry-info strong { font-size: 13px; display: block; }
.entry-info span { font-size: 11px; display: block; margin-top: 2px; }

/* 小贴士 */
.tip-card {
  display: flex; gap: 12px; margin-top: 16px;
  background: linear-gradient(135deg, var(--soft) 0%, var(--active) 100%);
  border: 1px dashed var(--line);
  border-radius: 14px; padding: 16px;
}
.tip-icon { font-size: 24px; flex-shrink: 0; line-height: 1; opacity: 0.85; }
.tip-text strong { font-size: 13px; }
.tip-text p { font-size: 12px; color: var(--muted); margin-top: 6px; line-height: 1.7; }
</style>
