<template>
  <div v-loading="loading" ref="pageRoot">
    <div class="breadcrumb">
      <span class="muted link" @click="router.push('/student/pre-study')">学生端 / 课前学习</span>
      <span class="muted"> / 导学详情</span>
    </div>

    <div class="reading-bar" v-if="readingPercent > 0 && readingPercent < 100">
      <div class="reading-fill" :style="{ width: readingPercent + '%' }"></div>
      <span class="reading-text">阅读进度 {{ readingPercent }}%</span>
    </div>

    <div class="page-header">
      <div>
        <h1>{{ chapter.title }}</h1>
        <p class="page-desc">{{ chapter.course }} · {{ chapter.className }} · {{ chapter.teacher }}</p>
      </div>
      <div class="header-actions">
        <el-button :icon="ArrowLeft" @click="router.push('/student/pre-study')">返回章节列表</el-button>
        <el-button :icon="ChatLineRound" @click="router.push('/student/ai-qa')">向 AI 提问</el-button>
        <el-button :icon="EditPen" type="primary" @click="router.push('/student/pre-study-quiz')">进入小测</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="12" style="margin-top: 16px">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <div class="stat-card">
          <div class="muted small">{{ stat.label }}</div>
          <div class="stat-num" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="muted small">{{ stat.desc }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- ========= 左侧主内容区 ========= -->
      <el-col :span="15">
        <!-- 教师布置任务区 -->
        <el-card shadow="never" class="section-card task-board">
          <template #header>
            <div class="section-header">
              <div class="sh-left">
                <span class="sh-icon">📋</span>
                <strong>王老师布置的学习任务</strong>
                <el-tag size="small" type="warning">{{ teacherTasks.filter(t=>t.required).length }} 项必做</el-tag>
              </div>
              <div class="sh-right">
                <span class="muted small">完成任务可获得积分</span>
              </div>
            </div>
          </template>
          <div class="task-board-grid">
            <div
              v-for="task in teacherTasks"
              :key="task.id"
              class="tb-task"
              :class="{ 'tb-done': task.status === '已完成' }"
            >
              <div class="tb-left">
                <div class="tb-check" :class="{ checked: task.status === '已完成' }">
                  <el-icon v-if="task.status === '已完成'" size="14"><Check /></el-icon>
                  <span v-else>{{ task.id }}</span>
                </div>
              </div>
              <div class="tb-body">
                <div class="tb-title">
                  {{ task.title }}
                  <el-tag
                    v-if="task.typeLabel"
                    size="small"
                    :type="task.type === 'video' ? '' : task.type === 'story' ? 'success' : task.type === 'quiz' ? 'danger' : 'info'"
                    effect="plain"
                  >{{ task.typeLabel }}</el-tag>
                </div>
                <div class="tb-meta">
                  <span v-if="task.required" class="tb-required">● 必做</span>
                  <span v-else class="tb-optional">○ 选做</span>
                  <span class="tb-points">+{{ task.points }} 积分</span>
                  <el-tag v-if="task.status" size="small" :type="task.statusType">{{ task.status }}</el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 导学档案（核心问题 + 学习目标） -->
        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <div class="sh-left">
                <span class="sh-icon">🎯</span>
                <strong>导学档案</strong>
              </div>
              <el-tag type="info">第 {{ chapter.chapterOrder }} 章</el-tag>
            </div>
          </template>
          <div class="guide-hero">
            <div class="hero-label">本节课先解决一个核心问题</div>
            <div class="hero-title">人的认识从哪里来，又怎样在实践中被检验和发展？</div>
            <p>{{ chapter.summary }}</p>
          </div>

          <div class="objective-grid">
            <div v-for="item in learningObjectives" :key="item.type">
              <span class="muted small obj-badge">{{ item.type }}</span>
              <strong>{{ item.content }}</strong>
            </div>
          </div>
        </el-card>

        <!-- ===== 混合多媒体内容块 ===== -->
        <div
          v-for="block in contentBlocks"
          :key="block.id"
          class="content-block-wrapper"
          :class="'block-type-' + block.type"
        >

          <!-- 📹 微视频块 -->
          <div v-if="block.type === 'video'" class="video-block">
            <div class="vb-badge">📹 微视频</div>
            <div class="vb-player">
              <div class="vb-thumb">
                <div class="vb-play-btn">▶</div>
                <span class="vb-duration">{{ block.duration }}</span>
              </div>
            </div>
            <div class="vb-info">
              <h3>{{ block.title }}</h3>
              <p>{{ block.desc }}</p>
              <div class="vb-teacher-note">
                <span>👨‍🏫 老师提示：</span>{{ block.teacherNote }}
              </div>
            </div>
          </div>

          <!-- 📖 趣味故事块 -->
          <div v-else-if="block.type === 'story'" class="story-block">
            <div class="sb-badge">📖 趣味故事</div>
            <div class="sb-scenario">
              <span class="sb-scene-icon">💡</span>
              <em>"{{ block.scenario }}"</em>
            </div>
            <div class="sb-body">
              <p v-for="(para, pi) in block.story.split('\n\n')" :key="pi">{{ para }}</p>
            </div>
            <div class="sb-insight">
              <div class="sb-insight-icon">🔑</div>
              <div>
                <strong>故事启示</strong>
                <p>{{ block.insight }}</p>
              </div>
            </div>
          </div>

          <!-- 📝 文本讲解块 -->
          <div v-else-if="block.type === 'text'" class="text-block">
            <div class="tb-badge">📝 文本讲解</div>
            <h3>{{ block.title }}</h3>
            <div class="text-body">
              <p v-for="(para, pi) in block.content.split('\n\n')" :key="pi" v-html="renderText(para)"></p>
            </div>
          </div>

          <!-- 🧩 概念卡片块 -->
          <div v-else-if="block.type === 'concept'" class="concept-block">
            <div class="cb-badge">🧩 核心概念</div>
            <div class="cb-head">
              <h3>{{ block.name }}</h3>
              <el-tag size="small" type="info">{{ block.source }}</el-tag>
            </div>
            <p class="cb-explain">{{ block.explain }}</p>
            <div class="cb-example">
              <span class="cb-example-label">📗 生活案例</span>
              <p>{{ block.example }}</p>
            </div>
            <div class="cb-misread">
              <span class="cb-misread-label">⚠️ 常见误区</span>
              <p>{{ block.misread }}</p>
            </div>
          </div>
        </div>

        <!-- 小测预览 -->
        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <div class="sh-left">
                <span class="sh-icon">📝</span>
                <strong>小测预览</strong>
              </div>
              <el-button size="small" type="primary" @click="router.push('/student/pre-study-quiz')">开始小测 →</el-button>
            </div>
          </template>
          <el-table :data="quizPreview" style="width: 100%">
            <el-table-column prop="knowledgePoint" label="知识点" width="130" />
            <el-table-column prop="type" label="题型" width="90" align="center" />
            <el-table-column prop="stem" label="题目" min-width="260" />
            <el-table-column prop="review" label="复习建议" min-width="180" />
          </el-table>
        </el-card>
      </el-col>

      <!-- ========= 右侧栏 ========= -->
      <el-col :span="9">
        <!-- 课前问题提交（放在右侧最上面，更醒目） -->
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <div class="sh-left">
                <span class="sh-icon">❓</span>
                <strong>课前问题提交</strong>
              </div>
              <el-tag size="small" type="warning">教师可见</el-tag>
            </div>
          </template>
          <el-input
            v-model="studentQuestion"
            type="textarea"
            :rows="4"
            placeholder="看完视频和故事后，有什么困惑？大胆提出来！"
          />
          <el-button type="primary" style="width: 100%; margin-top: 12px" @click="submitQuestion" :loading="submittingQuestion">
            {{ submittingQuestion ? '提交中...' : '提交问题' }}
          </el-button>
          <p class="muted hint">提交后匿名汇总给教师，帮助教师调整课堂重点。</p>
        </el-card>

        <!-- 积分进度 -->
        <el-card shadow="never" class="section-card" style="margin-top: 16px">
          <template #header>
            <div class="section-header">
              <div class="sh-left">
                <span class="sh-icon">⭐</span>
                <strong>我的积分</strong>
              </div>
              <span class="points-big">{{ earnedPoints }}/{{ totalPoints }}</span>
            </div>
          </template>
          <el-progress :percentage="pointsPercent" :stroke-width="8" :color="pointsPercent >= 80 ? '#67C23A' : '#409EFF'" />
          <p class="muted hint" style="margin-top: 8px">完成全部必做任务可获得 {{ totalPoints }} 积分</p>
        </el-card>

        <!-- 来源引用 -->
        <el-card shadow="never" class="section-card" style="margin-top: 16px">
          <template #header>
            <div class="section-header">
              <div class="sh-left">
                <span class="sh-icon">📚</span>
                <strong>来源引用</strong>
              </div>
            </div>
          </template>
          <div v-for="source in sourceRefs" :key="source.id" class="source-item">
            <div class="source-head">
              <strong>{{ source.title }}</strong>
              <el-tag size="small" type="success">{{ source.status }}</el-tag>
            </div>
            <p>{{ source.type }} · {{ source.locator }}</p>
            <el-button text type="primary" size="small" @click="router.push(`/student/source/${source.id}`)">查看来源 →</el-button>
          </div>
        </el-card>

        <!-- 学习时间线 -->
        <el-card shadow="never" class="section-card" style="margin-top: 16px">
          <template #header>
            <div class="section-header">
              <div class="sh-left">
                <span class="sh-icon">🕐</span>
                <strong>学习时间线</strong>
              </div>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item v-for="(item, i) in timeline" :key="i" :timestamp="item.time">
              <div class="timeline-title">{{ item.title }}</div>
              <div class="muted small">{{ item.desc }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ArrowLeft, ChatLineRound, Check, EditPen } from '@element-plus/icons-vue'
import { getPreStudyDetail, submitPreStudyQuestion } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const chapter = ref({})
const stats = ref([])
const learningObjectives = ref([])
const teacherTasks = ref([])
const contentBlocks = ref([])
const sourceRefs = ref([])
const quizPreview = ref([])
const timeline = ref([])

// 课前问题
const studentQuestion = ref('')
const submittingQuestion = ref(false)

// 积分计算
const totalPoints = computed(() => teacherTasks.value.reduce((s, t) => t.required ? s + t.points : s, 0))
const earnedPoints = computed(() => teacherTasks.value
  .filter(t => t.status === '已完成')
  .reduce((s, t) => t.required ? s + t.points : s, 0))
const pointsPercent = computed(() => totalPoints.value > 0 ? Math.round((earnedPoints.value / totalPoints.value) * 100) : 0)

// 阅读进度追踪
const pageRoot = ref(null)
const readingPercent = ref(0)
let scrollTimer = null

function trackReading() {
  if (!pageRoot.value) return
  const el = pageRoot.value
  const scrollHeight = el.scrollHeight - el.clientHeight
  if (scrollHeight <= 0) { readingPercent.value = 100; return }
  const pct = Math.min(100, Math.round((el.scrollTop / scrollHeight) * 100))
  readingPercent.value = pct
  try {
    localStorage.setItem(`reading-progress-${route.params.chapterId}`, String(pct))
  } catch { /* ignore */ }
}

function handleScroll() {
  clearTimeout(scrollTimer)
  scrollTimer = setTimeout(trackReading, 150)
}

function restoreReading() {
  try {
    const saved = localStorage.getItem(`reading-progress-${route.params.chapterId}`)
    if (saved && pageRoot.value) {
      const pct = parseInt(saved, 10)
      if (pct > 0 && pct < 100) {
        pageRoot.value.scrollTop = (pct / 100) * (pageRoot.value.scrollHeight - pageRoot.value.clientHeight)
      }
    }
  } catch { /* ignore */ }
}

// 富文本渲染：处理 **bold** 标记
function renderText(text) {
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getPreStudyDetail(route.params.chapterId)
  chapter.value = data.chapter || {}
  stats.value = data.stats || []
  learningObjectives.value = data.learningObjectives || []
  teacherTasks.value = data.teacherTasks || []
  contentBlocks.value = data.contentBlocks || []
  sourceRefs.value = data.sourceRefs || []
  quizPreview.value = data.quizPreview || []
  timeline.value = data.timeline || []
  setTimeout(restoreReading, 300)
}))

