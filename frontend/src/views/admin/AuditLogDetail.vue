<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 运行治理 / 日志详情</span></div>

    <div class="page-header">
      <div>
        <h1>{{ log.action }} · {{ log.targetLabel }}</h1>
        <p class="page-desc">{{ log.time }} · {{ log.operator }} · {{ log.ip }}</p>
      </div>
      <div class="header-actions">
        <el-button :icon="ArrowLeft" @click="router.push('/admin/audit-log')">返回日志</el-button>
        <el-button :icon="DocumentCopy">复制追踪号</el-button>
        <el-button :icon="Download" type="primary">导出详情</el-button>
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
              <strong>操作摘要</strong>
              <div class="tag-row">
                <el-tag :type="log.actionType">{{ log.action }}</el-tag>
                <el-tag :type="log.resultType">{{ log.result }}</el-tag>
                <el-tag :type="log.riskType">{{ log.risk }}</el-tag>
              </div>
            </div>
          </template>
          <div class="summary-grid">
            <div>
              <span class="muted small">日志编号</span>
              <strong>#{{ log.id }}</strong>
            </div>
            <div>
              <span class="muted small">操作编码</span>
              <strong>{{ log.actionCode }}</strong>
            </div>
            <div>
              <span class="muted small">目标类型</span>
              <strong>{{ log.targetType }}</strong>
            </div>
            <div>
              <span class="muted small">目标 ID</span>
              <strong>{{ log.targetId }}</strong>
            </div>
          </div>
          <p class="detail-text">{{ log.detail }}</p>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>字段变化</strong>
              <el-tag type="info" size="small">{{ changes.length }} 项</el-tag>
            </div>
          </template>
          <el-table :data="changes" style="width: 100%">
            <el-table-column prop="field" label="字段" width="160" />
            <el-table-column prop="before" label="变更前" min-width="160" />
            <el-table-column prop="after" label="变更后" min-width="160" />
            <el-table-column prop="desc" label="说明" min-width="240" />
          </el-table>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>原始上下文</strong>
              <el-tag type="info" size="small">{{ request.traceId }}</el-tag>
            </div>
          </template>
          <pre class="raw-json">{{ formattedRawContext }}</pre>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>操作主体</strong></template>
          <div class="actor-card">
            <div class="avatar">{{ actor.name?.slice(0, 1) || '系' }}</div>
            <div>
              <strong>{{ actor.name }}</strong>
              <div class="muted small">{{ actor.account }} · {{ actor.role }}</div>
            </div>
          </div>
          <div class="actor-scope">
            <span class="muted small">数据范围</span>
            <strong>{{ actor.dataScope }}</strong>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>请求上下文</strong></template>
          <div class="request-list">
            <div v-for="item in requestItems" :key="item.label">
              <span class="muted small">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>处理时间线</strong></template>
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
          <template #header><strong>关联记录</strong></template>
          <el-table :data="relatedRecords" style="width: 100%">
            <el-table-column prop="type" label="类型" width="130" />
            <el-table-column prop="id" label="ID" width="90" />
            <el-table-column prop="title" label="说明" min-width="260" />
            <el-table-column prop="status" label="状态" width="100" align="center" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>合规检查</strong></template>
          <div v-for="item in complianceChecks" :key="item.name" class="check-item">
            <div class="check-head">
              <strong>{{ item.name }}</strong>
              <el-tag size="small" :type="item.type">{{ item.result }}</el-tag>
            </div>
            <p>{{ item.desc }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, DocumentCopy, Download } from '@element-plus/icons-vue'
import { getAuditLogDetail } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const log = ref({})
const stats = ref([])
const actor = ref({})
const request = ref({})
const changes = ref([])
const relatedRecords = ref([])
const timeline = ref([])
const complianceChecks = ref([])
const rawContext = ref({})

const requestItems = computed(() => [
  { label: '请求方法', value: request.value.method || '-' },
  { label: '请求路径', value: request.value.route || '-' },
  { label: '来源 IP', value: request.value.ip || '-' },
  { label: '会话 ID', value: request.value.sessionId || '-' },
  { label: '追踪号', value: request.value.traceId || '-' },
  { label: '客户端', value: request.value.userAgent || '-' }
])

const formattedRawContext = computed(() => JSON.stringify(rawContext.value, null, 2))

onMounted(() => runPageLoad(loading, async () => {
  const data = await getAuditLogDetail(route.params.logId)
  log.value = data.log || {}
  stats.value = data.stats || []
  actor.value = data.actor || {}
  request.value = data.request || {}
  changes.value = data.changes || []
  relatedRecords.value = data.relatedRecords || []
  timeline.value = data.timeline || []
  complianceChecks.value = data.complianceChecks || []
  rawContext.value = data.rawContext || {}
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
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.summary-grid div, .request-list div, .actor-scope {
  background: var(--soft); border-radius: 10px; padding: 12px;
  display: flex; flex-direction: column; gap: 6px;
}
.detail-text { margin-top: 14px; font-size: 13px; color: #4d4d4d; line-height: 1.8; }
.raw-json {
  margin: 0; background: #2f2f2f; color: #f7f6f2; border-radius: 10px; padding: 14px;
  font-size: 12px; line-height: 1.7; overflow: auto;
}
.actor-card { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.avatar {
  width: 44px; height: 44px; border-radius: 12px; background: var(--active);
  display: flex; align-items: center; justify-content: center; font-weight: 800;
}
.request-list { display: grid; grid-template-columns: 1fr; gap: 10px; }
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.check-item { background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.check-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.check-item p { margin: 0; font-size: 13px; line-height: 1.7; color: #4d4d4d; }
</style>
