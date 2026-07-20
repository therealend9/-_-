<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / AI内容管理 / 审核治理</span></div>
    <div class="page-header">
      <h1>AI内容审核</h1>
      <div class="header-actions">
        <el-button>批量通过</el-button>
        <el-button type="primary">开始审核</el-button>
      </div>
    </div>
    <p class="page-desc">对AI生成的教案、导学、案例、题目等内容进行安全审核与治理</p>

    <!-- 审核统计 -->
    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <div class="stat-card">
          <div class="muted small">{{ stat.label }}</div>
          <div class="stat-num" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="muted small">{{ stat.desc }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 审核表格 -->
    <el-card shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <strong>AI内容审核列表</strong>
          <div style="display: flex; gap: 10px">
            <el-input placeholder="搜索内容标题或来源" style="width: 240px" size="small" />
            <el-select placeholder="内容类型" size="small" style="width: 140px">
              <el-option label="全部" value="all" />
              <el-option label="教案" value="plan" />
              <el-option label="导学" value="guide" />
              <el-option label="案例" value="case" />
              <el-option label="题目" value="question" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="reviewList" style="width: 100%">
        <el-table-column prop="title" label="内容标题" min-width="220" />
        <el-table-column prop="type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" min-width="180" />
        <el-table-column prop="author" label="生成者" width="120" align="center" />
        <el-table-column prop="time" label="生成时间" width="140" align="center" />
        <el-table-column label="审核状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.statusType">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.riskType">{{ row.risk }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="router.push(`/admin/ai-review/${row.id || 1}`)">查看详情</el-button>
            <el-button size="small" type="success" :loading="decidingId === `${row.id}-approve`" :disabled="Boolean(decidingId)" @click="handleDecision(row, 'approve')">通过</el-button>
            <el-button size="small" type="warning" :loading="decidingId === `${row.id}-revision`" :disabled="Boolean(decidingId)" @click="handleDecision(row, 'revision')">修改</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { decideAiReview, getAiReviewList } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const decidingId = ref('')
const stats = ref([])
const reviewList = ref([])

async function loadReviews() {
  const data = await getAiReviewList()
  stats.value = data.stats || []
  reviewList.value = data.reviewList || []
}

async function handleDecision(row, action) {
  if (decidingId.value) return

  decidingId.value = `${row.id}-${action}`
  try {
    const data = await decideAiReview(row.id, action)
    ElMessage.success(data.message || '审核状态已更新')
    await loadReviews()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '审核操作失败')
  } finally {
    decidingId.value = ''
  }
}

onMounted(() => runPageLoad(loading, loadReviews))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 32px; font-weight: 800; margin: 4px 0; }
</style>