onMounted(() => {
  const el = pageRoot.value
  if (el) el.addEventListener('scroll', handleScroll, { passive: true })
})
onUnmounted(() => {
  const el = pageRoot.value
  if (el) el.removeEventListener('scroll', handleScroll)
  clearTimeout(scrollTimer)
})

async function submitQuestion() {
  if (!studentQuestion.value.trim()) {
    ElMessage.warning('请先写下一个具体问题')
    return
  }
  submittingQuestion.value = true
  try {
    const result = await submitPreStudyQuestion(studentQuestion.value)
    ElMessage.success(result.message)
    studentQuestion.value = ''
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '提交问题失败')
  } finally {
    submittingQuestion.value = false
  }
}
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.muted.small { font-size: 12px; }
.muted.link { cursor: pointer; transition: color var(--duration-fast); }
.muted.link:hover { text-decoration: underline; color: var(--ink); }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-header h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; max-width: 65ch; }
.header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }

/* 阅读进度条 */
.reading-bar {
  position: sticky; top: 0; z-index: 10;
  height: 3px; background: var(--soft); border-radius: 2px; margin-bottom: 12px; overflow: hidden;
}
.reading-fill { height: 100%; background: var(--primary); border-radius: 2px; transition: width 0.3s var(--ease-out); }
.reading-text { position: absolute; right: 0; top: -18px; font-size: 11px; color: var(--muted); }

