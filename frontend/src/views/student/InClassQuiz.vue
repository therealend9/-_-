<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">学生端 / 课中互动 / 随堂测验</span></div>

    <!-- ========== 活跃测验：答题模式 ========== -->
    <template v-if="activeQuiz">
      <div class="page-header">
        <div>
          <h1>随堂测验</h1>
          <p class="page-desc">教师已推送 {{ activeQuiz.questions.length }} 道题 · 限时 {{ activeQuiz.durationMinutes }} 分钟</p>
        </div>
        <el-tag :type="wsConnected ? 'success' : 'danger'" size="small" effect="plain">
          {{ wsConnected ? '实时已连接' : '实时未连接' }}
        </el-tag>
      </div>

      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="16">
          <el-card
            shadow="never" class="card"
            v-for="(q, i) in activeQuiz.questions" :key="q.id"
            style="margin-bottom: 16px"
          >
            <template #header>
              <div class="q-head">
                <span class="q-num">{{ i + 1 }}</span>
                <span class="q-type">{{ q.type === 'single' ? '单选题' : q.type === 'judge' ? '判断题' : '多选题' }}</span>
                <el-tag size="small" effect="plain">{{ q.knowledgePoint }}</el-tag>
              </div>
            </template>
            <p class="q-stem">{{ q.stem }}</p>

            <el-radio-group
              v-if="q.type === 'single' || q.type === 'judge'"
              v-model="userAnswers[q.id]"
              class="options"
            >
              <el-radio v-for="(opt, oi) in q.options" :key="oi" :value="oi" size="large">
                {{ String.fromCharCode(65 + oi) }}. {{ opt }}
              </el-radio>
            </el-radio-group>

            <el-checkbox-group
              v-else
              v-model="userAnswers[q.id]"
              class="options"
            >
              <el-checkbox v-for="(opt, oi) in q.options" :key="oi" :value="oi" size="large">
                {{ String.fromCharCode(65 + oi) }}. {{ opt }}
              </el-checkbox>
            </el-checkbox-group>
          </el-card>

          <div class="submit-row">
            <el-button
              type="primary" size="large"
              :loading="submitting"
              :disabled="answeredCount < activeQuiz.questions.length"
              @click="submitQuiz"
            >
              {{ submitting ? '提交中...' : `提交测验（${answeredCount}/${activeQuiz.questions.length}）` }}
            </el-button>
          </div>
        </el-col>

        <el-col :span="8">
          <el-card shadow="never" class="card">
            <template #header><strong>答题卡</strong></template>
            <div class="answer-grid">
              <div
                v-for="(q, i) in activeQuiz.questions" :key="q.id"
                class="answer-cell"
                :class="{ done: isQuizAnswered(q.id) }"
              >
                {{ i + 1 }}
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- ========== 无活跃测验：等待 + 历史记录 ========== -->
    <template v-else>
      <div class="wait-wrapper">
        <div class="wait-card">
          <div class="wait-icon">
            <span class="wait-dot"></span>
          </div>
          <h1 class="wait-title">等待教师推送</h1>
          <p class="wait-desc">教师推送随堂测验后将自动切换为答题模式</p>
          <p class="wait-hint" v-if="!wsConnected">实时连接中断，正在轮询检查…</p>
          <el-button class="wait-refresh" @click="loadHistory">刷新</el-button>

          <!-- 历史推送记录 -->
          <div class="history-section">
            <div class="history-divider"></div>
            <h2 class="history-title">历史推送</h2>
            <div v-if="quizHistory.length === 0" class="history-empty">暂无历史推送记录</div>
            <div v-for="session in quizHistory" :key="session.id" class="history-card">
              <div class="hc-head">
                <div>
                  <strong class="hc-name">{{ session.title }}</strong>
                  <span class="hc-date">{{ session.pushedAt }}</span>
                </div>
                <div class="hc-score" :class="{ 'hc-score--full': session.errors.length === 0 }">
                  {{ session.score }}<span class="hc-score-unit">分</span>
                  <span class="hc-score-sub"> {{ session.correctCount }}/{{ session.totalQuestions }} 正确</span>
                </div>
              </div>
              <div v-if="session.errors.length > 0" class="hc-errors">
                <div v-for="(e, ei) in session.errors" :key="ei" class="hce-item">
                  <div class="hce-q">{{ e.question }}</div>
                  <div class="hce-row">
                    <span class="hce-badge hce-badge--wrong">你的答案：{{ e.yourAnswer }}</span>
                    <span class="hce-badge hce-badge--correct">正确：{{ e.correct }}</span>
                  </div>
                  <div class="hce-reason">{{ e.reason }}（{{ e.source }}）</div>
                </div>
              </div>
              <div v-else class="hc-all-correct">全部正确 ✓</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getInClassQuizDetail, getActiveQuiz, submitInClassQuiz } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'
