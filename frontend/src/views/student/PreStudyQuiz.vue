<template>
  <div v-loading="loading">
    <div class="breadcrumb">
      <span class="muted link" @click="router.push('/student/pre-study')">学生端 / 课前学习</span>
      <span class="muted"> / 预习小测</span>
    </div>

    <!-- ========== 未开始：确认开始界面 ========== -->
    <div v-if="!started" class="start-wrapper">
      <div class="start-card">
        <h1 class="start-title">预习小测</h1>

        <!-- 核心指标：仅保留限时和题量 -->
        <div class="start-metrics">
          <div class="metric">
            <span class="metric-num">{{ quizDuration }}</span>
            <span class="metric-label">分钟限时</span>
          </div>
          <div class="metric-divider"></div>
          <div class="metric">
            <span class="metric-num">{{ totalCount }}</span>
            <span class="metric-label">道题目</span>
          </div>
        </div>

        <!-- 一行精简提示 -->
        <p class="start-one-liner">全部答完后提交，即时出分并查看解析</p>

        <!-- 操作区 -->
        <div class="start-actions">
          <el-button size="large" class="btn-start" type="primary" @click="startQuiz" :loading="loading">
            开始小测
          </el-button>
          <el-button size="large" class="btn-back" @click="router.push('/student/pre-study')">
            返回
          </el-button>
        </div>
      </div>
    </div>

    <!-- ========== 已开始：答题界面 ========== -->
    <template v-if="started">
      <div class="page-header">
        <div>
          <h1>预习小测</h1>
          <p class="page-desc">完成 {{ totalCount }} 道小测，系统即时反馈正确答案、知识点、错因与复习建议</p>
        </div>
        <div class="header-actions">
          <!-- 倒计时 -->
          <div class="timer-box" :class="{ 'timer-warn': timerMinutes < 5, 'timer-danger': timerMinutes < 1 }">
            <el-icon size="16"><Timer /></el-icon>
            <span class="timer-text">{{ timerDisplay }}</span>
          </div>
          <span class="muted" v-if="totalCount > 0">已答 {{ answeredCount }}/{{ totalCount }}</span>
          <el-button
            v-if="!submitted"
            type="primary"
            :loading="submitting"
            @click="submitQuiz"
          >
            {{ submitting ? '判分中...' : '提交答卷' }}
          </el-button>
          <el-button
            v-if="submitted && wrongCount > 0"
            type="warning"
            @click="retryWrong"
          >
            重做错题 ({{ wrongCount }})
          </el-button>
          <el-button
            v-if="submitted && retryMode"
            @click="resetQuiz"
          >
            重新开始
          </el-button>
        </div>
      </div>

      <el-alert
        v-if="submitted && !retryMode"
        :title="`本次得分 ${score} 分，共 ${totalCount} 题，正确 ${correctCount} 题。薄弱点：${weakPoints.join('、') || '暂无'}`"
        :type="score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error'"
        :closable="false"
        style="margin-top: 16px"
        show-icon
      />

      <el-alert
        v-if="retryMode"
        title="重做模式：仅显示上次答错的题目，完成后可重新提交"
        type="warning"
        :closable="false"
        style="margin-top: 16px"
        show-icon
      />

      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="16">
          <el-card
            shadow="never"
            class="card"
            v-for="(q, qi) in displayQuestions"
            :key="q.id"
            style="margin-bottom: 20px"
          >
            <template #header>
              <div class="question-head">
                <div class="q-left">
                  <span class="q-number">{{ qi + 1 }}</span>
                  <strong>{{ q.type }}</strong>
                </div>
                <el-tag size="small" :type="submitted && !isCorrect(q) ? 'danger' : 'info'">
                  知识点：{{ q.tag }}
                </el-tag>
              </div>
            </template>
            <p class="question-title">{{ q.title }}</p>

            <!-- 单选题 + 判断题：Radio -->
            <el-radio-group
              v-if="q.type === '单选题' || q.type === '判断题'"
              v-model="q.answer"
              class="options"
              :disabled="submitted && !retryMode"
            >
              <el-radio
                v-for="(opt, oi) in q.options"
                :key="opt"
                :value="oi"
                size="large"
              >
                {{ String.fromCharCode(65 + oi) }}. {{ opt }}
              </el-radio>
            </el-radio-group>

            <!-- 多选题：Checkbox -->
            <el-checkbox-group
              v-if="q.type === '多选题'"
              v-model="q.answer"
              class="options"
              :disabled="submitted && !retryMode"
            >
              <el-checkbox
                v-for="(opt, oi) in q.options"
                :key="opt"
                :value="oi"
                size="large"
              >
                {{ String.fromCharCode(65 + oi) }}. {{ opt }}
              </el-checkbox>
            </el-checkbox-group>

            <!-- 已提交：结果展示 -->
            <div v-if="submitted && !retryMode" class="result-box" :class="{ wrong: !isCorrect(q) }">
              <div class="result-title">
                <el-tag size="small" :type="isCorrect(q) ? 'success' : 'danger'">
                  {{ isCorrect(q) ? '回答正确' : '需要复习' }}
                </el-tag>
                <span>正确答案：{{ correctAnswerLabel(q) }}</span>
              </div>
              <p>{{ q.analysis }}</p>
              <p class="muted">建议复习：{{ q.review }}</p>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card shadow="never" class="card">
            <template #header><strong>答题卡</strong></template>
            <div class="answer-grid">
              <div
                v-for="(q, qi) in displayQuestions"
                :key="q.id"
                class="answer-cell"
                :class="{
                  done: isAnswered(q),
                  wrong: submitted && !isCorrect(q),
                  correct: submitted && isCorrect(q)
                }"
              >
                {{ qi + 1 }}
              </div>
            </div>
            <div class="answer-legend" v-if="submitted">
              <span class="legend-item"><span class="dot correct-dot"></span> 正确</span>
              <span class="legend-item"><span class="dot wrong-dot"></span> 需复习</span>
            </div>
          </el-card>

          <el-card shadow="never" class="card" style="margin-top: 20px">
            <template #header>
              <div class="card-header-row">
                <strong>考试说明</strong>
              </div>
            </template>
            <div class="info-item">
              <el-icon size="14"><Timer /></el-icon>
              <span>限时 {{ quizDuration }} 分钟，超时可继续作答</span>
            </div>
            <div class="info-item">
              <el-icon size="14"><Document /></el-icon>
              <span>共 {{ totalCount }} 题：{{ typeSummary }}</span>
            </div>
            <div class="info-item">
              <el-icon size="14"><InfoFilled /></el-icon>
              <span>提交后可查看解析和正确答案</span>
            </div>
          </el-card>

          <el-card shadow="never" class="card" style="margin-top: 20px">
            <template #header><strong>来源说明</strong></template>
            <div class="source-item">教材：《马克思主义基本原理》第三章</div>
            <div class="source-item">课件：实践与认识课堂讲义</div>
            <div class="source-item">案例库：大学生社会实践调研</div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { Document, InfoFilled, Timer } from '@element-plus/icons-vue'
