<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">学生端 / 课后反馈 / 批改明细</span></div>

    <div class="page-header">
      <div>
        <h1>{{ submission.title }}</h1>
        <p class="page-desc">
          {{ submission.course }} · {{ submission.chapter }} · {{ submission.className }}
        </p>
      </div>
      <div class="header-actions">
        <el-button @click="router.push(`/student/feedback/${submission.assignmentId || 1}`)">返回反馈详情</el-button>
        <el-button type="primary">提交订正</el-button>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top: 20px">
      <el-col v-for="stat in summary" :key="stat.label" :span="6">
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
              <strong>作答与识别</strong>
              <el-tag :type="submission.statusType">{{ submission.status }}</el-tag>
            </div>
          </template>

          <div class="answer-meta">
            <div>
              <span class="muted small">学生</span>
              <strong>{{ submission.studentName }} / {{ submission.studentNo }}</strong>
            </div>
            <div>
              <span class="muted small">提交时间</span>
              <strong>{{ submission.submittedAt }}</strong>
            </div>
            <div>
              <span class="muted small">量规</span>
              <strong>{{ submission.rubricTitle }}</strong>
            </div>
          </div>

          <el-divider />
          <div class="prompt-box">
            <div class="box-title">题目要求</div>
            <p>{{ answer.prompt }}</p>
          </div>
          <div class="answer-box">
            <div class="box-title">原始作答文本</div>
            <p>{{ answer.originalText }}</p>
          </div>
          <div class="answer-box ocr">
            <div class="box-title">OCR 与结构化识别</div>
            <p>{{ answer.ocrText }}</p>
          </div>

          <div class="keyword-row">
            <el-tag v-for="keyword in answer.keywords" :key="keyword" size="small">{{ keyword }}</el-tag>
          </div>

          <div class="attachment-row">
            <div v-for="file in answer.attachments" :key="file.name" class="attachment-item">
              <strong>{{ file.name }}</strong>
              <span class="muted small">{{ file.status }} · 置信度 {{ file.confidence }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>复核结论</strong></template>
          <div class="score-panel">
            <span>最终得分</span>
            <strong>{{ submission.finalScore }}</strong>
            <em>AI建议 {{ submission.aiScore }} · 调整 {{ submission.teacherAdjustment }}</em>
          </div>
          <div class="review-block">
            <div class="box-title">教师评语</div>
            <p>{{ teacherReview.comment }}</p>
          </div>
          <div class="review-grid">
            <div>
              <span class="muted small">复核教师</span>
              <strong>{{ teacherReview.reviewer }}</strong>
            </div>
            <div>
              <span class="muted small">发布时间</span>
              <strong>{{ teacherReview.reviewedAt }}</strong>
            </div>
            <div>
              <span class="muted small">发布状态</span>
              <strong>{{ teacherReview.publishStatus }}</strong>
            </div>
          </div>
          <el-divider />
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
          <strong>量规分项明细</strong>
          <el-tag type="info" size="small">AI建议 + 教师确认</el-tag>
        </div>
      </template>
      <div class="rubric-grid">
        <div v-for="item in rubricItems" :key="item.id" class="rubric-item">
          <div class="rubric-head">
            <div>
              <div class="rubric-name">{{ item.name }}</div>
              <div class="muted small">{{ item.evidence }}</div>
            </div>
            <div class="score-badge">{{ item.finalScore }}/{{ item.weight }}</div>
          </div>
          <el-progress :percentage="scorePercent(item.finalScore, item.weight)" :stroke-width="10" />
          <div class="score-line">
            <span>AI {{ item.aiScore }}</span>
            <span>教师调整 {{ signed(item.teacherAdjustment) }}</span>
            <el-tag size="small" :type="levelType(item.level)">{{ item.level }}</el-tag>
          </div>
          <p class="rubric-comment">{{ item.comment }}</p>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="15">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>题目与证据记录</strong>
              <el-tag type="info" size="small">{{ answer.questionRecords.length }} 条</el-tag>
            </div>
          </template>
          <el-table :data="answer.questionRecords" style="width: 100%">
            <el-table-column prop="knowledgePoint" label="知识点" width="130" />
            <el-table-column prop="stem" label="题目" min-width="220" />
            <el-table-column prop="selectedAnswer" label="学生答案" min-width="150" />
            <el-table-column prop="correctAnswer" label="参考答案" min-width="150" />
            <el-table-column label="结果" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.resultType">{{ row.result }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>AI问题标记</strong></template>
          <div v-for="item in aiReview.riskFlags" :key="item.title" class="issue-item">
            <div class="issue-head">
              <strong>{{ item.title }}</strong>
              <el-tag size="small" :type="issueType(item.type)">{{ item.type === 'warning' ? '需关注' : '提示' }}</el-tag>
            </div>
            <p>{{ item.quote }}</p>
            <div class="muted small">{{ item.suggestion }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <strong>AI建议与教师调整依据</strong>
          <el-tag type="success" size="small">置信度 {{ aiReview.confidence }}</el-tag>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="review-block">
            <div class="box-title">AI评分结论</div>
            <p>{{ aiReview.conclusion }}</p>
            <div v-for="item in aiReview.suggestions" :key="item" class="suggestion-line">{{ item }}</div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="review-block">
            <div class="box-title">教师调整说明</div>
            <p>{{ teacherReview.adjustmentReason }}</p>
            <p>{{ teacherReview.comment }}</p>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getGradingDetail } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const submission = ref({})
const summary = ref([])
const answer = ref({ attachments: [], keywords: [], questionRecords: [] })
const rubricItems = ref([])
const aiReview = ref({ suggestions: [], riskFlags: [] })
const teacherReview = ref({})
const timeline = ref([])

function scorePercent(score, weight) {
  if (!Number(weight)) return 0
  return Math.round((Number(score || 0) / Number(weight)) * 100)
}

function levelType(level) {
  if (level === '优秀') return 'success'
  if (level === '合格') return 'warning'
  return 'danger'
}

function issueType(type) {
  if (type === 'warning') return 'warning'
  if (type === 'danger') return 'danger'
  return 'info'
}

function signed(value) {
  const number = Number(value || 0)
  return number > 0 ? `+${number}` : String(number)
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getGradingDetail(route.params.submissionId)
  submission.value = data.submission || {}
  summary.value = data.summary || []
  answer.value = data.answer || answer.value
  rubricItems.value = data.rubricItems || []
  aiReview.value = data.aiReview || aiReview.value
  teacherReview.value = data.teacherReview || {}
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
.answer-meta, .review-grid {
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px;
}
.answer-meta div, .review-grid div {
  background: var(--soft); border-radius: 10px; padding: 14px;
  display: flex; flex-direction: column; gap: 6px;
}
.prompt-box, .answer-box, .review-block {
  background: var(--soft); border-radius: 12px; padding: 14px; margin-bottom: 12px;
}
.answer-box.ocr { border: 1px dashed var(--line); }
.box-title { font-weight: 800; margin-bottom: 8px; }
.prompt-box p, .answer-box p, .review-block p {
  font-size: 13px; line-height: 1.85; color: #4d4d4d; margin: 0;
}
.keyword-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; }
.attachment-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.attachment-item {
  background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 12px;
  display: flex; flex-direction: column; gap: 4px;
}
.score-panel {
  background: var(--active); border-radius: 14px; padding: 18px; margin-bottom: 14px;
  display: flex; flex-direction: column; gap: 4px;
}
.score-panel strong { font-size: 42px; line-height: 1; }
.score-panel em { font-style: normal; color: var(--muted); font-size: 12px; }
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.rubric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.rubric-item { background: var(--soft); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
.rubric-head { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.rubric-name { font-size: 16px; font-weight: 800; margin-bottom: 6px; }
.score-badge {
  min-width: 70px; height: 34px; display: flex; align-items: center; justify-content: center;
  background: var(--active); border-radius: 8px; font-weight: 800;
}
.score-line { display: flex; align-items: center; gap: 12px; margin-top: 10px; font-size: 12px; color: var(--muted); }
.rubric-comment { margin: 12px 0 0; font-size: 13px; line-height: 1.7; color: #4d4d4d; }
.issue-item { background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.issue-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.issue-item p { margin: 8px 0 6px; font-size: 13px; line-height: 1.7; color: #4d4d4d; }
.suggestion-line { margin-top: 8px; padding: 10px 12px; background: #fff; border: 1px dashed var(--line); border-radius: 8px; font-size: 13px; color: #4d4d4d; }
</style>
