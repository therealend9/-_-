<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 运行治理 / 配置详情</span></div>

    <div class="page-header">
      <div>
        <h1>{{ config.name }}</h1>
        <p class="page-desc">{{ config.key }} · {{ config.group }} · {{ config.owner }}</p>
      </div>
      <div class="header-actions">
        <el-button :icon="ArrowLeft" @click="router.push('/admin/system-settings')">返回设置</el-button>
        <el-button :icon="RefreshRight">恢复默认</el-button>
        <el-button :icon="Edit" type="primary">编辑配置</el-button>
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
              <strong>配置档案</strong>
              <div class="tag-row">
                <el-tag :type="config.statusType">{{ config.status }}</el-tag>
                <el-tag type="info">{{ config.type }}</el-tag>
              </div>
            </div>
          </template>
          <div class="config-grid">
            <div>
              <span class="muted small">配置键</span>
              <strong>{{ config.key }}</strong>
            </div>
            <div>
              <span class="muted small">当前值</span>
              <strong>{{ config.displayValue }}</strong>
            </div>
            <div>
              <span class="muted small">默认值</span>
              <strong>{{ config.defaultValue }}</strong>
            </div>
            <div>
              <span class="muted small">允许范围</span>
              <strong>{{ config.range }}</strong>
            </div>
            <div>
              <span class="muted small">负责人</span>
              <strong>{{ config.owner }}</strong>
            </div>
            <div>
              <span class="muted small">最近更新</span>
              <strong>{{ config.updatedAt }}</strong>
            </div>
          </div>
          <p class="impact-text">{{ config.impact }}</p>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>变更历史</strong>
              <el-tag type="info" size="small">{{ changeHistory.length }} 条</el-tag>
            </div>
          </template>
          <el-table :data="changeHistory" style="width: 100%">
            <el-table-column prop="version" label="版本" width="90" />
            <el-table-column prop="operator" label="操作人" width="120" />
            <el-table-column prop="before" label="变更前" min-width="150" />
            <el-table-column prop="after" label="变更后" min-width="150" />
            <el-table-column prop="time" label="时间" width="150" />
            <el-table-column prop="status" label="状态" width="100" align="center" />
          </el-table>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>原始配置</strong>
              <el-tag type="info" size="small">{{ config.key }}</el-tag>
            </div>
          </template>
          <pre class="raw-json">{{ formattedRawConfig }}</pre>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>校验规则</strong></template>
          <div v-for="item in validationRules" :key="item.name" class="rule-item">
            <div class="rule-head">
              <strong>{{ item.name }}</strong>
              <el-tag size="small" :type="item.type">{{ item.result }}</el-tag>
            </div>
            <p>{{ item.desc }}</p>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>影响模块</strong></template>
          <div v-for="item in relatedModules" :key="item.module" class="module-item">
            <div class="module-head">
              <strong>{{ item.module }}</strong>
              <el-tag size="small" :type="item.usage === '直接影响' ? 'warning' : 'info'">{{ item.usage }}</el-tag>
            </div>
            <div class="muted small">{{ item.status }}</div>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>处理流程</strong></template>
          <el-timeline>
            <el-timeline-item v-for="item in timeline" :key="`${item.title}-${item.time}`" :timestamp="item.time">
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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Edit, RefreshRight } from '@element-plus/icons-vue'
import { getSystemConfigDetail } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const config = ref({})
const stats = ref([])
const validationRules = ref([])
const changeHistory = ref([])
const relatedModules = ref([])
const timeline = ref([])
const rawConfig = ref({})

const formattedRawConfig = computed(() => JSON.stringify(rawConfig.value, null, 2))

onMounted(() => runPageLoad(loading, async () => {
  const data = await getSystemConfigDetail(route.params.configKey)
  config.value = data.config || {}
  stats.value = data.stats || []
  validationRules.value = data.validationRules || []
  changeHistory.value = data.changeHistory || []
  relatedModules.value = data.relatedModules || []
  timeline.value = data.timeline || []
  rawConfig.value = data.rawConfig || {}
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
.config-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.config-grid div, .rule-item, .module-item {
  background: var(--soft); border-radius: 10px; padding: 12px;
}
.config-grid div { display: flex; flex-direction: column; gap: 6px; }
.impact-text { margin-top: 14px; font-size: 13px; color: #4d4d4d; line-height: 1.8; }
.rule-item, .module-item { margin-bottom: 10px; }
.rule-head, .module-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.rule-item p { margin: 0; font-size: 13px; line-height: 1.7; color: #4d4d4d; }
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.raw-json {
  margin: 0; background: #2f2f2f; color: #f7f6f2; border-radius: 10px; padding: 14px;
  font-size: 12px; line-height: 1.7; overflow: auto;
}
</style>
