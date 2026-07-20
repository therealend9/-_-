<template>
  <div class="workbench-page">
    <div class="breadcrumb"><span class="muted">教师端 / 课后 / 作业批改复核</span></div>

    <header class="page-header">
      <div>
        <h1>AI 辅助批改工作台</h1>
        <p class="page-desc">试题识别、答题卡模板、学生答案与批改复核在同一工作区完成</p>
      </div>
      <div class="header-actions">
        <el-button :loading="processing" @click="runRecognition">
          <el-icon><MagicStick /></el-icon> OCR 识别
        </el-button>
        <el-button type="warning" :disabled="!currentAnswer" @click="runAiGrade">
          <el-icon><EditPen /></el-icon> AI 批改
        </el-button>
        <el-button type="danger" plain @click="resetDemo">
          <el-icon><RefreshLeft /></el-icon> 退回重做
        </el-button>
        <el-button type="primary" :disabled="!aiReady" @click="publishResult">
          <el-icon><CircleCheck /></el-icon> 确认发布
        </el-button>
      </div>
    </header>

    <section class="context-bar">
      <div class="context-field exam-field">
        <span>当前考试</span>
        <el-select v-model="selectedExam" size="small">
          <el-option label="马原15-16期末试卷" value="mayuan-15-16" />
          <el-option label="马克思主义基本原理期中测试" value="mayuan-midterm" />
        </el-select>
      </div>
      <div class="context-field"><span>试题目录</span><strong>{{ questionItems.length }} 题</strong></div>
      <div class="context-field"><span>答题卡模板</span><strong>{{ templatePublished ? '马原15-16答题卡 v1.0' : '待创建' }}</strong></div>
      <div class="context-field"><span>处理状态</span><el-tag :type="statusType" size="small">{{ statusLabel }}</el-tag></div>
      <div class="context-spacer" />
      <el-button size="small" @click="openQueue"><el-icon><Files /></el-icon> 复核队列 {{ reviewQueue.length }}</el-button>
    </section>

    <main class="processing-center">
      <section class="center-head">
        <div>
          <div class="section-kicker">识别处理中心</div>
          <h2>文件识别与模板处理</h2>
        </div>
        <el-tag type="info" effect="plain">静态演示版，未连接后端</el-tag>
      </section>

      <el-tabs v-model="activePanel" class="work-tabs" @tab-change="handlePanelChange">
        <el-tab-pane name="template">
          <template #label><span><el-icon><Picture /></el-icon> 答题卡模板生成</span></template>
          <div class="panel-layout template-layout">
            <aside class="upload-panel">
              <h3>空白答题卡</h3>
              <input ref="templateInput" class="hidden-input" type="file" accept=".pdf,.png,.jpg,.jpeg,.docx" @change="event => selectFile(event, 'template')" />
              <button class="upload-dropzone" type="button" @click="templateInput?.click()">
                <el-icon><UploadFilled /></el-icon>
                <strong>{{ templateFile ? templateFile.name : '上传空白答题卡' }}</strong>
                <span>{{ templateFile ? templateFile.size : 'PDF、图片或 Word 文档' }}</span>
              </button>
              <el-form label-position="top" size="small" class="template-form">
                <el-form-item label="模板名称"><el-input v-model="templateName" /></el-form-item>
                <el-form-item label="模板版本"><el-input v-model="templateVersion" /></el-form-item>
              </el-form>
              <el-button type="primary" class="full-button" :loading="processing" @click="generateRegions">
                <el-icon><MagicStick /></el-icon> 自动识别区域
              </el-button>
              <p class="panel-note">自动结果仅作为草稿，发布前需要检查每个答题区域。</p>
            </aside>

            <section class="paper-stage">
              <div class="stage-toolbar">
                <span>第 1 页 / 共 1 页</span>
                <div>
                  <el-button size="small" :disabled="templatePublished" @click="addRegion"><el-icon><Plus /></el-icon> 新增区域</el-button>
                  <el-button size="small" @click="showCropPreview = !showCropPreview"><el-icon><View /></el-icon> 预览裁剪</el-button>
                </div>
              </div>
              <div class="answer-sheet-paper">
                <div class="paper-title">《马克思主义基本原理》期末考试答题卡</div>
                <div class="paper-meta">课程：马克思主义基本原理　　姓名：____________　　学号：____________</div>
                <div class="paper-rule" />
                <div v-for="region in templateRegions" :key="region.id" class="template-region" :class="{ selected: selectedRegionId === region.id, locked: templatePublished }" :style="regionStyle(region)" @click="selectRegion(region.id)">
                  <span>{{ region.no }} 题</span>
                  <span class="region-handle handle-tl" />
                  <span class="region-handle handle-br" />
                </div>
              </div>
            </section>

            <aside class="inspector-panel">
              <template v-if="selectedRegion">
                <div class="inspector-head">
                  <div><span class="eyebrow">当前区域</span><h3>第 {{ selectedRegion.no }} 题</h3></div>
                  <el-tag :type="templatePublished ? 'success' : 'warning'" size="small">{{ templatePublished ? '已发布' : '待复核' }}</el-tag>
                </div>
                <el-form label-position="top" size="small">
                  <el-form-item label="题号"><el-input v-model="selectedRegion.no" :disabled="templatePublished" /></el-form-item>
                  <el-form-item label="题目 ID"><el-select v-model="selectedRegion.questionId" :disabled="templatePublished"><el-option v-for="item in questionItems" :key="item.id" :label="`${item.no} - ${item.id}`" :value="item.id" /></el-select></el-form-item>
                  <el-form-item label="区域类型"><el-input model-value="answer" disabled /></el-form-item>
                </el-form>
                <div class="coordinate-grid"><span>x {{ selectedRegion.x }}</span><span>y {{ selectedRegion.y }}</span><span>w {{ selectedRegion.w }}</span><span>h {{ selectedRegion.h }}</span></div>
                <div class="nudge-row">
                  <span>微调位置</span>
                  <el-button-group>
                    <el-button size="small" :disabled="templatePublished" @click="nudgeRegion(-0.01, 0)">左</el-button>
                    <el-button size="small" :disabled="templatePublished" @click="nudgeRegion(0.01, 0)">右</el-button>
                    <el-button size="small" :disabled="templatePublished" @click="nudgeRegion(0, -0.01)">上</el-button>
                    <el-button size="small" :disabled="templatePublished" @click="nudgeRegion(0, 0.01)">下</el-button>
                  </el-button-group>
                </div>
                <div v-if="showCropPreview" class="crop-preview"><span>裁剪预览</span><p>第 {{ selectedRegion.no }} 题学生手写作答区域</p></div>
                <div class="inspector-actions">
                  <el-button :disabled="templatePublished" @click="deleteRegion"><el-icon><Delete /></el-icon> 删除区域</el-button>
                  <el-button type="primary" :disabled="templatePublished" @click="saveDraft">保存草稿</el-button>
                </div>
                <el-button type="success" class="full-button" :disabled="templatePublished || !templateRegions.length" @click="publishTemplate"><el-icon><Lock /></el-icon> 发布并绑定考试</el-button>
              </template>
              <div v-else class="empty-inspector"><el-icon><Picture /></el-icon><p>点击答题区域后可检查题号、题目 ID 和裁剪范围。</p></div>
            </aside>
          </div>
        </el-tab-pane>

        <el-tab-pane name="question">
          <template #label><span><el-icon><Document /></el-icon> 试题卷输入</span></template>
          <div class="panel-layout document-layout">
            <aside class="upload-panel">
              <h3>自由格式试题卷</h3>
              <input ref="questionInput" class="hidden-input" type="file" accept=".pdf,.png,.jpg,.jpeg,.docx" @change="event => selectFile(event, 'question')" />
              <button class="upload-dropzone" type="button" @click="questionInput?.click()"><el-icon><FolderOpened /></el-icon><strong>{{ questionFile ? questionFile.name : '上传试题卷' }}</strong><span>支持多页 PDF、图片和 Word 文档</span></button>
              <el-button type="primary" class="full-button" :loading="processing" @click="recognizeQuestions"><el-icon><MagicStick /></el-icon> 开始识别</el-button>
              <div class="flow-list"><span>1 文件解析</span><span>2 OCR 识别</span><span>3 题目切分</span><span>4 跨页合并</span></div>
            </aside>
            <section class="preview-stage">
              <div class="stage-toolbar"><span>试题卷第 {{ selectedQuestion?.page || 1 }} 页</span><el-tag size="small" type="success">{{ questionRecognized ? '识别完成' : '等待识别' }}</el-tag></div>
              <div class="question-paper-preview">
                <h3>马克思主义基本原理期末考试</h3>
                <p>一、材料分析题</p>
                <div v-for="item in questionItems" :key="item.id" class="paper-question" :class="{ active: selectedQuestion?.id === item.id }" @click="selectedQuestion = item"><strong>{{ item.no }}.</strong><span>{{ item.text }}</span></div>
              </div>
            </section>
            <aside class="result-list">
              <div class="list-head"><h3>题目识别结果</h3><el-tag size="small">{{ questionItems.length }} 题</el-tag></div>
              <button v-for="item in questionItems" :key="item.id" class="result-item" :class="{ active: selectedQuestion?.id === item.id }" type="button" @click="selectedQuestion = item"><strong>{{ item.no }} 题</strong><span>{{ item.text }}</span><small>{{ item.id }} · 第 {{ item.page }} 页</small></button>
              <el-button type="primary" class="full-button" @click="saveQuestionCatalog"><el-icon><CircleCheck /></el-icon> 确认题目目录</el-button>
            </aside>
          </div>
        </el-tab-pane>

        <el-tab-pane name="student">
          <template #label><span><el-icon><EditPen /></el-icon> 学生答题卷输入</span></template>
          <div class="panel-layout document-layout">
            <aside class="upload-panel">
              <h3>学生答题卷</h3>
              <div class="template-badge"><span>已匹配模板</span><strong>{{ templatePublished ? '马原15-16答题卡 v1.0' : '请先发布模板' }}</strong></div>
              <input ref="studentInput" class="hidden-input" type="file" accept=".pdf,.png,.jpg,.jpeg" @change="event => selectFile(event, 'student')" />
              <button class="upload-dropzone" type="button" :disabled="!templatePublished" @click="studentInput?.click()"><el-icon><UploadFilled /></el-icon><strong>{{ studentFile ? studentFile.name : '上传学生答题卷' }}</strong><span>按已发布模板固定区域处理</span></button>
              <el-button type="primary" class="full-button" :disabled="!templatePublished" :loading="processing" @click="recognizeAnswers"><el-icon><MagicStick /></el-icon> 开始识别</el-button>
              <div class="flow-list"><span>1 页面匹配</span><span>2 模板对齐</span><span>3 区域裁剪</span><span>4 手写识别</span></div>
            </aside>
            <section class="preview-stage">
              <div class="stage-toolbar"><span>第 {{ selectedAnswer?.page || 1 }} 页 · 第 {{ selectedAnswer?.no || 1 }} 题</span><el-button size="small" @click="showAligned = !showAligned"><el-icon><Connection /></el-icon>{{ showAligned ? '查看裁剪图' : '查看模板对齐' }}</el-button></div>
              <div class="student-paper" :class="{ aligned: showAligned }">
                <div class="student-paper-title">学生答题卡 {{ showAligned ? '模板对齐视图' : '答题区域裁剪图' }}</div>
                <div class="handwriting">{{ selectedAnswer?.handwriting || '请先选择学生答题卷并开始识别' }}</div>
                <div v-if="showAligned" class="alignment-line">模板边界已对齐 · 置信度 96%</div>
              </div>
            </section>
            <aside class="result-list answer-list">
              <div class="list-head"><h3>学生答案结果</h3><el-tag size="small" type="warning">{{ answerItems.length }} 项</el-tag></div>
              <button v-for="item in answerItems" :key="item.id" class="result-item" :class="{ active: selectedAnswer?.id === item.id }" type="button" @click="selectedAnswer = item"><strong>{{ item.no }} 题 <em v-if="item.blank">空白</em></strong><span>{{ item.text || '未检测到作答内容' }}</span><small>OCR {{ item.confidence }}% · {{ item.needsReview ? '需要复核' : '正常' }}</small></button>
              <el-button type="warning" class="full-button" :disabled="!selectedAnswer" @click="sendToAi"><el-icon><EditPen /></el-icon> 交给 AI 批改</el-button>
            </aside>
          </div>
        </el-tab-pane>

        <el-tab-pane name="answerKey">
          <template #label><span><el-icon><Document /></el-icon> 答案输入</span></template>
          <div class="answer-key-static">
            <div class="static-head"><div><span class="section-kicker">预留模块</span><h3>标准答案与评分要点</h3><p>当前版本仅展示录入界面，暂不保存或提交数据。</p></div><el-tag type="info">静态样式</el-tag></div>
            <div class="answer-key-grid">
              <section class="key-card"><h4>标准答案文件</h4><div class="disabled-dropzone"><el-icon><UploadFilled /></el-icon><span>选择答案文件</span><small>后续由批改模块接入</small></div><el-button disabled class="full-button">导入答案</el-button></section>
              <section class="key-card"><h4>第 1 题标准答案</h4><el-input type="textarea" :rows="7" disabled model-value="请在后续版本录入标准答案、得分点和参考表述。" /><el-button disabled class="full-button">保存答案</el-button></section>
              <section class="key-card"><h4>评分要点</h4><div class="rubric-placeholder"><span>理论概念准确</span><span>材料分析完整</span><span>逻辑结构清晰</span><span>结合现实问题</span></div><el-button disabled type="primary" class="full-button">交给批改模块</el-button></section>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </main>

    <section class="review-area">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card shadow="never" class="info-card"><template #header><div class="card-title"><span>AI 批改建议</span><el-tag v-if="aiReady" type="success" size="small">已生成</el-tag></div></template>
            <div v-if="aiReady" class="ai-summary"><div class="score-ring">82</div><div><strong>建议分：82 分</strong><p>理论概念使用准确，建议补充现实案例以增强论证完整性。</p></div></div>
            <div v-else class="empty-card"><el-icon><EditPen /></el-icon><p>确认学生答案后，可在此查看 AI 批改建议。</p></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never" class="info-card"><template #header><div class="card-title"><span>复核队列</span><el-button link type="primary" @click="openQueue">查看全部</el-button></div></template>
            <div v-for="item in reviewQueue.slice(0, 3)" :key="item.id" class="queue-row"><div><strong>{{ item.title }}</strong><p>{{ item.desc }}</p></div><el-tag :type="item.type" size="small">{{ item.tag }}</el-tag></div>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <el-drawer v-model="queueVisible" title="复核队列" size="420px"><div v-for="item in reviewQueue" :key="item.id" class="drawer-queue"><strong>{{ item.title }}</strong><p>{{ item.desc }}</p><el-tag :type="item.type" size="small">{{ item.tag }}</el-tag></div></el-drawer>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, Connection, Delete, Document, EditPen, Files, FolderOpened, Lock, MagicStick, Picture, Plus, RefreshLeft, UploadFilled, View } from '@element-plus/icons-vue'

