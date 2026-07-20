<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 账号与组织 / 组织架构</span></div>
    <div class="page-header">
      <div>
        <h1>组织架构管理</h1>
        <p class="page-desc">学院、专业、班级、部门与账号归属关系</p>
      </div>
      <div class="header-actions">
        <el-button :icon="RefreshRight">同步组织</el-button>
        <el-button :icon="Plus" type="primary">新增节点</el-button>
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
      <el-col :span="8">
        <el-card shadow="never" class="card">
          <template #header>
            <div class="section-header">
              <strong>组织树</strong>
              <el-tag type="info" size="small">{{ nodes.length }} 个节点</el-tag>
            </div>
          </template>
          <el-tree
            :data="tree"
            node-key="id"
            default-expand-all
            highlight-current
            :props="treeProps"
            @node-click="handleNodeClick"
          >
            <template #default="{ data }">
              <div class="tree-node">
                <span>{{ data.name }}</span>
                <el-tag size="small" :type="typeTag(data.type)">{{ data.type }}</el-tag>
              </div>
            </template>
          </el-tree>
        </el-card>

        <el-card shadow="never" class="card" style="margin-top: 20px">
          <template #header><strong>治理检查</strong></template>
          <div v-for="item in qualityChecks" :key="item.name" class="check-item">
            <div class="check-head">
              <strong>{{ item.name }}</strong>
              <el-tag size="small" :type="item.type">{{ item.result }}</el-tag>
            </div>
            <p>{{ item.desc }}</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never" class="card">
          <template #header>
            <div class="section-header">
              <div>
                <strong>组织节点</strong>
                <div class="muted small">{{ activeNode.name || '全部组织' }} · {{ filteredNodes.length }} 条</div>
              </div>
              <el-input v-model="keyword" placeholder="搜索节点、负责人、类型" size="small" style="width: 240px" clearable />
            </div>
          </template>
          <el-table :data="filteredNodes" style="width: 100%">
            <el-table-column prop="name" label="节点名称" min-width="170">
              <template #default="{ row }">
                <strong>{{ row.name }}</strong>
                <div class="muted" style="font-size: 11px">{{ row.desc }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="typeTag(row.type)">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="owner" label="负责人" width="110" />
            <el-table-column prop="userCount" label="用户" width="80" align="center" />
            <el-table-column prop="classCount" label="班级" width="80" align="center" />
            <el-table-column prop="courseCount" label="课程" width="80" align="center" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.statusType">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right" align="center">
              <template #default="{ row }">
                <el-button :icon="View" size="small" @click="router.push(`/admin/org-structure/${row.id}`)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>最近变更</strong>
              <el-tag type="info" size="small">{{ recentChanges.length }} 条</el-tag>
            </div>
          </template>
          <el-table :data="recentChanges" style="width: 100%">
            <el-table-column prop="action" label="动作" width="130" />
            <el-table-column prop="operator" label="操作人" width="120" />
            <el-table-column prop="target" label="对象" min-width="180" />
            <el-table-column prop="time" label="时间" width="150" />
            <el-table-column prop="status" label="状态" width="100" align="center" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, RefreshRight, View } from '@element-plus/icons-vue'
import { getOrgStructure } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const keyword = ref('')
const stats = ref([])
const nodes = ref([])
const tree = ref([])
const activeNode = ref({})
const recentChanges = ref([])
const qualityChecks = ref([])
const treeProps = { label: 'name', children: 'children' }

const scopedNodeIds = computed(() => {
  if (!activeNode.value.id) return []
  const ids = [activeNode.value.id]
  const collect = (parentId) => {
    nodes.value
      .filter((item) => item.parentId === parentId)
      .forEach((item) => {
        ids.push(item.id)
        collect(item.id)
      })
  }
  collect(activeNode.value.id)
  return ids
})

const filteredNodes = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  const scoped = scopedNodeIds.value.length
    ? nodes.value.filter((item) => scopedNodeIds.value.includes(item.id))
    : nodes.value

  if (!text) return scoped
  return scoped.filter((item) => [item.name, item.type, item.owner, item.desc].some((field) => String(field || '').toLowerCase().includes(text)))
})

function typeTag(type) {
  return {
    学校: 'danger',
    学院: 'success',
    专业: 'warning',
    班级: 'info',
    部门: ''
  }[type] || ''
}

function handleNodeClick(data) {
  activeNode.value = data
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getOrgStructure()
  stats.value = data.stats || []
  nodes.value = data.nodes || []
  tree.value = data.tree || []
  recentChanges.value = data.recentChanges || []
  qualityChecks.value = data.qualityChecks || []
  activeNode.value = nodes.value[0] || {}
}))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.section-header, .tree-node, .check-head {
  display: flex; justify-content: space-between; align-items: center; gap: 10px;
}
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.tree-node { width: 100%; padding-right: 8px; }
.check-item {
  background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px;
}
.check-item p { margin: 8px 0 0; color: #4d4d4d; font-size: 13px; line-height: 1.7; }
</style>
