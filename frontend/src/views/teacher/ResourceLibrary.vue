<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">教师端 / 资源中心 / 教学资源库</span></div>
    <div class="page-header">
      <h1>教学资源库</h1>
      <el-button type="primary" @click="uploadVisible = true">上传资源</el-button>
    </div>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6">
        <el-card shadow="never" class="card">
          <template #header><strong>资源分类</strong></template>
          <div class="category-list">
            <div v-for="c in categories" :key="c.name" class="category-item" :class="{ active: activeCat === c.name }" @click="activeCat = c.name">
              <span>{{ c.name }}</span>
              <el-tag size="small">{{ c.count }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-card shadow="never" class="card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <strong>{{ activeCat }}</strong>
              <el-input v-model="search" placeholder="搜索资源..." style="width: 260px" clearable />
            </div>
          </template>
          <el-table :data="filteredResources" empty-text="暂无资源" style="width: 100%">
            <el-table-column prop="title" label="资源名称" min-width="200">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 8px">
                  <el-tag size="small" :type="row.fileType === '视频' ? 'danger' : row.fileType === '文档' ? 'primary' : 'warning'">{{ row.fileType }}</el-tag>
                  <strong>{{ row.title }}</strong>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="chapter" label="关联章节" width="160" />
            <el-table-column prop="size" label="大小" width="80" />
            <el-table-column prop="uploadTime" label="上传时间" width="120" />
            <el-table-column label="操作" width="160">
              <template #default>
                <el-button size="small">预览</el-button>
                <el-button size="small" type="primary">下载</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 上传弹窗 -->
    <el-dialog v-model="uploadVisible" title="上传资源" width="480px">
      <el-form label-width="80px">
        <el-form-item label="选择文件">
          <input type="file" ref="fileInput" @change="onFileChange" style="display: block" />
        </el-form-item>
        <el-form-item label="资源标题">
          <el-input v-model="uploadForm.title" placeholder="请输入资源名称" />
        </el-form-item>
        <el-form-item label="资源类型">
          <el-select v-model="uploadForm.sourceType" style="width: 100%">
            <el-option label="课件" value="courseware" />
            <el-option label="案例" value="case" />
            <el-option label="教材" value="textbook" />
            <el-option label="题库" value="question_bank" />
            <el-option label="政策文件" value="policy" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="doUpload">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getTeacherResourceLibrary } from '../../api/teacher.js'
import { uploadKnowledgeFile } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const loading = ref(true)
const search = ref('')
const activeCat = ref('')
const categories = ref([])
const resources = ref([])
const uploadVisible = ref(false)
const uploading = ref(false)
const fileInput = ref(null)
const uploadForm = ref({ title: '', sourceType: 'courseware', description: '' })

const filteredResources = computed(() => {
  const keyword = search.value.trim()
  return resources.value.filter((item) => {
    const matchesCategory = !activeCat.value || item.category === activeCat.value
    const matchesSearch = !keyword || item.title.includes(keyword) || item.chapter.includes(keyword)
    return matchesCategory && matchesSearch
  })
})

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (file) uploadForm.value.title = file.name
}

async function doUpload() {
  const file = fileInput.value?.files?.[0]
  if (!file) { ElMessage.warning('请选择文件'); return }
  uploading.value = true
  try {
    await uploadKnowledgeFile(file, { ...uploadForm.value })
    ElMessage.success('上传成功，等待审核')
    uploadVisible.value = false
    const data = await getTeacherResourceLibrary()
    resources.value = data.resources || []
  } catch (e) { ElMessage.error(e?.message || '上传失败') }
  finally { uploading.value = false }
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getTeacherResourceLibrary()
  categories.value = data.categories || []
  resources.value = data.resources || []
  activeCat.value = categories.value[0]?.name || ''
}))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.category-list { display: flex; flex-direction: column; gap: 4px; }
.category-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; border-radius: 10px; cursor: pointer; font-size: 14px; transition: background 0.2s; }
.category-item:hover { background: var(--soft); }
.category-item.active { background: var(--active); font-weight: 700; }
</style>

