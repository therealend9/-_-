<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 运行治理 / 系统设置</span></div>
    <div class="page-header">
      <h1>系统设置</h1>
      <div class="header-actions">
        <el-button type="primary" :loading="saving" @click="saveAll">保存全部</el-button>
      </div>
    </div>
    <p class="page-desc">平台配置持久化存储，修改后立即生效</p>

    <el-card shadow="never" class="card" style="margin-top: 16px">
      <el-table :data="configList" style="width: 100%" size="small">
        <el-table-column prop="configKey" label="配置键" width="220" />
        <el-table-column label="配置值" min-width="300">
          <template #default="{ row }">
            <el-input v-model="row.configValue" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="saveOne(row)">保存</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getSystemSettings, saveSystemConfig } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const loading = ref(true)
const saving = ref(false)
const configList = ref([])

async function load() {
  await runPageLoad(loading, async () => {
    configList.value = await getSystemSettings()
  })
}

async function saveOne(row) {
  try {
    await saveSystemConfig(row.configKey, row.configValue)
    ElMessage.success(`${row.configKey} 已保存`)
  } catch (e) { ElMessage.error('保存失败') }
}

async function saveAll() {
  saving.value = true
  try {
    for (const row of configList.value) {
      await saveSystemConfig(row.configKey, row.configValue)
    }
    ElMessage.success('全部配置已保存')
  } catch (e) { ElMessage.error('部分保存失败') }
  finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
</style>
