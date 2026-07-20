<template>
  <div v-loading="loading" class="aiqa-root">
    <div class="breadcrumb"><span class="muted">学生端 / AI 学伴 / 学科问答</span></div>
    <div class="page-header">
      <div>
        <h1>🤖 AI 学伴 · 学科问答</h1>
        <p class="page-desc">基于课程知识库的智能问答，所有回答可溯源至教材、课件和案例，支持多轮追问</p>
      </div>
      <div class="header-actions">
        <el-button v-if="streaming" type="danger" @click="stopStreaming" :icon="VideoPause">停止生成</el-button>
        <el-button v-else type="primary" @click="newChat" :icon="Plus">新建对话</el-button>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top: 16px">
      <!-- ========== 左侧：会话 + 知识库 ========== -->
      <el-col :span="5">
        <!-- 对话记录 -->
        <el-card shadow="never" class="side-card">
          <template #header>
            <div class="side-card-hd">
              <span class="sc-title">📁 对话记录</span>
              <el-button size="small" text type="primary" @click="newChat">
                <el-icon><Plus /></el-icon> 新建
              </el-button>
            </div>
          </template>

          <div v-if="!sessions.length" class="side-empty">
            <span class="side-empty-icon">💬</span>
            <span class="side-empty-text">暂无对话</span>
          </div>

          <div
            v-for="s in sessions"
            :key="s.id"
            class="session-row"
            :class="{ active: currentSessionId === s.id }"
            @click="switchSession(s)"
          >
            <div class="sr-left">
              <span class="sr-dot"></span>
            </div>
            <div class="sr-body">
              <div class="sr-title">{{ s.title }}</div>
              <div class="sr-meta">
                <span>{{ s.messageCount }} 条消息</span>
                <span>·</span>
                <span>{{ formatTime(s.updatedAt) }}</span>
              </div>
            </div>
          </div>

          <el-divider style="margin: 14px 0" />

          <!-- 知识来源 -->
          <div class="sc-title" style="margin-bottom: 10px">📖 知识来源</div>
          <div v-for="s in sources" :key="s.id" class="source-row" @click="router.push(`/student/source/${s.id}`)">
            <span class="src-icon">{{ s.tag === '教材' ? '📕' : s.tag === '课件' ? '📊' : '📋' }}</span>
            <span class="src-title">{{ s.title }}</span>
            <el-icon size="14" class="src-arrow"><ArrowRight /></el-icon>
          </div>
        </el-card>
      </el-col>

      <!-- ========== 中间：聊天主区 ========== -->
      <el-col :span="12">
        <el-card shadow="never" class="chat-card">
          <template #header>
            <div class="chat-card-hd">
              <strong>{{ currentSessionTitle || '新对话' }}</strong>
              <el-tag v-if="streaming" size="small" type="warning" effect="dark">AI 回答中…</el-tag>
            </div>
          </template>

          <!-- 聊天消息区 -->
          <div class="chat-body" ref="chatBodyRef">
            <!-- 空状态 -->
            <div v-if="!messages.length && !streaming" class="chat-welcome">
              <div class="welcome-icon">🤖</div>
              <h2>你好，我是 AI 学伴</h2>
              <p class="welcome-desc">我是基于课程知识库训练的智能助手，可以为你解答马原学习中的疑惑。<br>所有回答都会标注来源，支持点击溯源验证。</p>

              <div class="welcome-questions">
                <div class="wq-label">🔥 同学们都在问：</div>
                <div class="wq-grid">
                  <div
                    v-for="(q, i) in hotQuestions.slice(0, 5)"
                    :key="q.id"
                    class="wq-chip"
                    @click="sendMessage(q.text)"
                  >
                    <span class="wq-num">{{ q.askCount }} 问</span>
                    {{ q.text }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 消息列表 -->
            <div v-for="(msg, i) in messages" :key="i" class="msg-row" :class="{ 'msg-user': msg.role === 'student' }">
              <div class="msg-avatar" :class="msg.role">
                {{ msg.role === 'student' ? '我' : 'AI' }}
              </div>
              <div class="msg-main">
                <div class="msg-bubble" :class="msg.role">
                  <div class="msg-text" v-html="renderContent(msg.content)"></div>
                  <!-- 引用标记 -->
                  <div v-if="msg.citations?.length" class="msg-refs">
                    <div class="refs-label">📚 引用来源：</div>
                    <div class="refs-list">
                      <span
                        v-for="c in msg.citations"
                        :key="c.sourceId"
                        class="ref-chip"
                        @click="router.push(`/student/source/${c.sourceId}`)"
                      >{{ c.title }}</span>
                    </div>
                  </div>
                </div>
                <div class="msg-time" v-if="msg.time">{{ msg.time }}</div>
              </div>
            </div>

            <!-- 流式输出中 -->
            <div v-if="streaming" class="msg-row">
              <div class="msg-avatar ai">AI</div>
              <div class="msg-main">
                <div class="msg-bubble ai streaming-bubble">
                  <div class="msg-text" v-html="renderContent(streamContent)"></div>
                  <span class="typing-cursor">|</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区 -->
          <div class="chat-input-area">
            <div class="input-row">
              <el-input
                v-model="input"
                placeholder="输入你的问题，例如：实践为什么是检验真理的唯一标准？"
                size="large"
                :disabled="streaming"
                @keyup.enter.exact="sendMessage()"
                clearable
                class="chat-input"
              >
                <template #prefix>
                  <el-icon><ChatDotRound /></el-icon>
                </template>
                <template #append>
                  <el-button
                    type="primary"
                    :disabled="!input.trim() || streaming"
                    @click="sendMessage()"
                    :loading="streaming"
                    class="send-btn"
                  >
                    {{ streaming ? '回答中' : '发送' }}
                  </el-button>
                </template>
              </el-input>
            </div>
            <div class="input-hints">
              <span>💡 提示：问题越具体，回答越精准。支持追问和辩论。</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- ========== 右侧：引用 + 推荐 ========== -->
      <el-col :span="7">
        <!-- 本轮引用来源 -->
        <el-card shadow="never" class="side-card">
          <template #header>
            <div class="side-card-hd">
              <span class="sc-title">📚 本轮引用来源</span>
              <el-tag size="small" :type="currentCitations.length ? 'success' : 'info'" effect="plain">
                {{ currentCitations.length || 0 }} 条
              </el-tag>
            </div>
          </template>
          <div v-if="!currentCitations.length" class="side-empty">
            <span class="side-empty-icon">📖</span>
            <span class="side-empty-text">发送问题后，AI 会展示<br>引用的知识来源</span>
          </div>
          <div
            v-for="c in currentCitations"
            :key="c.sourceId"
            class="citation-card"
            @click="router.push(`/student/source/${c.sourceId}`)"
          >
            <div class="cc-icon">📕</div>
            <div class="cc-body">
              <div class="cc-title">{{ c.title }}</div>
              <div class="cc-excerpt">"{{ c.excerpt }}"</div>
            </div>
            <el-icon size="16" class="cc-arrow"><ArrowRight /></el-icon>
          </div>
        </el-card>

        <!-- 推荐追问 → 热门追问 -->
        <el-card shadow="never" class="side-card" style="margin-top: 14px">
          <template #header>
            <div class="side-card-hd">
              <span class="sc-title">🔥 热门追问</span>
              <el-tag size="small" type="danger" effect="plain">本周</el-tag>
            </div>
          </template>
          <div class="hot-list">
            <div
              v-for="q in displayHotQuestions"
              :key="q.id"
              class="hot-row"
              @click="sendMessage(q.text)"
            >
              <span class="hot-rank" :class="'rank-' + q.id">{{ q.id <= 3 ? ['🥇','🥈','🥉'][q.id-1] : q.id }}</span>
              <span class="hot-text">{{ q.text }}</span>
              <span class="hot-count">{{ q.askCount }} 问</span>
            </div>
          </div>
          <div class="hot-footer">
            <span class="rotation-dot" :class="{ active: rotationIndex === i }" v-for="i in 2" :key="i"></span>
            <span class="rotation-hint">每 8 秒轮换</span>
          </div>
        </el-card>

        <!-- 学习小贴士 -->
        <div class="tip-mini" style="margin-top: 14px">
          <div class="tip-mini-icon">🎯</div>
          <div class="tip-mini-text">
            <strong>高效提问技巧</strong>
            <p>试试"请举例说明…""这两者有什么区别…""为什么不能说…"等问法，AI 的回答会更深入。</p>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, ChatDotRound, Plus, VideoPause } from '@element-plus/icons-vue'
