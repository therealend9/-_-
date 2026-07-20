<template>
  <div>
    <div class="breadcrumb"><span class="muted">教师端 / 课堂互动</span></div>
    <div class="page-header">
      <h1>课堂互动控制台</h1>
    </div>

    <!-- PPT 控制栏 -->
    <div class="ppt-strip" v-if="pptSlides.length">
      <div class="ppt-strip-left">
        <span class="ppt-badge">PPT 控制</span>
        <span class="ppt-info">第 {{ currentPptSlide + 1 }}/{{ pptSlides.length }} 页 · {{ currentPptData.title }}</span>
      </div>
      <div class="ppt-strip-right">
        <el-button size="small" :disabled="currentPptSlide === 0" @click="goSlide(currentPptSlide - 1)">上一页</el-button>
        <el-button size="small" :disabled="currentPptSlide >= pptSlides.length - 1" @click="goSlide(currentPptSlide + 1)">下一页</el-button>
        <span class="ppt-sync-hint">学生端实时同步</span>
      </div>
    </div>

    <!-- PPT 预览画面 -->
    <div class="ppt-preview" v-if="pptSlides.length">
      <div class="ppt-preview-header">
        <h3>{{ currentPptData.title }}</h3>
        <p v-if="currentPptData.subtitle">{{ currentPptData.subtitle }}</p>
      </div>
      <ul class="ppt-preview-bullets">
        <li v-for="(b, i) in currentPptData.bullets" :key="i">{{ b }}</li>
      </ul>
      <div class="ppt-preview-dots">
        <span v-for="(s, i) in pptSlides" :key="i" class="ppt-dot" :class="{ active: i === currentPptSlide, done: i < currentPptSlide }" @click="goSlide(i)"></span>
      </div>
    </div>

    <!-- 状态概览条 -->
    <div class="status-strip">
      <div v-for="card in statusCards" :key="card.label" class="ss-item">
        <span class="ss-label">{{ card.label }}</span>
        <span class="ss-val">{{ card.value }}</span>
        <el-tag size="small" :type="card.tagType">{{ card.tag }}</el-tag>
      </div>
    </div>

    <!-- 实时发布栏 -->
    <div class="publish-bar">
      <span class="pb-label">发布课堂题目：</span>
      <el-input-number v-model="liveDurationSeconds" :min="30" :max="1800" :step="30" size="default" style="width:120px" />
      <span class="muted" style="font-size:12px">秒</span>
      <el-input v-model="liveQuestionText" placeholder="输入题目内容…" size="large" @keyup.enter="publishQuestion" class="pb-input" />
      <el-button type="primary" size="large" :loading="publishing" @click="publishQuestion">发布</el-button>
      <el-button v-if="liveState.question" type="danger" size="large" plain :loading="closing" @click="closeQuestion">结束</el-button>
    </div>
    <div v-if="liveState.question" class="live-indicator">
      进行中 · {{ liveState.question.remainingSeconds }}s 剩余 · {{ liveState.question.answerCount || liveState.answerCount }} 人已答
    </div>

    <!-- 教学建议（整排） -->
    <div class="suggestion-strip" v-if="suggestions.length">
      <div v-for="(s,i) in suggestions" :key="i" class="sugg-card">
        <span class="sugg-num">{{ i + 1 }}</span>
        <span>{{ s }}</span>
      </div>
    </div>

    <!-- 实时回答 + 举手 -->
    <el-row :gutter="20" style="margin-top:16px" v-if="liveAnswers.length || handQuestions.length">
      <el-col :span="handQuestions.length ? 16 : 24">
        <el-card shadow="never" class="card" v-if="liveAnswers.length">
          <template #header><strong>实时回答（{{ liveAnswers.length }}）</strong></template>
          <div v-for="a in liveAnswers" :key="a.id||a.studentId" class="live-answer">
            <div class="la-head">
              <strong>{{ a.studentName }}</strong>
              <el-button size="small" @click="toggleHighlight(a)" :type="a.isHighlighted?'warning':'default'">{{ a.isHighlighted ? '已点评' : '点评' }}</el-button>
            </div>
            <div class="la-text">{{ a.answerText }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8" v-if="handQuestions.length">
        <el-card shadow="never" class="card">
          <template #header><strong>举手（{{ handQuestions.length }}）</strong></template>
          <div v-for="(h,i) in handQuestions" :key="i" class="hand-item">
            <strong>{{ h.studentName||'学生' }}</strong>
            <span class="hand-text">{{ h.question }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 回答汇总 + AI 助手 -->
    <el-row :gutter="20" style="margin-top:16px">
      <el-col :span="15">
        <el-card shadow="never" class="card">
          <template #header><strong>回答汇总</strong></template>
          <el-table :data="answers" style="width:100%">
            <el-table-column prop="viewpoint" label="观点类型" width="180" />
            <el-table-column prop="content" label="核心内容" min-width="280" />
            <el-table-column prop="count" label="人数" width="80" align="center" />
            <el-table-column label="操作" width="150">
              <template #default><el-button size="small">点评</el-button><el-button size="small" type="primary">展示</el-button></template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="9">
        <el-card shadow="never" class="card">
          <template #header><strong>AI 课堂助手</strong></template>
          <div class="chat-box">
            <div v-for="(msg,i) in messages" :key="i" class="chat-msg" :class="{ ai: msg.type==='ai'||msg.role==='AI' }">
              <span class="chat-role">{{ msg.role }}</span>
              <span class="chat-text">{{ msg.text }}</span>
            </div>
          </div>
          <div class="chat-bar">
            <el-input v-model="commandText" placeholder="输入指令…" size="small" @keyup.enter="sendCommand">
              <template #append><el-button :loading="sending" @click="sendCommand">发送</el-button></template>
            </el-input>
            <div class="chat-chips">
              <span class="chip" @click="quickCommand('开启30秒抢答，并把回答按观点聚类。')">发起抢答</span>
              <span class="chip" @click="quickCommand('请围绕社会实践和认识深化生成一个追问。')">生成追问</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { closeLiveInteractionQuestion, getClassInteraction, getLiveInteractionState, publishLiveInteractionQuestion, sendClassInteractionCommand, getLiveAnswers, highlightAnswer } from '../../api/teacher.js'
import { subscribeLiveInteraction } from '../../realtime/liveInteraction.js'

const sending = ref(false), commandText = ref(''), messages = ref([]), answers = ref([])
const pptSlides = ref([
  { id:1, title:'第三章：实践与认识及其发展规律', subtitle:'马克思主义基本原理', bullets:['本章核心问题：人的认识从哪里来？','学习目标：理解实践、认识、真理、价值的关系','重点：实践对认识的决定作用'] },
  { id:2, title:'一、实践的本质与特征', bullets:['实践是人类能动地改造世界的社会性物质活动','三个特征：客观物质性、自觉能动性、社会历史性'] },
  { id:3, title:'二、实践对认识的决定作用', bullets:['实践是认识的来源','实践是认识发展的动力','实践是认识的目的','实践是检验真理的唯一标准'] }
]), pptKeywords = ref([]), currentPptSlide = ref(0)
const currentPptData = computed(() => pptSlides.value[currentPptSlide.value] || { title:'', bullets:[] })
const statusCards = ref([
  { label:'当前问题', value:'如何理解实践是检验真理的唯一标准？', tag:'进行中', tagType:'warning' },
  { label:'互动状态', value:'41 人参与', tag:'实时', tagType:'success' }
])
const suggestions = ref([
  '用社会调研前后判断变化作为追问案例。',
  '展示一条观点完整但案例不足的回答，现场补充论证链条。',
  '将实践标准 vs 多数意见转成随堂微测。'
])
const liveQuestionText = ref(''), liveDurationSeconds = ref(300), publishing = ref(false), closing = ref(false)
const liveState = ref({ question: null, answerCount: 0 })
const liveAnswers = ref([]), handQuestions = ref([])
let unsubscribeLive = () => {}, countdownTimer

function refreshCountdown() {
  const q = liveState.value.question
  if (!q?.publishedAt || !q?.durationSeconds) return
  const endAt = new Date(q.publishedAt).getTime() + Number(q.durationSeconds) * 1000
  liveState.value = { ...liveState.value, question: { ...q, remainingSeconds: Math.max(0, Math.ceil((endAt - Date.now()) / 1000)) } }
}

function goSlide(index) {
  currentPptSlide.value = Math.max(0, Math.min(index, pptSlides.value.length - 1))
  liveState.value = { ...liveState.value, currentSlide: currentPptSlide.value }
}

async function loadData() {
  try {
    const data = await getClassInteraction()
    if (data.pptSlides?.length) pptSlides.value = data.pptSlides
    if (data.pptKeywords) pptKeywords.value = data.pptKeywords
    if (data.currentSlide !== undefined) currentPptSlide.value = data.currentSlide
    if (data.statusCards?.length) statusCards.value = data.statusCards
    if (data.messages?.length) messages.value = data.messages
    if (data.answers?.length) answers.value = data.answers
    if (data.suggestions?.length) suggestions.value = data.suggestions
    liveState.value = await getLiveInteractionState()
  } catch (e) { console.error(e) }
}

async function publishQuestion() {
  const text = liveQuestionText.value.trim(); if (!text || publishing.value) return
  publishing.value = true
  try { 
    liveState.value = await publishLiveInteractionQuestion(text, liveDurationSeconds.value)
    liveQuestionText.value = ''; ElMessage.success('已推送')
    fetchAiSuggestions(text)
  } catch (e) { ElMessage.error(e?.message || '失败') } finally { publishing.value = false }
}

async function fetchAiSuggestions(questionText) {
  try {
    const result = await sendClassInteractionCommand('请针对这道课堂题目，给出3条简短的教学建议（每条不超过40字），帮助教师引导学生思考和点评回答。题目：' + questionText)
    if (result?.reply) {
      const lines = result.reply.split(/\d+[.、)\s]/).filter(s => s.trim().length > 3).slice(0, 3)
      if (lines.length >= 2) suggestions.value = lines.map(s => s.trim())
    }
  } catch { /* 静默 */ }
}

async function closeQuestion() {
  const id = liveState.value.question?.id; if (!id || closing.value) return
  closing.value = true
  try { liveState.value = await closeLiveInteractionQuestion(id); ElMessage.success('已结束') } catch (e) { ElMessage.error(e?.message || '失败') } finally { closing.value = false }
}

async function sendCommand() {
  if (sending.value) return; const t = commandText.value.trim(); if (!t) return
  sending.value = true
  try { const r = await sendClassInteractionCommand(t); messages.value.push({ role:'教师', text:t }); if (r.reply) messages.value.push({ role:'AI', text:r.reply, type:'ai' }); commandText.value = '' } catch (e) { ElMessage.error(e?.message||'失败') } finally { sending.value = false }
}

async function toggleHighlight(a) { if (!a.id) return; try { const r = await highlightAnswer(a.id, !a.isHighlighted); a.isHighlighted = r.highlighted } catch { ElMessage.error('失败') } }
function quickCommand(text) { commandText.value = text; sendCommand() }

onMounted(async () => {
  await loadData()
  countdownTimer = setInterval(refreshCountdown, 1000)
  unsubscribeLive = subscribeLiveInteraction({
    onQuestion: (s) => { liveState.value = s; liveAnswers.value = []; handQuestions.value = []; if (s.question?.id) getLiveAnswers(s.question.id).then(a => liveAnswers.value = a||[]).catch(()=>{}); if (s.question?.text) fetchAiSuggestions(s.question.text) },
    onStats: (s) => { liveState.value = { ...liveState.value, ...s } },
    onClose: (s) => { liveState.value = s },
    onAnswerSubmitted: (d) => { liveAnswers.value.unshift(d); ElMessage({ message:d.studentName+' 提交了回答', type:'info', duration:1500 }) },
    onHandRaised: (d) => { handQuestions.value.unshift(d); ElMessage({ message:(d.studentName||'学生')+' 举手提问', type:'warning', duration:2000 }) }
  })
})

onUnmounted(() => { unsubscribeLive(); clearInterval(countdownTimer) })
</script>

<style scoped>
.breadcrumb { font-size:12px; margin-bottom:4px; }
.muted { color:var(--muted); }
.page-header { margin-bottom:12px; }
.page-header h1 { font-size:26px; font-weight:800; letter-spacing:-0.3px; }

/* PPT */
.ppt-strip { display:flex; align-items:center; justify-content:space-between; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:10px 16px; margin-bottom:12px; }
.ppt-strip-left { display:flex; align-items:center; gap:10px; }
.ppt-badge { background:#e74c3c; color:#fff; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700; }
.ppt-info { font-size:13px; color:var(--muted); }
.ppt-strip-right { display:flex; align-items:center; gap:8px; }
.ppt-sync-hint { font-size:11px; color:var(--success); font-weight:600; }
.ppt-preview { background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f1628 100%); border-radius:14px; border:1px solid #2a2a4a; padding:24px 28px 16px; margin-bottom:12px; }
.ppt-preview-header { margin-bottom:16px; }
.ppt-preview-header h3 { font-size:20px; font-weight:800; color:#fff; letter-spacing:-0.2px; }
.ppt-preview-header p { font-size:13px; color:rgba(255,255,255,.5); margin-top:2px; }
.ppt-preview-bullets { list-style:none; padding:0; margin-bottom:16px; }
.ppt-preview-bullets li { font-size:14px; color:rgba(255,255,255,.85); line-height:1.9; padding:6px 0 6px 20px; position:relative; border-bottom:1px solid rgba(255,255,255,.06); }
.ppt-preview-bullets li::before { content:'â–¸'; position:absolute; left:2px; color:#409EFF; font-size:12px; }
.ppt-preview-dots { display:flex; gap:8px; justify-content:center; }
.ppt-dot { width:8px; height:8px; border-radius:50%; background:rgba(255,255,255,.15); cursor:pointer; transition:all var(--duration-fast); }
.ppt-dot.active { background:#409EFF; width:20px; border-radius:4px; }
.ppt-dot.done { background:rgba(255,255,255,.35); }

/* 状态条 */
.status-strip { display:flex; gap:12px; margin-bottom:12px; }
.ss-item { flex:1; display:flex; align-items:center; gap:10px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 16px; }
.ss-label { font-size:13px; color:var(--muted); font-weight:600; }
.ss-val { font-size:15px; font-weight:800; flex:1; }

/* 发布栏 */
.publish-bar { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.pb-label { font-size:13px; font-weight:700; white-space:nowrap; }
.pb-input { flex:1; }
.live-indicator { font-size:13px; color:var(--danger); font-weight:600; padding:4px 12px; background:var(--danger-soft); border-radius:6px; display:inline-block; margin-bottom:4px; }

/* 教学建议 */
.suggestion-strip { display:flex; gap:12px; margin-top:8px; }
.sugg-card { flex:1; display:flex; align-items:flex-start; gap:8px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 14px; font-size:13px; line-height:1.7; color:#4d4d4d; }
.sugg-num { width:20px; height:20px; border-radius:50%; background:var(--soft); display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:800; color:var(--muted); flex-shrink:0; margin-top:1px; }

/* 卡片 */
.card { border-radius:14px; border:1px solid var(--line); background:var(--card); }

/* 实时回答 */
.live-answer { padding:10px 0; border-bottom:1px dashed var(--line); }
.live-answer:last-child { border-bottom:none; }
.la-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.la-text { font-size:13px; line-height:1.6; }

/* 举手 */
.hand-item { padding:8px 10px; margin-bottom:6px; background:var(--danger-soft); border-radius:6px; border-left:3px solid #F56C6C; }
.hand-text { display:block; font-size:12px; color:var(--muted); margin-top:2px; }

/* AI 聊天 */
.chat-box { display:flex; flex-direction:column; gap:10px; margin-bottom:10px; max-height:260px; overflow-y:auto; }
.chat-msg { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 12px; font-size:13px; }
.chat-msg.ai { background:var(--soft); }
.chat-role { font-weight:700; font-size:11px; color:var(--muted); display:block; margin-bottom:2px; }
.chat-text { line-height:1.5; }
.chat-bar { border-top:1px solid var(--line); padding-top:10px; }
.chat-chips { display:flex; gap:6px; margin-top:8px; }
.chip { font-size:11px; padding:4px 10px; border-radius:12px; background:var(--primary-soft); color:var(--primary); cursor:pointer; font-weight:600; transition:background var(--duration-fast); }
.chip:hover { background:#d0e4ff; }
</style>