const activePanel = ref('template')
const selectedExam = ref('mayuan-15-16')
const processing = ref(false)
const statusLabel = ref('待处理')
const statusType = ref('info')
const templateInput = ref(null)
const questionInput = ref(null)
const studentInput = ref(null)
const templateFile = ref(null)
const questionFile = ref(null)
const studentFile = ref(null)
const templateName = ref('马原15-16答题卡')
const templateVersion = ref('v1.0')
const selectedRegionId = ref('r1')
const templatePublished = ref(false)
const showCropPreview = ref(false)
const questionRecognized = ref(false)
const answerRecognized = ref(false)
const selectedQuestion = ref(null)
const selectedAnswer = ref(null)
const showAligned = ref(false)
const aiReady = ref(false)
const queueVisible = ref(false)

const questionItems = ref([
  { id: 'mayuan-15-16-q01', no: '1', page: 1, text: '结合材料，说明实践与认识的辩证关系。' },
  { id: 'mayuan-15-16-q02', no: '2', page: 1, text: '运用社会基本矛盾运动原理分析中国式现代化。' },
  { id: 'mayuan-15-16-q03', no: '3', page: 2, text: '阐释资本主义基本矛盾及其历史发展趋势。' },
])

const templateRegions = ref([
  { id: 'r1', no: '1', questionId: 'mayuan-15-16-q01', x: 0.10, y: 0.22, w: 0.80, h: 0.17 },
  { id: 'r2', no: '2', questionId: 'mayuan-15-16-q02', x: 0.10, y: 0.44, w: 0.80, h: 0.17 },
  { id: 'r3', no: '3', questionId: 'mayuan-15-16-q03', x: 0.10, y: 0.66, w: 0.80, h: 0.17 },
])

