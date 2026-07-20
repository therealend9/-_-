<template>
  <div>
    <div class="breadcrumb"><span class="muted">教师端 / AI 备课中心</span></div>
    <div class="page-header">
      <h1>AI 备课中心</h1>
      <div class="header-actions">
        <el-button :loading="generating" type="primary" @click="regenerate">🤖 AI 生成教案</el-button>
        <el-button :loading="saving" @click="saveDraft">💾 保存草稿</el-button>
        <el-button type="success" :loading="publishing" @click="publish">📤 发布给学生</el-button>
      </div>
    </div>
    <p class="page-desc">AI 根据章节内容自动生成结构化教案，包含教学目标、课堂结构、讨论题和案例推荐，教师审核后发布</p>

    <!-- 课程输入 -->
    <el-card shadow="never" class="card" style="margin-top: 16px">
      <template #header><strong>📖 课程信息</strong></template>
      <el-row :gutter="16">
        <el-col :span="8">
          <div class="field-label">课程名称</div>
          <el-input v-model="courseInput.courseName" placeholder="如：马克思主义基本原理" />
        </el-col>
        <el-col :span="10">
          <div class="field-label">章节主题</div>
          <el-input v-model="courseInput.chapterTitle" placeholder="如：第三章 实践与认识及其发展规律" />
        </el-col>
        <el-col :span="6">
          <div class="field-label">课时安排</div>
          <el-input-number v-model="config.classHours" :min="1" :max="4" size="default" style="width:100%" />
        </el-col>
      </el-row>
      <el-row :gutter="16" style="margin-top: 14px">
        <el-col :span="24">
          <div class="field-label">补充说明 <span class="muted">（可选：教学重点、特殊要求、学生情况等）</span></div>
          <el-input
            v-model="courseInput.extraNote"
            type="textarea"
            :rows="3"
            placeholder="例如：本节课希望重点突出实践检验真理的过程，学生已经预习过第三章，班级互动积极性高，希望多安排讨论环节……"
          />
        </el-col>
      </el-row>
    </el-card>

    <!-- 生成选项 -->
    <el-card shadow="never" class="card" style="margin-top: 16px">
      <template #header><strong>⚙️ 生成选项</strong></template>
      <el-row :gutter="16">
        <el-col :span="8">
          <span class="muted">重点领域：</span>
          <el-checkbox-group v-model="config.focusAreas" size="small">
            <el-checkbox label="理论基础">理论基础</el-checkbox>
            <el-checkbox label="案例分析">案例分析</el-checkbox>
            <el-checkbox label="价值引导">价值引导</el-checkbox>
          </el-checkbox-group>
        </el-col>
        <el-col :span="8">
          <span class="muted">包含测验：</span>
          <el-switch v-model="config.includeQuiz" size="small" />
          <span class="muted" style="margin-left:20px">包含讨论：</span>
          <el-switch v-model="config.includeDiscussion" size="small" />
        </el-col>
      </el-row>
    </el-card>

    <!-- 教案内容 -->
    <el-row :gutter="20" style="margin-top: 16px">
      <el-col :span="16">
        <el-card shadow="never" class="card" style="margin-bottom: 16px">
          <template #header><strong>📋 教学目标</strong></template>
          <div v-if="!teachingObjectives.length" class="empty-block">点击「AI 生成教案」开始</div>
          <div v-for="(obj, i) in teachingObjectives" :key="i" class="obj-item">
            <el-tag size="small" effect="dark">{{ obj.type }}</el-tag>
            <span>{{ obj.content }}</span>
          </div>
        </el-card>

        <el-card shadow="never" class="card" style="margin-bottom: 16px">
          <template #header><strong>🏫 课堂结构</strong></template>
          <div v-if="!classStructure.length" class="empty-block">待生成</div>
          <el-steps v-else direction="vertical" :active="classStructure.length">
            <el-step v-for="(s, i) in classStructure" :key="i" :title="s.phase" :description="s.content" />
          </el-steps>
        </el-card>

        <el-card shadow="never" class="card" style="margin-bottom: 16px">
          <template #header><strong>💬 课堂讨论题</strong></template>
          <div v-if="!discussionQuestions.length" class="empty-block">待生成</div>
          <div v-for="(q, i) in discussionQuestions" :key="i" class="discuss-item">
            <span class="discuss-num">{{ i + 1 }}</span>
            <span>{{ q }}</span>
          </div>
        </el-card>

        <el-card v-if="quizQuestions.length" shadow="never" class="card" style="margin-bottom: 16px">
          <template #header><strong>📝 随堂测验（{{ quizQuestions.length }} 题）</strong></template>
          <div v-for="(q, i) in quizQuestions" :key="i" class="quiz-item">
            <el-tag size="small" effect="plain">{{ q.type === 'single' ? '单选' : q.type }}</el-tag>
            <span>{{ i + 1 }}. {{ q.stem }}</span>
            <span class="muted" style="font-size:11px">知识点：{{ q.knowledgePoint }}</span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="card" style="margin-bottom: 16px">
          <template #header><strong>🔑 教学重点</strong></template>
          <div v-if="!keyPoints.length" class="empty-block">待生成</div>
          <div v-for="(kp, i) in keyPoints" :key="i" class="kp-item">
            <span class="kp-num">{{ i + 1 }}</span>
            <span style="font-size:13px">{{ kp }}</span>
          </div>
        </el-card>

        <el-card shadow="never" class="card" style="margin-bottom: 16px">
          <template #header><strong>📚 案例推荐</strong></template>
          <div v-if="!caseRecommendations.length" class="empty-block">待生成</div>
          <div v-for="c in caseRecommendations" :key="c.title" class="case-item">
            <el-tag size="small" effect="plain">{{ c.type }}</el-tag>
            <div style="margin-top:4px;font-weight:600;font-size:13px">{{ c.title }}</div>
            <div class="muted" style="font-size:12px;margin-top:2px">{{ c.usage }}</div>
          </div>
        </el-card>

        <el-card shadow="never" class="card">
          <template #header><strong>🔗 知识来源</strong></template>
          <div v-if="!sourceRefs.length" class="empty-block">待生成</div>
          <div v-for="s in sourceRefs" :key="s.id" class="source-item">
            <span style="font-weight:600;font-size:13px">{{ s.title }}</span>
            <span class="muted" style="font-size:11px">{{ s.citation }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { generateLessonDesign, saveLessonDesignDraft, publishLessonDesign } from '../../api/teacher.js'

const generating = ref(false)
const saving = ref(false)
const publishing = ref(false)

const courseInput = reactive({
  courseName: '马克思主义基本原理',
  chapterTitle: '第三章 实践与认识及其发展规律',
  extraNote: ''
})

const config = reactive({
  focusAreas: ['理论基础', '案例分析', '价值引导'],
  classHours: 2,
  includeQuiz: true,
  includeDiscussion: true
})

const teachingObjectives = ref([])
const classStructure = ref([])
const discussionQuestions = ref([])
const quizQuestions = ref([])
const keyPoints = ref([])
const caseRecommendations = ref([])
const sourceRefs = ref([])

let currentDesign = null

function applyDesign(design) {
  currentDesign = design
  teachingObjectives.value = design.teachingObjectives || []
  classStructure.value = design.classStructure || []
  discussionQuestions.value = design.discussionQuestions || []
  quizQuestions.value = design.quizQuestions || []
  keyPoints.value = design.keyPoints || []
  caseRecommendations.value = design.caseRecommendations || []
  sourceRefs.value = design.sourceRefs || []
}

async function regenerate() {
  if (generating.value) return
  if (!courseInput.chapterTitle.trim()) {
    ElMessage.warning('请先输入章节主题')
    return
  }
  generating.value = true
  try {
    const result = await generateLessonDesign(1, {
      ...config,
      courseName: courseInput.courseName,
      chapterTitle: courseInput.chapterTitle,
      extraNote: courseInput.extraNote
    })
    applyDesign(result.design)
    ElMessage.success('AI 教案已生成（DeepSeek）')
  } catch (e) {
    ElMessage.error(e?.message || '生成失败，请检查后端服务是否启动')
  } finally {
    generating.value = false
  }
}

async function saveDraft() {
  if (saving.value || !currentDesign) return
  saving.value = true
  try {
    await saveLessonDesignDraft(currentDesign.chapter?.id || 1, currentDesign)
    ElMessage.success('草稿已保存')
  } catch (e) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function publish() {
  if (publishing.value) return
  publishing.value = true
  try {
    const result = await publishLessonDesign()
    ElMessage.success(result.message || '教案已发布给学生')
  } catch (e) {
    ElMessage.error(e?.message || '发布失败')
  } finally {
    publishing.value = false
  }
}
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }

.field-label { font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--ink); }
.field-label .muted { font-weight: 400; font-size: 12px; }

.empty-block { text-align: center; padding: 32px 0; font-size: 13px; color: var(--muted); }

.obj-item { display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; font-size: 13px; line-height: 1.7; }
.obj-item:not(:last-child) { border-bottom: 1px dashed var(--line); }

.discuss-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; font-size: 13px; line-height: 1.6; }
.discuss-item:not(:last-child) { border-bottom: 1px dashed var(--line); }
.discuss-num { width: 22px; height: 22px; border-radius: 50%; background: #409EFF; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }

.quiz-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; font-size: 13px; }
.quiz-item:not(:last-child) { border-bottom: 1px dashed var(--line); }

.kp-item { display: flex; align-items: flex-start; gap: 8px; padding: 8px 0; }
.kp-item:not(:last-child) { border-bottom: 1px dashed var(--line); }
.kp-num { width: 20px; height: 20px; border-radius: 50%; background: var(--active); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }

.case-item { padding: 10px 0; }
.case-item:not(:last-child) { border-bottom: 1px dashed var(--line); }

.source-item { padding: 8px 0; }
.source-item:not(:last-child) { border-bottom: 1px dashed var(--line); }
</style>
