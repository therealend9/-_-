<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 运行治理 / 操作日志</span></div>
    <div class="page-header">
      <div>
        <h1>操作日志</h1>
        <p class="page-desc">登录、审核、发布、索引和权限变更记录</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Download" type="primary" :loading="exporting" @click="handleExport">导出日志</el-button>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top: 20px">
      <el-col v-for="stat in stats" :key="stat.label" :span="6">
        <div class="stat-card">
          <div class="muted small">{{ stat.label }}</div>
          <div class="stat-num" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="muted small">{{ stat.desc }}</div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never" class="card" style="margin-top: 20px">
      <template #header>
        <div class="table-header">
          <div class="filters">
            <el-select v-model="actionFilter" style="width: 120px" clearable placeholder="操作类型">
              <el-option label="登录" value="登录" />
              <el-option label="修改" value="修改" />
              <el-option label="审核" value="审核" />
              <el-option label="发布" value="发布" />
              <el-option label="索引" value="索引" />
              <el-option label="导出" value="导出" />
              <el-option label="催办" value="催办" />
            </el-select>
            <el-select v-model="roleFilter" style="width: 120px" clearable placeholder="角色">
              <el-option label="学生" value="student" />
              <el-option label="教师" value="teacher" />
              <el-option label="管理员" value="admin" />
              <el-option label="系统" value="system" />
            </el-select>
            <el-select v-model="resultFilter" style="width: 120px" clearable placeholder="结果">
              <el-option label="成功" value="成功" />
              <el-option label="失败" value="失败" />
            </el-select>
            <el-date-picker v-model="date" type="date" placeholder="选择日期" size="default" />
          </div>
          <span class="muted small">共 {{ filteredLogs.length }} 条记录</span>
        </div>
      </template>
      <el-table :data="filteredLogs" style="width: 100%">
        <el-table-column prop="time" label="时间" width="165" />
        <el-table-column prop="operator" label="操作人" width="120">
          <template #default="{ row }">
            <strong>{{ row.operator }}</strong>
            <div class="muted" style="font-size: 11px">{{ row.role }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.actionType" size="small">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="targetLabel" label="目标对象" width="120" />
        <el-table-column prop="detail" label="操作详情" min-width="260" />
        <el-table-column prop="ip" label="IP地址" width="130" />
        <el-table-column prop="result" label="结果" width="85" align="center">
          <template #default="{ row }">
            <el-tag :type="row.resultType" size="small">{{ row.result }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button :icon="View" size="small" @click="router.push(`/admin/audit-log/${row.id}`)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <el-pagination layout="prev, pager, next" :total="total" background size="small" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { Download, View } from '@element-plus/icons-vue'
import { exportAuditLogs, getAuditLogs } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const actionFilter = ref('')
const roleFilter = ref('')
const resultFilter = ref('')
const date = ref('')
const stats = ref([])
const logs = ref([])
const total = ref(0)
const exporting = ref(false)

const filteredLogs = computed(() => logs.value.filter((item) => {
  const matchesAction = !actionFilter.value || item.action === actionFilter.value
  const matchesRole = !roleFilter.value || item.roleCode === roleFilter.value
  const matchesResult = !resultFilter.value || item.result === resultFilter.value
  return matchesAction && matchesRole && matchesResult
}))

function formatDateFilter(value) {
  if (!value) return ''
  const dateValue = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(dateValue.getTime())) return ''

  const year = dateValue.getFullYear()
  const month = String(dateValue.getMonth() + 1).padStart(2, '0')
  const day = String(dateValue.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function downloadTextFile(filename, content) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename || 'audit-logs.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function handleExport() {
  if (exporting.value) return

  exporting.value = true
  try {
    const data = await exportAuditLogs({
      action: actionFilter.value,
      role: roleFilter.value,
      result: resultFilter.value,
      date: formatDateFilter(date.value)
    })
    downloadTextFile(data.filename, data.content || '')
    ElMessage.success(data.message || '日志已导出')
  } catch (error) {
    ElMessage.error(error.message || '日志导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getAuditLogs()
  stats.value = data.stats || []
  logs.value = data.logs || []
  total.value = data.total || 0
}))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.table-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.filters { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.pagination-row { margin-top: 16px; text-align: right; }
</style>
