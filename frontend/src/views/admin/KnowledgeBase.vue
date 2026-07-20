<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 知识库管理 / 知识来源与索引治理</span></div>
    <div class="page-header">
      <h1>知识库与来源管理</h1>
      <div class="header-actions">
        <el-button :loading="reindexingAll" @click="handleReindexAll">重新索引</el-button>
        <el-button type="primary">新增资源</el-button>
      </div>
    </div>
    <p class="page-desc">管理教材、课件、案例库、题库等知识来源，控制RAG检索范围与内容质量</p>

    <!-- 概览统计 -->
    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <div class="stat-card">
          <div class="muted small">{{ stat.label }}</div>
          <div class="stat-num" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="muted small">{{ stat.desc }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 知识资源列表 -->
    <el-card shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div style="display: flex; justify-content: space-between">
          <strong>知识来源列表</strong>
          <el-input placeholder="搜索知识来源" style="width: 240px" size="small" />
        </div>
      </template>
      <el-table :data="knowledgeList" style="width: 100%">
        <el-table-column prop="name" label="资源名称" min-width="200" />
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="course" label="关联课程" min-width="180" />
        <el-table-column prop="size" label="内容量" width="100" align="center" />
        <el-table-column label="索引状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.indexStatus === '已索引' ? 'success' : 'warning'">{{ row.indexStatus }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.auditType">{{ row.audit }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updateTime" label="更新时间" width="140" align="center" />
        <el-table-column label="操作" width="260" align="center">
          <template #default="{ row }">
            <el-button size="small" @click="router.push(`/admin/knowledge-base/${row.id || 1}`)">查看</el-button>
            <el-button size="small" type="primary" :loading="rowAction === `${row.id}-reindex`" :disabled="Boolean(rowAction)" @click="handleReindex(row)">索引</el-button>
            <el-button size="small" type="success" :loading="rowAction === `${row.id}-approve`" :disabled="Boolean(rowAction)" @click="handleAudit(row, 'approve')">审核</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { auditKnowledgeSource, getKnowledgeSources, reindexKnowledgeSource, reindexKnowledgeSources } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const reindexingAll = ref(false)
const rowAction = ref('')
const stats = ref([])
const knowledgeList = ref([])

async function loadSources() {
  const data = await getKnowledgeSources()
  stats.value = data.stats || []
  knowledgeList.value = data.knowledgeList || []
}

async function handleReindexAll() {
  if (reindexingAll.value) return

  reindexingAll.value = true
  try {
    const data = await reindexKnowledgeSources()
    ElMessage.success(data.message || '知识库已重新索引')
    await loadSources()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '重新索引失败')
  } finally {
    reindexingAll.value = false
  }
}

async function handleReindex(row) {
  if (rowAction.value) return

  rowAction.value = `${row.id}-reindex`
  try {
    const data = await reindexKnowledgeSource(row.id)
    ElMessage.success(data.message || '知识来源已重新索引')
    await loadSources()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '重新索引失败')
  } finally {
    rowAction.value = ''
  }
}

async function handleAudit(row, action) {
  if (rowAction.value) return

  rowAction.value = `${row.id}-${action}`
  try {
    const data = await auditKnowledgeSource(row.id, action)
    ElMessage.success(data.message || '知识来源审核状态已更新')
    await loadSources()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '审核知识来源失败')
  } finally {
    rowAction.value = ''
  }
}

onMounted(() => runPageLoad(loading, loadSources))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 32px; font-weight: 800; margin: 4px 0; }
</style>

