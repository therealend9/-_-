<template>
  <div v-loading="loading">
    <div class="breadcrumb"><span class="muted">学生端 / 课后反馈</span></div>
    <div class="page-header">
      <h1>课后反馈中心</h1>
      <p class="page-desc">每次课程结束后，系统自动生成课后反馈。点击查看预习小测、随堂测验、课中互动与PPT的综合情况。</p>
    </div>

    <div v-if="lessons.length === 0" class="empty-hint">
      <el-empty description="暂无课后反馈记录" :image-size="80" />
    </div>

    <div
      v-for="lesson in lessons" :key="lesson.id"
      class="lesson-card"
      @click="router.push(`/student/feedback/${lesson.id}`)"
    >
      <div class="lc-left">
        <span class="lc-score" :class="{ 'lc-score--high': lesson.overallScore >= 85 }">
          {{ lesson.overallScore }}
        </span>
      </div>
      <div class="lc-body">
        <div class="lc-top">
          <strong class="lc-title">{{ lesson.chapter }}</strong>
          <el-tag size="small" type="success">{{ lesson.status }}</el-tag>
        </div>
        <div class="lc-meta">{{ lesson.course }} · {{ lesson.teacher }} · {{ lesson.date }}</div>
        <div class="lc-tags">
          <el-tag size="small" v-for="t in lesson.tags" :key="t" effect="plain">{{ t }}</el-tag>
        </div>
      </div>
      <el-icon size="18" class="lc-arrow"><ArrowRight /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { onMounted, ref } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import { getFeedbackCenter } from '../../api/student.js'

const router = useRouter()
const loading = ref(false)
const lessons = ref([
  { id: 1, course: '马克思主义基本原理', chapter: '第三章：实践与认识及其发展规律', teacher: '王老师', date: '2026/07/07', overallScore: 83, tags: ['预习小测 85', '随堂测验 60', '课中互动 3次'], status: '已生成' },
  { id: 2, course: '马克思主义基本原理', chapter: '第二章：人类社会及其发展规律', teacher: '王老师', date: '2026/07/01', overallScore: 88, tags: ['预习小测 82', '随堂测验 80', '课中互动 2次'], status: '已生成' },
  { id: 3, course: '马克思主义基本原理', chapter: '第一章：物质世界及其发展规律', teacher: '王老师', date: '2026/06/24', overallScore: 90, tags: ['预习小测 90', '随堂测验 100', '课中互动 4次'], status: '已生成' }
])

onMounted(async () => {
  try {
    const data = await getFeedbackCenter()
    if (data && data.lessons && data.lessons.length > 0) {
      lessons.value = data.lessons
    }
  } catch (e) {
    console.error('加载课后反馈失败', e)
  }
})
</script>

<style scoped>
.breadcrumb { font-size: 12px; margin-bottom: 6px; }
.muted { color: var(--muted); }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.page-desc { font-size: 13px; color: var(--muted); margin-top: 4px; max-width: 65ch; }

.empty-hint { padding: 60px 0; text-align: center; }

.lesson-card {
  display: flex; align-items: center; gap: 18px;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 20px 22px; margin-bottom: 10px;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-normal) var(--ease-out),
              transform var(--duration-normal) var(--ease-out);
}
.lesson-card:hover {
  border-color: #909090; box-shadow: var(--shadow-md);
  transform: translateX(3px);
}

.lc-left { flex-shrink: 0; }
.lc-score {
  display: flex; align-items: center; justify-content: center;
  width: 52px; height: 52px; border-radius: 14px;
  font-size: 22px; font-weight: 800;
  background: var(--soft); color: var(--ink);
  transition: background var(--duration-fast) var(--ease-out);
}
.lc-score--high { background: var(--success-soft); color: var(--success); }
.lesson-card:hover .lc-score { background: var(--active); }
.lesson-card:hover .lc-score--high { background: var(--success-soft); }

.lc-body { flex: 1; min-width: 0; }
.lc-top { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.lc-title { font-size: 15px; font-weight: 700; letter-spacing: -0.2px; }
.lc-meta { font-size: 12px; color: var(--muted); margin-bottom: 8px; }
.lc-tags { display: flex; gap: 6px; flex-wrap: wrap; }

.lc-arrow {
  color: var(--muted); flex-shrink: 0;
  transition: transform var(--duration-fast) var(--ease-out),
              color var(--duration-fast) var(--ease-out);
}
.lesson-card:hover .lc-arrow { transform: translateX(3px); color: var(--ink); }
</style>
