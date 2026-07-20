<template>
  <div>
    <div class="breadcrumb"><span class="muted">教师端 / 随堂微测</span></div>
    <div class="page-header">
      <h1>随堂微测</h1>
      <div class="header-actions">
        <el-button @click="showAddDialog = true">+ 从题库添加</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">AI 生成新题</el-button>
        <el-button type="success" :loading="publishing" @click="handlePublish" :disabled="!selectedIds.size">
          推送选中 ({{ selectedIds.size }})
        </el-button>
      </div>
    </div>
    <p class="page-desc">勾选题目 → 推送给学生。学生提交后可实时查看结果统计</p>

    <el-row :gutter="20" style="margin-top: 16px">
      <el-col :span="16">
        <el-card shadow="never" class="card">
          <template #header>
            <div class="card-row">
              <div class="card-row-left">
                <strong>题目列表（已选 {{ selectedIds.size }}/{{ questions.length }}）</strong>
                <el-button size="small" text @click="selectAll">全选</el-button>
                <el-button size="small" text @click="deselectAll">取消全选</el-button>
              </div>
              <el-radio-group v-model="filter" size="small">
                <el-radio-button value="all">全部</el-radio-button>
                <el-radio-button value="single">单选</el-radio-button>
                <el-radio-button value="multi">多选</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div v-for="(q, i) in visibleQuestions" :key="q.id||i" class="q-card" :class="{ selected: selectedIds.has(q.id) }">
            <div class="qc-top">
              <el-checkbox :model-value="selectedIds.has(q.id)" @change="toggleSelect(q.id)" />
              <el-tag size="small" :type="q.type==='单选'?'primary':q.type==='多选'?'warning':'info'">{{ q.type }}</el-tag>
              <strong class="qc-stem">{{ i + 1 }}. {{ q.stem }}</strong>
            </div>
            <div class="qc-options">
              <span v-for="opt in q.options" :key="opt.key">{{ opt.key }}. {{ opt.text }}</span>
            </div>
            <div class="qc-meta">
              <el-tag size="small" type="success">答案: {{ q.answer }}</el-tag>
              <span class="muted">来源: {{ q.source }}</span>
              <el-button size="small" @click="openEdit(q)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeQuestion(i)">移除</el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="card">
          <template #header><strong>生成配置</strong></template>
          <div class="cfg-row">
            <span class="cfg-label">章节</span>
            <el-select v-model="chapter" size="small" style="width:100%">
              <el-option v-for="ch in chapters" :key="ch" :label="ch" :value="ch" />
            </el-select>
          </div>
          <div class="cfg-row">
            <span class="cfg-label">数量</span>
            <el-slider v-model="count" :min="3" :max="20" show-input size="small" />
          </div>
          <div class="cfg-row">
            <span class="cfg-label">题型</span>
            <el-radio-group v-model="ratio" size="small"><el-radio value="balanced">均衡</el-radio><el-radio value="singleMore">单选为主</el-radio></el-radio-group>
          </div>
          <div class="cfg-row">
            <span class="cfg-label">难度</span>
            <el-radio-group v-model="difficulty" size="small"><el-radio value="easy">偏易</el-radio><el-radio value="medium">中等</el-radio><el-radio value="hard">偏难</el-radio></el-radio-group>
          </div>
          <el-button type="primary" style="width:100%;margin-top:8px" :loading="generating" @click="handleGenerate">重新生成</el-button>
        </el-card>

        <el-card shadow="never" class="card" style="margin-top:16px">
          <template #header><strong>推送状态</strong></template>
          <div class="push-box">
            <el-progress type="dashboard" :percentage="pushStatus.percentage" :width="100">
              <template #default><span style="font-size:12px;color:var(--muted)">{{ pushStatus.label }}</span></template>
            </el-progress>
            <p class="muted" style="margin-top:10px">参与 {{ pushStatus.participantCount }} 人 · 限时 {{ pushStatus.durationMinutes }} 分钟</p>
            <el-button v-if="activeQuizId" type="danger" size="small" :loading="closing" @click="handleCloseQuiz" style="margin-top:8px;width:100%">关闭测验</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑题目" width="600px">
      <el-form v-if="editingQuestion" label-width="80px">
        <el-form-item label="题干"><el-input v-model="editingQuestion.stem" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="选项">
          <div v-for="(opt,oi) in editingQuestion.options" :key="oi" style="display:flex;gap:8px;margin-bottom:8px">
            <el-tag size="small">{{ opt.key }}</el-tag><el-input v-model="opt.text" size="small" style="flex:1" />
          </div>
        </el-form-item>
        <el-form-item label="答案"><el-input v-model="editingQuestion.answer" size="small" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="editVisible=false">取消</el-button><el-button type="primary" @click="editVisible=false">确定</el-button></template>
    </el-dialog>

    <!-- 题库添加 -->
    <el-dialog v-model="showAddDialog" title="从题库添加" width="700px">
      <el-input v-model="bankSearch" placeholder="搜索题干或知识点…" size="small" style="margin-bottom:12px" />
      <div v-for="q in filteredBank" :key="q.id" class="bank-item">
        <el-checkbox :model-value="selectedIds.has(q.id)" @change="toggleSelect(q.id)" />
        <div style="flex:1">
          <strong style="font-size:13px">{{ q.stem }}</strong>
          <div style="margin-top:4px;display:flex;gap:6px">
            <el-tag size="small">{{ q.questionType==='single'?'单选':q.questionType==='multiple'?'多选':'判断' }}</el-tag>
            <span class="muted" style="font-size:11px">{{ q.knowledgePoint }}</span>
          </div>
        </div>
        <el-button v-if="!questions.find(x=>x.id===q.id)" size="small" @click="addFromBank(q)">添加</el-button>
        <el-tag v-else size="small" type="success">已添加</el-tag>
      </div>
      <template #footer><el-button @click="showAddDialog=false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, reactive } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { generateLiveQuiz, getLiveQuiz, publishLiveQuiz, closeLiveQuiz, getQuizBank } from '../../api/teacher.js'

