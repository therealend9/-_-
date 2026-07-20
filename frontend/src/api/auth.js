import { isMockMode, request } from './http.js'
import { mockResolve } from './mockTransport.js'

const demoUsers = {
  student: { id: 2, username: 'student01', realName: '李明哲', role: 'student', token: 'demo-token-student' },
  teacher: { id: 1, username: 'teacher01', realName: '王老师', role: 'teacher', token: 'demo-token-teacher' },
  admin: { id: 3, username: 'admin01', realName: '平台管理员', role: 'admin', token: 'demo-token-admin' }
}

function normalizeRole(role) {
  return ['student', 'teacher', 'admin'].includes(role) ? role : 'student'
}

function mockLogin(payload) {
  const account = String(payload?.account || payload?.username || '').trim()
  const password = String(payload?.password || '')
  const role = normalizeRole(payload?.role)

  if (account === '123456' && password === '123456') {
    return mockResolve(demoUsers[role])
  }

  return new Promise((_, reject) => {
    window.setTimeout(() => reject(new Error('账号、密码或身份不匹配')), 180)
  })
}

function mockRegister(payload) {
  const username = String(payload?.username || payload?.account || '').trim()
  const realName = String(payload?.realName || payload?.name || '').trim()
  const password = String(payload?.password || '')
  const confirmPassword = String(payload?.confirmPassword || '')

  if (!username || !realName || !password) {
    return Promise.reject(new Error('账号、姓名和密码不能为空'))
  }

  if (!/^[A-Za-z0-9_]{4,50}$/.test(username)) {
    return Promise.reject(new Error('账号需为 4-50 位字母、数字或下划线'))
  }

  if (password.length < 6 || password.length > 64) {
    return Promise.reject(new Error('密码长度需为 6-64 位'))
  }

  if (confirmPassword && password !== confirmPassword) {
    return Promise.reject(new Error('两次输入的密码不一致'))
  }

  return mockResolve({
    success: true,
    message: '注册成功，请使用新账号登录'
  })
}

export function login(payload) {
  if (isMockMode()) {
    return mockLogin(payload)
  }

  return request('/login', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function register(payload) {
  if (isMockMode()) {
    return mockRegister(payload)
  }

  return request('/register', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function forgotPassword(username) {
  if (isMockMode()) {
    return Promise.resolve({ sent: true, message: '重置链接已发送至注册邮箱', devToken: 'mock-reset-token-123' })
  }
  return request('/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ username })
  })
}

export function resetPassword(token, password) {
  if (isMockMode()) {
    return Promise.resolve({ success: true, message: '密码已重置，请使用新密码登录' })
  }
  return request('/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, password })
  })
}