/* 统计卡片 */
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 16px 18px;
  border: 1px dashed var(--line); text-align: center;
  transition: transform var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast);
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.stat-num { font-size: 28px; font-weight: 800; margin: 4px 0; letter-spacing: -0.5px; }

/* Section card */
.section-card {
  border-radius: 14px; border: 1px solid var(--line);
  background: var(--card);
  transition: box-shadow var(--duration-fast) var(--ease-out);
}
.section-card:hover { box-shadow: var(--shadow-sm); }
.section-header { display: flex; justify-content: space-between; align-items: center; }
.sh-left { display: flex; align-items: center; gap: 8px; }
.sh-icon { font-size: 18px; }
.sh-right { display: flex; align-items: center; gap: 10px; }

/* 教师任务板 */
.task-board { border-left: 4px solid var(--warning); }
.task-board-grid { display: flex; flex-direction: column; gap: 6px; }
.tb-task {
  display: flex; gap: 14px; padding: 12px 14px;
  background: var(--soft); border-radius: 10px;
  transition: background var(--duration-fast);
}
.tb-task:hover { background: var(--active); }
.tb-task.tb-done { opacity: 0.7; }
.tb-left { flex-shrink: 0; }
.tb-check {
  width: 28px; height: 28px; border-radius: 8px;
  background: var(--active); display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 800; color: var(--muted);
}
.tb-check.checked { background: var(--success-soft); color: var(--success); }
.tb-body { flex: 1; min-width: 0; }
.tb-title { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
.tb-meta { display: flex; align-items: center; gap: 12px; font-size: 12px; }
.tb-required { color: #e6a23c; font-weight: 600; }
.tb-optional { color: var(--muted); }
.tb-points { color: var(--primary); font-weight: 600; }

/* 积分 */
.points-big { font-size: 20px; font-weight: 800; color: var(--primary); }

/* 导学档案 */
.guide-hero {
  background: var(--active); border: 1px solid #606060; border-radius: 14px;
  padding: 20px 22px; margin-bottom: 16px;
}
.hero-label { font-size: 11px; color: var(--muted); font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
.hero-title { font-size: 20px; font-weight: 800; margin: 8px 0; letter-spacing: -0.3px; line-height: 1.4; }
.guide-hero p { font-size: 13px; line-height: 1.75; color: #4d4d4d; }
.objective-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.objective-grid > div {
  background: var(--soft); border-radius: 10px; padding: 12px;
  display: flex; flex-direction: column; gap: 6px;
  transition: background var(--duration-fast);
}
.objective-grid > div:hover { background: var(--active); }
.obj-badge { display: inline-block; background: var(--active); border-radius: 4px; padding: 1px 6px; font-weight: 600; width: fit-content; }

/* === 内容块通用 === */
.content-block-wrapper { margin-top: 20px; }

/* 📹 微视频块 */
.video-block {
  background: #1a1a2e; border-radius: 16px; overflow: hidden;
  color: #e0e0e0; border: 1px solid #333;
}
.vb-badge {
  display: inline-block; background: #e74c3c; color: #fff;
  padding: 4px 12px; border-radius: 0 0 10px 0; font-size: 12px; font-weight: 700;
}
.vb-player { padding: 0 20px 16px; }
.vb-thumb {
  width: 100%; height: 220px; border-radius: 12px;
  background: linear-gradient(135deg, #16213e 0%, #0f3460 50%, #1a1a2e 100%);
  display: flex; align-items: center; justify-content: center; position: relative;
}
.vb-play-btn {
  width: 60px; height: 60px; border-radius: 50%;
  background: rgba(255,255,255,.15); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; color: #fff; cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}
.vb-play-btn:hover { background: rgba(255,255,255,.25); transform: scale(1.08); }
.vb-duration {
  position: absolute; bottom: 12px; right: 16px;
  background: rgba(0,0,0,.7); color: #fff; padding: 3px 10px;
  border-radius: 6px; font-size: 12px; font-weight: 600;
}
.vb-info { padding: 0 20px 20px; }
.vb-info h3 { font-size: 18px; font-weight: 700; margin-bottom: 6px; color: #fff; }
.vb-info p { font-size: 13px; color: #aaa; line-height: 1.6; margin-bottom: 10px; }
.vb-teacher-note {
  background: rgba(255,193,7,.1); border-left: 3px solid #ffc107;
  padding: 10px 14px; border-radius: 0 8px 8px 0; font-size: 12px; color: #ccc; line-height: 1.6;
}

/* 📖 趣味故事块 */
.story-block {
  background: #fef9e7; border: 1px solid #f5dab1; border-radius: 16px;
  overflow: hidden;
}
.sb-badge {
  display: inline-block; background: #67c23a; color: #fff;
  padding: 4px 12px; border-radius: 0 0 10px 0; font-size: 12px; font-weight: 700;
}
.sb-scenario {
  padding: 18px 22px 12px; font-size: 15px; color: #6d4c41;
  display: flex; align-items: flex-start; gap: 8px;
}
.sb-scene-icon { font-size: 20px; flex-shrink: 0; margin-top: 1px; }
.sb-body { padding: 0 22px 16px; }
.sb-body p {
  font-size: 14px; line-height: 2; color: #4d3e2e; text-indent: 2em; margin-bottom: 8px;
  background: #fff; padding: 12px 16px; border-radius: 8px; border: 1px solid #f5dab1;
}
.sb-insight {
  margin: 0 16px 16px; background: #e8f5e9; border: 1px solid #a5d6a7;
  border-radius: 12px; padding: 14px 16px; display: flex; gap: 10px;
}
.sb-insight-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }
.sb-insight strong { font-size: 14px; color: #2e7d32; display: block; margin-bottom: 4px; }
.sb-insight p { font-size: 13px; color: #33691e; line-height: 1.7; margin: 0; }

/* 📝 文本讲解块 */
.text-block {
  background: #fcfcfa; border: 1px solid var(--line); border-radius: 16px;
  padding: 20px 22px;
}
.tb-badge {
  display: inline-block; background: #409eff; color: #fff;
  padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-bottom: 10px;
}
.text-block h3 { font-size: 18px; font-weight: 700; margin-bottom: 14px; }
.text-body p {
  font-size: 14px; line-height: 1.85; color: #4d4d4d; margin-bottom: 12px;
}

/* 🧩 概念卡片块 */
.concept-block {
  background: #fcfcfa; border: 1px solid var(--line); border-radius: 16px;
  padding: 20px 22px; border-left: 4px solid var(--primary);
}
.cb-badge {
  display: inline-block; background: #909399; color: #fff;
  padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-bottom: 10px;
}
.cb-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.cb-head h3 { font-size: 20px; font-weight: 800; }
.cb-explain { font-size: 14px; line-height: 1.8; color: #4d4d4d; margin-bottom: 12px; }
.cb-example {
  background: var(--success-soft); border: 1px solid var(--success-border);
  border-radius: 10px; padding: 12px 14px; margin-bottom: 8px;
}
.cb-example-label { font-size: 11px; font-weight: 700; color: #388e3c; }
.cb-example p { font-size: 13px; color: #33691e; line-height: 1.7; margin: 4px 0 0; }
.cb-misread {
  background: var(--warning-soft); border: 1px solid var(--warning-border);
  border-radius: 10px; padding: 12px 14px;
}
.cb-misread-label { font-size: 11px; font-weight: 700; color: #e6a23c; }
.cb-misread p { font-size: 13px; color: #8d6e00; line-height: 1.7; margin: 4px 0 0; }

/* 来源引用 */
.source-item { padding: 10px 0; border-bottom: 1px dashed var(--line); }
.source-item:last-child { border-bottom: none; }
.source-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.source-head strong { font-size: 13px; }
.source-item p { font-size: 12px; color: var(--muted); margin: 4px 0; }

/* 时间线 */
.timeline-title { font-weight: 800; }

.hint { margin-top: 8px; line-height: 1.6; font-size: 12px; }
</style>
