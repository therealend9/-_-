<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 账号与组织 / 组织节点详情</span></div>

    <div class="page-header">
      <div>
        <h1>{{ node.name }}</h1>
        <p class="page-desc">{{ node.id }} · {{ node.type }} · {{ node.owner }}</p>
      </div>
      <div class="header-actions">
        <el-button :icon="ArrowLeft" @click="router.push('/admin/org-structure')">返回组织树</el-button>
        <el-button :icon="RefreshRight">同步节点</el-button>
        <el-button :icon="Edit" type="primary">编辑节点</el-button>
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
              <strong>节点档案</strong>
              <div class="tag-row">
                <el-tag :type="typeTag(node.type)">{{ node.type }}</el-tag>
                <el-tag :type="node.statusType">{{ node.status }}</el-tag>
              </div>
            </div>
          </template>
          <div class="profile-grid">
            <div v-for="item in profileItems" :key="item.label">
              <span class="muted small">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
          <p class="desc-text">{{ node.desc }}</p>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>下级节点</strong>
              <el-tag type="info" size="small">{{ children.length }} 个</el-tag>
            </div>
          </template>
          <el-table :data="children" style="width: 100%">
            <el-table-column prop="name" label="节点名称" min-width="160" />
            <el-table-column prop="type" label="类型" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="typeTag(row.type)">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="owner" label="负责人" width="110" />
            <el-table-column prop="userCount" label="用户" width="80" align="center" />
            <el-table-column prop="classCount" label="班级" width="80" align="center" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.statusType">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button :icon="View" size="small" @click="router.push(`/admin/org-structure/${row.id}`)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>成员账号</strong>
              <el-tag type="info" size="small">{{ members.length }} 人</el-tag>
            </div>
          </template>
          <el-table :data="members" style="width: 100%">
            <el-table-column prop="name" label="姓名" width="110">
              <template #default="{ row }">
                <strong>{{ row.name }}</strong>
                <div class="muted" style="font-size: 11px">{{ row.account }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="role" label="角色" width="90" />
            <el-table-column prop="major" label="专业/方向" min-width="140" />
            <el-table-column prop="className" label="班级/部门" min-width="150" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.statusType">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>原始节点配置</strong>
              <el-tag type="info" size="small">{{ node.id }}</el-tag>
            </div>
          </template>
          <pre class="raw-json">{{ formattedRawNode }}</pre>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>治理规则</strong></template>
          <div v-for="item in governanceRules" :key="item.name" class="rule-item">
            <div class="rule-head">
              <strong>{{ item.name }}</strong>
              <el-tag size="small" :type="item.type">{{ item.result }}</el-tag>
            </div>
            <p>{{ item.desc }}</p>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>关联课程</strong></template>
          <div v-if="relatedCourses.length" class="mini-list">
            <div v-for="course in relatedCourses" :key="course.id" class="mini-item">
              <div>
                <strong>{{ course.name }}</strong>
                <div class="muted small">{{ course.code }} · {{ course.semester }}</div>
              </div>
              <el-tag size="small" :type="course.statusType">{{ course.status }}</el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无关联课程" />
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>教学班级</strong></template>
          <div v-if="boundClasses.length" class="mini-list">
            <div v-for="item in boundClasses" :key="item.id" class="mini-item">
              <div>
                <strong>{{ item.name }}</strong>
                <div class="muted small">{{ item.course }} · {{ item.teacher }}</div>
              </div>
              <span class="muted small">{{ item.studentCount }} 人</span>
            </div>
          </div>
          <el-empty v-else description="暂无教学班级" />
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>节点时间线</strong></template>
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
import { ArrowLeft, Edit, RefreshRight, View } from '@element-plus/icons-vue'
import { getOrgNodeDetail } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const node = ref({})
const stats = ref([])
const children = ref([])
const members = ref([])
const boundClasses = ref([])
const relatedCourses = ref([])
const governanceRules = ref([])
const timeline = ref([])
const rawNode = ref({})

const profileItems = computed(() => [
  { label: '节点 ID', value: node.value.id || '-' },
  { label: '上级节点', value: node.value.parentId || '根节点' },
  { label: '层级', value: String(node.value.level ?? '-') },
  { label: '负责人', value: node.value.owner || '-' },
  { label: '学生数量', value: String(node.value.studentCount || 0) },
  { label: '教师数量', value: String(node.value.teacherCount || 0) },
  { label: '教学班级', value: String(node.value.classCount || 0) },
  { label: '最近更新', value: node.value.updatedAt || '-' }
])

const formattedRawNode = computed(() => JSON.stringify(rawNode.value, null, 2))

function typeTag(type) {
  return {
    学校: 'danger',
    学院: 'success',
    专业: 'warning',
    班级: 'info',
    部门: ''
  }[type] || ''
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getOrgNodeDetail(route.params.nodeId)
  node.value = data.node || {}
  stats.value = data.stats || []
  children.value = data.children || []
  members.value = data.members || []
  boundClasses.value = data.boundClasses || []
  relatedCourses.value = data.relatedCourses || []
  governanceRules.value = data.governanceRules || []
  timeline.value = data.timeline || []
  rawNode.value = data.rawNode || {}
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
.section-header, .tag-row, .rule-head, .mini-item {
  display: flex; justify-content: space-between; align-items: center; gap: 10px;
}
.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.profile-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.profile-grid div, .rule-item, .mini-item {
  background: var(--soft); border-radius: 10px; padding: 12px;
}
.profile-grid div { display: flex; flex-direction: column; gap: 6px; }
.desc-text { margin: 14px 0 0; font-size: 13px; line-height: 1.8; color: #4d4d4d; }
.rule-item { margin-bottom: 10px; }
.rule-item p { margin: 8px 0 0; color: #4d4d4d; font-size: 13px; line-height: 1.7; }
.mini-list { display: flex; flex-direction: column; gap: 10px; }
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.raw-json {
  margin: 0; background: #2f2f2f; color: #f7f6f2; border-radius: 10px; padding: 14px;
  font-size: 12px; line-height: 1.7; overflow: auto;
}
</style>
