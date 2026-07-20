<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 知识治理 / 知识图谱管理</span></div>
    <div class="page-header">
      <h1>知识图谱管理</h1>
      <div class="header-actions">
        <el-button @click="resetZoom">重置视图</el-button>
        <el-button type="primary" @click="loadData">刷新数据</el-button>
      </div>
    </div>
    <p class="page-desc">管理和维护课程知识图谱，可视化编辑知识点节点和逻辑关系，绑定学习资源</p>

    <!-- 课程选择 -->
    <div style="margin-top: 16px">
      <el-select v-model="selectedCourseId" placeholder="选择课程" @change="loadData" style="width: 240px">
        <el-option label="马克思主义基本原理" :value="1" />
      </el-select>
      <el-tag v-for="ch in chapters" :key="ch.id" style="margin-left: 8px" effect="plain">
        第{{ ch.chapterOrder }}章 · {{ ch.title }}（{{ ch.nodeCount }} 节点）
      </el-tag>
    </div>

    <el-row :gutter="16" style="margin-top: 16px">
      <!-- 图谱可视化 -->
      <el-col :span="16">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <strong>知识关系图谱</strong>
              <div style="display: flex; gap: 6px">
                <el-tag v-for="r in relationTypes" :key="r.value" :color="relationColor(r.value)" effect="dark" size="small" style="color: #fff">{{ r.label }}</el-tag>
              </div>
            </div>
          </template>
          <div ref="chartRef" class="graph-container"></div>
          <div class="graph-stats">
            <span>节点：{{ nodes.length }} 个</span>
            <el-divider direction="vertical" />
            <span>关系：{{ edges.length }} 条</span>
          </div>
        </el-card>
      </el-col>

      <!-- 节点详情 / 列表 -->
      <el-col :span="8">
        <el-card shadow="never" class="section-card" style="min-height: 500px">
          <template #header>
            <el-tabs v-model="activeTab" style="margin: -4px 0 -10px 0">
              <el-tab-pane label="节点列表" name="list" />
              <el-tab-pane label="详情" name="detail" :disabled="!selectedNode" />
            </el-tabs>
          </template>

          <!-- 节点列表 -->
          <div v-if="activeTab === 'list'" class="node-list">
            <el-input v-model="nodeFilter" placeholder="搜索知识点..." size="small" clearable style="margin-bottom: 10px" />
            <div v-for="n in filteredNodes" :key="n.id"
                 class="node-list-item"
                 :class="{ active: selectedNode?.id === n.id }"
                 @click="selectNode(n)">
              <div class="node-list-name">
                <span class="node-dot" :style="{ background: n.color }"></span>
                {{ n.name }}
              </div>
              <div style="display: flex; gap: 4px; flex-wrap: wrap">
                <el-tag size="small" :color="n.color" effect="dark" style="color: #fff">{{ n.nodeTypeLabel }}</el-tag>
                <el-tag size="small" effect="plain">{{ n.difficultyLabel }}</el-tag>
              </div>
              <div class="node-list-chapter">{{ n.chapterTitle }}</div>
            </div>
          </div>

          <!-- 节点详情 -->
          <div v-else class="node-detail">
            <div class="node-header" :style="{ borderLeftColor: selectedNode?.color }">
              <h3>{{ selectedNode?.name }}</h3>
              <div style="display: flex; gap: 6px; flex-wrap: wrap">
                <el-tag size="small" :color="selectedNode?.color" effect="dark" style="color: #fff">{{ selectedNode?.nodeTypeLabel }}</el-tag>
                <el-tag size="small" effect="plain">{{ selectedNode?.difficultyLabel }}</el-tag>
              </div>
            </div>
            <p class="node-desc">{{ selectedNode?.description }}</p>
            <div class="node-meta">
              <div><strong>所属章节：</strong>{{ selectedNode?.chapterTitle }}</div>
              <div><strong>父节点：</strong>{{ parentName || '无（根节点）' }}</div>
              <div><strong>子节点：</strong>{{ childrenCount }} 个</div>
            </div>

            <div v-if="nodeDetail?.sources?.length" class="node-section">
              <strong style="font-size: 13px">绑定资源 ({{ nodeDetail.sources.length }})</strong>
              <div v-for="s in nodeDetail.sources" :key="s.id" class="source-item">
                <span>{{ s.title }}</span>
                <el-tag size="small" effect="plain">{{ s.type }}</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getAdminKnowledgeGraph, getAdminNodeDetail, getRelationTypes, getNodeTypes } from '../../api/knowledge-graph.js'

const chartRef = ref(null)
const loading = ref(false)
const activeTab = ref('list')
const selectedCourseId = ref(1)
const nodeFilter = ref('')

const chapters = ref([])
const nodes = ref([])
const edges = ref([])
const selectedNode = ref(null)
const nodeDetail = ref(null)
const relationTypes = ref([])
const nodeTypes = ref([])
let chart = null

