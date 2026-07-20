<template>
  <div class="interaction-root">
    <div class="breadcrumb">
      <span class="muted">学生端 / 课中互动 / 互动中心</span>
      <el-tag :type="wsConnected ? 'success' : 'danger'" size="small" effect="plain" style="margin-left:12px">
        {{ wsConnected ? '✓ 实时已连接' : '⚠ 轮询中' }}
      </el-tag>
    </div>

    <!-- ============ 上部：PPT展示 + AI问答 ============ -->
    <el-row :gutter="16" style="margin-top: 12px">
      <!-- PPT 展示区（大框） -->
      <el-col :span="16">
        <div class="ppt-stage">
          <!-- PPT 头部导航 -->
          <div class="ppt-header">
            <div class="ppt-header-left">
              <span class="ppt-badge">📊 教师PPT</span>
              <span class="ppt-slide-info">第 {{ currentSlide + 1 }}/{{ pptSlides.length }} 页</span>
            </div>
            <div class="ppt-header-right">
              <el-button size="small" text :disabled="currentSlide === 0" @click="prevSlide">◀ 上一页</el-button>
              <el-button size="small" text :disabled="currentSlide >= pptSlides.length - 1" @click="nextSlide">下一页 ▶</el-button>
            </div>
          </div>

          <!-- PPT 内容区 -->
          <div class="ppt-body" ref="pptBody">
            <transition name="slide-fade" mode="out-in">
              <div class="ppt-slide" :key="currentSlide">
                <div class="ppt-slide-header">
                  <h2>{{ currentSlideData.title }}</h2>
                  <p v-if="currentSlideData.subtitle" class="ppt-subtitle">{{ currentSlideData.subtitle }}</p>
                </div>
                <div class="ppt-slide-content">
                  <ul class="ppt-bullets">
                    <li v-for="(b, i) in currentSlideData.bullets" :key="i">{{ b }}</li>
                  </ul>
                  <div v-if="currentSlideData.image" class="ppt-image-placeholder">
                    📷 图示区域
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <!-- PPT 底部进度 -->
          <div class="ppt-footer">
            <div class="ppt-progress-dots">
              <span
                v-for="(s, i) in pptSlides"
                :key="i"
                class="ppt-dot"
                :class="{ active: i === currentSlide, done: i < currentSlide }"
                @click="currentSlide = i"
              ></span>
            </div>
          </div>
        </div>

        <!-- 当前PPT关键词标签 -->
        <div class="ppt-keywords">
          <span class="kw-label">🔑 当前关键词：</span>
          <el-tag
            v-for="kw in pptKeywords"
            :key="kw"
            size="small"
            class="kw-tag"
            @click="askKeyword(kw)"
          >{{ kw }}</el-tag>
        </div>
      </el-col>

      <!-- AI 实时问答框 -->
      <el-col :span="8">
        <div class="ai-panel">
          <div class="ai-panel-header">
            <div class="ai-header-left">
              <span class="ai-icon">🤖</span>
              <strong>AI 课堂助手</strong>
            </div>
            <el-tag size="small" type="success" effect="plain">实时</el-tag>
          </div>

          <!-- 聊天消息区 -->
          <div class="ai-messages" ref="aiMsgBody">
            <div class="ai-msg system">
              <div class="ai-msg-content">{{ aiWelcome }}</div>
            </div>
            <div
              v-for="(msg, i) in aiMessages"
              :key="i"
              class="ai-msg"
              :class="msg.role"
            >
              <div class="ai-msg-content">{{ msg.content }}</div>
              <div v-if="msg.streaming" class="typing-cursor">|</div>
            </div>
          </div>

          <!-- 推荐问题 -->
          <div class="ai-suggestions" v-if="aiMessages.length === 1">
            <div
              v-for="q in aiSampleQuestions"
              :key="q"
              class="ai-suggest-chip"
              @click="askAI(q)"
            >{{ q }}</div>
          </div>

          <!-- 输入框 -->
          <div class="ai-input-row">
            <el-input
              v-model="aiInput"
              placeholder="输入问题，AI 实时补充讲解..."
              size="small"
              @keyup.enter="askAI(aiInput)"
              :disabled="aiLoading"
            >
              <template #suffix>
                <el-button
                  text
                  size="small"
                  type="primary"
                  :loading="aiLoading"
                  @click="askAI(aiInput)"
                  :disabled="!aiInput.trim()"
                >发送</el-button>
              </template>
            </el-input>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ============ 下部：教师提问区（原版风格） ============ -->
    <div class="teacher-section">
      <div class="section-divider">
        <span>👇 教师提问区</span>
      </div>

      <el-row :gutter="20">
        <el-col :span="15">
          <el-card shadow="never" class="card" style="margin-bottom: 16px">
            <template #header>
              <div class="card-header-row">
                <strong>📢 当前问题</strong>
                <el-tag v-if="liveState.question" size="small" type="warning">
                  剩余 {{ liveState.question.remainingSeconds || '--' }} 秒
                </el-tag>
              </div>
            </template>
            <div class="question-box">
              <div class="question-label">{{ currentQuestion.label }}</div>
              <div class="question-text">{{ currentQuestion.text }}</div>
              <div v-if="liveState.question" class="live-meta">
                {{ liveState.readCount || 0 }} 人已读 · {{ liveState.answerCount || 0 }} 人已答
              </div>
              <div class="answer-row">
                <el-input
                  v-model="answerText"
                  placeholder="输入关键词，AI帮你扩展为完整回答"
                  size="large"
                  class="answer-input"
                />
                <el-button
                  type="primary"
                  size="large"
                  :disabled="!liveState.question || liveState.hasAnswered"
                  :loading="submitting"
                  @click="handleSubmit"
                >{{ liveState.hasAnswered ? '已提交' : '提交回答' }}</el-button>
                <el-button
                  size="large"
                  :disabled="!liveState.question"
                  @click="handleRaiseHand"
                >🙋 举手</el-button>
              </div>
            </div>
          </el-card>

          <el-card shadow="never" class="card">
            <template #header><strong>🤖 AI辅助回答</strong></template>
            <div class="ai-suggest-box">
              <div class="muted">AI 根据你的关键词扩展建议</div>
              <p class="ai-suggest-text">{{ aiSuggestion }}</p>
              <el-button size="small" @click="answerText = aiSuggestion">使用此回答</el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :span="9">
          <el-card shadow="never" class="card">
            <template #header>
              <div class="card-header-row">
                <strong>📊 互动状态</strong>
              </div>
            </template>
            <div class="stats-row">
              <div class="stat-box" v-for="stat in stats" :key="stat.label">
                <div class="stat-num">{{ stat.value }}</div>
                <div class="stat-label-text">{{ stat.label }}</div>
              </div>
            </div>
            <el-divider />
            <strong>🏆 实时互动积分</strong>
            <div class="leaderboard" style="margin-top: 12px">
              <div
                v-for="(s, i) in scores"
                :key="i"
                class="lb-row"
                :class="{ 'lb-me': s.name === '李明哲' }"
              >
                <span class="lb-rank" :class="'rank-' + (i + 1)">{{ i + 1 }}</span>
                <span class="lb-name">{{ s.name }}</span>
                <el-tag size="small" :type="i === 0 ? 'warning' : 'info'">{{ s.score }} 分</el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import {
  getStudentClassInteraction, getStudentLiveInteractionState,
  markLiveInteractionQuestionRead, submitLiveInteractionAnswer, raiseHand,
  streamAiChat
} from '../../api/student.js'
import { subscribeLiveInteraction } from '../../realtime/liveInteraction.js'

