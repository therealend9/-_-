<template>
  <div class="page">
    <div class="card">
      <h2>找回密码</h2>
      <p class="sub">输入账号，我们将发送重置链接至注册邮箱</p>

      <!-- 步骤1：输入账号 -->
      <div v-if="step === 1">
        <el-input v-model="username" placeholder="请输入账号" size="large" style="margin-bottom: 16px" @keyup.enter="requestReset" />
        <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="requestReset">发送重置链接</el-button>
        <div class="link"><router-link to="/login">返回登录</router-link></div>
      </div>

      <!-- 步骤2：输入 token + 新密码 -->
      <div v-else-if="step === 2">
        <p class="muted">重置链接已发送，请在下方输入收到的验证码和新密码。开发环境下 token 显示在页面顶部。</p>
        <div v-if="devToken" class="dev-hint">🔑 开发环境 Token：{{ devToken }}</div>
        <el-input v-model="token" placeholder="输入重置验证码/Token" size="large" style="margin-bottom: 12px" />
        <el-input v-model="password" placeholder="新密码（6-64位）" type="password" show-password size="large" style="margin-bottom: 12px" />
        <el-input v-model="confirmPassword" placeholder="确认新密码" type="password" show-password size="large" style="margin-bottom: 16px" @keyup.enter="doReset" />
        <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="doReset">重置密码</el-button>
      </div>

      <!-- 步骤3：完成 -->
      <div v-else class="done">
        <div class="done-icon">✅</div>
        <h3>密码重置成功</h3>
        <p class="muted">请使用新密码登录</p>
        <el-button type="primary" size="large" style="margin-top: 16px" @click="$router.push('/login')">返回登录</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { forgotPassword, resetPassword } from '../../api/auth.js'

const step = ref(1)
const loading = ref(false)
const username = ref('')
const token = ref('')
const password = ref('')
const confirmPassword = ref('')
const devToken = ref('')

async function requestReset() {
  if (!username.value.trim()) { ElMessage.warning('请输入账号'); return }
  loading.value = true
  try {
    const result = await forgotPassword(username.value.trim())
    if (result.sent) {
      devToken.value = result.devToken || ''
      step.value = 2
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (e) { ElMessage.error(e?.message || '请求失败') }
  finally { loading.value = false }
}

async function doReset() {
  if (!token.value.trim()) { ElMessage.warning('请输入验证码'); return }
  if (password.value.length < 6) { ElMessage.warning('密码至少6位'); return }
  if (password.value !== confirmPassword.value) { ElMessage.warning('两次密码不一致'); return }

  loading.value = true
  try {
    const result = await resetPassword(token.value.trim(), password.value)
    if (result.success) {
      step.value = 3
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (e) { ElMessage.error(e?.message || '重置失败') }
  finally { loading.value = false }
}
</script>

<style scoped>
.page { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f7f6f2; }
.card { width: 420px; background: #fff; border-radius: 12px; padding: 36px; border: 1px solid #c9c9c9; }
h2 { margin: 0 0 6px 0; font-size: 24px; }
.sub { font-size: 13px; color: #8a8a8a; margin-bottom: 24px; }
.muted { color: #8a8a8a; font-size: 13px; }
.link { text-align: center; margin-top: 16px; font-size: 13px; }
.link a { color: #2f2f2f; font-weight: 700; }
.dev-hint { background: #fef0f0; border: 1px dashed #F56C6C; padding: 10px; border-radius: 8px; font-size: 12px; margin-bottom: 16px; word-break: break-all; }
.done { text-align: center; padding: 20px 0; }
.done-icon { font-size: 48px; margin-bottom: 12px; }
</style>
