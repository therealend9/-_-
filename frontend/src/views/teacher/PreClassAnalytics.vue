<template>
  <div>
    <div class="breadcrumb"><span class="muted">教师端 / 学情分析</span></div>
    <div class="page-header">
      <h1>班级学情分析</h1>
      <el-button @click="loadData">刷新数据</el-button>
    </div>
    <p class="page-desc">班级级别学情统计、知识点掌握热力、学生排名与风险预警</p>

    <!-- 概览卡片 -->
    <el-row :gutter="16" style="margin-top: 20px">
      <el-col :span="6" v-for="s in classStats" :key="s.label">
        <div class="stat-card">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-num" :style="{ color: s.color }">{{ s.value }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 知识点热力 -->
      <el-col :span="12">
        <el-card shadow="never" class="section-card">
          <template #header><strong>知识点掌握度</strong></template>
          <div class="heatmap">
            <div v-for="h in heatmap" :key="h.name" class="heatmap-row">
              <span class="heatmap-label">{{ h.name }}</span>
              <div class="heatmap-bar">
                <div class="heatmap-fill" :style="{ width: h.rate + '%', background: h.color }"></div>
              </div>
              <span class="heatmap-val">{{ h.rate }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- AI 总结 + 预警 -->
      <el-col :span="12">
        <el-card shadow="never" class="section-card">
          <template #header><strong>AI 分析总结</strong></template>
          <div v-if="summary" class="ai-box">
            <span class="ai-badge" :style="{ background: summary.color }">{{ summary.label }}</span>
            <p class="ai-text">{{ summary.content }}</p>
          </div>
          <el-divider />
          <strong style="font-size:13px">⚠️ 预警学生</strong>
          <div v-if="!warningList.length" class="empty-sm">暂无预警学生</div>
          <div v-for="w in warningList" :key="w.name" class="warn-item">
            <div class="warn-head">
              <strong>{{ w.name }}</strong>
              <el-tag type="danger" size="small">{{ w.total }} 分</el-tag>
            </div>
            <div class="warn-reason">{{ w.reason }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 学生排名 + 关注 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card shadow="never" class="section-card">
          <template #header><strong>学生综合排名</strong></template>
          <el-table :data="studentScores" style="width:100%" size="small">
            <el-table-column prop="rank" label="#" width="50" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="total" label="综合分" width="80" sortable>
              <template #default="{ row }">
                <span :style="{ color: row.total >= 80 ? '#67C23A' : row.total >= 60 ? '#409EFF' : '#F56C6C', fontWeight: 700 }">{{ row.total }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="avgScore" label="测验均分" width="80" />
            <el-table-column prop="quizRate" label="正确率" width="80">
              <template #default="{ row }">{{ row.quizRate }}%</template>
            </el-table-column>
            <el-table-column prop="trend" label="趋势" width="70">
              <template #default="{ row }">
                <span :style="{ color: row.trend >= 0 ? '#67C23A' : '#F56C6C' }">{{ row.trend >= 0 ? '↑' : '↓' }}{{ Math.abs(row.trend) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="riskLevel" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.riskLevel === 'warning' ? 'danger' : row.riskLevel === 'attention' ? 'warning' : 'success'" size="small">
                  {{ row.riskLevel === 'warning' ? '预警' : row.riskLevel === 'attention' ? '关注' : '正常' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="section-card">
          <template #header><strong>需关注学生</strong></template>
          <div v-if="!attentionList.length" class="empty-sm">暂无</div>
          <div v-for="a in attentionList" :key="a.name" class="attention-item">
            <el-tag type="warning" size="small" effect="plain">关注</el-tag>
            <div class="att-body">
              <strong>{{ a.name }} · {{ a.total }}分</strong>
              <div class="att-reason">{{ a.reason }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getClassAnalytics } from '../../api/teacher.js'

const classStats = ref([])
const heatmap = ref([])
const studentScores = ref([])
const warningList = ref([])
const attentionList = ref([])
const summary = ref(null)

async function loadData() {
  try {
    const data = await getClassAnalytics()
    classStats.value = data.classStats || []
    heatmap.value = data.heatmap || []
    studentScores.value = data.studentScores || []
    warningList.value = data.warningList || []
    attentionList.value = data.attentionList || []
    summary.value = data.summary || null
  } catch (e) { console.error('加载学情失败', e) }
}

onMounted(loadData)
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }

.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.empty-sm { font-size: 13px; color: var(--muted); padding: 16px 0; text-align: center; }

.stat-card {
  background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 20px; text-align: center;
  transition: box-shadow var(--duration-fast);
}
.stat-card:hover { box-shadow: var(--shadow-sm); }
.stat-label { font-size: 12px; color: var(--muted); }
.stat-num { font-size: 32px; font-weight: 800; margin-top: 6px; }

.heatmap { display: flex; flex-direction: column; gap: 14px; padding: 8px 0; }
.heatmap-row { display: flex; align-items: center; }
.heatmap-label { width: 80px; font-size: 13px; color: var(--muted); flex-shrink: 0; }
.heatmap-bar { flex: 1; height: 24px; background: var(--soft); border-radius: 12px; overflow: hidden; margin: 0 12px; }
.heatmap-fill { height: 100%; border-radius: 12px; transition: width 0.6s var(--ease-out); }
.heatmap-val { font-weight: 700; font-size: 13px; width: 40px; }

.ai-box { padding: 4px 0 8px; }
.ai-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; color: #fff; font-size: 12px; font-weight: 600; margin-bottom: 8px; }
.ai-text { font-size: 13px; line-height: 1.8; color: #4d4d4d; }

.warn-item {
  padding: 10px 12px; background: var(--soft); border-radius: 8px;
  margin-top: 8px; border-left: 3px solid #F56C6C;
}
.warn-head { display: flex; justify-content: space-between; align-items: center; }
.warn-reason { font-size: 12px; color: var(--muted); margin-top: 4px; }

.attention-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 12px; background: var(--soft); border-radius: 8px; margin-top: 8px;
}
.att-body { flex: 1; }
.att-body strong { font-size: 13px; }
.att-reason { font-size: 12px; color: var(--muted); margin-top: 2px; }
</style>
