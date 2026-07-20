<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 账号与组织 / 权限详情</span></div>

    <div class="page-header">
      <div>
        <h1>{{ role.name }}</h1>
        <p class="page-desc">{{ role.id }} · {{ role.type }} · {{ role.dataScope }}</p>
      </div>
      <div class="header-actions">
        <el-button :icon="ArrowLeft" @click="router.push('/admin/role-permission')">返回列表</el-button>
        <el-button :icon="RefreshRight">同步权限</el-button>
        <el-button :icon="Edit" type="primary">编辑权限</el-button>
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
              <strong>角色档案</strong>
              <div class="tag-row">
                <el-tag :type="role.type === '系统' ? 'danger' : ''">{{ role.type }}</el-tag>
                <el-tag :type="role.statusType">{{ role.status }}</el-tag>
              </div>
            </div>
          </template>
          <div class="profile-grid">
            <div v-for="item in profileItems" :key="item.label">
              <span class="muted small">{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
          <p class="desc-text">{{ role.desc }}</p>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>权限矩阵</strong>
              <el-tag type="info" size="small">{{ role.permissionCount }} 项已授权</el-tag>
            </div>
          </template>
          <div v-for="group in permissionGroups" :key="group.name" class="permission-group">
            <div class="permission-group-head">
              <strong>{{ group.name }}</strong>
              <el-tag type="info" size="small">{{ grantedCount(group) }}/{{ group.permissions.length }}</el-tag>
            </div>
            <div class="permission-grid">
              <div
                v-for="permission in group.permissions"
                :key="permission.key"
                class="permission-node"
                :class="{ granted: permission.granted }"
              >
                <div class="permission-node-head">
                  <strong>{{ permission.label }}</strong>
                  <el-tag size="small" :type="permission.type">{{ permission.status }}</el-tag>
                </div>
                <span class="muted small">{{ permission.key }} · {{ permission.level }}</span>
                <p>{{ permission.desc }}</p>
              </div>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header>
            <div class="section-header">
              <strong>原始权限配置</strong>
              <el-tag type="info" size="small">{{ role.id }}</el-tag>
            </div>
          </template>
          <pre class="raw-json">{{ formattedRawConfig }}</pre>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="section-header">
              <strong>绑定用户</strong>
              <el-tag type="info" size="small">{{ assignedUsers.length }} 条示例</el-tag>
            </div>
          </template>
          <div v-if="assignedUsers.length" class="user-list">
            <div v-for="user in assignedUsers" :key="user.id" class="user-item">
              <div>
                <strong>{{ user.name }}</strong>
                <div class="muted small">{{ user.account }} · {{ user.dept }}</div>
              </div>
              <el-tag size="small" :type="user.statusType">{{ user.status }}</el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无直接绑定用户" />
        </el-card>

        <el-card shadow="never" class="section-card" style="margin-top: 20px">
          <template #header><strong>合规检查</strong></template>
          <div v-for="item in complianceChecks" :key="item.name" class="check-item">
            <div class="check-head">
              <strong>{{ item.name }}</strong>
              <el-tag size="small" :type="item.type">{{ item.result }}</el-tag>
            </div>
            <p>{{ item.desc }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="section-card" style="margin-top: 20px">
      <template #header>
        <div class="section-header">
          <strong>变更历史</strong>
          <el-tag type="info" size="small">{{ changeHistory.length }} 条</el-tag>
        </div>
      </template>
      <el-table :data="changeHistory" style="width: 100%">
        <el-table-column prop="version" label="版本" width="90" />
        <el-table-column prop="operator" label="操作人" width="130" />
        <el-table-column prop="before" label="变更前" min-width="220" />
        <el-table-column prop="after" label="变更后" min-width="220" />
        <el-table-column prop="time" label="时间" width="160" />
        <el-table-column prop="status" label="状态" width="110" align="center" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Edit, RefreshRight } from '@element-plus/icons-vue'
import { getRolePermissionDetail } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const role = ref({})
const stats = ref([])
const permissionGroups = ref([])
const assignedUsers = ref([])
const changeHistory = ref([])
const complianceChecks = ref([])
const rawPermissionConfig = ref({})

const profileItems = computed(() => [
  { label: '角色编码', value: role.value.code || '-' },
  { label: '角色类型', value: role.value.type || '-' },
  { label: '数据范围', value: role.value.dataScope || '-' },
  { label: '负责人', value: role.value.owner || '-' },
  { label: '绑定用户', value: `${role.value.userCount || 0} 个` },
  { label: '最近更新', value: role.value.updatedAt || '-' }
])

const formattedRawConfig = computed(() => JSON.stringify(rawPermissionConfig.value, null, 2))

function grantedCount(group) {
  return group.permissions.filter((permission) => permission.granted).length
}

onMounted(() => runPageLoad(loading, async () => {
  const data = await getRolePermissionDetail(route.params.roleId)
  role.value = data.role || {}
  stats.value = data.stats || []
  permissionGroups.value = data.permissionGroups || []
  assignedUsers.value = data.assignedUsers || []
  changeHistory.value = data.changeHistory || []
  complianceChecks.value = data.complianceChecks || []
  rawPermissionConfig.value = data.rawPermissionConfig || {}
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
.section-header, .tag-row, .permission-group-head, .permission-node-head, .user-item, .check-head {
  display: flex; justify-content: space-between; align-items: center; gap: 10px;
}
.section-card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.profile-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.profile-grid div, .permission-node, .user-item, .check-item {
  background: var(--soft); border-radius: 10px; padding: 12px;
}
.profile-grid div { display: flex; flex-direction: column; gap: 6px; }
.desc-text { margin: 14px 0 0; font-size: 13px; line-height: 1.8; color: #4d4d4d; }
.permission-group { margin-bottom: 18px; }
.permission-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 10px; }
.permission-node { border: 1px dashed transparent; }
.permission-node.granted { border-color: #67C23A; background: #f2fbf4; }
.permission-node p, .check-item p {
  margin: 8px 0 0; color: #4d4d4d; font-size: 13px; line-height: 1.7;
}
.user-list { display: flex; flex-direction: column; gap: 10px; }
.check-item { margin-bottom: 10px; }
.raw-json {
  margin: 0; background: #2f2f2f; color: #f7f6f2; border-radius: 10px; padding: 14px;
  font-size: 12px; line-height: 1.7; overflow: auto;
}
</style>