import { getPreStudyQuiz, submitPreStudyQuiz } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const started = ref(false)         // 是否已确认开始
const submitting = ref(false)
const submitted = ref(false)
const retryMode = ref(false)
const apiResult = ref(null)
const allQuestions = ref([])        // 所有题目（预加载，用于开始页展示题量信息）
const displayQuestions = ref([])    // 当前展示的题目（全部 or 错题）
const quizDuration = 15             // 限时 15 分钟
const elapsedSeconds = ref(0)       // 已用秒数

// 倒计时显示
const timerMinutes = computed(() => Math.max(0, Math.floor((quizDuration * 60 - elapsedSeconds.value) / 60)))
const timerSeconds = computed(() => Math.max(0, Math.floor((quizDuration * 60 - elapsedSeconds.value) % 60)))
const timerDisplay = computed(() => {
  const m = timerMinutes.value
  const s = timerSeconds.value
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const totalCount = computed(() => allQuestions.value.length)
const answeredCount = computed(() => displayQuestions.value.filter((q) => isAnswered(q)).length)
const correctCount = computed(() => allQuestions.value.filter((q) => isCorrect(q)).length)
const wrongCount = computed(() => allQuestions.value.filter((q) => !isCorrect(q)).length)

const score = computed(() => {
  if (apiResult.value?.score !== undefined) return apiResult.value.score
  if (!totalCount.value) return 0
  return Math.round((correctCount.value / totalCount.value) * 100)
})

const weakPoints = computed(() => {
  if (apiResult.value?.weakPoints?.length) return apiResult.value.weakPoints
  return allQuestions.value
    .filter((q) => q.answer !== null && !isCorrect(q))
    .map((q) => q.tag)
})

const typeSummary = computed(() => {
  const counts = {}
  allQuestions.value.forEach(q => {
    counts[q.type] = (counts[q.type] || 0) + 1
  })
  return Object.entries(counts).map(([k, v]) => `${k} ${v} 道`).join('、')
})

// 判断是否已回答
function isAnswered(question) {
  const ans = question.answer
  if (ans === null || ans === undefined) return false
  if (Array.isArray(ans)) return ans.length > 0
  return true
}

// 判断是否正确
function isCorrect(question) {
  const correctIndices = question.correctIndices || [question.correctIndex]
  const answer = question.answer
  if (!Array.isArray(answer)) {
    return answer === (correctIndices.length === 1 ? correctIndices[0] : undefined) &&
      correctIndices.length === 1
  }
  return correctIndices.length === answer.length &&
    correctIndices.every(idx => answer.includes(idx))
}

// 正确答案标签
function correctAnswerLabel(question) {
  const correctIndices = question.correctIndices || [question.correctIndex]
  return correctIndices.map(i => String.fromCharCode(65 + i)).join('、')
}

// 开始小测：确认后进入答题界面并启动计时
async function startQuiz() {
  // 如果 onMounted 已预加载题目，直接复用
  if (allQuestions.value.length > 0) {
    displayQuestions.value = allQuestions.value.map(q => ({ ...q }))
    started.value = true
    startTimer()
    return
  }

  // 兜底：如果没有预加载成功，再次加载
  loading.value = true
  try {
    const questions = await getPreStudyQuiz() || []
    allQuestions.value = questions.map(q => ({
      ...q,
      answer: q.type === '多选题' ? [] : null
    }))
    displayQuestions.value = [...allQuestions.value]
    started.value = true
    startTimer()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '加载题目失败，请重试')
  } finally {
    loading.value = false
  }
}

function startTimer() {
  timerHandle = setInterval(() => {
    if (!submitted.value) {
      elapsedSeconds.value++
    }
  }, 1000)
}

// 提交答卷
async function submitQuiz() {
  if (submitting.value) return
  const unanswered = displayQuestions.value.filter(q => !isAnswered(q))
  if (unanswered.length > 0) {
    ElMessage.warning(`还有 ${unanswered.length} 题未作答，请完成全部题目`)
    return
  }

  submitting.value = true
  try {
    apiResult.value = await submitPreStudyQuiz(
      displayQuestions.value.map((question) => ({
        questionId: question.id,
        selectedIndex: question.answer
      }))
    )
    // 将测试结果也应用到所有 allQuestions
    submitted.value = true
    retryMode.value = false
    displayQuestions.value = [...allQuestions.value]
    ElMessage.success(`提交成功，本次得分 ${score.value} 分`)
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '提交答卷失败')
  } finally {
    submitting.value = false
  }
}

