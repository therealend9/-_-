<template>
  <div class="login-page">
    <!-- 左侧平台介绍区 -->
    <div class="login-left">
      <div class="left-glow glow-one"></div>
      <div class="left-glow glow-two"></div>

      <div class="left-content">
        <div class="brand">
          <span class="brand-logo">MA</span>
          <div>
            <div class="brand-name">马原智学 Agent</div>
            <div class="brand-sub">《马克思主义基本原理》智慧教学与学习支持系统</div>
          </div>
        </div>

        <div class="ai-intro">
          <h1 class="hero-title">选择课程，<span>开始提问</span></h1>
        </div>

        <div class="course-selector" aria-label="选择课程 AI">
          <button class="course-nav" type="button" aria-label="查看前面的课程" @click="scrollCourseTabs(-1)">‹</button>
          <div ref="courseTabsRef" class="course-tabs" role="tablist" aria-label="选择课程 AI">
            <button v-for="course in aiCourses" :key="course.key" :class="{ active: selectedCourse.key === course.key }" :disabled="publicStreaming" @click="selectCourse(course)">{{ course.name }}</button>
          </div>
          <button class="course-nav" type="button" aria-label="查看后面的课程" @click="scrollCourseTabs(1)">›</button>
        </div>

        <section class="public-ai" :style="{ '--dialogue-height': `${chatHeight}px` }" aria-label="高校思政课总体问答 AI">
          <div class="ai-head">
            <div class="ai-head-title"><span class="ai-orb">AI</span><strong>{{ selectedCourse.name }}专属 AI</strong></div>
            <span class="ai-state"><i></i> 体验模式</span>
          </div>

          <div class="ai-dialogue">
            <div v-if="!publicMessages.length && !publicStreaming" class="ai-welcome">
              <span class="welcome-orb">AI</span>
              <h3>你好，我是{{ selectedCourse.name }}学习助手</h3>
              <p>{{ selectedCourse.greeting }}</p>
            </div>
            <div v-for="(message, index) in publicMessages" :key="index" class="ai-message" :class="message.role">
              <span class="message-avatar">{{ message.role === 'user' ? '你' : 'AI' }}</span>
              <p>{{ message.content }}</p>
            </div>
            <div v-if="publicStreaming" class="ai-message assistant">
              <span class="message-avatar">AI</span>
              <p>{{ publicStream || '正在梳理课程知识…' }}<span class="typing-dot">●</span></p>
            </div>
          </div>
          <div class="chat-resize-handle" title="拖动调整问答框高度" @pointerdown="startChatResize"><span></span></div>

          <div v-if="publicCitations.length" class="ai-citations">
            <span>参考来源</span>
            <em v-for="citation in publicCitations" :key="citation.sourceId">{{ citation.title }}</em>
          </div>

          <div class="ai-quick-questions">
            <button v-for="question in quickQuestions" :key="question" :disabled="publicStreaming" @click="askPublicAi(question)">{{ question }}</button>
          </div>

          <div class="ai-input-row">
            <el-input v-model="publicQuestion" :disabled="publicStreaming" :placeholder="selectedCourse.placeholder" @keyup.enter.exact="askPublicAi()" />
            <el-button type="primary" :loading="publicStreaming" :disabled="!publicQuestion.trim()" @click="askPublicAi()">提问</el-button>
          </div>
          <p class="ai-tip">体验问答不保存记录；完整学习档案将在登录后生成。</p>
        </section>

        <div class="left-footer">
          <div>
            <strong>课程导向</strong>
            <span>以问题驱动理论学习</span>
          </div>
          <div>
            <strong>学习支持</strong>
            <span>问答、导学与反馈协同</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="login-right">
      <div class="login-card">
        <h2>登录平台</h2>
        <p class="login-sub">请选择身份并输入账号信息</p>

        <el-radio-group v-model="role" size="large" class="role-group">
          <el-radio-button value="student">学生</el-radio-button>
          <el-radio-button value="teacher">教师</el-radio-button>
          <el-radio-button value="admin">管理</el-radio-button>
        </el-radio-group>

        <div class="form-item">
          <label>账号</label>
          <el-input v-model="account" placeholder="请输入账号" size="large" @keyup.enter="login" />
        </div>

        <div class="form-item">
          <label>密码</label>
          <el-input v-model="password" placeholder="请输入密码" type="password" show-password size="large" @keyup.enter="login" />
        </div>

        <div class="form-extra">
          <el-checkbox v-model="remember">记住本设备</el-checkbox>
          <a class="forgot">忘记密码</a>
        </div>

        <div class="auth-actions">
          <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="login">登录</el-button>
          <el-button size="large" class="register-btn" @click="goRegister">学生注册</el-button>
        </div>

        <el-divider />

        <div class="login-others">
          <el-button class="other-btn">统一身份认证</el-button>
          <el-button class="other-btn">扫码登录</el-button>
        </div>

        <p class="login-footer">登录即表示遵守平台教学数据与内容安全规范</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { login as loginApi } from '../../api/auth.js'
