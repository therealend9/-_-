<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 课程班级 / 课程结构详情</span></div>

    <div class="page-header">
      <div>
        <h1>{{ course.name }}</h1>
        <p class="page-desc">{{ course.code }} · {{ course.semester }} · {{ course.college }}</p>
      </div>
      <div class="header-actions">
        <el-button :icon="ArrowLeft" @click="router.push('/admin/course-management')">返回课程</el-button>
        <el-button :icon="DocumentChecked">结构校验</el-button>
        <el-button :icon="Edit" type="primary">编辑结构</el-button>
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
      <el-col :span="15">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>课程档案</strong>
              <div class="tag-row">
                <el-tag :type="course.statusType">{{ course.status }}</el-tag>
                <el-tag type="info">{{ course.owner }}</el-tag>
              </div>
            </div>
          </template>
          <div class="course-meta">
            <div>
              <span class="muted small">课程代码</span>
              <strong>{{ course.code }}</strong>
            </div>
            <div>
              <span class="muted small">学期</span>
              <strong>{{ course.semester }}</strong>
            </div>
            <div>
              <span class="muted small">开课院系</span>
              <strong>{{ course.college }}</strong>
            </div>
            <div>
              <span class="muted small">负责人</span>
              <strong>{{ course.owner }}</strong>
            </div>
          </div>
          <p class="course-desc">{{ course.description }}</p>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>章节结构</strong>
              <el-tag type="info" size="small">{{ chapters.length }} 个章节</el-tag>
            </div>
          </template>
          <div class="chapter-list">
            <div v-for="chapter in chapters" :key="chapter.id" class="chapter-item">
              <div class="chapter-order">{{ chapter.order }}</div>
              <div class="chapter-main">
                <div class="chapter-head">
                  <strong>{{ chapter.title }}</strong>
                  <el-tag size="small" :type="chapter.statusType">{{ chapter.status }}</el-tag>
                </div>
                <p>{{ chapter.summary }}</p>
                <div class="point-row">
                  <el-tag v-for="point in chapter.knowledgePoints" :key="`${chapter.id}-${point}`" size="small" effect="plain">{{ point }}</el-tag>
                </div>
              </div>
              <div class="chapter-side">
                <span>{{ chapter.taskCount }} 任务</span>
                <span>{{ chapter.resourceCount }} 资源</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>质量检查</strong></template>
          <div v-for="item in qualityChecks" :key="item.name" class="quality-item">
            <div class="quality-head">
              <strong>{{ item.name }}</strong>
              <el-tag size="small" :type="item.type">{{ item.result }}</el-tag>
            </div>
            <p>{{ item.desc }}</p>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>结构变更记录</strong></template>
          <el-timeline>
            <el-timeline-item v-for="item in timeline" :key="`${item.title}-${item.time}`" :timestamp="item.time">
              <div class="timeline-title">{{ item.title }}</div>
              <div class="muted small">{{ item.desc }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>教学任务链</strong>
              <el-tag type="success" size="small">课前-课中-课后-治理</el-tag>
            </div>
          </template>
          <el-table :data="taskChain" style="width: 100%">
            <el-table-column prop="phase" label="阶段" width="90" />
            <el-table-column prop="title" label="任务节点" width="150" />
            <el-table-column prop="owner" label="责任方" width="100" />
            <el-table-column prop="target" label="目标" min-width="240" />
            <el-table-column label="状态" width="110" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.statusType">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>班级覆盖</strong></template>
          <div v-if="classCoverage.length" class="coverage-list">
            <div v-for="item in classCoverage" :key="item.name" class="coverage-item">
              <div class="coverage-head">
                <strong>{{ item.name }}</strong>
                <span class="muted small">{{ item.teacher }} · {{ item.students }} 人</span>
              </div>
              <el-progress :percentage="item.progress" :stroke-width="10" />
              <div class="coverage-meta">
                <span>预习完成 {{ item.progress }}%</span>
                <span>小测均分 {{ item.quizAvg || '待统计' }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无班级绑定" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <strong>资源与来源绑定</strong>
          <el-tag type="info" size="small">{{ resources.length }} 项</el-tag>
        </div>
      </template>
      <el-table :data="resources" style="width: 100%">
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="title" label="资源名称" min-width="260" />
        <el-table-column prop="chapter" label="关联章节" min-width="180" />
        <el-table-column prop="indexStatus" label="索引状态" width="120" align="center" />
        <el-table-column prop="auditStatus" label="审核状态" width="120" align="center" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, DocumentChecked, Edit } from '@element-plus/icons-vue'
import { getCourseStructureDetail } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const course = ref({})
const stats = ref([])
const chapters = ref([])
const taskChain = ref([])
const classCoverage = ref([])
const resources = ref([])
const qualityChecks = ref([])
const timeline = ref([])

onMounted(() => runPageLoad(loading, async () => {
  const data = await getCourseStructureDetail(route.params.courseId)
  course.value = data.course || {}
  stats.value = data.stats || []
  chapters.value = data.chapters || []
  taskChain.value = data.taskChain || []
  classCoverage.value = data.classCoverage || []
  resources.value = data.resources || []
  qualityChecks.value = data.qualityChecks || []
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
.header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.section-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.tag-row { display: flex; gap: 8px; align-items: center; }
.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.course-meta { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.course-meta div {
  background: var(--soft); border-radius: 10px; padding: 14px;
  display: flex; flex-direction: column; gap: 6px;
}
.course-desc { margin-top: 14px; font-size: 13px; color: #4d4d4d; line-height: 1.8; }
.chapter-list { display: flex; flex-direction: column; gap: 12px; }
.chapter-item {
  display: grid; grid-template-columns: 42px minmax(0, 1fr) 86px; gap: 12px;
  background: var(--soft); border: 1px solid var(--line); border-radius: 12px; padding: 14px;
}
.chapter-order {
  width: 42px; height: 42px; border-radius: 10px; background: var(--active);
  display: flex; align-items: center; justify-content: center; font-weight: 800;
}
.chapter-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.chapter-main p { margin: 8px 0 10px; font-size: 13px; line-height: 1.7; color: #4d4d4d; }
.point-row { display: flex; gap: 8px; flex-wrap: wrap; }
.chapter-side {
  display: flex; flex-direction: column; justify-content: center; align-items: flex-end; gap: 6px;
  color: var(--muted); font-size: 12px;
}
.quality-item {
  background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px;
}
.quality-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.quality-item p { margin: 0; font-size: 13px; line-height: 1.7; color: #4d4d4d; }
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.coverage-list { display: flex; flex-direction: column; gap: 12px; }
.coverage-item { background: var(--soft); border-radius: 10px; padding: 12px; }
.coverage-head { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.coverage-meta {
  display: flex; justify-content: space-between; gap: 10px; margin-top: 8px;
  font-size: 12px; color: var(--muted);
}
</style>