const answerItems = ref([
  { id: 'a1', no: '1', page: 1, text: '实践是认识的来源、动力和目的，也是检验真理的唯一标准。', handwriting: '实践是认识的来源、动力和目的，也是检验真理的唯一标准。', confidence: 94, blank: false, needsReview: false },
  { id: 'a2', no: '2', page: 1, text: '社会基本矛盾推动社会发展，中国式现代化要不断解放和发展生产力。', handwriting: '社会基本矛盾推动社会发展，中国式现代化要不断解放和发展生产力。', confidence: 78, blank: false, needsReview: true },
  { id: 'a3', no: '3', page: 2, text: '', handwriting: '', confidence: 100, blank: true, needsReview: true },
])

const reviewQueue = ref([
  { id: 1, title: '第 2 题学生答案', desc: '手写 OCR 置信度较低，建议核对裁剪区域和文本。', tag: '优先', type: 'danger' },
  { id: 2, title: '第 3 题学生答案', desc: '检测为空白答题区域，建议人工确认。', tag: '异常', type: 'warning' },
  { id: 3, title: '答题卡模板第 1 页', desc: '第 2 题区域边界经过人工微调，等待发布。', tag: '模板', type: 'info' },
])

const selectedRegion = computed(() => templateRegions.value.find(item => item.id === selectedRegionId.value) || null)
const currentAnswer = computed(() => selectedAnswer.value || answerItems.value[0])

