<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 课后评价 / 评分量规</span></div>
    <div class="page-header">
      <div>
        <h1>评分量规管理</h1>
        <p class="page-desc">为 AI 批改建议和教师复核提供统一评分依据</p>
      </div>
      <div class="header-actions">
        <el-select v-model="courseFilter" clearable placeholder="按课程筛选" style="width: 180px">
          <el-option v-for="course in courses" :key="course" :label="course" :value="course" />
        </el-select>
        <el-button>导出量规</el-button>
        <el-button type="primary" @click="dialogVisible = true">新增量规</el-button>
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
              <strong>量规列表</strong>
              <el-input v-model="keyword" placeholder="搜索量规名称" style="width: 220px" size="small" />
            </div>
          </template>

          <el-table :data="filteredRubrics" style="width: 100%">
            <el-table-column prop="title" label="量规名称" min-width="210" />
            <el-table-column prop="scenario" label="适用场景" width="140" />
            <el-table-column prop="itemCount" label="维度" width="70" align="center" />
            <el-table-column prop="totalScore" label="总分" width="70" align="center" />
            <el-table-column prop="totalWeight" label="权重" width="90" align="center">
              <template #default="{ row }">
                <span :class="row.totalWeight === 100 ? 'good' : 'warn'">{{ row.totalWeight }}%</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.statusType">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="updatedAt" label="更新时间" width="150" align="center" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card active-card">
          <template #header>
            <div class="section-header">
              <strong>当前启用量规</strong>
              <el-tag v-if="activeRubric" size="small" :type="activeRubric.statusType">{{ activeRubric.status }}</el-tag>
            </div>
          </template>

          <template v-if="activeRubric">
            <div class="rubric-title">{{ activeRubric.title }}</div>
            <div class="rubric-meta">
              <span>{{ activeRubric.course }}</span>
              <span>{{ activeRubric.scenario }}</span>
              <span>{{ activeRubric.owner }}</span>
            </div>
            <p class="rubric-desc">{{ activeRubric.description }}</p>
            <div class="weight-row">
              <span>权重合计</span>
              <el-progress :percentage="activeWeight" :stroke-width="10" :show-text="false" />
              <strong :class="activeWeight === 100 ? 'good' : 'warn'">{{ activeWeight }}%</strong>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="activeRubric" shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <strong>评分维度与等级说明</strong>
          <el-tag type="info" size="small">{{ activeRubric.totalScore }} 分制</el-tag>
        </div>
      </template>

      <div class="criteria-grid">
        <div v-for="item in activeRubric.items" :key="item.id" class="criterion">
          <div class="criterion-head">
            <div>
              <div class="criterion-name">{{ item.name }}</div>
              <div class="muted small">{{ item.evidence }}</div>
            </div>
            <div class="weight-badge">{{ item.weight }}%</div>
          </div>

          <el-table :data="item.levels" size="small" style="width: 100%; margin-top: 12px">
            <el-table-column prop="level" label="等级" width="80" />
            <el-table-column prop="score" label="建议分" width="80" align="center" />
            <el-table-column prop="desc" label="判定说明" min-width="220" />
          </el-table>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新增评分量规" width="520px">
      <el-form label-width="96px">
        <el-form-item label="量规名称">
          <el-input v-model="draftForm.title" placeholder="如：材料分析题评分量规" />
        </el-form-item>
        <el-form-item label="适用课程">
          <el-select v-model="draftForm.course" placeholder="选择课程" style="width: 100%">
            <el-option v-for="course in courses" :key="course" :label="course" :value="course" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用场景">
          <el-input v-model="draftForm.scenario" placeholder="如：课后材料分析作业" />
        </el-form-item>
        <el-form-item label="总分">
          <el-input-number v-model="draftForm.totalScore" :min="10" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveDraftRubric">保存草稿</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { createRubric, getRubrics } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const loading = ref(true)
const keyword = ref('')
const courseFilter = ref('')
const dialogVisible = ref(false)
const stats = ref([])
const rubricList = ref([])
const activeRubric = ref(null)
const saving = ref(false)
const draftForm = reactive({
  title: '',
  course: '马克思主义基本原理',
  scenario: '',
  totalScore: 100
})

const courses = computed(() => {
  const values = rubricList.value.map((item) => item.course).filter(Boolean)
  return [...new Set(['马克思主义基本原理', ...values])]
})

const filteredRubrics = computed(() => rubricList.value.filter((item) => {
  const matchesCourse = !courseFilter.value || item.course === courseFilter.value
  const matchesKeyword = !keyword.value || item.title.includes(keyword.value)
  return matchesCourse && matchesKeyword
}))

const activeWeight = computed(() => activeRubric.value?.items?.reduce((sum, item) => sum + Number(item.weight || 0), 0) || 0)

async function saveDraftRubric() {
  if (!draftForm.title || !draftForm.scenario) {
    ElMessage.warning('请补全量规名称和适用场景')
    return
  }
  if (saving.value) return

  saving.value = true
  try {
    const data = await createRubric({
      title: draftForm.title,
      course: draftForm.course,
      scenario: draftForm.scenario,
      totalScore: draftForm.totalScore
    })
    stats.value = data.stats || []
    rubricList.value = data.rubricList || []
    activeRubric.value = data.activeRubric || null
    dialogVisible.value = false
    draftForm.title = ''
    draftForm.scenario = ''
    draftForm.totalScore = 100
    ElMessage.success(data.message || '量规草稿已保存')
  } catch (error) {
    ElMessage.error(error.message || '量规草稿保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getRubrics()
  stats.value = data.stats || []
  rubricList.value = data.rubricList || []
  activeRubric.value = data.activeRubric || null
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
.active-card { min-height: 252px; }
.rubric-title { font-size: 18px; font-weight: 800; line-height: 1.4; }
.rubric-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; color: var(--muted); font-size: 12px; }
.rubric-meta span { padding: 4px 8px; background: var(--soft); border-radius: 8px; }
.rubric-desc { margin-top: 14px; font-size: 13px; line-height: 1.8; color: #4d4d4d; }
.weight-row { display: grid; grid-template-columns: 70px 1fr 48px; align-items: center; gap: 10px; margin-top: 18px; font-size: 13px; }
.criteria-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.criterion { background: var(--soft); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
.criterion-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; }
.criterion-name { font-size: 16px; font-weight: 800; margin-bottom: 6px; }
.weight-badge {
  min-width: 54px; height: 32px; display: flex; align-items: center; justify-content: center;
  border-radius: 8px; background: var(--active); font-weight: 800;
}
.good { color: #67C23A; font-weight: 800; }
.warn { color: #F56C6C; font-weight: 800; }
</style>