const filter = ref('all'), chapter = ref('第三章 实践与认识及其发展规律')
const generating = ref(false), publishing = ref(false), closing = ref(false)
const chapters = ref([]), count = ref(10), ratio = ref('balanced'), difficulty = ref('medium')
const questions = ref([]), selectedIds = reactive(new Set())
const editVisible = ref(false), editingQuestion = ref(null)
const showAddDialog = ref(false), bankSearch = ref(''), bankQuestions = ref([])
const pushStatus = ref({ label:'未推送', percentage:0, participantCount:0, durationMinutes:5 })
const activeQuizId = ref(null)

const visibleQuestions = computed(() => {
  if (filter.value === 'all') return questions.value
  return questions.value.filter(q => filter.value==='single' ? q.typeCode==='single' : q.typeCode==='multiple')
})
const filteredBank = computed(() => {
  if (!bankSearch.value) return bankQuestions.value
  const kw = bankSearch.value.toLowerCase()
  return bankQuestions.value.filter(q => (q.stem||'').toLowerCase().includes(kw) || (q.knowledgePoint||'').toLowerCase().includes(kw))
})

function toggleSelect(id) { selectedIds.has(id) ? selectedIds.delete(id) : selectedIds.add(id) }
function selectAll() { questions.value.forEach(q => selectedIds.add(q.id)) }
function deselectAll() { selectedIds.clear() }

async function loadData() {
  try {
    const data = await getLiveQuiz()
    chapters.value = data.chapters || []; chapter.value = data.config?.chapter || chapter.value
    count.value = data.config?.count || count.value; questions.value = data.questions || []
    pushStatus.value = data.pushStatus || pushStatus.value; activeQuizId.value = data.activeQuiz?.id || null
    questions.value.forEach(q => selectedIds.add(q.id))
  } catch (e) { console.error('加载失败', e) }
}