selectedQuestion.value = questionItems.value[0]
selectedAnswer.value = answerItems.value[0]

function selectFile(event, type) {
  const file = event.target.files?.[0]
  if (!file) return
  const data = { name: file.name, size: `${Math.max(1, Math.round(file.size / 1024))} KB` }
  if (type === 'template') templateFile.value = data
  if (type === 'question') questionFile.value = data
  if (type === 'student') studentFile.value = data
  statusLabel.value = '文件已选择（演示）'
  statusType.value = 'info'
}

function simulateProcessing(done) {
  processing.value = true
  statusLabel.value = '处理中（演示）'
  statusType.value = 'warning'
  window.setTimeout(() => {
    processing.value = false
    statusLabel.value = '处理完成（演示）'
    statusType.value = 'success'
    done()
  }, 700)
}

function generateRegions() {
  simulateProcessing(() => {
    if (!templateRegions.value.length) addRegion()
    selectedRegionId.value = templateRegions.value[0].id
    ElMessage.success('已生成答题区域草稿（演示）')
  })
}

function recognizeQuestions() {
  simulateProcessing(() => {
    questionRecognized.value = true
    selectedQuestion.value = questionItems.value[0]
    ElMessage.success('试题卷识别完成（演示）')
  })
}

function recognizeAnswers() {
  simulateProcessing(() => {
    answerRecognized.value = true
    selectedAnswer.value = answerItems.value[0]
    ElMessage.success('学生答题卷识别完成（演示）')
  })
}