import { getAiQaData, streamAiChat, getAiChatSessions, getAiChatMessages } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const input = ref('')
const streaming = ref(false)
const streamContent = ref('')
const currentCitations = ref([])
const currentSessionId = ref(null)
const currentSessionTitle = ref('')
const chatBodyRef = ref(null)

const sources = ref([])
const sessions = ref([])
const messages = ref([])
const hotQuestions = ref([])
const rotationIndex = ref(0)
let rotationTimer = null

// 热门追问：10条分2页轮换，每页5条
const displayHotQuestions = computed(() => {
  const start = rotationIndex.value * 5
  return hotQuestions.value.slice(start, start + 5)
})

const suggestedQuestions = ref([
  '实践为什么是检验真理的唯一标准？',
  '感性认识和理性认识有什么区别？',
  '如何理解真理的绝对性与相对性？',
  '举例说明实践对认识的决定作用'
])

let streamController = null

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now - d
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function renderContent(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

async function loadPage() {
  const [data, sessData] = await Promise.all([getAiQaData(), getAiChatSessions()])
  sources.value = data.sources || []
  hotQuestions.value = data.hotQuestions || []
  suggestedQuestions.value = data.suggestedQuestions?.length ? data.suggestedQuestions : suggestedQuestions.value
  sessions.value = sessData || []
  if (sessions.value.length) switchSession(sessions.value[0])
}

function newChat() {
  currentSessionId.value = null
  currentSessionTitle.value = '新对话'
  messages.value = []
  currentCitations.value = []
  streamContent.value = ''
}

async function switchSession(session) {
  currentSessionId.value = session.id
  currentSessionTitle.value = session.title
  try {
    const msgs = await getAiChatMessages(session.id)
    messages.value = (msgs || []).map(m => ({
      role: m.role, content: m.content, citations: m.citations || []
    }))
  } catch { messages.value = [] }
  currentCitations.value = []
  scrollToBottom()
}

function sendMessage(text) {
  const question = (text || input.value).trim()
  if (!question || streaming.value) return
  input.value = ''
  messages.value.push({ role: 'student', content: question, citations: [] })
  scrollToBottom()
  streaming.value = true
  streamContent.value = ''
  currentCitations.value = []

  streamController = streamAiChat(question, {
    onSession(data) {
      if (!currentSessionId.value) {
        currentSessionId.value = data.sessionId
        currentSessionTitle.value = question.length > 20 ? question.slice(0, 20) + '…' : question
        getAiChatSessions().then(s => { sessions.value = s || [] })
      }
    },
    onCitations(citations) { currentCitations.value = citations || [] },
    onChunk(content) { streamContent.value += content; scrollToBottom() },
    onDone(data) {
      streaming.value = false
      messages.value.push({ role: 'assistant', content: data.fullContent || streamContent.value, citations: data.citations || [] })
      streamContent.value = ''
      currentCitations.value = []
      scrollToBottom()
      getAiChatSessions().then(s => { sessions.value = s || [] })
    },
    onError(err) {
      streaming.value = false
      messages.value.push({ role: 'assistant', content: '抱歉，请求遇到了问题：' + (err.message || '未知错误') + '\n请稍后重试。', citations: [] })
      streamContent.value = ''
      currentCitations.value = []
    }
  }, currentSessionId.value, null)
}

function stopStreaming() {
  if (streamController) { streamController.abort(); streamController = null }
  streaming.value = false
  if (streamContent.value.trim()) {
    messages.value.push({ role: 'assistant', content: streamContent.value + '\n\n*(已停止生成)*', citations: currentCitations.value })
  }
  streamContent.value = ''
  currentCitations.value = []
}

function scrollToBottom() {
  nextTick(() => {
    if (chatBodyRef.value) chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  })
}

onMounted(() => {
  runPageLoad(loading, loadPage)
  // 每 8 秒轮换显示热门问题
  rotationTimer = setInterval(() => {
    rotationIndex.value = (rotationIndex.value + 1) % 2
  }, 8000)
})
onUnmounted(() => {
  if (rotationTimer) { clearInterval(rotationTimer); rotationTimer = null }
})
</script>

<style scoped>
.aiqa-root { max-width: 100%; }
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-header h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; max-width: 65ch; }

