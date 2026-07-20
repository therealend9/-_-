<template>
  <div v-loading="loading">
    <div class="breadcrumb">
      <span class="muted link" @click="router.push('/student/feedback')">学生端 / 课后反馈</span>
      <span class="muted"> / {{ assignment.chapter || '反馈详情' }}</span>
    </div>
    <div class="page-header">
      <div>
        <h1>{{ assignment.chapter || assignment.title }}</h1>
        <p class="page-desc">{{ assignment.course }} · {{ assignment.className }} · {{ assignment.submittedAt }}</p>
      </div>
      <div class="header-actions">
        <el-button @click="router.push('/student/feedback')">返回</el-button>
        <el-button type="primary" @click="router.push(`/student/grading/${assignment.id || 1}`)">查看批改明细</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col v-for="stat in summary" :key="stat.label" :span="6">
        <div class="stat-card">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-num" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="stat-desc">{{ stat.desc }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 三大模块概览 -->
    <div class="section-title">模块概况</div>
    <el-row :gutter="16" style="margin-top: 12px">
      <el-col :span="8">
        <div class="module-card">
          <div class="mc-head"><span class="mc-dot mc-dot--pre"></span><strong>预习小测</strong></div>
          <div class="mc-score">{{ lessonSummary.preStudyQuiz.avgScore }}<span class="mc-unit">分</span></div>
          <div class="mc-sub">完成 {{ lessonSummary.preStudyQuiz.completed }}/{{ lessonSummary.preStudyQuiz.total }} 次</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="module-card">
          <div class="mc-head"><span class="mc-dot mc-dot--in"></span><strong>随堂测验</strong></div>
          <div class="mc-score">{{ lessonSummary.inClassQuiz.avgScore }}<span class="mc-unit">分</span></div>
          <div class="mc-sub">参与 {{ lessonSummary.inClassQuiz.completed }}/{{ lessonSummary.inClassQuiz.total }} 次</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="module-card">
          <div class="mc-head"><span class="mc-dot mc-dot--interact"></span><strong>课中互动</strong></div>
          <div class="mc-score">{{ lessonSummary.classInteraction.participated }}<span class="mc-unit">次</span></div>
          <div class="mc-sub">教师点评 {{ lessonSummary.classInteraction.teacherComments }} 次</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 24px">
      <el-col :span="15">
        <!-- PPT 历史 -->
        <div class="section-title">教师PPT</div>
        <div v-if="!pptHistory.length" class="empty-sm">暂无PPT</div>
        <div v-for="ppt in pptHistory" :key="ppt.id" class="ppt-card">
          <div class="ppt-icon"><el-icon size="20"><Present /></el-icon></div>
          <div class="ppt-body">
            <div class="ppt-title">{{ ppt.title }}</div>
            <div class="ppt-meta">{{ ppt.slides }} 页 · {{ ppt.pushedAt }}</div>
          </div>
        </div>

        <!-- 作业批改 -->
        <div class="section-title" style="margin-top: 20px">作业批改</div>
        <div v-if="!feedbacks.length" class="empty-sm">暂无批改</div>
        <div v-for="f in feedbacks" :key="f.id" class="fb-card">
          <span class="fb-score" :class="'fb-score--' + (f.scoreType || 'primary')">{{ f.score }}</span>
          <div class="fb-body">
            <strong class="fb-title">{{ f.title }}</strong>
            <div class="fb-comment">{{ f.comment }}</div>
            <div class="fb-tags"><el-tag size="small" v-for="t in f.tags" :key="t">{{ t }}</el-tag></div>
          </div>
        </div>

        <!-- 反馈概览 -->
        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>反馈概览</strong>
              <el-tag :type="assignment.statusType">{{ assignment.status }}</el-tag>
            </div>
          </template>
          <div class="overview-grid">
            <div><span class="muted small">作业类型</span><strong>{{ assignment.type }}</strong></div>
            <div><span class="muted small">提交时间</span><strong>{{ assignment.submittedAt || '待提交' }}</strong></div>
            <div><span class="muted small">综合评分</span><strong>{{ assignment.score }}</strong></div>
            <div><span class="muted small">状态</span><strong>{{ assignment.status }}</strong></div>
          </div>
          <el-divider />
          <div class="comment-block">
            <div class="comment-title">教师评语</div>
            <p>{{ teacherComment }}</p>
          </div>
          <div class="comment-block ai">
            <div class="comment-title">AI 改进建议</div>
            <p>{{ aiComment }}</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>反馈流程</strong></template>
          <el-timeline>
            <el-timeline-item v-for="item in timeline" :key="item.title" :timestamp="item.time">
              <div class="timeline-title">{{ item.title }}</div>
              <div class="muted small">{{ item.desc }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 16px">
          <template #header><strong>下一步建议</strong></template>
          <div v-for="item in suggestions" :key="item.title" class="suggestion">
            <div class="suggestion-title">{{ item.title }}</div>
            <div class="muted small">{{ item.desc }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <strong>分项评估</strong>
          <el-tag type="info" size="small">{{ assignment.rubricTitle || '综合评估量规' }}</el-tag>
        </div>
      </template>
      <div class="criteria-grid">
        <div v-for="item in criteria" :key="item.name" class="criterion">
          <div class="criterion-head">
            <div>
              <div class="criterion-name">{{ item.name }}</div>
              <div class="muted small">{{ item.comment }}</div>
            </div>
            <div class="score-badge">{{ item.score }}/{{ item.weight }}</div>
          </div>
          <el-progress :percentage="Math.round((item.score / item.weight) * 100)" :stroke-width="10" />
          <el-tag size="small" :type="item.level === '优秀' ? 'success' : item.level === '合格' ? 'warning' : 'danger'">{{ item.level }}</el-tag>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="15">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>题目反馈</strong>
              <el-tag type="info" size="small">{{ questionFeedback.length }} 项</el-tag>
            </div>
          </template>
          <el-table :data="questionFeedback" style="width: 100%">
            <el-table-column prop="knowledgePoint" label="知识点" width="130" />
            <el-table-column prop="stem" label="题目" min-width="230" />
            <el-table-column label="结果" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.isCorrect ? 'success' : 'danger'">{{ row.isCorrect ? '正确' : '需复习' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="suggestion" label="建议" min-width="190" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>反馈依据</strong></template>
          <div v-for="source in sources" :key="source.title" class="source-item">
            <el-tag size="small">{{ source.type }}</el-tag>
            <strong>{{ source.title }}</strong>
            <p class="muted small">{{ source.desc }}</p>
            <el-button size="small" text type="primary" @click="router.push(`/student/source/${source.id || 1}`)">查看溯源</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Present } from '@element-plus/icons-vue'
import { getFeedbackDetail } from '../../api/student.js'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const assignment = ref({ title: '加载中…', course: '', chapter: '', className: '', submittedAt: '', status: '', statusType: '', score: '', type: '' })
const summary = ref([])
const lessonSummary = ref({ preStudyQuiz: { avgScore: '-', completed: 0, total: 0 }, inClassQuiz: { avgScore: '-', completed: 0, total: 0 }, classInteraction: { participated: 0, teacherComments: 0 } })
const pptHistory = ref([])
const feedbacks = ref([])
const teacherComment = ref('')
const aiComment = ref('')
const criteria = ref([])
const questionFeedback = ref([])
const suggestions = ref([])
const sources = ref([])
const timeline = ref([])

onMounted(async () => {
  try {
    const data = await getFeedbackDetail(route.params.assignmentId)
    assignment.value = data.assignment || assignment.value
    summary.value = data.summary || []
    lessonSummary.value = data.lessonSummary || data.summary?.lessonSummary || lessonSummary.value
    pptHistory.value = data.pptHistory || []
    feedbacks.value = data.feedbacks || []
    teacherComment.value = data.teacherComment || ''
    aiComment.value = data.aiComment || ''
    criteria.value = data.criteria || []
    questionFeedback.value = data.questionFeedback || []
    suggestions.value = data.suggestions || []
    sources.value = data.sources || []
    timeline.value = data.timeline || []
  } catch (e) {
    console.error('加载反馈详情失败', e)
  }
})
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.muted.small { font-size: 12px; }
.muted.link { cursor: pointer; transition: color var(--duration-fast); }
.muted.link:hover { text-decoration: underline; color: var(--ink); }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-header h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.header-actions { display: flex; gap: 10px; align-items: center; }

.section-title { font-size: 15px; font-weight: 700; margin-top: 4px; }
.empty-sm { font-size: 13px; color: var(--muted); padding: 16px 0; }

.stat-card {
  background: var(--soft); border-radius: 14px; padding: 16px 18px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-label { font-size: 12px; color: var(--muted); }
.stat-num { font-size: 28px; font-weight: 800; margin: 4px 0; }
.stat-desc { font-size: 11px; color: var(--muted); }

/* 模块卡片 */
.module-card {
  background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 20px 22px;
  transition: box-shadow var(--duration-fast) var(--ease-out);
}
.module-card:hover { box-shadow: var(--shadow-sm); }
.mc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.mc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.mc-dot--pre      { background: #3a7bd5; }
.mc-dot--in       { background: #e6a23c; }
.mc-dot--interact { background: #67c23a; }
.mc-score { font-size: 30px; font-weight: 800; letter-spacing: -0.4px; line-height: 1.1; }
.mc-unit { font-size: 15px; font-weight: 600; color: var(--muted); }
.mc-sub { font-size: 12px; color: var(--muted); margin-top: 4px; }

/* PPT */
.ppt-card {
  display: flex; align-items: center; gap: 14px;
  background: var(--soft); border: 1px solid var(--line);
  border-radius: 12px; padding: 14px 16px; margin-top: 8px;
}
.ppt-icon {
  width: 40px; height: 40px; border-radius: 10px;
  background: var(--active); display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; color: var(--muted);
}
.ppt-body { flex: 1; min-width: 0; }
.ppt-title { font-size: 14px; font-weight: 700; }
.ppt-meta { font-size: 12px; color: var(--muted); margin-top: 2px; }

/* 作业批改 */
.fb-card {
  display: flex; align-items: flex-start; gap: 14px;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 12px; padding: 16px; margin-top: 8px;
}
.fb-score {
  width: 42px; height: 42px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 800; background: var(--soft);
}
.fb-score--success { background: var(--success-soft); color: var(--success); }
.fb-score--primary { background: var(--primary-soft); color: var(--primary); }
.fb-body { flex: 1; min-width: 0; }
.fb-title { font-size: 14px; font-weight: 700; display: block; margin-bottom: 4px; }
.fb-comment { font-size: 13px; color: #4d4d4d; line-height: 1.6; margin-bottom: 6px; }
.fb-tags { display: flex; gap: 6px; flex-wrap: wrap; }

.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.section-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.overview-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.overview-grid div {
  background: var(--soft); border-radius: 10px; padding: 14px;
  display: flex; flex-direction: column; gap: 6px;
}
.comment-block { background: var(--soft); border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.comment-block.ai { border: 1px dashed var(--line); }
.comment-title { font-weight: 800; margin-bottom: 8px; }
.comment-block p { font-size: 13px; line-height: 1.8; color: #4d4d4d; }
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.criteria-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.criterion { background: var(--soft); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
.criterion-head { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.criterion-name { font-size: 16px; font-weight: 800; margin-bottom: 6px; }
.score-badge {
  min-width: 70px; height: 34px; display: flex; align-items: center; justify-content: center;
  background: var(--active); border-radius: 8px; font-weight: 800;
}
.suggestion { background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.suggestion-title { font-weight: 800; margin-bottom: 6px; }
.source-item { background: var(--soft); border: 1px dashed var(--line); border-radius: 12px; padding: 14px; margin-bottom: 10px; }
.source-item:last-child { margin-bottom: 0; }
.source-item strong { display: block; margin: 10px 0 6px; }
.source-item .el-button { margin-top: 8px; padding-left: 0; }
</style>
