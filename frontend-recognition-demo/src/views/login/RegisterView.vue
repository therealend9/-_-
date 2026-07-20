<template>
  <div class="register-page">
    <section class="register-info">
      <div class="brand">
        <span class="brand-logo">AI</span>
        <div>
          <div class="brand-name">马原智学 Agent</div>
          <div class="brand-sub">面向思政课程的智慧教学与学习支持系统</div>
        </div>
      </div>

      <div class="intro">
        <h1>创建学生账号</h1>
        <p>注册后可进入学生端，使用导学、小测、AI 问答、作业反馈和学习报告等功能。</p>
      </div>

      <div class="notice-list">
        <div class="notice-item">
          <strong>学生账号自助注册</strong>
          <span>默认创建为学生角色，账号通过后端写入用户表。</span>
        </div>
        <div class="notice-item">
          <strong>教师与管理员账号</strong>
          <span>由平台管理员在管理端创建，避免高权限账号开放注册。</span>
        </div>
        <div class="notice-item">
          <strong>后续优化方向</strong>
          <span>可继续接入班级邀请码、统一身份认证和注册审核流程。</span>
        </div>
      </div>
    </section>

    <section class="register-panel">
      <div class="register-card">
        <h2>账号注册</h2>
        <p class="register-sub">请填写真实姓名和学生账号信息</p>

        <el-form label-position="top" class="register-form" @submit.prevent>
          <el-form-item label="账号">
            <el-input v-model="form.username" placeholder="4-50 位字母、数字或下划线" size="large" maxlength="50" />
          </el-form-item>

          <el-form-item label="姓名">
            <el-input v-model="form.realName" placeholder="请输入真实姓名" size="large" maxlength="50" />
          </el-form-item>

          <el-form-item label="学号">
            <el-input v-model="form.studentNo" placeholder="可选，用于后续绑定班级和课程" size="large" maxlength="50" />
          </el-form-item>

          <el-form-item label="学院">
            <el-input v-model="form.college" placeholder="马克思主义学院" size="large" maxlength="100" />
          </el-form-item>

          <el-form-item label="专业">
            <el-input v-model="form.major" placeholder="可选" size="large" maxlength="100" />
          </el-form-item>

          <el-form-item label="班级">
            <el-input v-model="form.className" placeholder="可选，例如 2023级本科1班" size="large" maxlength="100" />
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              placeholder="6-64 位密码"
              type="password"
              show-password
              size="large"
              maxlength="64"
              @keyup.enter="submit"
            />
          </el-form-item>

          <el-form-item label="确认密码">
            <el-input
              v-model="form.confirmPassword"
              placeholder="请再次输入密码"
              type="password"
              show-password
              size="large"
              maxlength="64"
              @keyup.enter="submit"
            />
          </el-form-item>

          <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="submit">
            注册
          </el-button>
        </el-form>

        <div class="login-link">
          <span>已有账号？</span>
          <router-link to="/login">返回登录</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { register as registerApi } from '../../api/auth.js'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: '',
  realName: '',
  studentNo: '',
  college: '马克思主义学院',
  major: '',
  className: '',
  password: '',
  confirmPassword: ''
})

function validateForm() {
  const username = form.username.trim()
  const realName = form.realName.trim()
  const college = form.college.trim()
  const studentNo = form.studentNo.trim()
  const major = form.major.trim()
  const className = form.className.trim()

  if (!username || !realName || !form.password) {
    return '请填写账号、姓名和密码'
  }

  if (!/^[A-Za-z0-9_]{4,50}$/.test(username)) {
    return '账号需为 4-50 位字母、数字或下划线'
  }

  if (realName.length > 50) {
    return '姓名不能超过 50 个字符'
  }

  if (college.length > 100) {
    return '学院不能超过 100 个字符'
  }

  if (studentNo.length > 50) {
    return '学号不能超过 50 个字符'
  }

  if (major.length > 100) {
    return '专业不能超过 100 个字符'
  }

  if (className.length > 100) {
    return '班级不能超过 100 个字符'
  }

  if (form.password.length < 6 || form.password.length > 64) {
    return '密码长度需为 6-64 位'
  }

  if (form.password !== form.confirmPassword) {
    return '两次输入的密码不一致'
  }

  return ''
}

async function submit() {
  const message = validateForm()
  if (message) {
    ElMessage.warning(message)
    return
  }

  loading.value = true
  try {
    const result = await registerApi({
      username: form.username.trim(),
      realName: form.realName.trim(),
      studentNo: form.studentNo.trim(),
      college: form.college.trim(),
      major: form.major.trim(),
      className: form.className.trim(),
      password: form.password,
      confirmPassword: form.confirmPassword
    })
    ElMessage.success(result.message || '注册成功，请登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  display: flex;
  min-height: 100vh;
  background: #f7f6f2;
}

.register-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding: 56px 64px;
  background: #e6e4de;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-logo {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fcfcfa;
  border-radius: 12px;
  font-size: 22px;
  font-weight: 800;
}

.brand-name {
  font-size: 24px;
  font-weight: 800;
}

.brand-sub {
  font-size: 13px;
  color: #6f6f6f;
}

.intro {
  max-width: 680px;
  margin-top: 32px;
}

.intro h1 {
  font-size: 34px;
  line-height: 1.35;
  margin-bottom: 14px;
}

.intro p {
  font-size: 15px;
  color: #5f5f5f;
  line-height: 1.9;
}

.notice-list {
  display: grid;
  gap: 14px;
  max-width: 680px;
}

.notice-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: #efeee9;
  border: 1px dashed #c9c9c9;
  border-radius: 8px;
  padding: 16px 18px;
}

.notice-item strong {
  font-size: 15px;
}

.notice-item span {
  font-size: 13px;
  color: #6f6f6f;
  line-height: 1.7;
}

.register-panel {
  width: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.register-card {
  width: 100%;
  background: #fff;
  border: 1px solid #c9c9c9;
  border-radius: 8px;
  padding: 36px;
}

.register-card h2 {
  font-size: 26px;
  font-weight: 800;
}

.register-sub {
  font-size: 13px;
  color: #8a8a8a;
  margin: 6px 0 24px;
}

.register-form {
  margin-top: 8px;
}

.submit-btn {
  width: 100%;
  height: 46px;
  font-size: 16px;
}

.login-link {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 18px;
  font-size: 13px;
  color: #6f6f6f;
}

.login-link a {
  color: #2f2f2f;
  font-weight: 700;
}

@media (max-width: 900px) {
  .register-page {
    flex-direction: column;
  }

  .register-info,
  .register-panel {
    width: 100%;
    padding: 32px 24px;
  }

  .intro {
    margin-top: 0;
  }

  .intro h1 {
    font-size: 28px;
  }
}
</style>