async function handleGenerate() {
  if (generating.value) return; generating.value = true; selectedIds.clear()
  try {
    const data = await generateLiveQuiz({ chapter:chapter.value, count:count.value, ratio:ratio.value, difficulty:difficulty.value })
    questions.value = data.questions || []; questions.value.forEach(q => selectedIds.add(q.id))
    ElMessage.success(data.message||'已生成')
  } catch (e) { ElMessage.error(e?.message||'失败') } finally { generating.value = false }
}

async function handlePublish() {
  if (publishing.value || !selectedIds.size) return; publishing.value = true
  try {
    const ids = [...selectedIds]; const data = await publishLiveQuiz(ids)
    pushStatus.value = data.pushStatus || pushStatus.value; activeQuizId.value = data.quizId || null
    ElMessage.success(`已推送 ${ids.length} 道题`)
  } catch (e) { ElMessage.error(e?.message||'失败') } finally { publishing.value = false }
}

async function handleCloseQuiz() {
  if (closing.value || !activeQuizId.value) return; closing.value = true
  try { await closeLiveQuiz(activeQuizId.value); activeQuizId.value = null; pushStatus.value = { ...pushStatus.value, label:'已关闭' }; ElMessage.success('已关闭') }
  catch (e) { ElMessage.error(e?.message||'失败') } finally { closing.value = false }
}

function removeQuestion(i) { const q = questions.value[i]; if (q) selectedIds.delete(q.id); questions.value.splice(i,1) }
function openEdit(q) { editingQuestion.value = JSON.parse(JSON.stringify(q)); editVisible.value = true }

async function addFromBank(q) {
  questions.value.push({
    id:q.id, type:q.questionType==='single'?'单选':q.questionType==='multiple'?'多选':'判断',
    typeCode:q.questionType, stem:q.stem,
    options:(q.options||[]).map((t,i)=>({key:String.fromCharCode(65+i),text:t})),
    answer:q.answer?.map?.(a=>String.fromCharCode(65+a)).join('')||'', source:q.knowledgePoint||'', knowledgePoint:q.knowledgePoint
  }); selectedIds.add(q.id)
}

async function openAddDialog() {
  showAddDialog.value = true
  if (!bankQuestions.value.length) { try { bankQuestions.value = await getQuizBank({}) } catch { bankQuestions.value = [] } }
}

onMounted(loadData)
</script>

<style scoped>
.breadcrumb { font-size:12px; margin-bottom:6px; }
.muted { color:var(--muted); font-size:13px; }
.page-header { display:flex; justify-content:space-between; align-items:center; }
.page-header h1 { font-size:26px; font-weight:800; letter-spacing:-0.3px; }
.header-actions { display:flex; gap:10px; }
.page-desc { font-size:13px; color:var(--muted); margin-top:4px; }
.card { border-radius:14px; border:1px solid var(--line); background:var(--card); }
.card-row { display:flex; justify-content:space-between; align-items:center; }
.card-row-left { display:flex; align-items:center; gap:10px; }

.q-card { padding:16px; margin-bottom:10px; background:var(--soft); border-radius:12px; border:1px dashed var(--line); transition:all 0.2s; }
.q-card.selected { border-color:#409EFF; border-style:solid; background:#ecf5ff; }
.q-card:last-child { margin-bottom:0; }
.qc-top { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.qc-stem { font-size:14px; }
.qc-options { display:flex; flex-direction:column; gap:3px; margin:8px 0 8px 36px; font-size:13px; color:#4d4d4d; }
.qc-meta { display:flex; align-items:center; gap:8px; margin-left:36px; }

.cfg-row { margin-bottom:12px; }
.cfg-label { display:block; font-size:13px; font-weight:600; margin-bottom:4px; }
.push-box { text-align:center; padding:8px 0; }

.bank-item { display:flex; align-items:flex-start; gap:10px; padding:8px 0; border-bottom:1px dashed var(--line); }
</style>
