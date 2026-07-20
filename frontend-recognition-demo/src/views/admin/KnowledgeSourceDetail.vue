<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 知识库管理 / 资源详情</span></div>

    <div class="page-header">
      <div>
        <h1>{{ source.title }}</h1>
        <p class="page-desc">{{ source.course }} · {{ source.chapter }} · {{ source.type }}</p>
      </div>
      <div class="header-actions">
        <el-button @click="router.push('/admin/knowledge-base')">返回知识库</el-button>
        <el-button :loading="acting === 'reindex'" :disabled="Boolean(acting)" @click="handleReindex">重新索引</el-button>
        <el-button type="success" :loading="acting === 'approve'" :disabled="Boolean(acting)" @click="handleAudit('approve')">审核通过</el-button>
        <el-button type="warning" :loading="acting === 'reject'" :disabled="Boolean(acting)" @click="handleAudit('reject')">退回</el-button>
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
              <strong>资源档案</strong>
              <div class="tag-row">
                <el-tag :type="source.indexType">{{ source.indexStatus }}</el-tag>
                <el-tag :type="source.auditType">{{ source.auditStatus }}</el-tag>
              </div>
            </div>
          </template>

          <div class="source-meta">
            <div>
              <span class="muted small">课程</span>
              <strong>{{ source.course }}</strong>
            </div>
            <div>
              <span class="muted small">章节</span>
              <strong>{{ source.chapter }}</strong>
            </div>
            <div>
              <span class="muted small">资源类型</span>
              <strong>{{ source.type }}</strong>
            </div>
            <div>
              <span class="muted small">更新时间</span>
              <strong>{{ source.updatedAt }}</strong>
            </div>
          </div>

          <el-divider />
          <div class="desc-block">
            <div class="block-title">资源说明</div>
            <p>{{ source.description }}</p>
          </div>
          <div class="desc-block citation">
            <div class="block-title">引用信息</div>
            <p>{{ source.citation }}</p>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>索引切片</strong>
              <el-tag type="info" size="small">{{ chunks.length }} 个文本块</el-tag>
            </div>
          </template>
          <el-table :data="chunks" style="width: 100%">
            <el-table-column prop="title" label="切片标题" width="150" />
            <el-table-column prop="locator" label="定位" width="160" />
            <el-table-column prop="content" label="内容摘要" min-width="260" />
            <el-table-column prop="tokenCount" label="Token" width="90" align="center" />
            <el-table-column prop="embeddingStatus" label="向量状态" width="110" align="center" />
            <el-table-column label="质量" width="80" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.quality === '高' ? 'success' : 'warning'">{{ row.quality }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>索引流程</strong></template>
          <el-timeline>
            <el-timeline-item v-for="item in indexJobs" :key="item.step" :timestamp="item.time">
              <div class="timeline-title">
                {{ item.step }}
                <el-tag size="small" :type="item.statusType">{{ item.status }}</el-tag>
              </div>
              <div class="muted small">{{ item.desc }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>质量检查</strong></template>
          <div v-for="item in qualityChecks" :key="item.name" class="quality-item">
            <div class="quality-head">
              <strong>{{ item.name }}</strong>
              <el-tag size="small" :type="item.type">{{ item.result }}</el-tag>
            </div>
            <p>{{ item.desc }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>关联题目</strong>
              <el-tag type="info" size="small">{{ relatedQuestions.length }} 道</el-tag>
            </div>
          </template>
          <el-table :data="relatedQuestions" style="width: 100%">
            <el-table-column prop="knowledgePoint" label="知识点" width="130" />
            <el-table-column prop="type" label="题型" width="100" align="center" />
            <el-table-column prop="stem" label="题目" min-width="260" />
            <el-table-column prop="auditStatus" label="审核" width="100" align="center" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>AI 审核记录</strong></template>
          <div v-if="aiReviews.length">
            <div v-for="item in aiReviews" :key="item.id" class="review-item">
              <div class="review-head">
                <strong>{{ item.title }}</strong>
                <el-tag size="small" :type="item.statusType">{{ item.status }}</el-tag>
              </div>
              <div class="muted small">{{ item.risk }} · {{ item.time }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无审核记录" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header><strong>引用使用情况</strong></template>
          <div class="usage-grid">
            <div v-for="item in usageRecords" :key="`${item.scene}-${item.target}`" class="usage-item">
              <div class="usage-head">
                <strong>{{ item.scene }}</strong>
                <el-tag size="small" type="success">{{ item.status }}</el-tag>
              </div>
              <p>{{ item.target }}</p>
              <span class="muted small">{{ item.time }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>治理日志</strong></template>
          <div v-if="auditLogs.length">
            <div v-for="item in auditLogs" :key="`${item.action}-${item.time}`" class="log-item">
              <strong>{{ item.action }}</strong>
              <span class="muted small">{{ item.operator }} · {{ item.time }}</span>
              <p>{{ item.detail }}</p>
            </div>
          </div>
          <el-empty v-else description="暂无治理日志" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { auditKnowledgeSource, getKnowledgeSourceDetail, reindexKnowledgeSource } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const acting = ref('')
const source = ref({})
const stats = ref([])
const chunks = ref([])
const indexJobs = ref([])
const relatedQuestions = ref([])
const aiReviews = ref([])
const usageRecords = ref([])
const auditLogs = ref([])
const qualityChecks = ref([])

function applyDetailData(data) {
  source.value = data.source || {}
  stats.value = data.stats || []
  chunks.value = data.chunks || []
  indexJobs.value = data.indexJobs || []
  relatedQuestions.value = data.relatedQuestions || []
  aiReviews.value = data.aiReviews || []
  usageRecords.value = data.usageRecords || []
  auditLogs.value = data.auditLogs || []
  qualityChecks.value = data.qualityChecks || []
}

async function loadDetail() {
  const data = await getKnowledgeSourceDetail(route.params.sourceId)
  applyDetailData(data)
}

async function handleReindex() {
  if (acting.value) return

  acting.value = 'reindex'
  try {
    const data = await reindexKnowledgeSource(route.params.sourceId)
    applyDetailData(data)
    ElMessage.success(data.message || '知识来源已重新索引')
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '重新索引失败')
  } finally {
    acting.value = ''
  }
}

async function handleAudit(action) {
  if (acting.value) return

  acting.value = action
  try {
    const data = await auditKnowledgeSource(route.params.sourceId, action)
    applyDetailData(data)
    ElMessage.success(data.message || '知识来源审核状态已更新')
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '审核知识来源失败')
  } finally {
    acting.value = ''
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
.header-actions { display: flex; gap: 10px; align-items: center; }
.section-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.tag-row { display: flex; gap: 8px; align-items: center; }
.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.source-meta { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.source-meta div {
  background: var(--soft); border-radius: 10px; padding: 14px;
  display: flex; flex-direction: column; gap: 6px;
}
.desc-block { background: var(--soft); border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.desc-block.citation { border: 1px dashed var(--line); }
.block-title { font-weight: 800; margin-bottom: 8px; }
.desc-block p, .quality-item p, .usage-item p, .log-item p {
  font-size: 13px; line-height: 1.75; color: #4d4d4d; margin: 0;
}
.timeline-title { display: flex; justify-content: space-between; align-items: center; gap: 10px; font-weight: 800; margin-bottom: 4px; }
.quality-item, .review-item, .usage-item, .log-item {
  background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px;
}
.quality-head, .review-head, .usage-head {
  display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px;
}
.usage-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.log-item { display: flex; flex-direction: column; gap: 6px; }
</style>
