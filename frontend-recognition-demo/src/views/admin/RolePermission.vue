<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 账号与组织 / 角色权限</span></div>
    <div class="page-header">
      <div>
        <h1>角色与权限管理</h1>
        <p class="page-desc">角色列表、权限矩阵、用户绑定和高危权限复核</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Plus" type="primary">新增角色</el-button>
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
              <strong>角色列表</strong>
              <el-tag type="info" size="small">{{ roles.length }} 个</el-tag>
            </div>
          </template>
          <div class="role-list">
            <div
              v-for="role in roles"
              :key="role.id"
              class="role-item"
              :class="{ active: activeRole === role.id }"
              @click="activeRole = role.id"
            >
              <div class="role-head">
                <strong>{{ role.name }}</strong>
                <el-tag size="small" :type="role.type === '系统' ? 'danger' : ''">{{ role.type }}</el-tag>
              </div>
              <div class="muted small">{{ role.desc }}</div>
              <div class="role-meta">
                <span>{{ role.userCount }} 个用户</span>
                <el-tag size="small" :type="role.statusType">{{ role.status }}</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never" class="card">
          <template #header>
            <div class="section-header">
              <div>
                <strong>{{ activeRoleData.name || '-' }} - 权限配置</strong>
                <div class="muted small">{{ activeRoleData.dataScope || '-' }} · {{ activeRoleData.owner || '-' }}</div>
              </div>
              <el-button :icon="View" type="primary" plain :disabled="!activeRole" @click="goDetail">查看详情</el-button>
            </div>
          </template>

          <div v-for="group in activePermissionGroups" :key="group.name" class="permission-group">
            <div class="permission-title">
              <strong>{{ group.name }}</strong>
              <el-tag type="info" size="small">{{ group.grantedCount }}/{{ group.permissions.length }}</el-tag>
            </div>
            <el-divider style="margin: 10px 0" />
            <div class="permission-list">
              <el-checkbox
                v-for="permission in group.permissions"
                :key="permission.key"
                :model-value="permission.granted"
                border
                size="small"
                @change="(checked) => togglePermission(permission.key, checked)"
              >
                {{ permission.label }}
              </el-checkbox>
            </div>
          </div>

          <el-divider />
          <div class="action-row">
            <el-button :disabled="saving" @click="resetPermissions">重置</el-button>
            <el-button type="primary" :loading="saving" @click="savePermissions">保存权限</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getRolePermissions, saveRolePermissions } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const activeRole = ref('')
const stats = ref([])
const roles = ref([])
const permissionGroups = ref([])
const editablePermissionKeys = ref([])

const activeRoleData = computed(() => roles.value.find((role) => role.id === activeRole.value) || {})

const activePermissionGroups = computed(() => permissionGroups.value.map((group) => {
  const permissions = group.permissions.map((permission) => ({
    ...permission,
    granted: editablePermissionKeys.value.includes(permission.key)
  }))

  return {
    ...group,
    permissions,
    grantedCount: permissions.filter((permission) => permission.granted).length
  }
}))

function currentRolePermissionKeys() {
  return permissionGroups.value.flatMap((group) => group.permissions
    .filter((permission) => Boolean(permission.grants?.[activeRole.value]))
    .map((permission) => permission.key))
}

function syncEditablePermissions() {
  editablePermissionKeys.value = currentRolePermissionKeys()
}

function togglePermission(key, checked) {
  if (checked) {
    if (!editablePermissionKeys.value.includes(key)) editablePermissionKeys.value.push(key)
    return
  }

  editablePermissionKeys.value = editablePermissionKeys.value.filter((item) => item !== key)
}

function resetPermissions() {
  syncEditablePermissions()
}

async function loadRoles() {
  const data = await getRolePermissions()
  stats.value = data.stats || []
  roles.value = data.roles || []
  permissionGroups.value = data.permissionGroups || []
  if (!activeRole.value) activeRole.value = roles.value[0]?.id || ''
  syncEditablePermissions()
}

async function savePermissions() {
  if (saving.value || !activeRole.value) return

  saving.value = true
  try {
    const data = await saveRolePermissions(activeRole.value, editablePermissionKeys.value)
    ElMessage.success(data.message || '角色权限已保存')
    await loadRoles()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '保存角色权限失败')
  } finally {
    saving.value = false
  }
}

function goDetail() {
  if (!activeRole.value) return
  router.push(`/admin/role-permission/${activeRole.value}/permissions`)
}

watch(activeRole, syncEditablePermissions)

onMounted(() => runPageLoad(loading, loadRoles))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.section-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.role-list { display: flex; flex-direction: column; gap: 8px; }
.role-item {
  padding: 14px; border-radius: 10px; cursor: pointer;
  border: 1px dashed transparent; transition: all 0.2s;
}
.role-item:hover { background: var(--soft); }
.role-item.active { background: var(--active); border-color: #606060; }
.role-head, .role-meta, .permission-title, .action-row {
  display: flex; justify-content: space-between; align-items: center; gap: 10px;
}
.role-meta { margin-top: 8px; color: var(--muted); font-size: 12px; }
.permission-group { margin-bottom: 20px; }
.permission-list { display: flex; flex-wrap: wrap; gap: 10px; }
.action-row { justify-content: flex-end; }
</style>
