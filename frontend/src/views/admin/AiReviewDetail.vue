<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / AI内容管理 / 审核详情</span></div>

    <div class="page-header">
      <div>
        <h1>{{ review.title }}</h1>
        <p class="page-desc">
          {{ target.course }} · {{ target.chapter }} · {{ review.type }}
        </p>
      </div>
      <div class="header-actions">
        <el-button @click="router.push('/admin/ai-review')">返回审核列表</el-button>
        <el-button type="success" :loading="deciding === 'approve'" :disabled="Boolean(deciding)" @click="handleDecision('approve')">通过</el-button>
        <el-button type="warning" :loading="deciding === 'revision'" :disabled="Boolean(deciding)" @click="handleDecision('revision')">要求修改</el-button>
        <el-button type="danger" :loading="deciding === 'reject'" :disabled="Boolean(deciding)" @click="handleDecision('reject')">拒绝</el-button>
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
              <strong>审核对象</strong>
              <div class="tag-row">
                <el-tag :type="review.riskType">{{ review.risk }}</el-tag>
                <el-tag :type="review.statusType">{{ review.status }}</el-tag>
              </div>
            </div>
          </template>

          <div class="target-meta">
            <div>
              <span class="muted small">内容类型</span>
              <strong>{{ target.type }}</strong>
            </div>
            <div>
              <span class="muted small">负责人</span>
              <strong>{{ target.owner }}</strong>
            </div>
            <div>
              <span class="muted small">版本</span>
              <strong>{{ target.version }}</strong>
            </div>
            <div>
              <span class="muted small">更新时间</span>
              <strong>{{ target.updatedAt || review.createdAt }}</strong>
            </div>
          </div>

          <el-divider />
          <div class="preview-block">
            <div class="block-title">内容预览</div>
            <p>{{ review.contentPreview }}</p>
          </div>
          <div v-for="section in target.sections" :key="section.title" class="content-section">
            <div class="block-title">{{ section.title }}</div>
            <p>{{ section.content }}</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>审核流程</strong></template>
          <div class="decision-panel">
            <span>建议处理</span>
            <strong>{{ decision.recommendedAction }}</strong>
            <em>审核人：{{ decision.reviewer }}</em>
          </div>
          <div class="comment-block">
            <div class="block-title">审核意见</div>
            <p>{{ decision.comment }}</p>
          </div>
          <el-timeline>
            <el-timeline-item v-for="item in timeline" :key="item.title" :timestamp="item.time">
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
              <strong>风险项检查</strong>
              <el-tag type="info" size="small">{{ riskItems.length }} 项</el-tag>
            </div>
          </template>
          <div v-for="item in riskItems" :key="item.title" class="risk-item">
            <div class="risk-head">
              <div>
                <strong>{{ item.title }}</strong>
                <div class="muted small">证据：{{ item.evidence }}</div>
              </div>
              <el-tag :type="item.type" size="small">{{ item.level }}风险</el-tag>
            </div>
            <p>{{ item.suggestion }}</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>来源依据</strong></template>
          <div v-if="target.sources.length" class="source-grid">
            <div v-for="source in target.sources" :key="source.title" class="source-item">
              <el-tag size="small">{{ source.type }}</el-tag>
              <strong>{{ source.title }}</strong>
              <span class="muted small">{{ source.status }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无来源依据" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header><strong>处理动作说明</strong></template>
          <div class="action-grid">
            <div v-for="item in decision.actions" :key="item.label" class="action-item">
              <el-tag :type="item.type">{{ item.label }}</el-tag>
              <p>{{ item.desc }}</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>审核日志</strong></template>
          <div v-if="auditLogs.length">
            <div v-for="item in auditLogs" :key="`${item.action}-${item.time}`" class="log-item">
              <strong>{{ item.action }}</strong>
              <span class="muted small">{{ item.operator }} · {{ item.time }}</span>
              <p>{{ item.detail }}</p>
            </div>
          </div>
          <el-empty v-else description="暂无审核日志" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { decideAiReview, getAiReviewDetail } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const deciding = ref('')
const review = ref({})
const target = ref({ sections: [], sources: [] })
const stats = ref([])
const riskItems = ref([])
const decision = ref({ actions: [] })
const timeline = ref([])
const auditLogs = ref([])

function applyDetailData(data) {
  review.value = data.review || {}
  target.value = data.target || target.value
  stats.value = data.stats || []
  riskItems.value = data.riskItems || []
  decision.value = data.decision || decision.value
  timeline.value = data.timeline || []
  auditLogs.value = data.auditLogs || []
}

async function loadDetail() {
  const data = await getAiReviewDetail(route.params.reviewId)
  applyDetailData(data)
}

async function handleDecision(action) {
  if (deciding.value) return

  deciding.value = action
  try {
    const data = await decideAiReview(route.params.reviewId, action)
    applyDetailData(data)
    ElMessage.success(data.message || '审核状态已更新')
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '审核操作失败')
  } finally {
    deciding.value = ''
  }
}

onMounted(() => runPageLoad(loading, loadDetail))
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
.target-meta {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px;
}
.target-meta div {
  background: var(--soft); border-radius: 10px; padding: 14px;
  display: flex; flex-direction: column; gap: 6px;
}
.preview-block, .content-section, .comment-block {
  background: var(--soft); border-radius: 12px; padding: 14px; margin-bottom: 12px;
}
.content-section { border: 1px solid var(--line); background: #fff; }
.block-title { font-weight: 800; margin-bottom: 8px; }
.preview-block p, .content-section p, .comment-block p {
  font-size: 13px; line-height: 1.85; color: #4d4d4d; margin: 0;
}
.decision-panel {
  background: var(--active); border-radius: 14px; padding: 18px; margin-bottom: 14px;
  display: flex; flex-direction: column; gap: 4px;
}
.decision-panel strong { font-size: 28px; line-height: 1.2; }
.decision-panel em { font-style: normal; color: var(--muted); font-size: 12px; }
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.risk-item { background: var(--soft); border: 1px solid var(--line); border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.risk-head { display: flex; justify-content: space-between; gap: 14px; align-items: flex-start; }
.risk-item p { margin: 10px 0 0; font-size: 13px; line-height: 1.7; color: #4d4d4d; }
.source-grid { display: grid; grid-template-columns: 1fr; gap: 10px; }
.source-item {
  background: var(--soft); border: 1px dashed var(--line); border-radius: 10px; padding: 12px;
  display: flex; flex-direction: column; gap: 8px;
}
.action-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.action-item { background: var(--soft); border-radius: 10px; padding: 12px; }
.action-item p { margin: 10px 0 0; font-size: 13px; line-height: 1.7; color: #4d4d4d; }
.log-item { background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px; display: flex; flex-direction: column; gap: 6px; }
.log-item p { margin: 0; font-size: 13px; line-height: 1.6; color: #4d4d4d; }
</style>
