<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">{{ mode === 'teacher' ? '教师端 / 知识图谱 / 教学导航' : '学生端 / 知识图谱 / 理论学习导航' }}</span></div>
    <div class="page-header">
      <h1>知识图谱导航</h1>
      <div class="header-actions">
        <el-select v-model="selectedChapterId" @change="loadData" style="width:200px;margin-right:8px">
          <el-option
            v-for="chapter in chapters"
            :key="chapter.id"
            :label="`第${chapter.chapterOrder}章 ${chapter.title}`"
            :value="chapter.id"
          />
        </el-select>
        <el-button @click="resetZoom">重置视图</el-button>
        <el-button type="primary" @click="$router.push(mode === 'teacher' ? '/teacher/dashboard' : '/student/pre-study')">{{ mode === 'teacher' ? '返回教师首页' : '返回课前学习' }}</el-button>
      </div>
    </div>
    <p class="page-desc">以可视化图谱展示本章知识点之间的逻辑关系，点击节点查看详情、关联资源和学习建议</p>

    <el-row :gutter="16" style="margin-top: 20px">
      <!-- 左侧：图谱区 -->
      <el-col :span="17">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <strong>知识关系图谱</strong>
              <div style="display: flex; gap: 8px">
                <el-tag v-for="r in relationTypes" :key="r.value" :color="relationColor(r.value)" effect="dark" size="small" style="color: #fff">
                  {{ r.label }}
                </el-tag>
              </div>
            </div>
          </template>

          <div ref="chartRef" class="graph-container"></div>

          <div class="graph-stats">
            <span>节点：{{ summary.totalNodes }} 个</span>
            <el-divider direction="vertical" />
            <span>关系：{{ summary.totalEdges }} 条</span>
            <el-divider direction="vertical" />
            <span>类型：{{ summary.relationTypes?.length || 0 }} 种</span>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：节点详情 -->
      <el-col :span="7">
        <el-card shadow="never" class="section-card" style="min-height: 500px">
          <template #header><strong>节点详情</strong></template>

          <div v-if="!selectedNode" class="empty-hint">
            <el-icon :size="48" color="#c0c4cc"><component is="InfoFilled" /></el-icon>
            <p style="margin-top: 12px; color: #909399">点击图谱中的节点<br/>查看知识点详情</p>
          </div>

          <div v-else class="node-detail">
            <div class="node-header" :style="{ borderLeftColor: selectedNode.color }">
              <h3>{{ selectedNode.name }}</h3>
              <div style="display: flex; gap: 6px; flex-wrap: wrap">
                <el-tag size="small" :color="selectedNode.color" effect="dark" style="color: #fff">{{ selectedNode.nodeTypeLabel }}</el-tag>
                <el-tag size="small" effect="plain">{{ selectedNode.difficultyLabel }}</el-tag>
              </div>
            </div>

            <p class="node-desc">{{ selectedNode.description }}</p>

            <!-- 关联边 -->
            <div v-if="relatedEdges.length" class="node-section">
              <strong style="font-size: 13px">关联关系</strong>
              <div v-for="e in relatedEdges" :key="e.id" class="edge-item">
                <el-tag size="small" effect="plain">{{ e.relationLabel }}</el-tag>
                <span class="edge-target">{{ e.sourceName === selectedNode.name ? e.targetName : e.sourceName }}</span>
              </div>
            </div>

            <!-- 关联资源 -->
            <div v-if="selectedNode.sources?.length" class="node-section">
              <strong style="font-size: 13px">学习资源</strong>
              <div v-for="s in selectedNode.sources" :key="s.id" class="source-item">
                <el-icon :size="14"><component is="Document" /></el-icon>
                <span style="margin-left: 4px; font-size: 13px">{{ s.title }}</span>
              </div>
            </div>

            <div style="margin-top: 16px">
              <el-button size="small" type="primary" @click="goToSource(selectedNode)">查看学习资源</el-button>
              <el-button size="small" @click="goToPreStudy(selectedNode)">进入导学</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getStudentKnowledgeGraph, getStudentKnowledgeGraphChapters, getStudentNodeDetail, getTeacherKnowledgeGraph, getTeacherKnowledgeGraphChapters, getTeacherNodeDetail } from '../../api/knowledge-graph.js'
