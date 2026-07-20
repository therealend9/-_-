<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 账号与组织 / 用户管理</span></div>
    <div class="page-header">
      <div>
        <h1>用户管理</h1>
        <p class="page-desc">账号、角色、课程班级与状态治理</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Upload" @click="router.push('/admin/users/batch')">批量导入</el-button>
        <el-button :icon="Plus" type="primary">新增用户</el-button>
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

    <el-card shadow="never" class="card" style="margin-top: 20px">
      <template #header>
        <div class="table-header">
          <div class="filters">
            <el-select v-model="roleFilter" style="width: 120px" clearable placeholder="角色">
              <el-option label="学生" value="student" />
              <el-option label="教师" value="teacher" />
              <el-option label="管理员" value="admin" />
            </el-select>
            <el-select v-model="statusFilter" style="width: 120px" clearable placeholder="状态">
              <el-option label="正常" value="active" />
              <el-option label="禁用" value="disabled" />
            </el-select>
            <el-input v-model="search" placeholder="搜索姓名/账号/编号" style="width: 240px" clearable />
          </div>
          <span class="muted small">共 {{ filteredUsers.length }} 条记录</span>
        </div>
      </template>

      <el-table :data="filteredUsers" empty-text="暂无用户" style="width: 100%">
        <el-table-column prop="userCode" label="编号" width="90" />
        <el-table-column prop="account" label="账号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.roleCode)" size="small">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dept" label="院系/部门" min-width="150" />
        <el-table-column prop="className" label="班级/范围" min-width="150" />
        <el-table-column prop="course" label="关联课程" min-width="170" />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.statusCode === 'active'"
              :loading="statusLoading === row.id"
              :disabled="Boolean(statusLoading)"
              active-color="#67C23A"
              inactive-color="#F56C6C"
              @change="(value) => handleStatusChange(row, value)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="lastLogin" label="最后登录" width="150" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button :icon="View" size="small" @click="router.push(`/admin/users/${row.id}`)">查看</el-button>
            <el-button :icon="Key" size="small" type="primary">重置</el-button>
            <el-button
              :icon="CircleClose"
              size="small"
              :type="row.statusCode === 'active' ? 'danger' : 'success'"
              :loading="statusLoading === row.id"
              :disabled="Boolean(statusLoading)"
              @click="handleStatusChange(row, row.statusCode !== 'active')"
            >
              {{ row.statusCode === 'active' ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <el-pagination layout="prev, pager, next" :total="total" background size="small" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CircleClose, Key, Plus, Upload, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getUsers, updateUserStatus } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const statusLoading = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const search = ref('')
const stats = ref([])
const users = ref([])
const total = ref(0)

const filteredUsers = computed(() => users.value.filter((item) => {
  const keyword = search.value.trim().toLowerCase()
  const matchesRole = !roleFilter.value || item.roleCode === roleFilter.value
  const matchesStatus = !statusFilter.value || item.statusCode === statusFilter.value
  const matchesKeyword = !keyword ||
    item.name.toLowerCase().includes(keyword) ||
    item.account.toLowerCase().includes(keyword) ||
    item.userCode.toLowerCase().includes(keyword)

  return matchesRole && matchesStatus && matchesKeyword
}))

function roleTagType(roleCode) {
  if (roleCode === 'teacher') return 'success'
  if (roleCode === 'admin') return 'warning'
  return ''
}

async function loadUsers() {
  const data = await getUsers()
  stats.value = data.stats || []
  users.value = data.users || []
  total.value = data.total || 0
}

async function handleStatusChange(row, enabled) {
  if (statusLoading.value) return

  statusLoading.value = row.id
  try {
    const data = await updateUserStatus(row.id, enabled ? 'active' : 'disabled')
    ElMessage.success(data.message || '用户状态已更新')
    await loadUsers()
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.message || '更新用户状态失败')
  } finally {
    statusLoading.value = ''
  }
}

onMounted(() => runPageLoad(loading, loadUsers))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.muted.small { font-size: 12px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; }
.header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.table-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.filters { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.pagination-row { margin-top: 16px; text-align: right; }
</style>