function runRecognition() {
  if (activePanel.value === 'template') generateRegions()
  else if (activePanel.value === 'question') recognizeQuestions()
  else if (activePanel.value === 'student') recognizeAnswers()
  else ElMessage.info('答案输入模块当前仅提供静态样式')
}

function addRegion() {
  const number = String(templateRegions.value.length + 1)
  const question = questionItems.value[templateRegions.value.length % questionItems.value.length]
  const region = { id: `r${Date.now()}`, no: number, questionId: question.id, x: 0.10, y: 0.72, w: 0.80, h: 0.12 }
  templateRegions.value.push(region)
  selectedRegionId.value = region.id
}

function deleteRegion() {
  if (!selectedRegion.value) return
  templateRegions.value = templateRegions.value.filter(item => item.id !== selectedRegion.value.id)
  selectedRegionId.value = templateRegions.value[0]?.id || ''
}

function nudgeRegion(x, y) {
  if (!selectedRegion.value) return
  selectedRegion.value.x = Number(Math.min(0.9 - selectedRegion.value.w, Math.max(0.02, selectedRegion.value.x + x)).toFixed(2))
  selectedRegion.value.y = Number(Math.min(0.92 - selectedRegion.value.h, Math.max(0.08, selectedRegion.value.y + y)).toFixed(2))
}

function regionStyle(region) {
  return { left: `${region.x * 100}%`, top: `${region.y * 100}%`, width: `${region.w * 100}%`, height: `${region.h * 100}%` }
}