// 重做错题
function retryWrong() {
  const wrongIds = allQuestions.value
    .filter(q => !isCorrect(q))
    .map(q => q.id)
  displayQuestions.value = allQuestions.value
    .filter(q => wrongIds.includes(q.id))
    .map(q => ({ ...q, answer: q.type === '多选题' ? [] : null }))
  retryMode.value = true
  submitted.value = false
  apiResult.value = null
}

// 重新开始
function resetQuiz() {
  displayQuestions.value = allQuestions.value.map(q => ({ ...q, answer: q.type === '多选题' ? [] : null }))
  retryMode.value = false
  submitted.value = false
  apiResult.value = null
  elapsedSeconds.value = 0
}

// 计时器
let timerHandle = null

// 进入页面先预加载题目信息（用于开始页展示），但不启动计时
onMounted(() => runPageLoad(loading, async () => {
  const questions = await getPreStudyQuiz() || []
  allQuestions.value = questions.map(q => ({
    ...q,
    answer: q.type === '多选题' ? [] : null
  }))
}))

onUnmounted(() => {
  clearInterval(timerHandle)
})
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.muted.link { cursor: pointer; transition: color var(--duration-fast); }
.muted.link:hover { text-decoration: underline; color: var(--ink); }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-header h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.header-actions { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; max-width: 65ch; }

/* 倒计时 */
.timer-box {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 10px;
  background: var(--soft); border: 1px solid var(--line);
  transition: background var(--duration-fast) var(--ease-out),
              border-color var(--duration-fast) var(--ease-out);
}
.timer-text {
  font-size: 15px; font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.5px;
}
.timer-warn { background: var(--warning-soft); border-color: var(--warning-border); }
.timer-warn .timer-text { color: var(--warning); }
.timer-danger { background: var(--danger-soft); border-color: var(--danger-border); animation: pulse-border 1s infinite; }
.timer-danger .timer-text { color: var(--danger); }

@keyframes pulse-border {
  0%, 100% { border-color: var(--danger-border); }
  50% { border-color: var(--danger); }
}

.card {
  border-radius: 14px; border: 1px solid var(--line);
  background: var(--card);
  transition: box-shadow var(--duration-fast) var(--ease-out);
}
.card:hover { box-shadow: var(--shadow-sm); }
.card-header-row { display: flex; justify-content: space-between; align-items: center; }

