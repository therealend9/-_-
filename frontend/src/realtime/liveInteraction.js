import { io } from 'socket.io-client'

let socket
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 10

function readToken() {
  try { return JSON.parse(window.sessionStorage.getItem('sizheng-user') || 'null')?.token || '' }
  catch { return '' }
}

function socketUrl() {
  const apiBase = import.meta.env.VITE_API_BASE_URL || window.location.origin
  return apiBase.replace(/\/api\/?$/, '')
}

/**
 * 订阅课堂实时互动事件（含 WebSocket 连接状态反馈）
 *
 * 回调列表：
 * - onQuestion(data)      教师发布文字问答
 * - onStats(data)         答题统计更新
 * - onClose(data)         教师关闭问答
 * - onAnswerSubmitted(data) 学生提交回答
 * - onHandRaised(data)    学生举手
 * - onAnswerHighlighted(data) 教师高亮回答
 * - onQuizPublished(data) 教师推送随堂测验
 * - onQuizClosed(data)    教师关闭/测验过期
 * - onConnected()         WebSocket 连接成功
 * - onDisconnected()      WebSocket 断开
 */
export function subscribeLiveInteraction({
  onClose, onQuestion, onStats, onAnswerSubmitted, onHandRaised, onAnswerHighlighted,
  onQuizPublished, onQuizClosed,
  onConnected, onDisconnected
}) {
  const token = readToken()
  if (!token) {
    console.warn('[LiveInteraction] No auth token, WebSocket disabled')
    if (onDisconnected) onDisconnected()
    return () => {}
  }

  // 断开旧连接
  if (socket) {
    socket.removeAllListeners()
    socket.disconnect()
    socket = undefined
  }

  reconnectAttempts = 0

  socket = io(socketUrl(), {
    auth: { token },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: MAX_RECONNECT_ATTEMPTS,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
    timeout: 10000
  })

  socket.on('connect', () => {
    console.log('[LiveInteraction] WebSocket connected')
    reconnectAttempts = 0
    if (onConnected) onConnected()
  })

  socket.on('disconnect', (reason) => {
    console.warn('[LiveInteraction] WebSocket disconnected:', reason)
    if (onDisconnected) onDisconnected()
  })

  socket.on('connect_error', (err) => {
    console.error('[LiveInteraction] WebSocket connect error:', err.message)
    reconnectAttempts++
    if (onDisconnected) onDisconnected()
  })

  // 业务事件订阅
  if (onQuestion) socket.on('live-question:published', onQuestion)
  if (onStats) socket.on('live-question:stats', onStats)
  if (onClose) socket.on('live-question:closed', onClose)
  if (onAnswerSubmitted) socket.on('live-answer:submitted', onAnswerSubmitted)
  if (onHandRaised) socket.on('live-hand:raised', onHandRaised)
  if (onAnswerHighlighted) socket.on('live-answer:highlighted', onAnswerHighlighted)
  if (onQuizPublished) socket.on('live-quiz:published', onQuizPublished)
  if (onQuizClosed) socket.on('live-quiz:closed', onQuizClosed)

  // 返回取消订阅函数
  return () => {
    if (socket) {
      socket.removeAllListeners()
      socket.disconnect()
      socket = undefined
    }
  }
}

/**
 * 获取当前 WebSocket 连接状态
 */
export function isLiveConnected() {
  return !!(socket && socket.connected)
}
