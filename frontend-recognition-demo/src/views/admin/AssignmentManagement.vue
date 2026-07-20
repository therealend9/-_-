<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 内容治理 / 作业管理</span></div>
    <div class="page-header">
      <h1>作业管理</h1>
      <div>
        <el-select v-model="courseFilter" style="width: 180px; margin-right: 10px" clearable placeholder="按课程筛选">
          <el-option v-for="c in courses" :key="c" :label="c" :value="c" />
        </el-select>
        <el-button type="primary">批量导出</el-button>
      </div>
    </div>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6" v-for="s in summary" :key="s.label">
        <div class="stat-card">
          <div class="muted small">{{ s.label }}</div>
          <div class="stat-num" :style="{ color: s.color }">{{ s.value }}</div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never" class="card" style="margin-top: 20px">
      <template #header><strong>作业列表</strong></template>
      <el-table :data="filteredAssignments" empty-text="暂无作业" style="width: 100%">
        <el-table-column prop="title" label="作业标题" min-width="180" />
        <el-table-column prop="course" label="所属课程" width="160" />
        <el-table-column prop="class" label="班级" width="100" />
        <el-table-column prop="submitCount" label="提交/总数" width="100" />
        <el-table-column prop="avgScore" label="均分" width="70">
          <template #default="{ row }">
            <span :style="{ color: row.avgScore >= 80 ? '#67C23A' : '#E6A23C', fontWeight: 700 }">{{ row.avgScore }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="deadline" label="截止时间" width="140" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '批改中' ? 'warning' : row.status === '已完成' ? 'success' : 'primary'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="router.push(`/admin/assignments/${row.id}`)">查看详情</el-button>
            <el-button size="small" type="primary" :loading="remindingId === row.id" :disabled="Boolean(remindingId)" @click="handleRemind(row)">催交</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getAssignmentManagement, remindAssignment } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const courseFilter = ref('')
const loading = ref(true)
const courses = ref([])
const summary = ref([])
const assignments = ref([])
const remindingId = ref(null)

const filteredAssignments = computed(() => {
  if (!courseFilter.value) return assignments.value
  return assignments.value.filter((item) => item.course === courseFilter.value)
})

function applyPayload(data) {
  courses.value = data.courses || []
  summary.value = data.summary || []
  assignments.value = data.assignments || []
}

async function handleRemind(row) {
  if (remindingId.value) return

  remindingId.value = row.id
  try {
    const data = await remindAssignment(row.id)
    applyPayload(data)
    ElMessage.success(data.message || '催交通知已发送')
  } catch (error) {
    ElMessage.error(error.message || '催交失败')
  } finally {
    remindingId.value = null
  }
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getAssignmentManagement()
  applyPayload(data)
}))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card { background: var(--soft); border-radius: 14px; padding: 20px; text-align: center; border: 1px dashed var(--line); }
.stat-num { font-size: 36px; font-weight: 800; margin-top: 4px; }
</style>