function saveDraft() {
  statusLabel.value = '模板草稿已保存（演示）'
  statusType.value = 'success'
  ElMessage.success('模板草稿已保存')
}

function publishTemplate() {
  templatePublished.value = true
  statusLabel.value = '模板已发布并绑定（演示）'
  statusType.value = 'success'
  ElMessage.success('答题卡模板已发布并绑定到当前考试')
}

function saveQuestionCatalog() {
  questionRecognized.value = true
  statusLabel.value = '题目目录已确认（演示）'
  statusType.value = 'success'
  ElMessage.success('题目目录已确认')
}

function sendToAi() {
  aiReady.value = false
  simulateProcessing(() => {
    aiReady.value = true
    ElMessage.success('当前答案已送入 AI 批改演示流程')
  })
}

function runAiGrade() {
  sendToAi()
}

function publishResult() {
  statusLabel.value = '批改结果已发布（演示）'
  statusType.value = 'success'
  ElMessage.success('批改结果已确认发布')
}

function resetDemo() {
  aiReady.value = false
  answerRecognized.value = false
  questionRecognized.value = false
  statusLabel.value = '已退回等待处理（演示）'
  statusType.value = 'info'
  ElMessage.info('已重置当前演示处理状态')
}

function openQueue() {
  queueVisible.value = true
}

function handlePanelChange() {
  showAligned.value = false
  showCropPreview.value = false
}
</script>