import { streamPublicAiChat } from '../../api/public-ai.js'

const role = ref('student')
const account = ref('123456')
const password = ref('123456')
const remember = ref(false)
const loading = ref(false)
const publicQuestion = ref('')
const publicStreaming = ref(false)
const publicStream = ref('')
const publicCitations = ref([])
const publicMessages = ref([])
const courseTabsRef = ref(null)
const chatHeight = ref(250)
const router = useRouter()

const aiCourses = [
  { key: 'general', name: '思政总助手', greeting: '我可以帮你梳理思政课学习路径、概念关系与学习方法。', placeholder: '例如：怎样建立思政课整体学习框架？', questions: ['思政课之间有什么联系？', '怎样学好思政课？', '理论联系实际怎么做？'] },
  { key: 'marxism', name: '马克思主义基本原理', greeting: '我可以陪你理解唯物史观、认识论、政治经济学等核心问题。', placeholder: '例如：实践为什么是检验真理的唯一标准？', questions: ['什么是马克思主义？', '实践为什么重要？', '如何理解真理的相对性？'] },
  { key: 'maozedong', name: '毛泽东思想和中国特色社会主义理论体系概论', greeting: '我可以协助梳理中国化时代化马克思主义的理论脉络。', placeholder: '例如：如何理解马克思主义中国化时代化？', questions: ['什么是中国化时代化？', '理论创新的意义是什么？', '如何理解中国式现代化？'] },
  { key: 'history', name: '中国近现代史纲要', greeting: '我可以帮助你从历史脉络理解中国人民的选择。', placeholder: '例如：为什么说历史和人民选择了中国共产党？', questions: ['近代中国的基本国情是什么？', '为什么要走社会主义道路？', '怎样看待历史选择？'] },
  { key: 'morality', name: '思想道德与法治', greeting: '我可以和你讨论理想信念、道德修养、法治素养等问题。', placeholder: '例如：大学生如何坚定理想信念？', questions: ['如何理解理想信念？', '自由与规则如何统一？', '怎样提升法治素养？'] }
]
const selectedCourse = ref(aiCourses[0])
const quickQuestions = computed(() => selectedCourse.value.questions)
let publicAiController = null
let resizeStartY = 0
let resizeStartHeight = 0

function selectCourse(course) {
  if (course.key === selectedCourse.value.key || publicStreaming.value) return
  selectedCourse.value = course
  publicQuestion.value = ''
  publicMessages.value = []
  publicStream.value = ''
  publicCitations.value = []
}

function scrollCourseTabs(direction) {
  courseTabsRef.value?.scrollBy({ left: direction * 280, behavior: 'smooth' })
}

function startChatResize(event) {
  resizeStartY = event.clientY
  resizeStartHeight = chatHeight.value
  window.addEventListener('pointermove', resizeChat)
  window.addEventListener('pointerup', stopChatResize, { once: true })
}

function resizeChat(event) {
  chatHeight.value = Math.min(560, Math.max(190, resizeStartHeight + event.clientY - resizeStartY))
}

