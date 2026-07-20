<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 账号与组织 / 批量导入</span></div>

    <div class="page-header">
      <div>
        <h1>用户批量导入</h1>
        <p class="page-desc">{{ template.name }} · {{ template.version }} · {{ template.updatedAt }}</p>
      </div>
      <div class="header-actions">
        <el-button :icon="ArrowLeft" @click="router.push('/admin/user-management')">返回列表</el-button>
        <el-button :icon="Download">下载模板</el-button>
        <el-button :icon="Check" type="primary" :loading="confirming" @click="confirmImport">确认导入</el-button>
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
      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>名单文件</strong></template>
          <el-upload drag action="#" :auto-upload="false" class="upload-box">
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">拖拽 Excel 文件到此处，或点击选择</div>
            <template #tip>
              <div class="muted small">支持 .xlsx 模板，单次建议不超过 500 行。</div>
            </template>
          </el-upload>

          <div class="required-fields">
            <div class="block-title">必填字段</div>
            <div class="field-tags">
              <el-tag v-for="field in template.requiredFields" :key="field" size="small">{{ field }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>字段映射</strong>
              <el-tag type="warning" size="small">2 项待确认</el-tag>
            </div>
          </template>
          <el-table :data="mappings" style="width: 100%">
            <el-table-column prop="source" label="模板字段" width="120" />
            <el-table-column prop="target" label="系统字段" width="170" />
            <el-table-column prop="rule" label="校验规则" min-width="220" />
            <el-table-column label="状态" width="110" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.statusType">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <strong>预检结果</strong>
          <el-button :icon="RefreshRight" size="small">重新校验</el-button>
        </div>
      </template>
      <el-table :data="previewRows" style="width: 100%">
        <el-table-column prop="row" label="行号" width="80" align="center" />
        <el-table-column prop="account" label="账号" width="130" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="role" label="角色" width="100" />
        <el-table-column prop="dept" label="院系" min-width="150" />
        <el-table-column prop="className" label="班级/部门" min-width="150" />
        <el-table-column prop="course" label="关联课程" min-width="170" />
        <el-table-column label="校验结果" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.resultType">{{ row.result }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>冲突处理</strong>
              <el-tag type="danger" size="small">{{ conflicts.length }} 类</el-tag>
            </div>
          </template>
          <div class="conflict-grid">
            <div v-for="item in conflicts" :key="item.type" class="conflict-item">
              <div class="conflict-head">
                <strong>{{ item.type }}</strong>
                <el-tag size="small" type="warning">{{ item.count }} 条</el-tag>
              </div>
              <p>{{ item.strategy }}</p>
              <span class="muted small">处理人：{{ item.owner }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>导入流程</strong></template>
          <el-timeline>
            <el-timeline-item v-for="item in steps" :key="item.title" :timestamp="item.time">
              <div class="timeline-title">{{ item.title }}</div>
              <div class="muted small">{{ item.desc }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ArrowLeft, Check, Download, RefreshRight, UploadFilled } from '@element-plus/icons-vue'
import { confirmUserBatchImport, getUserBatchImport } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const confirming = ref(false)
const stats = ref([])
const template = ref({ requiredFields: [] })
const mappings = ref([])
const previewRows = ref([])
const conflicts = ref([])
const steps = ref([])

function applyPayload(data) {
  stats.value = data.stats || []
  template.value = data.template || template.value
  mappings.value = data.mappings || []
  previewRows.value = data.previewRows || []
  conflicts.value = data.conflicts || []
  steps.value = data.steps || []
}

async function confirmImport() {
  if (confirming.value) return

  confirming.value = true
  try {
    const data = await confirmUserBatchImport()
    applyPayload(data)
    ElMessage.success(data.message || '导入已完成')
  } catch (error) {
    ElMessage.error(error.message || '导入失败')
  } finally {
    confirming.value = false
  }
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getUserBatchImport()
  applyPayload(data)
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
.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.upload-box { width: 100%; }
.upload-icon { font-size: 34px; color: #409EFF; margin-bottom: 8px; }
.upload-text { font-size: 14px; color: var(--ink); }
.required-fields {
  margin-top: 16px; background: var(--soft); border-radius: 12px; padding: 14px;
}
.block-title { font-weight: 800; margin-bottom: 10px; }
.field-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.conflict-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.conflict-item {
  background: var(--soft); border: 1px dashed var(--line); border-radius: 10px; padding: 12px;
}
.conflict-head {
  display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px;
}
.conflict-item p {
  min-height: 46px; font-size: 13px; line-height: 1.7; color: #4d4d4d; margin: 0 0 8px;
}
.timeline-title { font-weight: 800; margin-bottom: 4px; }
</style>