<style scoped>
.workbench-page { min-width: 1080px; }
.breadcrumb { margin-bottom: 8px; font-size: 12px; }
.muted, .page-desc, .panel-note { color: var(--muted); }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
.page-header h1 { margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 0; }
.page-desc { margin: 5px 0 0; font-size: 13px; }
.header-actions, .stage-toolbar, .inspector-actions, .card-title, .list-head, .static-head { display: flex; align-items: center; }
.header-actions { gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.header-actions .el-icon, .work-tabs .el-icon, .full-button .el-icon, .context-bar .el-icon { margin-right: 5px; }
.context-bar { display: flex; align-items: center; gap: 18px; min-height: 54px; padding: 0 16px; margin-top: 18px; background: #fff; border: 1px solid var(--line); border-radius: 8px; }
.context-field { display: flex; flex-direction: column; gap: 3px; min-width: 130px; font-size: 12px; color: var(--muted); }
.context-field strong { color: #303133; font-size: 13px; font-weight: 600; }
.exam-field { min-width: 220px; }
.context-spacer { flex: 1; }
.processing-center { margin-top: 18px; background: #fff; border: 1px solid var(--line); border-radius: 8px; }
.center-head { display: flex; justify-content: space-between; align-items: center; padding: 18px 20px 12px; }
.section-kicker, .eyebrow { color: #7a8494; font-size: 11px; font-weight: 600; letter-spacing: 0; }
.center-head h2 { margin: 3px 0 0; font-size: 17px; }
.work-tabs :deep(.el-tabs__header) { margin: 0; padding: 0 20px; border-bottom: 1px solid var(--line); }
.work-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.work-tabs :deep(.el-tabs__item) { height: 44px; font-size: 14px; }
.work-tabs :deep(.el-tabs__item span) { display: inline-flex; align-items: center; }
.work-tabs :deep(.el-tabs__content) { padding: 18px 20px 20px; }
.panel-layout { display: grid; gap: 16px; min-height: 468px; }
.template-layout { grid-template-columns: 230px minmax(420px, 1fr) 258px; }
.document-layout { grid-template-columns: 230px minmax(390px, 1fr) 290px; }
.upload-panel, .inspector-panel, .result-list { border: 1px solid var(--line); border-radius: 7px; padding: 14px; background: #fcfcfd; }
.upload-panel h3, .result-list h3, .inspector-panel h3, .answer-key-static h3 { margin: 0; font-size: 15px; }
.hidden-input { display: none; }
.upload-dropzone { width: 100%; min-height: 130px; margin: 14px 0; padding: 18px 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: #687386; background: #f7f8fa; border: 1px dashed #c8d0dc; border-radius: 6px; cursor: pointer; }
.upload-dropzone:disabled { cursor: not-allowed; opacity: .58; }
.upload-dropzone .el-icon { font-size: 24px; color: #409eff; }
.upload-dropzone strong { color: #3b4554; font-size: 13px; max-width: 190px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.upload-dropzone span, .upload-dropzone small { color: #909399; font-size: 11px; }
.template-form { margin: 4px 0 10px; }
.template-form :deep(.el-form-item) { margin-bottom: 10px; }
.template-form :deep(.el-form-item__label) { padding-bottom: 4px; font-size: 12px; }
.full-button { width: 100%; margin-top: 10px; }
.panel-note { margin: 12px 0 0; font-size: 12px; line-height: 1.65; }
.paper-stage, .preview-stage { display: flex; flex-direction: column; min-width: 0; border: 1px solid var(--line); border-radius: 7px; overflow: hidden; background: #f5f6f8; }
.stage-toolbar { justify-content: space-between; min-height: 42px; padding: 0 12px; border-bottom: 1px solid var(--line); background: #fff; color: #6b7280; font-size: 12px; }
.answer-sheet-paper { position: relative; width: min(100%, 560px); height: 396px; margin: auto; padding: 28px 38px; box-sizing: border-box; background: #fff; box-shadow: 0 2px 10px rgb(18 27 45 / 10%); }
.paper-title { text-align: center; font-size: 16px; font-weight: 700; }
.paper-meta { margin-top: 16px; font-size: 11px; color: #666; }
.paper-rule { height: 1px; margin-top: 13px; background: #cfd5dd; }
.template-region { position: absolute; display: flex; align-items: flex-start; padding: 5px; box-sizing: border-box; border: 2px solid #67c23a; background: rgb(103 194 58 / 8%); cursor: pointer; }
.template-region span:first-child { padding: 2px 5px; color: #fff; background: #67c23a; border-radius: 3px; font-size: 11px; line-height: 1; }
.template-region.selected { border-color: #409eff; background: rgb(64 158 255 / 10%); }
.template-region.selected span:first-child { background: #409eff; }
.template-region.locked { cursor: default; opacity: .82; }
.region-handle { position: absolute; width: 7px; height: 7px; background: #409eff; border: 1px solid #fff; }
.handle-tl { top: -5px; left: -5px; }.handle-br { right: -5px; bottom: -5px; }
.inspector-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 10px; }
.inspector-panel :deep(.el-form-item) { margin-bottom: 9px; }.inspector-panel :deep(.el-form-item__label) { padding-bottom: 3px; font-size: 12px; }
.coordinate-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 10px 0; }.coordinate-grid span { padding: 6px 7px; background: #f4f6f8; border-radius: 4px; color: #707784; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; }
.nudge-row { display: flex; flex-direction: column; gap: 6px; margin: 12px 0; color: #687386; font-size: 12px; }.nudge-row :deep(.el-button) { padding: 5px 8px; }
.crop-preview { padding: 10px; background: #eef6ff; border: 1px dashed #91bff0; border-radius: 5px; color: #4a6c8c; font-size: 12px; }.crop-preview p { margin: 5px 0 0; }
.inspector-actions { gap: 8px; margin-top: 14px; }.inspector-actions .el-button { flex: 1; }
.empty-inspector { min-height: 270px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #98a1ad; text-align: center; }.empty-inspector .el-icon { font-size: 30px; }.empty-inspector p { padding: 0 18px; font-size: 12px; line-height: 1.7; }
.flow-list { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 18px; }.flow-list span { padding: 8px; color: #717b89; background: #f3f5f7; border-radius: 4px; font-size: 11px; }
.question-paper-preview { width: min(100%, 560px); min-height: 350px; margin: auto; padding: 34px 42px; box-sizing: border-box; background: #fff; box-shadow: 0 2px 10px rgb(18 27 45 / 10%); }.question-paper-preview h3 { margin: 0 0 22px; text-align: center; font-size: 17px; }.question-paper-preview p { font-weight: 600; font-size: 13px; }.paper-question { display: flex; gap: 8px; padding: 11px 8px; border-bottom: 1px dashed #dfe3e8; cursor: pointer; font-size: 13px; line-height: 1.65; }.paper-question.active { margin: 0 -8px; color: #176dc6; background: #ecf5ff; border-radius: 4px; }
.list-head { justify-content: space-between; margin-bottom: 10px; }.result-list { display: flex; flex-direction: column; }.result-item { display: flex; flex-direction: column; gap: 4px; width: 100%; padding: 10px; margin-bottom: 7px; text-align: left; color: #525c6b; background: #fff; border: 1px solid #e4e7ed; border-radius: 5px; cursor: pointer; }.result-item:hover, .result-item.active { border-color: #8ac0f6; background: #f0f8ff; }.result-item strong { color: #303133; font-size: 13px; }.result-item span { display: -webkit-box; overflow: hidden; -webkit-box-orient: vertical; -webkit-line-clamp: 2; font-size: 12px; line-height: 1.45; }.result-item small { color: #939aa5; font-size: 11px; }.result-item em { padding: 2px 4px; margin-left: 4px; color: #e6a23c; background: #fdf6ec; border-radius: 3px; font-size: 10px; font-style: normal; }
.template-badge { display: flex; flex-direction: column; gap: 3px; padding: 10px; margin: 14px 0 0; background: #f0f9eb; border: 1px solid #c2e7b0; border-radius: 5px; }.template-badge span { color: #6a8a5c; font-size: 11px; }.template-badge strong { color: #48793c; font-size: 12px; }
.student-paper { width: min(100%, 560px); min-height: 350px; margin: auto; padding: 28px 34px; box-sizing: border-box; background: repeating-linear-gradient(0deg, #fff 0 29px, #edf0f3 30px); box-shadow: 0 2px 10px rgb(18 27 45 / 10%); }.student-paper.aligned { background: repeating-linear-gradient(0deg, #f7fbff 0 29px, #d7e9fb 30px); outline: 2px dashed #79b6ed; }.student-paper-title { padding-bottom: 12px; color: #64748b; border-bottom: 1px solid #d6dce3; font-size: 12px; }.handwriting { padding: 27px 8px; color: #364a5e; font-family: KaiTi, STKaiti, serif; font-size: 19px; line-height: 2.25; transform: rotate(-1deg); }.alignment-line { padding: 8px; color: #337ab7; background: #eaf5ff; border-radius: 4px; font-size: 12px; }
.answer-key-static { padding: 6px 2px 2px; }.static-head { justify-content: space-between; }.static-head h3 { margin: 4px 0; }.static-head p { margin: 0; color: #8c95a3; font-size: 12px; }.answer-key-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 18px; }.key-card { min-height: 224px; padding: 16px; background: #fcfcfd; border: 1px solid var(--line); border-radius: 7px; }.key-card h4 { margin: 0 0 12px; font-size: 14px; }.disabled-dropzone { min-height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 7px; color: #a5adba; background: #f6f7f9; border: 1px dashed #d8dde5; border-radius: 5px; font-size: 12px; }.disabled-dropzone .el-icon { font-size: 22px; }.disabled-dropzone small { font-size: 11px; }.rubric-placeholder { display: flex; flex-wrap: wrap; gap: 8px; min-height: 126px; align-content: flex-start; }.rubric-placeholder span { padding: 7px 9px; color: #76808e; background: #f3f5f7; border-radius: 4px; font-size: 12px; }
.review-area { margin-top: 16px; }.info-card { min-height: 146px; border-radius: 8px; border-color: var(--line); }.card-title { justify-content: space-between; }.ai-summary { display: flex; align-items: center; gap: 14px; }.score-ring { display: flex; align-items: center; justify-content: center; width: 58px; height: 58px; color: #e6a23c; border: 5px solid #f9e4b7; border-radius: 50%; font-size: 20px; font-weight: 800; }.ai-summary strong { color: #303133; }.ai-summary p { margin: 5px 0 0; color: #687386; font-size: 12px; line-height: 1.55; }.empty-card { min-height: 70px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #99a1ad; font-size: 12px; }.empty-card .el-icon { font-size: 22px; }.empty-card p { margin: 5px 0; }.queue-row, .drawer-queue { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; padding: 9px 0; border-bottom: 1px dashed #e2e5e9; }.queue-row:last-child { border-bottom: 0; }.queue-row strong, .drawer-queue strong { font-size: 13px; }.queue-row p, .drawer-queue p { margin: 4px 0 0; color: #7a8492; font-size: 12px; line-height: 1.45; }.drawer-queue { display: block; }.drawer-queue .el-tag { margin-top: 7px; }
@media (max-width: 1250px) { .template-layout { grid-template-columns: 210px minmax(370px, 1fr) 235px; }.document-layout { grid-template-columns: 210px minmax(340px, 1fr) 260px; }.workbench-page { min-width: 1000px; } }
</style>
