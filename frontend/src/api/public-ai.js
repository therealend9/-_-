import { streamAiChat } from './student.js'
import { isMockMode } from './http.js'

/**
 * 登录页公开体验问答。
 * 不创建学生会话、不写入学习记录；登录后的完整多轮问答仍使用 student.js。
 */
export function streamPublicAiChat(question, callbacks, courseKey = 'general') {
  if (isMockMode()) {
    return streamAiChat(question, callbacks)
  }

  const controller = new AbortController()
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''

  fetch(`${apiBaseUrl}/public/ai-chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, courseKey }),
    signal: controller.signal
  }).then(async (response) => {
    if (!response.ok || !response.body) {
      const message = await response.text().catch(() => '请求失败')
      callbacks.onError?.(new Error(message))
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'citations') callbacks.onCitations?.(data.citations || [])
          if (data.type === 'chunk') callbacks.onChunk?.(data.content || '')
          if (data.type === 'done') callbacks.onDone?.(data)
          if (data.type === 'error') callbacks.onError?.(new Error(data.message || 'AI 服务调用失败'))
        } catch {
          // 忽略流式传输中的不完整片段
        }
      }
    }
  }).catch((error) => {
    if (error.name !== 'AbortError') callbacks.onError?.(error)
  })

  return controller
}
