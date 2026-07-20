<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">管理端 / 账号与组织 / 课程班级管理</span></div>
    <div class="page-header">
      <div>
        <h1>课程与班级管理</h1>
        <p class="page-desc">课程结构、教学班级、教师与学生覆盖</p>
      </div>
      <div class="header-actions">
        <el-button :icon="DocumentAdd" type="primary">新建课程</el-button>
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
              <strong>课程列表</strong>
              <el-tag type="info" size="small">{{ courses.length }} 门</el-tag>
            </div>
          </template>
          <div class="course-list">
            <div
              v-for="courseItem in courses"
              :key="courseItem.id"
              class="course-item"
              :class="{ active: activeCourse === courseItem.id }"
              @click="activeCourse = courseItem.id"
            >
              <div class="course-head">
                <strong>{{ courseItem.name }}</strong>
                <el-tag size="small" :type="courseItem.statusType">{{ courseItem.status }}</el-tag>
              </div>
              <div class="muted small">{{ courseItem.code }} · {{ courseItem.semester }}</div>
              <div class="course-meta">
                <span>{{ courseItem.classCount }} 个班级</span>
                <span>{{ courseItem.studentCount }} 名学生</span>
                <span>{{ courseItem.chapterCount }} 章</span>
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
                <strong>{{ activeCourseInfo?.name || '班级列表' }}</strong>
                <div class="muted small">资源 {{ activeCourseInfo?.resourceCount || 0 }} 项 · 章节 {{ activeCourseInfo?.chapterCount || 0 }} 个</div>
              </div>
              <div class="header-actions">
                <el-button :icon="View" size="small" @click="router.push(`/admin/courses/${activeCourse}/structure`)">查看结构</el-button>
                <el-button :icon="Plus" type="primary" size="small">添加班级</el-button>
              </div>
            </div>
          </template>
          <el-table :data="activeClasses" style="width: 100%">
            <el-table-column prop="name" label="班级名称" min-width="150" />
            <el-table-column prop="teacher" label="授课教师" width="110" />
            <el-table-column prop="studentCount" label="学生人数" width="90" align="center" />
            <el-table-column prop="semester" label="学期" width="120" />
            <el-table-column prop="schedule" label="上课时间" min-width="140" />
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.statusType" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="210" fixed="right">
              <template #default>
                <el-button size="small">编辑</el-button>
                <el-button size="small">学生名单</el-button>
                <el-button size="small" type="danger">归档</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { DocumentAdd, Plus, View } from '@element-plus/icons-vue'
import { getCourses } from '../../api/admin.js'
import { runPageLoad } from '../../utils/pageLoad.js'

const router = useRouter()
const loading = ref(true)
const activeCourse = ref(null)
const stats = ref([])
const courses = ref([])
const classes = ref([])

const activeCourseInfo = computed(() => courses.value.find((item) => item.id === activeCourse.value))
const activeClasses = computed(() => classes.value.filter((item) => item.courseId === activeCourse.value))

onMounted(() => runPageLoad(loading, async () => {
  const data = await getCourses()
  stats.value = data.stats || []
  courses.value = data.courses || []
  classes.value = data.classes || []
  activeCourse.value = courses.value[0]?.id || null
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
.section-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.stat-card {
  background: var(--soft); border-radius: 14px; padding: 18px 20px;
  border: 1px dashed var(--line); text-align: center;
}
.stat-num { font-size: 30px; font-weight: 800; margin: 4px 0; }
.card { border-radius: 14px; border: 1px solid var(--line); background: var(--card); }
.course-list { display: flex; flex-direction: column; gap: 8px; }
.course-item {
  padding: 14px; border-radius: 10px; cursor: pointer; border: 1px dashed transparent;
  transition: all 0.2s; background: transparent;
}
.course-item:hover { background: var(--soft); }
.course-item.active { background: var(--active); border-color: #606060; }
.course-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 6px; }
.course-head strong { line-height: 1.4; }
.course-meta { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; color: var(--muted); font-size: 12px; }
</style>
