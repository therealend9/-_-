<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">学生端 / 个人中心 / 账户设置</span></div>
    <div class="page-header"><h1>个人中心</h1></div>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="8">
        <el-card shadow="never" class="card" style="text-align: center">
          <el-avatar :size="80" style="background: #e6e4de; color: #2f2f2f; font-size: 30px; font-weight: 800">{{ profile.avatarText }}</el-avatar>
          <h3 style="margin: 12px 0 4px">{{ profile.name }}</h3>
          <p class="muted">{{ profile.grade }} · {{ profile.college }}</p>
          <el-divider />
          <div class="info-row"><span>学号</span><span>{{ profile.studentNo }}</span></div>
          <div class="info-row"><span>当前课程</span><span>{{ profile.course }}</span></div>
          <div class="info-row"><span>学期</span><span>{{ profile.semester }}</span></div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never" class="card">
          <template #header><strong>账户安全</strong></template>
          <el-form label-width="80px">
            <el-form-item label="手机号"><el-input v-model="profile.phone" /></el-form-item>
            <el-form-item label="邮箱"><el-input v-model="profile.email" /></el-form-item>
            <el-form-item label="密码"><el-input type="password" value="********" /></el-form-item>
            <el-form-item><el-button type="primary">保存修改</el-button></el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" class="card" style="margin-top: 20px">
          <template #header><strong>学习数据</strong></template>
          <div style="display: flex; gap: 16px">
            <div class="data-box" v-for="d in stats" :key="d.label">
              <div class="data-val">{{ d.value }}</div>
              <div class="muted small">{{ d.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getStudentProfile } from '../../api/student.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const loading = ref(true)
const profile = ref({
  name: '学生',
  avatarText: '学',
  grade: '2023级',
  college: '马克思主义学院',
  studentNo: '-',
  course: '马克思主义基本原理',
  semester: '2025-2026-2',
  phone: '',
  email: ''
})
const stats = ref([])

onMounted(() => runPageLoad(loading, async () => {
  const data = await getStudentProfile()
  profile.value = data.profile || profile.value
  stats.value = data.stats || []
}))
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); font-size: 13px; }
.muted.small { font-size: 12px; }
.page-header h1 { font-size: 26px; font-weight: 800; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.info-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; color: var(--muted); }
.data-box { flex: 1; text-align: center; padding: 16px; background: var(--soft); border-radius: 12px; border: 1px dashed var(--line); }
.data-val { font-size: 24px; font-weight: 800; margin-bottom: 4px; }
</style>

