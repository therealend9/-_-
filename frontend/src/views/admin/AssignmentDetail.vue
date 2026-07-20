<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 作业小测 / 作业详情</span></div>
    <div class="page-header">
      <div>
        <h1>{{ assignment.title }}</h1>
        <p class="page-desc">{{ assignment.course }} · {{ assignment.chapter }} · {{ assignment.className }}</p>
      </div>
      <div class="header-actions">
        <el-button @click="router.back()">返回列表</el-button>
        <el-button>导出提交</el-button>
        <el-button type="primary">进入复核</el-button>
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

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>作业信息</strong>
              <el-tag :type="assignment.statusType">{{ assignment.status }}</el-tag>
            </div>
          </template>
          <div class="info-grid">
            <div><span class="muted small">作业类型</span><strong>{{ assignment.type }}</strong></div>
            <div><span class="muted small">发布教师</span><strong>{{ assignment.publisher }}</strong></div>
            <div><span class="muted small">截止时间</span><strong>{{ assignment.deadline }}</strong></div>
            <div><span class="muted small">绑定量规</span><strong>{{ assignment.rubricTitle }}</strong></div>
          </div>
          <p class="assignment-desc">{{ assignment.description }}</p>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>评分分布</strong></template>
          <div class="score-bars">
            <div v-for="item in scoreDistribution" :key="item.range" class="bar-item">
              <div class="bar" :style="{ height: `${item.height}px`, background: item.color }"></div>
              <div class="bar-count">{{ item.count }}</div>
              <div class="bar-label">{{ item.range }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>关联评分量规</strong>
              <el-tag type="success" size="small">{{ rubric.status }}</el-tag>
            </div>
          </template>
          <div class="rubric-title">{{ rubric.title }}</div>
          <p class="assignment-desc">{{ rubric.description }}</p>
          <div class="rubric-items">
            <div v-for="item in rubric.items" :key="item.id" class="rubric-item">
              <span>{{ item.name }}</span>
              <strong>{{ item.weight }}%</strong>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never" class="section-card">
          <template #header><strong>处理流程</strong></template>
          <el-timeline>
            <el-timeline-item v-for="item in timeline" :key="item.title" :timestamp="item.time">
              <div class="timeline-title">{{ item.title }}</div>
              <div class="muted small">{{ item.desc }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <strong>题目与知识点</strong>
          <el-tag type="info" size="small">{{ questions.length }} 项</el-tag>
        </div>
      </template>
      <el-table :data="questions" style="width: 100%">
        <el-table-column prop="order" label="#" width="60" align="center" />
        <el-table-column prop="type" label="题型" width="120" />
        <el-table-column prop="knowledgePoint" label="知识点" width="150" />
        <el-table-column prop="stem" label="题干/任务说明" min-width="260" />
        <el-table-column prop="source" label="来源" width="140" />
        <el-table-column prop="auditStatus" label="审核" width="100" align="center" />
      </el-table>
    </el-card>

    <el-card shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <strong>学生提交与复核状态</strong>
          <el-input v-model="keyword" placeholder="搜索学生" size="small" style="width: 220px" />
        </div>
      </template>
      <el-table :data="filteredSubmissions" style="width: 100%">
        <el-table-column prop="studentName" label="学生" width="120" />
        <el-table-column prop="studentNo" label="账号" width="120" />
        <el-table-column prop="answered" label="完成题目" width="100" align="center" />
        <el-table-column label="得分" width="90" align="center">
          <template #default="{ row }">
            <span :class="Number(row.score) >= 80 ? 'good' : Number(row.score) > 0 ? 'warn' : 'muted'">{{ row.score }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="submittedAt" label="提交时间" width="160" />
        <el-table-column label="提交状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.statusType">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="复核状态" width="140" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.reviewType">{{ row.reviewStatus }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center">
          <template #default>
            <el-button size="small">查看作答</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAssignmentDetail } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const keyword = ref('')
const assignment = ref({})
const stats = ref([])
const rubric = ref({ items: [] })
const questions = ref([])
const submissions = ref([])
const scoreDistribution = ref([])
const timeline = ref([])

const filteredSubmissions = computed(() => submissions.value.filter((item) => {
  if (!keyword.value) return true
  return item.studentName.includes(keyword.value) || item.studentNo.includes(keyword.value)
}))

onMounted(() => runPageLoad(loading, async () => {
  const data = await getAssignmentDetail(route.params.assignmentId)
  assignment.value = data.assignment || {}
  stats.value = data.stats || []
  rubric.value = data.rubric || { items: [] }
  questions.value = data.questions || []
  submissions.value = data.submissions || []
  scoreDistribution.value = data.scoreDistribution || []
  timeline.value = data.timeline || []
}))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.section-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 32px; font-weight: 800; margin: 4px 0; }
.info-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.info-grid div {
  background: var(--soft); border-radius: 10px; padding: 14px;
  display: flex; flex-direction: column; gap: 6px;
}
.assignment-desc { margin-top: 14px; font-size: 13px; color: #4d4d4d; line-height: 1.8; }
.score-bars { height: 218px; display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; padding: 10px 0; }
.bar-item { flex: 1; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.bar { width: 36px; border-radius: 8px 8px 0 0; min-height: 18px; }
.bar-count { font-size: 13px; font-weight: 800; margin-top: 6px; }
.bar-label { font-size: 11px; color: var(--muted); margin-top: 2px; }
.rubric-title { font-size: 17px; font-weight: 800; }
.rubric-items { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
.rubric-item {
  background: var(--soft); border-radius: 10px; padding: 12px;
  display: flex; justify-content: space-between; gap: 12px; font-size: 13px;
}
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.good { color: #67C23A; font-weight: 800; }
.warn { color: #E6A23C; font-weight: 800; }
</style>