function stopChatResize() {
  window.removeEventListener('pointermove', resizeChat)
}

function askPublicAi(text) {
  const question = String(text || publicQuestion.value).trim()
  if (!question || publicStreaming.value) return

  publicQuestion.value = ''
  publicMessages.value.push({ role: 'user', content: question })
  publicStreaming.value = true
  publicStream.value = ''
  publicCitations.value = []

  publicAiController = streamPublicAiChat(question, {
    onCitations(citations) {
      publicCitations.value = citations || []
    },
    onChunk(content) {
      publicStream.value += content
    },
    onDone(data) {
      publicMessages.value.push({ role: 'assistant', content: data.fullContent || publicStream.value || '已完成回答。' })
      publicStreaming.value = false
      publicStream.value = ''
      publicAiController = null
    },
    onError(error) {
      publicMessages.value.push({ role: 'assistant', content: `暂时无法完成回答：${error.message || 'AI 服务未就绪'}。你可以先登录，或稍后再试。` })
      publicStreaming.value = false
      publicStream.value = ''
      publicAiController = null
    }
  }, selectedCourse.value.key)
}

onBeforeUnmount(() => {
  publicAiController?.abort()
  stopChatResize()
})

async function login() {
  if (!account.value.trim() || !password.value) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  loading.value = true
  try {
    const user = await loginApi({
      account: account.value.trim(),
      password: password.value,
      role: role.value
    })
    sessionStorage.setItem('sizheng-user', JSON.stringify(user))
    ElMessage.success(`欢迎登录，${user.realName}`)
    router.push(user.role === 'student' ? '/student/course-selection' : `/${user.role}/dashboard`)
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}

function goRegister() {
  router.push('/register')
}
</script>

<style scoped>
.login-page { display: flex; min-height: 100vh; background: #f5f7fb; }
.login-left {
  position: relative; flex: 1; min-width: 0; overflow: hidden; color: #f6f9ff;
  background: radial-gradient(circle at 76% 12%, rgba(74, 142, 255, .5), transparent 28%),
    linear-gradient(135deg, #102a58 0%, #123b78 49%, #0a2045 100%);
}
.left-content {
  position: relative; z-index: 1; box-sizing: border-box; min-height: 100vh; width: 100%; max-width: none;
  margin: 0; padding: 42px 38px 26px; display: flex; flex-direction: column; gap: 18px;
}
.left-glow { position: absolute; border-radius: 50%; filter: blur(2px); opacity: .38; }
.glow-one { width: 360px; height: 360px; right: -110px; bottom: -145px; background: #2f93ff; }
.glow-two { width: 180px; height: 180px; left: 25%; top: 28%; background: #4866d8; }
.brand { display: flex; align-items: center; gap: 13px; }
.brand-logo {
  width: 44px; height: 44px; display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255, 255, 255, .42); border-radius: 13px; background: rgba(255, 255, 255, .13);
  color: #fff; font-size: 14px; font-weight: 800; letter-spacing: .08em; backdrop-filter: blur(8px);
}
.brand-name { color: #fff; font-size: 19px; font-weight: 700; letter-spacing: .02em; }
.brand-sub { margin-top: 3px; color: rgba(230, 239, 255, .72); font-size: 12px; }
.ai-intro { width: 100%; text-align: center; }
.eyebrow { margin-bottom: 12px; color: #a9c9ff; font-size: 11px; font-weight: 700; letter-spacing: .16em; }
.hero-title { margin: 0; color: #fff; font-size: clamp(36px, 3.2vw, 50px); font-weight: 700; letter-spacing: -.04em; line-height: 1.16; }
.hero-title span { color: #9bc5ff; }
.hero-desc { max-width: 570px; margin: 18px 0 0; color: rgba(229, 239, 255, .82); font-size: 15px; line-height: 1.9; }
.course-selector { display: flex; align-items: center; gap: 10px; width: min(100%, 1120px); margin: 0 auto; }
.public-ai { box-sizing: border-box; width: min(100%, 1120px); margin: 0 auto; padding: 18px 20px 15px; border: 1px solid rgba(195, 219, 255, .24); border-radius: 22px; background: rgba(8, 30, 72, .4); box-shadow: 0 18px 48px rgba(3, 16, 44, .2); backdrop-filter: blur(12px); }
.course-tabs { display: flex; flex: 1; gap: 10px; overflow-x: auto; padding: 1px; scrollbar-width: none; scroll-behavior: smooth; }
.course-tabs::-webkit-scrollbar { display: none; }
.course-tabs button { flex: 0 0 220px; padding: 6px 18px; border: 1px solid rgba(180, 211, 255, .2); border-radius: 9px; background: rgba(255, 255, 255, .05); color: #bdD9ff; cursor: pointer; font-size: 18px; font-weight: 600; line-height: 1.15; transition: .18s ease; white-space: nowrap; }
.course-tabs button:hover { background: rgba(160, 199, 255, .13); }
.course-tabs button.active { border-color: rgba(167, 207, 255, .78); background: rgba(137, 188, 255, .22); color: #fff; box-shadow: inset 0 0 0 1px rgba(255,255,255,.08); }
.course-tabs button:disabled { cursor: not-allowed; opacity: .65; }
.course-nav { width: 34px; height: 34px; flex: 0 0 34px; padding: 0; border: 1px solid rgba(180, 211, 255, .32); border-radius: 50%; background: rgba(255, 255, 255, .1); color: #d8e9ff; cursor: pointer; font-size: 28px; line-height: 28px; transition: .18s ease; }
.course-nav:hover { background: rgba(144, 190, 255, .25); color: #fff; }
.ai-head { display: flex; align-items: center; justify-content: space-between; padding: 0 0 13px; border-bottom: 1px solid rgba(195, 219, 255, .14); }
.ai-head-title { display: flex; align-items: center; gap: 9px; color: #fff; font-size: 15px; }
.ai-orb, .message-avatar { display: inline-grid; place-items: center; border-radius: 50%; background: linear-gradient(135deg, #8bc0ff, #4f74e9); color: #fff; font-size: 10px; font-weight: 800; }
.ai-orb { width: 28px; height: 28px; font-size: 11px; }
.ai-state { display: flex; align-items: center; gap: 6px; color: #a9c9ff; font-size: 12px; }
.ai-state i { width: 6px; height: 6px; border-radius: 50%; background: #68d391; box-shadow: 0 0 0 4px rgba(104, 211, 145, .12); }
.ai-dialogue { display: flex; flex-direction: column; gap: 12px; height: var(--dialogue-height, 250px); overflow-y: auto; padding: 18px 4px 12px; }
.ai-welcome { display: flex; flex: 1; flex-direction: column; align-items: center; justify-content: center; min-height: 160px; text-align: center; }
.welcome-orb { display: grid; width: 54px; height: 54px; place-items: center; border-radius: 18px; background: linear-gradient(135deg, #b3d5ff, #607bea); box-shadow: 0 10px 24px rgba(90, 137, 235, .35); color: #fff; font-size: 16px; font-weight: 800; }
.ai-welcome h3 { margin: 16px 0 8px; color: #fff; font-size: 18px; font-weight: 650; }
.ai-welcome p { max-width: 420px; margin: 0; color: rgba(220, 236, 255, .72); font-size: 12px; line-height: 1.8; }
.ai-message { display: flex; align-items: flex-start; gap: 8px; }
.ai-message.user { flex-direction: row-reverse; }
.message-avatar { flex: 0 0 22px; width: 22px; height: 22px; background: rgba(160, 199, 255, .2); color: #cfe5ff; }
.ai-message p { max-width: 82%; margin: 0; padding: 10px 12px; border-radius: 4px 12px 12px; background: rgba(255, 255, 255, .1); color: #eaf3ff; font-size: 16px; line-height: 1.7; white-space: pre-wrap; }
.ai-message.user p { border-radius: 12px 4px 12px 12px; background: #2e75cf; color: #fff; }
.typing-dot { margin-left: 4px; color: #8bc0ff; animation: blink 1s infinite; }
.chat-resize-handle { display: grid; height: 14px; place-items: center; cursor: ns-resize; touch-action: none; }
.chat-resize-handle span { width: 52px; height: 4px; border-radius: 99px; background: rgba(185, 214, 255, .45); transition: .18s ease; }
.chat-resize-handle:hover span { width: 72px; background: #a8ceff; }
.ai-citations { display: flex; align-items: center; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; color: #a9c9ff; font-size: 10px; }
.ai-citations em { max-width: 180px; overflow: hidden; padding: 3px 6px; border-radius: 99px; background: rgba(144, 190, 255, .12); color: #dcecff; font-style: normal; text-overflow: ellipsis; white-space: nowrap; }
.ai-quick-questions { display: flex; flex-wrap: wrap; gap: 7px; margin: 2px 0 12px; }
.ai-quick-questions button { padding: 8px 12px; border: 1px solid rgba(180, 211, 255, .22); border-radius: 99px; background: transparent; color: #bdd9ff; cursor: pointer; font-size: 16px; line-height: 1.25; }
.ai-quick-questions button:hover, .ai-quick-questions button:disabled { background: rgba(174, 209, 255, .12); }
.ai-input-row { display: flex; gap: 8px; padding: 7px; border: 1px solid rgba(255, 255, 255, .35); border-radius: 15px; background: rgba(255, 255, 255, .96); }
.ai-input-row :deep(.el-input__wrapper) { min-height: 34px; background: transparent; box-shadow: none; }
.ai-input-row .el-button { flex: 0 0 64px; height: 34px; border-radius: 10px; }
.ai-tip { margin: 8px 0 0; color: rgba(205, 225, 255, .55); font-size: 10px; }
.left-footer { display: flex; gap: 30px; width: min(100%, 1120px); margin: auto auto 0; padding-top: 6px; }
.left-footer div { display: flex; align-items: baseline; gap: 7px; }
.left-footer strong { color: #fff; font-size: 13px; font-weight: 700; }
.left-footer span { color: rgba(222, 236, 255, .62); font-size: 11px; }
@keyframes blink { 50% { opacity: .2; } }
@media (max-width: 1080px) {
  .left-content { padding: 42px 28px 26px; }
  .login-right { width: 410px; padding: 32px; }
}
@media (max-width: 820px) {
  .login-page { display: block; }
  .login-left { min-height: auto; }
  .left-content { min-height: auto; padding: 28px 20px; }
  .hero-title { font-size: 36px; }
  .login-right { box-sizing: border-box; width: 100%; padding: 24px; }
  .left-footer { margin-top: 0; flex-wrap: wrap; }
}
.login-right {
  width: 480px; display: flex; align-items: center; justify-content: center;
  background: #f7f6f2; padding: 48px;
}
.login-card {
  width: 100%; background: #fff; border-radius: 24px; padding: 40px 36px;
  border: 1px solid #c9c9c9; text-align: center;
}
.login-card h2 { font-size: 26px; font-weight: 800; }
.login-sub { font-size: 13px; color: #8a8a8a; margin: 6px 0 24px; }
.role-group { margin-bottom: 24px; }
.form-item { text-align: left; margin-bottom: 16px; }
.form-item label { display: block; font-size: 14px; font-weight: 700; margin-bottom: 6px; }
.form-extra { display: flex; justify-content: space-between; align-items: center; font-size: 13px; margin-bottom: 4px; }
.forgot { color: #2f2f2f; font-weight: 700; cursor: pointer; }
.auth-actions { display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 18px; }
.login-btn,
.register-btn { width: 100%; height: 48px; font-size: 16px; }
.register-btn {
  border-color: #2f2f2f;
  color: #2f2f2f;
  font-weight: 700;
}
.login-others { display: flex; gap: 12px; justify-content: center; }
.other-btn { flex: 1; }
.login-footer { font-size: 11px; color: #8a8a8a; margin-top: 14px; }
</style>