/* ===== 侧边卡片 ===== */
.side-card {
  border-radius: 14px; border: 1px solid var(--line);
  background: var(--card);
  transition: box-shadow var(--duration-fast) var(--ease-out);
}
.side-card:hover { box-shadow: var(--shadow-sm); }
.side-card-hd { display: flex; justify-content: space-between; align-items: center; }
.sc-title { font-size: 14px; font-weight: 700; }

/* 侧边空状态 */
.side-empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 28px 0; gap: 8px;
}
.side-empty-icon { font-size: 28px; opacity: 0.5; }
.side-empty-text { font-size: 12px; color: var(--muted); text-align: center; line-height: 1.6; }

/* 对话记录行 */
.session-row {
  display: flex; gap: 10px; padding: 10px 12px;
  border-radius: 10px; cursor: pointer; margin-bottom: 4px;
  transition: background var(--duration-fast) var(--ease-out);
}
.session-row:hover { background: var(--soft); }
.session-row.active { background: var(--active); border: 1px solid #909090; }
.sr-left { padding-top: 3px; }
.sr-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--line);
  display: block;
}
.session-row.active .sr-dot { background: var(--primary); }
.sr-body { flex: 1; min-width: 0; }
.sr-title { font-size: 13px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sr-meta { font-size: 11px; color: var(--muted); display: flex; gap: 4px; margin-top: 2px; }

/* 知识来源行 */
.source-row {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px; border-radius: 8px; cursor: pointer;
  transition: background var(--duration-fast); margin-bottom: 2px;
}
.source-row:hover { background: var(--soft); }
.src-icon { font-size: 15px; flex-shrink: 0; }
.src-title { flex: 1; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.src-arrow { color: var(--muted); flex-shrink: 0; opacity: 0; transition: opacity var(--duration-fast); }
.source-row:hover .src-arrow { opacity: 1; }

/* ===== 聊天卡片 ===== */
.chat-card {
  border-radius: 16px; border: 1px solid var(--line); background: var(--card);
  display: flex; flex-direction: column; height: calc(100vh - 200px);
  overflow: hidden;
}
.chat-card > :deep(.el-card__body) {
  display: flex; flex-direction: column; flex: 1; padding: 0; overflow: hidden;
}
.chat-card-hd {
  display: flex; justify-content: space-between; align-items: center;
}

/* 聊天消息区 */
.chat-body {
  flex: 1; overflow-y: auto; padding: 20px 22px;
  display: flex; flex-direction: column; gap: 18px;
  background: linear-gradient(180deg, var(--bg) 0%, var(--card) 30%);
}

/* 欢迎页 */
.chat-welcome {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; flex: 1; text-align: center; padding: 20px 0;
}
.welcome-icon { font-size: 56px; margin-bottom: 12px; }
.chat-welcome h2 { font-size: 22px; font-weight: 800; margin: 0 0 8px; }
.welcome-desc { font-size: 13px; color: var(--muted); line-height: 1.7; max-width: 400px; }

.welcome-questions { margin-top: 24px; width: 100%; max-width: 440px; }
.wq-label { font-size: 13px; font-weight: 600; color: var(--muted); margin-bottom: 12px; text-align: left; }
.wq-grid { display: flex; flex-direction: column; gap: 8px; }
.wq-chip {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; border-radius: 12px;
  background: var(--card); border: 1px solid var(--line);
  font-size: 13px; cursor: pointer; text-align: left;
  transition: all var(--duration-fast) var(--ease-out);
}
.wq-chip:hover { border-color: var(--primary); background: var(--primary-soft); transform: translateX(4px); }
.wq-num {
  width: 24px; height: 24px; border-radius: 6px;
  background: var(--soft); display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 800; color: var(--muted); flex-shrink: 0;
}

/* 消息行 */
.msg-row {
  display: flex; gap: 10px; align-items: flex-start;
}
.msg-row.msg-user { flex-direction: row-reverse; }
.msg-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 800; flex-shrink: 0;
}
.msg-avatar.student { background: var(--primary-soft); color: var(--primary); }
.msg-avatar.assistant, .msg-avatar.ai { background: var(--success-soft); color: var(--success); }
.msg-main { max-width: 78%; }

.msg-bubble {
  padding: 12px 16px; border-radius: 16px;
  font-size: 13px; line-height: 1.7; word-break: break-word;
  box-shadow: var(--shadow-sm);
}
.msg-bubble.student {
  background: var(--primary-soft); border-bottom-right-radius: 6px;
}
.msg-bubble.assistant, .msg-bubble.ai {
  background: var(--card); border: 1px solid var(--line);
  border-bottom-left-radius: 6px;
}
.msg-bubble.streaming-bubble { border-color: var(--primary-border); background: var(--primary-soft); }
.msg-text { color: var(--ink); }
.msg-text :deep(strong) { color: var(--ink); font-weight: 800; }

.typing-cursor { display: inline; color: var(--primary); font-weight: 700; animation: blink 0.8s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* 引用 */
.msg-refs { margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--line); }
.refs-label { font-size: 11px; color: var(--muted); margin-bottom: 4px; }
.refs-list { display: flex; flex-wrap: wrap; gap: 6px; }
.ref-chip {
  font-size: 11px; padding: 3px 10px; border-radius: 14px;
  background: var(--primary-soft); color: var(--primary);
  cursor: pointer; border: 1px solid var(--primary-border);
  transition: background var(--duration-fast);
}
.ref-chip:hover { background: var(--primary); color: #fff; }

/* 输入区 */
.chat-input-area { padding: 12px 20px 14px; border-top: 1px solid var(--line); background: var(--card); }
.input-row { display: flex; gap: 8px; }
.chat-input { flex: 1; }
.send-btn { min-width: 72px; }
.input-hints { margin-top: 6px; font-size: 11px; color: var(--muted); }

/* ===== 右侧引用卡片 ===== */
.citation-card {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 12px; border-radius: 10px; background: var(--soft);
  margin-bottom: 8px; cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.citation-card:hover { background: var(--active); transform: translateX(2px); }
.cc-icon { font-size: 18px; flex-shrink: 0; margin-top: 1px; }
.cc-body { flex: 1; min-width: 0; }
.cc-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.cc-excerpt { font-size: 11px; color: var(--muted); line-height: 1.5; }
.cc-arrow { color: var(--muted); flex-shrink: 0; opacity: 0; transition: opacity var(--duration-fast); margin-top: 4px; }
.citation-card:hover .cc-arrow { opacity: 1; }

/* 热门追问 */
.hot-list { display: flex; flex-direction: column; gap: 2px; }
.hot-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px; cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.hot-row:hover { background: var(--soft); transform: translateX(3px); }
.hot-rank {
  width: 22px; height: 22px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 800; flex-shrink: 0;
  background: var(--soft); color: var(--muted);
}
.hot-rank.rank-1, .hot-rank.rank-2, .hot-rank.rank-3 {
  background: transparent; font-size: 16px;
}
.hot-text { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hot-count {
  font-size: 11px; color: var(--muted); flex-shrink: 0;
  background: var(--soft); padding: 2px 8px; border-radius: 10px;
}
.hot-footer {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--line);
}
.rotation-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--line);
  transition: background var(--duration-fast);
}
.rotation-dot.active { background: var(--danger); width: 16px; border-radius: 3px; }
.rotation-hint { font-size: 10px; color: var(--muted); }

/* 移除旧推荐追问样式 */
.suggest-list, .suggest-row, .suggest-text, .suggest-arrow { /* replaced by hot-list */ }

/* 小贴士 */
.tip-mini {
  display: flex; gap: 10px; padding: 14px;
  background: linear-gradient(135deg, var(--soft) 0%, var(--active) 100%);
  border: 1px dashed var(--line); border-radius: 12px;
}
.tip-mini-icon { font-size: 20px; flex-shrink: 0; }
.tip-mini-text strong { font-size: 12px; }
.tip-mini-text p { font-size: 11px; color: var(--muted); margin-top: 4px; line-height: 1.6; }
</style>
