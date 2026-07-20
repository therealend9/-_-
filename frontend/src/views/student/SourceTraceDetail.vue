<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">学生端 / 理论溯源 / 来源详情</span></div>

    <div class="page-header">
      <div>
        <h1>{{ source.title }}</h1>
        <p class="page-desc">{{ source.course }} · {{ source.chapter }} · {{ source.type }}</p>
      </div>
      <div class="header-actions">
        <el-button @click="router.back()">返回上一页</el-button>
        <el-button type="primary">加入复习材料</el-button>
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
              <strong>来源档案</strong>
              <div class="tag-row">
                <el-tag type="info">{{ source.indexStatus }}</el-tag>
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
              <span class="muted small">来源类型</span>
              <strong>{{ source.type }}</strong>
            </div>
            <div>
              <span class="muted small">更新时间</span>
              <strong>{{ source.updatedAt }}</strong>
            </div>
          </div>

          <el-divider />
          <div class="desc-block">
            <div class="block-title">来源说明</div>
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
              <strong>可回看证据摘录</strong>
              <el-tag type="success" size="small">{{ excerpts.length }} 段</el-tag>
            </div>
          </template>
          <div v-for="item in excerpts" :key="item.title" class="excerpt-item">
            <div class="excerpt-head">
              <strong>{{ item.title }}</strong>
              <el-tag size="small" type="info">{{ item.locator }}</el-tag>
            </div>
            <p>{{ item.content }}</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>引用链路</strong></template>
          <el-timeline>
            <el-timeline-item v-for="item in citationChain" :key="item.step" :timestamp="item.status">
              <div class="timeline-title">{{ item.step }} · {{ item.title }}</div>
              <div class="muted small">{{ item.desc }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>关联知识点</strong></template>
          <div v-for="item in knowledgePoints" :key="item.name" class="concept-item">
            <strong>{{ item.name }}</strong>
            <p>{{ item.desc }}</p>
            <span class="muted small">{{ item.source }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="15">
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
            <el-table-column prop="analysis" label="解析依据" min-width="240" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>使用记录</strong></template>
          <div v-for="item in usageRecords" :key="`${item.scene}-${item.target}`" class="usage-item">
            <div class="usage-head">
              <strong>{{ item.scene }}</strong>
              <el-tag size="small" type="success">{{ item.status }}</el-tag>
            </div>
            <p>{{ item.target }}</p>
            <span class="muted small">{{ item.time }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSourceTraceDetail } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const source = ref({})
const stats = ref([])
const excerpts = ref([])
const knowledgePoints = ref([])
const relatedQuestions = ref([])
const citationChain = ref([])
const usageRecords = ref([])

onMounted(() => runPageLoad(loading, async () => {
  const data = await getSourceTraceDetail(route.params.sourceId)
  source.value = data.source || {}
  stats.value = data.stats || []
  excerpts.value = data.excerpts || []
  knowledgePoints.value = data.knowledgePoints || []
  relatedQuestions.value = data.relatedQuestions || []
  citationChain.value = data.citationChain || []
  usageRecords.value = data.usageRecords || []
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
.desc-block {
  background: var(--soft); border-radius: 12px; padding: 14px; margin-bottom: 12px;
}
.desc-block.citation { border: 1px dashed var(--line); }
.block-title { font-weight: 800; margin-bottom: 8px; }
.desc-block p, .excerpt-item p, .concept-item p, .usage-item p {
  font-size: 13px; line-height: 1.75; color: #4d4d4d; margin: 0;
}
.excerpt-item { background: var(--soft); border: 1px solid var(--line); border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.excerpt-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 8px; }
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.concept-item { background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.concept-item p { margin: 6px 0; }
.usage-item { background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px; }
.usage-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.usage-item p { margin-bottom: 6px; }
</style>
