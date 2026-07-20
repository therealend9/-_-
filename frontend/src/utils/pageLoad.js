import { ElMessage } from 'element-plus/es/components/message/index.mjs'

export async function runPageLoad(loading, task, fallbackMessage = '页面数据加载失败') {
  loading.value = true

  try {
    await task()
    return true
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || fallbackMessage)
    return false
  } finally {
    loading.value = false
  }
}