const filteredNodes = computed(() => {
  if (!nodeFilter.value) return nodes.value
  const kw = nodeFilter.value.toLowerCase()
  return nodes.value.filter(n => n.name.toLowerCase().includes(kw) || (n.description || '').toLowerCase().includes(kw))
})

const parentName = computed(() => {
  if (!selectedNode.value?.parentId) return null
  const p = nodes.value.find(n => n.id === selectedNode.value.parentId)
  return p?.name || ''
})

const childrenCount = computed(() => {
  if (!selectedNode.value) return 0
  return nodes.value.filter(n => n.parentId === selectedNode.value.id).length
})

function relationColor(type) {
  const map = { contains: '#67C23A', prerequisite: '#409EFF', related: '#E6A23C', derives: '#F56C6C', applies: '#909399', contrasts: '#F56C6C' }
  return map[type] || '#409EFF'
}

function loadData() {
  loading.value = true
  Promise.all([
    getAdminKnowledgeGraph(selectedCourseId.value),
    getRelationTypes(),
    getNodeTypes()
  ]).then(([graph, relTypes, ndTypes]) => {
    chapters.value = graph.chapters || []
    nodes.value = graph.nodes || []
    edges.value = graph.edges || []
    relationTypes.value = relTypes || []
    nodeTypes.value = ndTypes || []
    loading.value = false
    nextTick(() => renderChart())
  }).catch(() => {
    loading.value = false
  })
}

function renderChart() {
  if (!chartRef.value) return
  if (chart) chart.dispose()

  chart = echarts.init(chartRef.value)

  const categories = [...new Set(nodes.value.map(n => n.nodeType))].map(type => ({
    name: type,
    itemStyle: { color: nodes.value.find(n => n.nodeType === type)?.color || '#409EFF' }
  }))

  chart.setOption({
    tooltip: { trigger: 'item', formatter(p) {
      if (p.dataType === 'node') return `<strong>${p.data.name}</strong><br/>${p.data.nodeTypeLabel || ''} · ${p.data.difficultyLabel || ''}`
      return p.data.label || p.data.relationLabel || ''
    }},
    legend: { bottom: 0, data: categories.map(c => c.name), textStyle: { fontSize: 11 } },
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: true, categories,
      data: nodes.value.map(n => ({
        id: n.id, name: n.name, category: n.nodeType,
        symbolSize: n.parentId ? 26 : 38,
        nodeTypeLabel: n.nodeTypeLabel, difficultyLabel: n.difficultyLabel,
        itemStyle: { color: n.color },
        label: { show: true, fontSize: n.parentId ? 10 : 12, fontWeight: n.parentId ? 'normal' : 'bold' }
      })),
      links: edges.value.map(e => ({
        source: e.source, target: e.target,
        label: { show: true, formatter: e.relationLabel, fontSize: 9 },
        lineStyle: { color: relationColor(e.relationType), width: Math.max(1, e.weight * 2), curveness: 0.2 }
      })),
      force: { repulsion: 350, gravity: 0.1, edgeLength: [100, 220], layoutAnimation: true },
      emphasis: { focus: 'adjacency', lineStyle: { width: 4 } }
    }]
  })

  chart.on('click', (params) => {
    if (params.dataType === 'node') {
      const node = nodes.value.find(n => n.id === params.data.id)
      if (node) selectNode(node)
    }
  })

  window.addEventListener('resize', handleResize)
}

function selectNode(node) {
  selectedNode.value = node
  activeTab.value = 'detail'

  getAdminNodeDetail(node.id).then(detail => {
    nodeDetail.value = detail
  }).catch(() => {
    nodeDetail.value = { sources: [], edges: [] }
  })
}

function resetZoom() {
  if (chart) chart.dispatchAction({ type: 'restore' })
}

function handleResize() {
  if (chart) chart.resize()
}

onMounted(loadData)

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) chart.dispose()
})
</script>

<style scoped>
.graph-container {
  width: 100%;
  height: calc(100vh - 310px);
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

.node-list { max-height: 480px; overflow-y: auto; }

.node-list-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
  margin-bottom: 6px;
}
.node-list-item:hover { background: #f5f7fa; }
.node-list-item.active { border-color: #409EFF; background: #ecf5ff; }

.node-list-name {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.node-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}

.node-list-chapter {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.node-detail .node-header {
  border-left: 4px solid #409EFF;
  padding-left: 12px;
  margin-bottom: 12px;
}
.node-detail .node-header h3 { margin: 0 0 6px 0; font-size: 16px; }
.node-desc { color: #606266; font-size: 13px; line-height: 1.7; margin: 10px 0; }
.node-meta { font-size: 13px; color: #606266; line-height: 1.8; }
.node-section { margin-top: 14px; }

.source-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 13px;
  padding: 6px 8px;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>
