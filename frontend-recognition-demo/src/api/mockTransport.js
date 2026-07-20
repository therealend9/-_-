const MOCK_DELAY = 180

export function clone(data) {
  return JSON.parse(JSON.stringify(data))
}

export function mockResolve(data, delay = MOCK_DELAY) {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(clone(data)), delay)
  })
}

export function mockAction(data = { success: true }, delay = MOCK_DELAY) {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(clone(data)), delay)
  })
}
