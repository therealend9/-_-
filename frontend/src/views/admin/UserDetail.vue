<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 账号与组织 / 用户详情</span></div>

    <div class="page-header">
      <div>
        <h1>{{ user.name }}</h1>
        <p class="page-desc">{{ user.account }} · {{ user.dept }} · {{ user.role }}</p>
      </div>
      <div class="header-actions">
        <el-button :icon="ArrowLeft" @click="router.push('/admin/user-management')">返回列表</el-button>
        <el-button :icon="Key">重置密码</el-button>
        <el-button :icon="Edit" type="primary">编辑账号</el-button>
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
              <strong>账号档案</strong>
              <div class="tag-row">
                <el-tag :type="roleType">{{ user.role }}</el-tag>
                <el-tag :type="user.statusType">{{ user.status }}</el-tag>
              </div>
            </div>
          </template>

          <div class="profile-grid">
            <div v-for="item in profileItems" :key="item.label">
              <span class="muted small">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>课程与班级绑定</strong>
              <el-tag type="info" size="small">{{ courseBindings.length }} 项</el-tag>
            </div>
          </template>
          <el-table :data="courseBindings" style="width: 100%">
            <el-table-column prop="course" label="课程" min-width="180" />
            <el-table-column prop="className" label="班级/范围" min-width="160" />
            <el-table-column prop="role" label="身份" width="110" />
            <el-table-column prop="status" label="状态" width="120" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === '生效中' || row.status === '可管理' ? 'success' : 'info'">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header><strong>状态与安全</strong></template>
          <div v-for="item in security" :key="item.name" class="security-item">
            <div class="security-head">
              <strong>{{ item.name }}</strong>
              <el-tag size="small" :type="item.type">{{ item.result }}</el-tag>
            </div>
            <p>{{ item.desc }}</p>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>账号轨迹</strong></template>
          <el-timeline>
            <el-timeline-item v-for="item in timeline" :key="`${item.title}-${item.time}`" :timestamp="item.time">
              <div class="timeline-title">{{ item.title }}</div>
              <div class="muted small">{{ item.desc }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>权限范围</strong>
              <el-tag type="info" size="small">{{ user.dataScope }}</el-tag>
            </div>
          </template>
          <el-table :data="permissions" style="width: 100%">
            <el-table-column prop="name" label="权限名称" min-width="220" />
            <el-table-column prop="code" label="权限编码" width="150" />
            <el-table-column label="授权状态" width="120" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.type">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header><strong>治理日志</strong></template>
          <div v-if="auditLogs.length">
            <div v-for="item in auditLogs" :key="`${item.action}-${item.time}`" class="log-item">
              <strong>{{ item.action }}</strong>
              <span class="muted small">{{ item.operator }} · {{ item.time }}</span>
              <p>{{ item.detail }}</p>
            </div>
          </div>
          <el-empty v-else description="暂无治理日志" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Edit, Key } from '@element-plus/icons-vue'
import { getUserDetail } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const user = ref({})
const stats = ref([])
const security = ref([])
const permissions = ref([])
const courseBindings = ref([])
const timeline = ref([])
const auditLogs = ref([])

const roleType = computed(() => {
  if (user.value.roleCode === 'teacher') return 'success'
  if (user.value.roleCode === 'admin') return 'warning'
  return ''
})

const profileItems = computed(() => [
  { label: '用户编号', value: user.value.userCode || '-' },
  { label: '登录账号', value: user.value.account || '-' },
  { label: '所属院系', value: user.value.dept || '-' },
  { label: '专业/方向', value: user.value.major || '-' },
  { label: '班级/部门', value: user.value.className || '-' },
  { label: '关联课程', value: user.value.course || '-' },
  { label: '手机号', value: user.value.phone || '-' },
  { label: '邮箱', value: user.value.email || '-' },
  { label: '创建时间', value: user.value.createdAt || '-' },
  { label: '最后登录', value: user.value.lastLogin || '-' }
])

onMounted(() => runPageLoad(loading, async () => {
  const data = await getUserDetail(route.params.userId)
  user.value = data.user || {}
  stats.value = data.stats || []
  security.value = data.security || []
  permissions.value = data.permissions || []
  courseBindings.value = data.courseBindings || []
  timeline.value = data.timeline || []
  auditLogs.value = data.auditLogs || []
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
.profile-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.profile-grid div {
  background: var(--soft); border-radius: 10px; padding: 14px;
  display: flex; flex-direction: column; gap: 6px;
}
.security-item, .log-item {
  background: var(--soft); border-radius: 10px; padding: 12px; margin-bottom: 10px;
}
.security-head {
  display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px;
}
.security-item p, .log-item p {
  font-size: 13px; line-height: 1.7; color: #4d4d4d; margin: 0;
}
.timeline-title { font-weight: 800; margin-bottom: 4px; }
.log-item { display: flex; flex-direction: column; gap: 6px; }
</style>
