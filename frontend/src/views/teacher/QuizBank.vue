<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">教师端 / 题库管理</span></div>
    <div class="page-header">
      <h1>题库管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="openCreate">+ 新建题目</el-button>
        <el-button @click="loadData">刷新</el-button>
      </div>
    </div>
    <p class="page-desc">管理课程题库，支持新建、编辑、删除题目，可按类型和知识点筛选</p>

    <!-- 筛选 -->
    <el-row :gutter="12" style="margin-top: 16px">
      <el-col :span="5">
        <el-select v-model="filterType" placeholder="题型" clearable @change="loadData" style="width: 100%">
          <el-option label="单选题" value="single" />
          <el-option label="多选题" value="multiple" />
          <el-option label="判断题" value="judge" />
        </el-select>
      </el-col>
      <el-col :span="5">
        <el-select v-model="filterStatus" placeholder="审核状态" clearable @change="loadData" style="width: 100%">
          <el-option label="已审核" value="approved" />
          <el-option label="待审核" value="pending" />
        </el-select>
      </el-col>
      <el-col :span="5">
        <el-input v-model="filterKeyword" placeholder="搜索题干/知识点" clearable @clear="loadData" @keyup.enter="loadData" />
      </el-col>
      <el-col :span="3">
        <el-button @click="loadData">搜索</el-button>
      </el-col>
      <el-col :span="6" style="text-align: right">
        <span class="muted">共 {{ questions.length }} 道题</span>
      </el-col>
    </el-row>

    <!-- 题目列表 -->
    <el-card shadow="never" class="card" style="margin-top: 16px">
      <el-table :data="questions" style="width: 100%" size="small">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="stem" label="题干" min-width="280" show-overflow-tooltip />
        <el-table-column label="题型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.questionType === 'single' ? 'primary' : row.questionType === 'multiple' ? 'warning' : 'info'">
              {{ row.questionType === 'single' ? '单选' : row.questionType === 'multiple' ? '多选' : '判断' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="knowledgePoint" label="知识点" width="120" show-overflow-tooltip />
        <el-table-column prop="auditStatus" label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.auditStatus === 'approved' ? 'success' : 'warning'">
              {{ row.auditStatus === 'approved' ? '已审核' : '待审' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除这道题？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button size="small" text type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑题目' : '新建题目'" width="680px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="题型">
          <el-radio-group v-model="form.questionType">
            <el-radio value="single">单选题</el-radio>
            <el-radio value="multiple">多选题</el-radio>
            <el-radio value="judge">判断题</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="知识点">
          <el-input v-model="form.knowledgePoint" placeholder="如：实践对认识的决定作用" />
        </el-form-item>
        <el-form-item label="题干">
          <el-input v-model="form.stem" type="textarea" :rows="3" placeholder="请输入题目题干" />
        </el-form-item>
        <el-form-item label="选项">
          <div v-for="(opt, i) in form.options" :key="i" style="display: flex; gap: 8px; margin-bottom: 8px; align-items: center">
            <el-tag size="small" :type="form.answer.includes(i) ? 'success' : 'info'">{{ String.fromCharCode(65 + i) }}</el-tag>
            <el-input v-model="form.options[i]" :placeholder="'选项 ' + String.fromCharCode(65 + i)" size="small" style="flex: 1" />
            <el-button size="small" :type="form.answer.includes(i) ? 'success' : 'default'" circle @click="toggleAnswer(i)">
              {{ form.answer.includes(i) ? '✓' : '○' }}
            </el-button>
            <el-button v-if="form.options.length > 2" size="small" type="danger" circle @click="form.options.splice(i, 1); form.answer = form.answer.filter(a => a !== i).map(a => a > i ? a - 1 : a)">×</el-button>
          </div>
          <el-button size="small" @click="form.options.push('')" style="margin-top: 4px">+ 添加选项</el-button>
        </el-form-item>
        <el-form-item label="答案解析">
          <el-input v-model="form.analysis" type="textarea" :rows="2" placeholder="可选，用于展示给学生的解析" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">{{ editingId ? '保存修改' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getQuizBank, createQuizQuestion, updateQuizQuestion, deleteQuizQuestion } from '../../api/teacher.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const loading = ref(true)
const saving = ref(false)
const questions = ref([])
const filterType = ref('')
const filterStatus = ref('')
const filterKeyword = ref('')
const dialogVisible = ref(false)
const editingId = ref(null)
const form = ref({ questionType: 'single', knowledgePoint: '', stem: '', options: ['', ''], answer: [], analysis: '' })

function resetForm() {
  editingId.value = null
  form.value = { questionType: 'single', knowledgePoint: '', stem: '', options: ['', ''], answer: [], analysis: '' }
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.value = {
    questionType: row.questionType,
    knowledgePoint: row.knowledgePoint,
    stem: row.stem,
    options: [...row.options],
    answer: [...row.answer],
    analysis: row.analysis || ''
  }
  dialogVisible.value = true
}

function toggleAnswer(i) {
  const idx = form.value.answer.indexOf(i)
  if (idx >= 0) form.value.answer.splice(idx, 1)
  else if (form.value.questionType === 'single') form.value.answer = [i]
  else form.value.answer.push(i)
}

async function handleSave() {
  const f = form.value
  if (!f.stem.trim() || f.options.some(o => !o.trim())) {
    ElMessage.warning('题干和选项不能为空'); return
  }
  if (!f.answer.length) { ElMessage.warning('请设置正确答案'); return }

  saving.value = true
  try {
    if (editingId.value) {
      await updateQuizQuestion(editingId.value, f)
      ElMessage.success('已更新')
    } else {
      await createQuizQuestion(f)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    await loadData()
  } catch (e) { ElMessage.error(e?.message || '操作失败') }
  finally { saving.value = false }
}

async function handleDelete(id) {
  try {
    await deleteQuizQuestion(id)
    ElMessage.success('已删除')
    await loadData()
  } catch (e) { ElMessage.error(e?.message || '删除失败') }
}

async function loadData() {
  await runPageLoad(loading, async () => {
    questions.value = await getQuizBank({
      type: filterType.value || undefined,
      status: filterStatus.value || undefined,
      keyword: filterKeyword.value || undefined
    })
  })
}

onMounted(loadData)
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
</style>
