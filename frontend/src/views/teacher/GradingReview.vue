<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">教师端 / 课后 / 作业批改复核</span></div>
    <div class="page-header">
      <h1>AI 辅助批改工作台</h1>
      <div class="header-actions">
        <el-button :loading="ocrRunning" @click="runOcr">📷 OCR 识别</el-button>
        <el-button type="warning" :loading="aiGrading" @click="runAiGrade">🤖 AI 批改</el-button>
        <el-button type="danger" :loading="confirming === 'return'" :disabled="Boolean(confirming)" @click="handleConfirm('return')">退回重批</el-button>
        <el-button type="primary" :loading="confirming === 'publish'" :disabled="Boolean(confirming)" @click="handleConfirm('publish')">确认发布</el-button>
      </div>
    </div>
    <p class="page-desc">OCR 识别手写作答 → AI 按评分量规逐项打分 → 教师复核确认后发布反馈</p>

    <!-- 三栏复核 -->
    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :span="8">
        <el-card shadow="never" class="card" style="min-height: 400px">
          <template #header><strong>📄 原始答卷 / OCR 文本</strong></template>
          <div v-if="ocrResult" class="ocr-box">
            <div class="ocr-meta">
              <el-tag size="small" type="success">置信度 {{ ocrResult.confidence }}%</el-tag>
              <span class="muted" style="font-size: 12px">关键词：{{ (ocrResult.keywords || []).join('、') }}</span>
            </div>
            <div class="ocr-text">{{ ocrResult.text }}</div>
          </div>
          <div v-else class="empty-hint">
            <p class="muted">点击"OCR 识别"模拟识别手写作答</p>
            <el-button @click="runOcr" style="margin-top: 10px">开始识别</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="card" style="min-height: 400px">
          <template #header><strong>🤖 AI 批改建议</strong></template>
          <div v-if="!aiResult" class="empty-hint">
            <p class="muted">点击"AI 批改"生成评分建议</p>
            <el-button type="warning" @click="runAiGrade" style="margin-top: 10px">开始批改</el-button>
          </div>
          <div v-else>
            <div style="text-align: center; margin-bottom: 16px">
              <el-progress type="dashboard" :percentage="aiResult.confidence" :width="80" :color="aiResult.totalScore >= 80 ? '#67C23A' : '#E6A23C'">
                <template #default><span style="font-size: 18px; font-weight: 800">{{ aiResult.totalScore }}</span></template>
              </el-progress>
              <div style="font-weight: 700; margin-top: 4px">AI 建议分：{{ aiResult.totalScore }} 分</div>
              <div class="muted" style="font-size: 11px">置信度 {{ aiResult.confidence }}%</div>
            </div>
            <div v-for="item in aiResult.rubricItems" :key="item.id" class="rubric-row">
              <div style="display: flex; justify-content: space-between; align-items: center">
                <span style="font-size: 13px; font-weight: 600">{{ item.name }}（权重 {{ item.weight }}%）</span>
                <el-tag :type="item.aiScore >= 85 ? 'success' : item.aiScore >= 60 ? 'warning' : 'danger'" size="small">{{ item.level }} · {{ item.aiScore }}</el-tag>
              </div>
              <div class="muted" style="font-size: 11px; margin-top: 2px">{{ item.comment }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="card" style="min-height: 400px">
          <template #header><strong>⚠️ 风险标记与建议</strong></template>
          <div v-if="!aiResult" class="empty-hint">
            <p class="muted">AI 批改后将展示风险标记</p>
          </div>
          <div v-else>
            <div v-if="!aiResult.riskFlags?.length" style="text-align: center; padding: 20px">
              <span style="color: #67C23A; font-size: 14px">✅ 未发现明显风险</span>
            </div>
            <div v-for="(flag, i) in aiResult.riskFlags" :key="i" class="flag-item" :class="flag.type">
              <el-tag :type="flag.type === 'warning' ? 'danger' : 'info'" size="small">{{ flag.title }}</el-tag>
              <div class="muted" style="font-size: 12px; margin-top: 4px">{{ flag.suggestion }}</div>
            </div>

            <el-divider style="margin: 12px 0" />

            <strong style="font-size: 13px">💡 改进建议</strong>
            <div v-for="(s, i) in aiResult.suggestions" :key="i" class="suggest-item">· {{ s }}</div>

            <div class="meta-row" style="margin-top: 12px">
              <span class="muted">字数：{{ aiResult.wordCount }}</span>
              <el-tag size="small" :type="aiResult.hasConcept ? 'success' : 'info'">概念{{ aiResult.hasConcept ? '✓' : '?' }}</el-tag>
              <el-tag size="small" :type="aiResult.hasCaseAnalysis ? 'success' : 'info'">案例{{ aiResult.hasCaseAnalysis ? '✓' : '?' }}</el-tag>
              <el-tag size="small" :type="aiResult.hasStructure ? 'success' : 'info'">结构{{ aiResult.hasStructure ? '✓' : '?' }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 复核队列 + 流程 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="never" class="card">
          <template #header><strong>复核队列</strong></template>
          <div v-for="(q, i) in reviewQueue" :key="i" class="queue-item">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <strong style="font-size: 14px">{{ q.name }}</strong>
              <el-tag size="small" :type="q.type">{{ q.tag }}</el-tag>
            </div>
            <div class="muted" style="font-size: 12px; margin-top: 2px">{{ q.desc }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="card">
          <template #header><strong>复核流程</strong></template>
          <el-steps :active="activeStep" align-center>
            <el-step title="定位" description="查看答题区域" />
            <el-step title="识别" description="OCR 文本提取" />
            <el-step title="批改" description="AI 分项评分" />
            <el-step title="发布" description="生成学生反馈" />
          </el-steps>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { confirmGradingReview, getGradingReview, aiGradeSubmission, ocrRecognize } from '../../api/teacher.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const loading = ref(true)
const confirming = ref('')
const ocrRunning = ref(false)
const aiGrading = ref(false)
const reviewQueue = ref([])
const activeStep = ref(1)
const reviewState = ref({ label: '待教师复核', type: 'warning', desc: '', updatedAt: '' })
const ocrResult = ref(null)
const aiResult = ref(null)

async function loadData() {
  await runPageLoad(loading, async () => {
    const data = await getGradingReview()
    reviewQueue.value = data.reviewQueue || []
    activeStep.value = data.activeStep || 1
    reviewState.value = data.reviewState || reviewState.value
  })
}

async function runOcr() {
  if (ocrRunning.value) return
  ocrRunning.value = true
  try {
    ocrResult.value = await ocrRecognize(null)
    activeStep.value = Math.max(activeStep.value, 2)
    ElMessage.success('OCR 识别完成')
  } catch (e) { ElMessage.error(e?.message || 'OCR 识别失败') }
  finally { ocrRunning.value = false }
}

async function runAiGrade() {
  if (aiGrading.value) return
  aiGrading.value = true
  try {
    const answerText = ocrResult.value?.text || '在社区调研前，我对基层治理的理解主要来自教材和新闻材料。进入社区访谈后，我发现居民参与、问题反馈和实际执行之间存在复杂联系。通过整理访谈记录和对照教材，我认识到实践不仅提供认识材料，也会检验并修正原有判断，使认识从感性材料上升到更系统的理性理解。'
    aiResult.value = await aiGradeSubmission(1, answerText, null)
    activeStep.value = Math.max(activeStep.value, 3)
    ElMessage.success(`AI 批改完成，建议分 ${aiResult.value.totalScore} 分`)
  } catch (e) { ElMessage.error(e?.message || 'AI 批改失败') }
  finally { aiGrading.value = false }
}

async function handleConfirm(action) {
  if (confirming.value) return
  confirming.value = action
  try {
    const result = await confirmGradingReview(action)
    reviewState.value = result.reviewState || reviewState.value
    activeStep.value = result.activeStep || (action === 'return' ? 2 : 4)
    ElMessage.success(result.message)
  } catch (e) { ElMessage.error(e?.message || '操作失败') }
  finally { confirming.value = '' }
}

onMounted(loadData)
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }

.ocr-box { padding: 4px 0; }
.ocr-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.ocr-text { font-size: 13px; line-height: 1.8; padding: 12px; background: var(--soft); border-radius: 8px; border: 1px dashed var(--line); }

.empty-hint { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 20px; text-align: center; }

.rubric-row { padding: 10px 0; border-bottom: 1px dashed var(--line); }
.rubric-row:last-child { border-bottom: none; }

.flag-item { padding: 8px 12px; border-radius: 8px; margin-bottom: 8px; background: var(--soft); }
.flag-item.warning { border-left: 3px solid #F56C6C; }

.suggest-item { font-size: 12px; color: var(--muted); padding: 4px 0; }

.meta-row { display: flex; gap: 8px; align-items: center; }

.queue-item { padding: 10px 0; }
.queue-item:not(:last-child) { border-bottom: 1px dashed var(--line); }
</style>