import { subscribeLiveInteraction } from '../../realtime/liveInteraction.js'

const loading = ref(true), submitting = ref(false)
const quizHistory = ref([])
const activeQuiz = ref(null), userAnswers = reactive({})
const wsConnected = ref(false)
let unsub = () => {}
let pollTimer = null
let lastQuizId = null

const answeredCount = computed(() => {
  if (!activeQuiz.value) return 0
  return activeQuiz.value.questions.filter(q => {
    const ans = userAnswers[q.id]
    return ans !== undefined && (Array.isArray(ans) ? ans.length > 0 : ans >= 0)
  }).length
})

function isQuizAnswered(qId) {
  const ans = userAnswers[qId]
  if (ans === undefined) return false
  if (Array.isArray(ans)) return ans.length > 0
  return ans >= 0
}

async function loadHistory() {
  await runPageLoad(loading, async () => {
    const data = await getInClassQuizDetail()
    quizHistory.value = data.history || []
  })
}

async function pollActiveQuiz() {
  try {
    const data = await getActiveQuiz()
    if (data.active && data.quiz) {
      if (lastQuizId === data.quiz.id) return
      lastQuizId = data.quiz.id
      applyQuizData({ ...data.quiz, questions: data.quiz.questions || [] })
    } else if (lastQuizId && !data.active) {
      lastQuizId = null
      if (activeQuiz.value) {
        ElMessage.info('教师已关闭随堂测验')
      }
    }
  } catch { /* 轮询失败静默 */ }
}

function applyQuizData(data) {
  activeQuiz.value = { ...data, questions: data.questions || [], durationMinutes: data.durationMinutes || 5 }
  Object.keys(userAnswers).forEach(k => delete userAnswers[k])
  ElMessage.warning(`教师推送了 ${data.questionCount || data.questions?.length || 0} 道随堂测验题！`)
}

async function submitQuiz() {
  if (submitting.value || !activeQuiz.value) return
  submitting.value = true
  try {
    const answers = activeQuiz.value.questions.map(q => ({
      questionId: q.id,
      selectedIndex: q.type === 'multiple' ? userAnswers[q.id] || [] : userAnswers[q.id]
    }))
    const data = await submitInClassQuiz(answers)

    const isFullMark = data.score === 100
    if (isFullMark) {
      ElMessage.success({ message: '🎉 满分！恭喜你呀，真厉害！', duration: 3000 })
    } else {
      ElMessage.warning({ message: `得分 ${data.score} 分，${data.correctCount}/${data.total} 正确。点击下方「历史推送」查看错题详情`, duration: 4000 })
    }

    setTimeout(() => {
      activeQuiz.value = null
      loadHistory()
    }, 2000)
  } catch (e) { ElMessage.error(e?.message || '提交失败') }
  finally { submitting.value = false }
}

onMounted(() => {
  loadHistory()
  unsub = subscribeLiveInteraction({
    onQuizPublished: (data) => { applyQuizData({ ...data, questions: data.questions || [] }) },
    onQuizClosed: () => {
      lastQuizId = null
      if (activeQuiz.value) { ElMessage.info('教师已关闭随堂测验') }
    },
    onConnected: () => { wsConnected.value = true },
    onDisconnected: () => { wsConnected.value = false }
  })
  pollTimer = setInterval(pollActiveQuiz, 5000)
  pollActiveQuiz()
})

onUnmounted(() => {
  unsub()
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
})
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }

/* ===== 活跃测验：答题模式 ===== */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-header h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }

.card {
  border-radius: 14px; border: 1px solid var(--line);
  background: var(--card);
  transition: box-shadow var(--duration-fast) var(--ease-out);
}
.card:hover { box-shadow: var(--shadow-sm); }