.question-head { display: flex; justify-content: space-between; align-items: center; }
.q-left { display: flex; align-items: center; gap: 10px; }
.q-number {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 8px;
  background: var(--active); font-weight: 800; font-size: 14px;
  transition: background var(--duration-fast) var(--ease-out);
}
.card:hover .q-number { background: var(--primary-soft); }

.question-title { font-size: 15px; font-weight: 700; margin-bottom: 18px; line-height: 1.7; letter-spacing: -0.15px; }

.options { display: flex; flex-direction: column; gap: 8px; align-items: flex-start; }
.options .el-radio, .options .el-checkbox {
  padding: 10px 14px; border-radius: 10px;
  border: 1px solid transparent; transition: background var(--duration-fast) var(--ease-out),
              border-color var(--duration-fast) var(--ease-out);
  width: 100%;
}
.options .el-radio:hover, .options .el-checkbox:hover {
  background: var(--soft); border-color: var(--line);
}

.result-box {
  margin-top: 16px; border-radius: 12px;
  border: 1px solid var(--success-border); background: var(--success-soft);
  padding: 14px 16px; font-size: 13px; line-height: 1.7;
  transition: border-color var(--duration-fast);
}
.result-box.wrong {
  border-color: var(--danger-border); background: var(--danger-soft);
}
.result-title {
  display: flex; align-items: center; gap: 10px;
  font-weight: 700; margin-bottom: 8px;
}
.result-box p { margin: 6px 0; }

.answer-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.answer-cell {
  width: 44px; height: 44px; display: flex; align-items: center; justify-content: center;
  border-radius: 10px; font-size: 16px; font-weight: 700;
  background: #fcfcfa; border: 2px solid var(--line);
  transition: all var(--duration-fast) var(--ease-out);
}
.answer-cell.done { background: var(--active); border-color: #909090; }
.answer-cell.correct { background: var(--success-soft); border-color: var(--success-border); color: var(--success); }
.answer-cell.wrong { background: var(--danger-soft); border-color: var(--danger-border); color: var(--danger); }

.answer-legend { display: flex; gap: 16px; margin-top: 12px; font-size: 12px; color: var(--muted); }
.legend-item { display: flex; align-items: center; gap: 4px; }
.dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.correct-dot { background: var(--success); }
.wrong-dot { background: var(--danger); }

.info-item {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 0; border-bottom: 1px dashed var(--line);
  font-size: 13px; color: var(--muted);
}
.info-item:last-child { border-bottom: none; }
.info-item .el-icon { color: var(--primary); }

.source-item {
  padding: 10px 0; border-bottom: 1px dashed var(--line);
  font-size: 13px; color: var(--muted);
}
.source-item:last-child { border-bottom: none; }

/* ========== 开始确认界面 ========== */
.start-wrapper {
  display: flex; justify-content: center; padding: 48px 0 60px;
}

.start-card {
  max-width: 440px; width: 100%;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 20px; padding: 48px 52px 44px;
  text-align: center;
  transition: box-shadow var(--duration-normal) var(--ease-out);
}
.start-card:hover { box-shadow: var(--shadow-lg); }

.start-title {
  font-size: 28px; font-weight: 800; letter-spacing: -0.4px;
  margin-bottom: 36px;
}

/* 核心指标：两大数字并排 */
.start-metrics {
  display: flex; align-items: center; justify-content: center;
  gap: 0; margin-bottom: 28px;
}
.metric {
  display: flex; flex-direction: column; align-items: center;
  padding: 0 36px;
}
.metric-num {
  font-size: 48px; font-weight: 800; letter-spacing: -1px;
  line-height: 1.1; color: var(--ink);
  font-variant-numeric: tabular-nums;
}
.metric-label {
  font-size: 13px; color: var(--muted); font-weight: 600;
  margin-top: 6px; letter-spacing: 0.3px;
}
.metric-divider {
  width: 1px; height: 56px; background: var(--line);
}

/* 一行提示 */
.start-one-liner {
  font-size: 13px; color: var(--muted); margin-bottom: 32px;
}

/* 操作按钮 */
.start-actions {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
}
.btn-start {
  width: 100%; max-width: 280px; border-radius: 12px;
  font-weight: 700; font-size: 16px; height: 48px;
  letter-spacing: -0.2px;
  transition: transform var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out);
}
.btn-start:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(58, 123, 213, 0.3);
}
.btn-back {
  font-size: 13px; color: var(--muted); font-weight: 500;
}
</style>