import { Document, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const props = defineProps({ mode: { type: String, default: 'student' } })
const mode = props.mode
const chartRef = ref(null)
const loading = ref(false)
const chapters = ref([])
const selectedChapterId = ref(null)
const graphData = ref({ nodes: [], edges: [], summary: {} })
const selectedNode = ref(null)
const relatedEdges = ref([])
let chart = null

const relationTypes = [
  { value: 'contains', label: '包含' },
  { value: 'prerequisite', label: '前置' },
  { value: 'related', label: '相关' },
  { value: 'derives', label: '派生' },
  { value: 'applies', label: '应用' }
]

const summary = ref({ totalNodes: 0, totalEdges: 0, relationTypes: [] })

function relationColor(type) {
  const map = { contains: '#67C23A', prerequisite: '#409EFF', related: '#E6A23C', derives: '#F56C6C', applies: '#909399', contrasts: '#F56C6C' }
  return map[type] || '#409EFF'
}

function loadData() {
  if (!selectedChapterId.value) return
  loading.value = true
  const getGraph = mode === 'teacher' ? getTeacherKnowledgeGraph : getStudentKnowledgeGraph
  getGraph(selectedChapterId.value).then(data => {
    graphData.value = data
    summary.value = data.summary || { totalNodes: data.nodes.length, totalEdges: data.edges.length, relationTypes: [...new Set(data.edges.map(e => e.relationType))] }
    loading.value = false
    nextTick(() => renderChart())
  }).catch((error) => {
    loading.value = false
    ElMessage.error(error.message || '知识图谱加载失败，请稍后重试')
  })
}

function renderChart() {
  if (!chartRef.value) return
  if (chart) chart.dispose()

  chart = echarts.init(chartRef.value)
  const { nodes, edges } = graphData.value

  const categories = [...new Set(nodes.map(n => n.nodeType))].map((type, i) => ({
    name: type,
    itemStyle: { color: nodes.find(n => n.nodeType === type)?.color || '#409EFF' }
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter(params) {
        if (params.dataType === 'node') {
          const d = params.data
          return `<strong>${d.name}</strong><br/>${d.nodeTypeLabel || ''} · ${d.difficultyLabel || ''}<br/>${d.description || ''}`
        }
        return `${params.data.label || params.data.relationLabel || ''}`
      }
    },
    legend: {
      bottom: 0,
      data: categories.map(c => c.name),
      textStyle: { fontSize: 11 }
    },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      categories,
      data: nodes.map(n => ({
        id: n.id,
        name: n.name,
        category: n.nodeType,
        symbolSize: n.parentId ? 28 : 40,
        value: n.description,
        nodeTypeLabel: n.nodeTypeLabel,
        difficultyLabel: n.difficultyLabel,
        itemStyle: { color: n.color },
        label: { show: true, fontSize: n.parentId ? 11 : 13, fontWeight: n.parentId ? 'normal' : 'bold' }
      })),
      links: edges.map(e => ({
        source: e.source,
        target: e.target,
        label: { show: true, formatter: e.relationLabel, fontSize: 10 },
        lineStyle: { color: relationColor(e.relationType), width: Math.max(1, e.weight * 2), curveness: 0.2 }
      })),
      force: {
        repulsion: 300,
        gravity: 0.08,
        edgeLength: [100, 200],
        layoutAnimation: true
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 }
      }
    }]
  }

  chart.setOption(option)

  chart.on('click', (params) => {
    if (params.dataType === 'node') {
      onNodeClick(params.data)
    }
  })

  window.addEventListener('resize', handleResize)
}

function onNodeClick(nodeData) {
  const node = graphData.value.nodes.find(n => n.id === nodeData.id)
  if (!node) return

  // 获取该节点相关的边
  const edges = graphData.value.edges.filter(
    e => e.source === node.id || e.target === node.id
  )
  // 补全边的名称信息
  relatedEdges.value = edges.map(e => {
    const sourceNode = graphData.value.nodes.find(n => n.id === e.source)
    const targetNode = graphData.value.nodes.find(n => n.id === e.target)
    return { ...e, sourceName: sourceNode?.name || '', targetName: targetNode?.name || '' }
  })

  // 如果有更多详情（含资源），从后端获取
  const getNodeDetail = mode === 'teacher' ? getTeacherNodeDetail : getStudentNodeDetail
  getNodeDetail(node.id).then(detail => {
    selectedNode.value = { ...node, sources: detail.sources || [], edges: detail.edges || [] }
    relatedEdges.value = detail.edges || relatedEdges.value
  }).catch(() => {
    selectedNode.value = node
  })
}

function resetZoom() {
  if (chart) {
    chart.dispatchAction({ type: 'restore' })
  }
}

function goToSource(node) {
  if (node.sources?.length) {
    router.push(`/student/source/${node.sources[0].id}`)
  }
}

function goToPreStudy(node) {
  router.push('/student/pre-study')
}

function handleResize() {
  if (chart) chart.resize()
}

onMounted(async () => {
  loading.value = true
  try {
    chapters.value = await (mode === 'teacher' ? getTeacherKnowledgeGraphChapters() : getStudentKnowledgeGraphChapters())
    const currentChapter = chapters.value.find(chapter => chapter.chapterOrder === 3) || chapters.value[0]
    if (!currentChapter) {
      ElMessage.warning('当前课程暂无章节数据')
      return
    }
    selectedChapterId.value = currentChapter.id
    await loadData()
  } catch (error) {
    ElMessage.error(error.message || '章节列表加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) chart.dispose()
})
</script>

<style scoped>
.graph-container {
  width: 100%;
  height: calc(100vh - 280px);
  min-height: 460px;
}

.graph-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
}

.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.node-detail .node-header {
  border-left: 4px solid #409EFF;
  padding-left: 12px;
  margin-bottom: 12px;
}

.node-detail .node-header h3 {
  margin: 0 0 6px 0;
  font-size: 16px;
}

.node-desc {
  color: #606266;
  font-size: 13px;
  line-height: 1.7;
  margin: 10px 0;
}

.node-section {
  margin-top: 14px;
}

.edge-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 13px;
}

.edge-target {
  color: #409EFF;
  cursor: pointer;
}

.source-item {
  display: flex;
  align-items: center;
  margin-top: 6px;
  color: #606266;
}
</style>
