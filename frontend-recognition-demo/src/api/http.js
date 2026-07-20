const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
const REQUEST_TIMEOUT = 15000
const TOKEN_REFRESH_MARGIN = 3600 // 提前1小时刷新token

export function isMockMode() {
  return USE_MOCK
}

function readStoredUser() {
  try {
    return JSON.parse(window.sessionStorage.getItem('sizheng-user') || 'null')
  } catch {
    return null
  }
}

function getAuthToken() {
  return readStoredUser()?.token || ''
}

/**
 * 解析 JWT payload 获取过期时间
 */
function getTokenExpiry(token) {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return 0
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    return Number(payload.exp) || 0
  } catch {
    return 0
  }
}

/**
 * 静默刷新 token（如果快过期了）
 */
let refreshPromise = null
async function maybeRefreshToken() {
  if (USE_MOCK) return

  const stored = readStoredUser()
  if (!stored?.token) return

  const exp = getTokenExpiry(stored.token)
  const now = Math.floor(Date.now() / 1000)
  // 还没到刷新窗口，不需要刷新
  if (exp - now > TOKEN_REFRESH_MARGIN) return

  // 已经过期了，不刷新
  if (now >= exp) return

  // 避免并发刷新
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000)
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${stored.token}`
        },
        signal: controller.signal
      })
      clearTimeout(timeoutId)
      if (response.ok) {
        const data = await response.json()
        if (data.token) {
          window.sessionStorage.setItem('sizheng-user', JSON.stringify({
            ...stored,
            token: data.token,
            user: data.user || stored.user
          }))
        }
      }
    } catch {
      // 静默刷新失败不影响正常请求
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

// 页面加载时尝试刷新一次
maybeRefreshToken()

async function readJson(response) {
  const text = await response.text()
  if (!text) return null

  try {
    return JSON.parse(text)
  } catch {
    throw new Error('API 返回内容不是有效 JSON')
  }
}

function unwrapResponse(data) {
  if (!data || typeof data !== 'object' || !('code' in data)) {
    return data
  }

  if (data.code === 0 || data.code === '0') {
    return 'data' in data ? data.data : data
  }

  throw new Error(data.message || 'API 返回业务错误')
}

export async function request(path, options = {}) {
  if (!API_BASE_URL) {
    throw new Error('缺少 VITE_API_BASE_URL，当前应使用 mock API')
  }

  const { headers, ...fetchOptions } = options
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT)
  let response

  try {
    const publicPaths = new Set(['/login', '/register'])
    const authToken = publicPaths.has(path) ? '' : getAuthToken()
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...fetchOptions,
      headers: {
        'Content-Type': 'application/json',
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...(headers || {})
      },
      signal: controller.signal
    })
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`API 请求超时：${path}`)
    }

    throw new Error(`API 请求失败：${path}`)
  } finally {
    window.clearTimeout(timeoutId)
  }

  if (!response.ok) {
    let message = `API 请求失败：${response.status}`
    try {
      const errorData = await readJson(response)
      message = errorData.message || message
    } catch {
      // Keep the status-based message when the response has no JSON body.
    }
    if (response.status === 401 || response.status === 403) {
      window.sessionStorage.removeItem('sizheng-user')
    }

    throw new Error(message)
  }

  const data = await readJson(response)
  const result = unwrapResponse(data)

  // 请求成功后，静默检查并刷新 token
  maybeRefreshToken()

  return result
}