// === 基础状态 ===
const loading = ref(true)
const submitting = ref(false)

// === PPT 状态 ===
const pptSlides = ref([])
const pptKeywords = ref([])
const currentSlide = ref(0)
const currentSlideData = computed(() => pptSlides.value[currentSlide.value] || { title: '', subtitle: '', bullets: [], image: '' })

function prevSlide() { if (currentSlide.value > 0) currentSlide.value-- }
function nextSlide() { if (currentSlide.value < pptSlides.value.length - 1) currentSlide.value++ }

// === AI 问答状态 ===
const aiWelcome = ref('')
const aiSampleQuestions = ref([])
const aiMessages = ref([])
const aiInput = ref('')
const aiLoading = ref(false)
const aiMsgBody = ref(null)

function scrollAIBottom() {
  nextTick(() => {
    const el = aiMsgBody.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function addAIMessage(role, content, streaming = false) {
  if (streaming) {
    // 检查是否已有 streaming 消息
    const last = aiMessages.value[aiMessages.value.length - 1]
    if (last && last.streaming) {
      last.content += content
      scrollAIBottom()
      return
    }
  }
  aiMessages.value.push({ role, content, streaming })
  scrollAIBottom()
}

function finishStreaming() {
  const last = aiMessages.value[aiMessages.value.length - 1]
  if (last && last.streaming) last.streaming = false
}

function askKeyword(keyword) {
  askAI(`请结合当前PPT内容，详细讲解一下"${keyword}"这个概念`)
}

async function askAI(question) {
  const q = (question || aiInput.value).trim()
  if (!q || aiLoading.value) return
  aiInput.value = ''
  aiLoading.value = true
  addAIMessage('user', q)
  addAIMessage('assistant', '', true)

  try {
    streamAiChat(q, {
      onChunk: (chunk) => { addAIMessage('assistant', chunk, true) },
      onDone: () => { finishStreaming(); aiLoading.value = false },
      onError: (err) => {
        finishStreaming()
        addAIMessage('assistant', '抱歉，AI 服务暂时不可用，请稍后重试。')
        aiLoading.value = false
      }
    })
  } catch {
    finishStreaming()
    aiLoading.value = false
  }
}

// === 教师提问状态 ===
const answerText = ref('')
const currentQuestion = ref({ label: '教师发问', text: '' })
const aiSuggestion = ref('')
const stats = ref([])
const scores = ref([])
const liveState = ref({ question: null, answerCount: 0, participantCount: 0, hasAnswered: false })
const wsConnected = ref(false)

let unsubscribeLive = () => {}
let countdownTimer
let pollTimer
let lastQuestionId = null

function refreshCountdown() {
  const question = liveState.value.question
  if (!question?.publishedAt || !question?.durationSeconds) return
  const endAt = new Date(question.publishedAt).getTime() + Number(question.durationSeconds) * 1000
  liveState.value = {
    ...liveState.value,
    question: { ...question, remainingSeconds: Math.max(0, Math.ceil((endAt - Date.now()) / 1000)) }
  }
}

async function handleSubmit() {
  const text = answerText.value.trim()
  if (!text) { ElMessage.warning('请先输入回答内容'); return }
  if (submitting.value) return
  submitting.value = true
  try {
    if (!liveState.value.question) { ElMessage.warning('请等待教师发布课堂题目'); return }
    const data = await submitLiveInteractionAnswer(liveState.value.question.id, text)
    applyLiveState(data)
    ElMessage.success(data.message || '回答已提交')
    answerText.value = ''
  } catch (error) {
    ElMessage.error(error?.message || '提交回答失败')
  } finally { submitting.value = false }
}

function applyLiveState(state) {
  liveState.value = { ...liveState.value, ...state }
  if (state.question) {
    currentQuestion.value = { label: '教师实时推送', text: state.question.text }
    lastQuestionId = state.question.id
  }
  // 教师同步 PPT 翻页
  if (state.currentSlide !== undefined && state.currentSlide !== null) {
    currentSlide.value = state.currentSlide
  }
  stats.value = [
    { label: '已参与', value: String(state.participantCount || 0) },
    { label: '已提交', value: String(state.answerCount || 0) },
    { label: '答题状态', value: state.hasAnswered ? '已完成' : '待提交' }
  ]
  scores.value = state.leaderboard || []
}

async function pollLiveState() {
  try {
    const live = await getStudentLiveInteractionState()
    if (live.question) {
      const qid = live.question.id
      if (qid !== lastQuestionId || live.question.status !== liveState.value.question?.status) {
        applyLiveState(live); await markQuestionRead(live)
      } else if (live.answerCount !== liveState.value.answerCount) {
        applyLiveState(live)
      }
    } else if (lastQuestionId) {
      lastQuestionId = null; applyLiveState(live)
    }
  } catch { /* silent */ }
}

async function handleRaiseHand() {
  const q = prompt('请输入你想问教师的问题：')
  if (!q?.trim()) return
  try { await raiseHand(q.trim()); ElMessage.success('已发送给教师') } catch (e) { ElMessage.error(e?.message || '失败') }
}

async function markQuestionRead(state) {
  if (!state.question || state.hasRead) return
  try { applyLiveState(await markLiveInteractionQuestionRead(state.question.id)) } catch { /* silent */ }
}

onMounted(async () => {
  try {
    const data = await getStudentClassInteraction()
    pptSlides.value = data.pptSlides || []
    pptKeywords.value = data.pptKeywords || []
    currentSlide.value = data.currentSlide || 0
    aiWelcome.value = data.aiWelcome || ''
    aiSampleQuestions.value = data.aiSampleQuestions || []
    aiMessages.value = [{ role: 'system', content: data.aiWelcome || '' }]
    currentQuestion.value = data.currentQuestion || currentQuestion.value
    aiSuggestion.value = data.aiSuggestion || ''
    stats.value = data.stats || []
    scores.value = data.scores || []

    const live = await getStudentLiveInteractionState()
    applyLiveState(live)
    await markQuestionRead(live)
    countdownTimer = window.setInterval(refreshCountdown, 1000)
    unsubscribeLive = subscribeLiveInteraction({
      onQuestion: async (s) => { applyLiveState(s); await markQuestionRead(s) },
      onStats: applyLiveState,
      onClose: applyLiveState,
      onAnswerHighlighted: () => { ElMessage.success('✨ 教师点评了你的回答') },
      onConnected: () => { wsConnected.value = true },
      onDisconnected: () => { wsConnected.value = false }
    })
    pollTimer = window.setInterval(pollLiveState, 5000)
    scrollAIBottom()
  } catch (e) { console.error('加载互动中心失败', e) }
})

onUnmounted(() => {
  unsubscribeLive()
  window.clearInterval(countdownTimer)
  if (pollTimer) { window.clearInterval(pollTimer); pollTimer = null }
})
</script>

<style scoped>
.interaction-root { max-width: 100%; }
.breadcrumb { font-size: 12px; margin-bottom: 6px; display: flex; align-items: center; }
.muted { color: var(--muted); }

/* ===== PPT 展示区 ===== */
.ppt-stage {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f1628 100%);
  border-radius: 18px; overflow: hidden;
  border: 1px solid #2a2a4a; min-height: 420px;
  display: flex; flex-direction: column;
}
.ppt-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; background: rgba(255,255,255,.04);
  border-bottom: 1px solid rgba(255,255,255,.08);
}
.ppt-header-left { display: flex; align-items: center; gap: 12px; }
.ppt-badge {
  background: #e74c3c; color: #fff; padding: 4px 10px;
  border-radius: 6px; font-size: 12px; font-weight: 700;
}
.ppt-slide-info { font-size: 12px; color: rgba(255,255,255,.5); }
.ppt-header-right { display: flex; gap: 4px; }

.ppt-body {
  flex: 1; padding: 28px 36px; overflow-y: auto;
  display: flex; align-items: flex-start;
}
.ppt-slide { width: 100%; }
.ppt-slide-header { margin-bottom: 20px; }
.ppt-slide-header h2 {
  font-size: 24px; font-weight: 800; color: #fff;
  letter-spacing: -0.3px; margin-bottom: 4px;
}
.ppt-subtitle { font-size: 14px; color: rgba(255,255,255,.5); }
.ppt-slide-content { display: flex; gap: 24px; align-items: flex-start; }
.ppt-bullets { flex: 1; list-style: none; padding: 0; }
.ppt-bullets li {
  font-size: 15px; color: rgba(255,255,255,.85); line-height: 1.9;
  padding: 8px 0 8px 24px; position: relative;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.ppt-bullets li::before {
  content: '▸'; position: absolute; left: 4px; color: #409EFF;
  font-size: 12px;
}
.ppt-image-placeholder {
  width: 200px; height: 160px; border-radius: 12px;
  background: rgba(255,255,255,.05); border: 1px dashed rgba(255,255,255,.12);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: rgba(255,255,255,.3); flex-shrink: 0;
}

.ppt-footer { padding: 10px 20px; background: rgba(255,255,255,.03); border-top: 1px solid rgba(255,255,255,.06); }
.ppt-progress-dots { display: flex; gap: 8px; justify-content: center; }
.ppt-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: rgba(255,255,255,.15); cursor: pointer;
  transition: background var(--duration-fast);
}
.ppt-dot.active { background: #409EFF; width: 20px; border-radius: 4px; }
.ppt-dot.done { background: rgba(255,255,255,.35); }

/* PPT 切换动画 */
.slide-fade-enter-active { transition: all 0.3s var(--ease-out); }
.slide-fade-leave-active { transition: all 0.2s var(--ease-out); }
.slide-fade-enter-from { opacity: 0; transform: translateX(20px); }
.slide-fade-leave-to { opacity: 0; transform: translateX(-20px); }

/* PPT 关键词标签 */
.ppt-keywords {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-top: 10px; padding: 10px 14px;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 12px;
}
.kw-label { font-size: 12px; font-weight: 700; color: var(--muted); flex-shrink: 0; }
.kw-tag { cursor: pointer; transition: transform var(--duration-fast); }
.kw-tag:hover { transform: scale(1.05); }

/* ===== AI 问答面板 ===== */
.ai-panel {
  display: flex; flex-direction: column;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 18px; overflow: hidden; height: 420px;
}
.ai-panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-bottom: 1px solid var(--line);
  background: var(--soft);
}
.ai-header-left { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.ai-icon { font-size: 20px; }

.ai-messages {
  flex: 1; overflow-y: auto; padding: 12px 14px;
  display: flex; flex-direction: column; gap: 8px;
}
.ai-msg { display: flex; }
.ai-msg.user { justify-content: flex-end; }
.ai-msg-content {
  max-width: 90%; padding: 10px 14px; border-radius: 12px;
  font-size: 13px; line-height: 1.65; white-space: pre-wrap;
}
.ai-msg.system .ai-msg-content,
.ai-msg.assistant .ai-msg-content {
  background: var(--soft); color: var(--ink);
  border-bottom-left-radius: 4px;
}
.ai-msg.user .ai-msg-content {
  background: var(--primary-soft); color: var(--ink);
  border-bottom-right-radius: 4px;
}
.typing-cursor {
  display: inline; color: var(--primary); font-weight: 700;
  animation: blink 0.8s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

.ai-suggestions { padding: 8px 14px; display: flex; flex-wrap: wrap; gap: 6px; }
.ai-suggest-chip {
  font-size: 11px; padding: 5px 10px; border-radius: 14px;
  background: var(--soft); border: 1px solid var(--line);
  cursor: pointer; transition: background var(--duration-fast);
}
.ai-suggest-chip:hover { background: var(--primary-soft); border-color: var(--primary-border); }

.ai-input-row { padding: 10px 12px; border-top: 1px solid var(--line); }

/* ===== 教师提问区分隔 ===== */
.teacher-section { margin-top: 24px; }
.section-divider {
  text-align: center; padding: 8px 0 16px; font-size: 13px; color: var(--muted); font-weight: 600;
}
.section-divider span {
  display: inline-block; background: var(--soft); border: 1px dashed var(--line);
  border-radius: 20px; padding: 6px 20px;
}

/* ===== 卡片 ===== */
.card {
  border-radius: 14px; border: 1px solid var(--line);
  background: var(--card);
  transition: box-shadow var(--duration-fast) var(--ease-out);
}
.card:hover { box-shadow: var(--shadow-sm); }
.card-header-row { display: flex; justify-content: space-between; align-items: center; }

/* 教师问题区 */
.question-box { padding: 4px 0; }
.question-label { font-size: 12px; color: var(--muted); font-weight: 700; margin-bottom: 4px; }
.question-text { font-size: 20px; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.2px; }
.live-meta { font-size: 13px; color: var(--muted); margin-bottom: 14px; }
.answer-row { display: flex; gap: 10px; }
.answer-input { flex: 1; }

.ai-suggest-box {
  background: var(--soft); border-radius: 12px; padding: 16px;
  border: 1px dashed var(--line);
}
.ai-suggest-text { font-size: 14px; margin-top: 8px; line-height: 1.8; color: var(--ink); }

/* 互动状态 */
.stats-row { display: flex; gap: 12px; margin-bottom: 12px; }
.stat-box {
  flex: 1; text-align: center; padding: 14px 8px;
  background: var(--soft); border-radius: 12px; border: 1px dashed var(--line);
  transition: transform var(--duration-fast);
}
.stat-box:hover { transform: translateY(-1px); }
.stat-num { font-size: 26px; font-weight: 800; }
.stat-label-text { font-size: 11px; color: var(--muted); margin-top: 4px; }

/* 排行榜 */
.leaderboard { display: flex; flex-direction: column; gap: 4px; }
.lb-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 10px;
  border-bottom: 1px dashed var(--line);
  transition: background var(--duration-fast);
}
.lb-row:last-child { border-bottom: none; }
.lb-row:hover { background: var(--soft); }
.lb-row.lb-me { background: var(--primary-soft); }
.lb-rank {
  width: 24px; height: 24px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 800; background: var(--soft);
}
.rank-1 { background: #fdf6ec; color: #e6a23c; }
.rank-2 { background: #e8e8e8; color: #909090; }
.rank-3 { background: #f5e6d3; color: #c0823c; }
.lb-name { flex: 1; font-size: 13px; font-weight: 600; }
</style>
