<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">学生端 / 学习报告 / 学情画像</span></div>
    <div class="page-header">
      <h1>学情画像 · 学习报告</h1>
      <div class="header-actions">
        <el-button @click="loadData">刷新数据</el-button>
      </div>
    </div>
    <p class="page-desc">基于学习行为数据的多维能力画像，识别薄弱点，获取个性化学习建议</p>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6" v-for="s in stats" :key="s.label">
        <div class="stat-card">
          <div class="muted small">{{ s.label }}</div>
          <div class="stat-num" :style="{ color: s.color }">{{ s.value }}</div>
          <div class="muted small" style="margin-top: 2px">{{ s.desc }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 五维雷达图 -->
      <el-col :span="12">
        <el-card shadow="never" class="card">
          <template #header><strong>五维能力雷达</strong></template>
          <div ref="radarRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 强弱项 + 推荐 -->
      <el-col :span="12">
        <el-card shadow="never" class="card">
          <template #header><strong>学习建议</strong></template>
          <div class="insight-section">
            <div class="insight-row">
              <span class="insight-label">✅ 优势维度</span>
              <div style="display: flex; gap: 6px; flex-wrap: wrap">
                <el-tag v-for="s in strengths" :key="s" type="success" effect="plain">{{ s }}</el-tag>
                <span v-if="!strengths.length" class="muted">暂无数据</span>
              </div>
            </div>
            <div class="insight-row">
              <span class="insight-label">⚠️ 薄弱维度</span>
              <div style="display: flex; gap: 6px; flex-wrap: wrap">
                <el-tag v-for="w in weakPoints" :key="w" type="warning" effect="plain">{{ w }}</el-tag>
                <span v-if="!weakPoints.length" class="muted">表现均衡，继续保持</span>
              </div>
            </div>
            <div class="insight-row">
              <span class="insight-label">🎯 风险等级</span>
              <el-tag :type="riskTagType">{{ riskLabel }}</el-tag>
            </div>
          </div>

          <el-divider style="margin: 12px 0" />

          <div>
            <strong style="font-size: 13px">📋 个性化推荐</strong>
            <div v-for="r in recommendations" :key="r.type" class="rec-item" @click="r.route && router.push(r.route)">
              <span class="rec-text">{{ r.text }}</span>
              <span style="color: #409EFF; font-size: 13px">去看看 →</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 学习时间线 -->
    <el-card shadow="never" class="card" style="margin-top: 20px">
      <template #header><strong>学习轨迹</strong></template>
      <el-steps :active="timeline.length" align-center>
        <el-step v-for="(t, i) in timeline" :key="i"
                 :title="t.title" :description="t.desc">
          <template #icon>
            <span class="step-dot">{{ i + 1 }}</span>
          </template>
        </el-step>
      </el-steps>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getStudentAnalytics } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const radarRef = ref(null)
let chart = null

const stats = ref([])
const abilityRadar = ref([])
const weakPoints = ref([])
const strengths = ref([])
const recommendations = ref([])
const timeline = ref([])
const riskLevel = ref('normal')

const riskTagType = ref('success')
const riskLabel = ref('正常')

function loadData() {
  return runPageLoad(loading, async () => {
    const data = await getStudentAnalytics()
    stats.value = data.stats || []
    abilityRadar.value = data.abilityRadar || []
    weakPoints.value = data.weakPoints || []
    strengths.value = data.strengths || []
    recommendations.value = data.recommendations || []
    timeline.value = data.timeline || []
    riskLevel.value = data.riskLevel || 'normal'

    switch (data.riskLevel) {
      case 'warning': riskTagType.value = 'danger'; riskLabel.value = '预警'; break
      case 'attention': riskTagType.value = 'warning'; riskLabel.value = '需关注'; break
      default: riskTagType.value = 'success'; riskLabel.value = '正常'
    }

    nextTick(() => renderRadar())
  })
}

function renderRadar() {
  if (!radarRef.value) return
  if (chart) chart.dispose()

  chart = echarts.init(radarRef.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, data: ['当前水平'] },
    radar: {
      center: ['50%', '48%'],
      radius: '70%',
      indicator: abilityRadar.value.map(a => ({ name: a.name, max: 100 })),
      axisName: { fontSize: 12 }
    },
    series: [{
      type: 'radar',
      name: '当前水平',
      data: [{ value: abilityRadar.value.map(a => a.value), name: '当前水平' }],
      areaStyle: { color: 'rgba(64,158,255,0.2)' },
      lineStyle: { color: '#409EFF', width: 2 },
      itemStyle: { color: '#409EFF' },
      symbolSize: 5
    }]
  })

  window.addEventListener('resize', () => chart?.resize())
}

onMounted(loadData)
onBeforeUnmount(() => { if (chart) chart.dispose() })
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.header-actions { display: flex; gap: 10px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card { background: var(--soft); border-radius: 14px; padding: 20px; text-align: center; border: 1px dashed var(--line); }
.stat-num { font-size: 36px; font-weight: 800; margin-top: 4px; }
.chart-container { width: 100%; height: 340px; }
.insight-section { display: flex; flex-direction: column; gap: 14px; }
.insight-row { display: flex; align-items: center; gap: 10px; }
.insight-label { font-size: 13px; font-weight: 600; white-space: nowrap; min-width: 80px; }
.rec-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 12px; margin-top: 8px; background: var(--soft);
  border-radius: 8px; cursor: pointer; transition: background 0.15s;
}
.rec-item:hover { background: var(--active); }
.rec-text { font-size: 13px; line-height: 1.5; flex: 1; margin-right: 12px; }
.step-dot {
  width: 24px; height: 24px; border-radius: 50%;
  background: #409EFF; color: #fff; display: flex;
  align-items: center; justify-content: center; font-size: 12px; font-weight: 700;
}
</style>