.q-head { display: flex; align-items: center; gap: 10px; }
.q-num {
  width: 26px; height: 26px; border-radius: 8px;
  background: var(--active); display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 13px;
}
.q-type { font-weight: 700; font-size: 13px; }
.q-stem { font-size: 15px; font-weight: 700; margin-bottom: 16px; line-height: 1.7; }

.options { display: flex; flex-direction: column; gap: 6px; align-items: flex-start; }
.options .el-radio, .options .el-checkbox {
  padding: 8px 14px; border-radius: 10px; width: 100%;
  border: 1px solid transparent;
  transition: background var(--duration-fast) var(--ease-out);
}
.options .el-radio:hover, .options .el-checkbox:hover {
  background: var(--soft); border-color: var(--line);
}

.submit-row { margin-top: 8px; text-align: center; }

.answer-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.answer-cell {
  width: 42px; height: 42px; display: flex; align-items: center; justify-content: center;
  border-radius: 10px; font-size: 15px; font-weight: 700;
  background: #fcfcfa; border: 2px solid var(--line);
  transition: all var(--duration-fast) var(--ease-out);
}
.answer-cell.done { background: var(--active); border-color: #909090; }

/* ===== 等待模式 ===== */
.wait-wrapper {
  display: flex; justify-content: center; padding: 60px 0;
}
.wait-card {
  max-width: 680px; width: 100%;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 20px; padding: 48px 44px 40px;
  text-align: center;
  transition: box-shadow var(--duration-normal) var(--ease-out);
}
.wait-card:hover { box-shadow: var(--shadow-lg); }

.wait-icon {
  display: flex; justify-content: center; margin-bottom: 20px;
}
.wait-dot {
  width: 12px; height: 12px; border-radius: 50%; background: var(--warning);
  animation: wait-pulse 2s ease-in-out infinite;
}
@keyframes wait-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(1.3); }
}

.wait-title {
  font-size: 22px; font-weight: 800; letter-spacing: -0.3px; margin-bottom: 8px;
}
.wait-desc {
  font-size: 14px; color: var(--muted); margin-bottom: 4px;
}
.wait-hint {
  font-size: 12px; color: var(--danger); margin-bottom: 16px;
}

.wait-refresh { margin-top: 12px; }

/* 历史推送记录（在卡片内） */
.history-divider {
  height: 1px; background: var(--line); margin: 28px 0 24px;
}
.history-section {
  text-align: left;
}
.history-title {
  font-size: 16px; font-weight: 700; margin-bottom: 14px;
  letter-spacing: -0.2px;
}
.history-empty {
  font-size: 13px; color: var(--muted); padding: 16px 0; text-align: center;
}
.history-card {
  background: var(--soft); border: 1px solid var(--line);
  border-radius: 12px; padding: 18px 20px; margin-bottom: 10px;
  transition: box-shadow var(--duration-fast) var(--ease-out);
}
.history-card:hover { box-shadow: var(--shadow-sm); }

.hc-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 16px; margin-bottom: 10px;
}
.hc-name { font-size: 14px; font-weight: 700; display: block; }
.hc-date { font-size: 12px; color: var(--muted); display: block; margin-top: 2px; }
.hc-score {
  font-size: 28px; font-weight: 800; letter-spacing: -0.5px;
  color: var(--warning); text-align: right; flex-shrink: 0; line-height: 1.1;
}
.hc-score--full { color: var(--success); }
.hc-score-unit { font-size: 15px; font-weight: 600; }
.hc-score-sub { display: block; font-size: 12px; font-weight: 500; color: var(--muted); letter-spacing: 0; }

.hc-all-correct {
  font-size: 13px; color: var(--success); font-weight: 600;
}

.hc-errors { border-top: 1px dashed var(--line); padding-top: 10px; }
.hce-item { margin-bottom: 10px; }
.hce-item:last-child { margin-bottom: 0; }
.hce-q { font-size: 13px; font-weight: 600; margin-bottom: 6px; line-height: 1.6; }
.hce-row { display: flex; gap: 10px; margin-bottom: 4px; flex-wrap: wrap; }
.hce-badge {
  font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 600;
}
.hce-badge--wrong   { background: var(--danger-soft); color: #c62828; }
.hce-badge--correct { background: var(--success-soft); color: #2e7d32; }
.hce-reason { font-size: 12px; color: var(--muted); line-height: 1.6; }
</style>
