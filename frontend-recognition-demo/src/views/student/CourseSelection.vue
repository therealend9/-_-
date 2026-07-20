<template>
  <main class="course-selection-page">
    <header class="course-selection-header">
      <button class="brand" type="button" @click="logout">
        <span class="brand-mark">MA</span><span>马原智学</span>
      </button>
      <button class="logout" type="button" @click="logout">退出登录</button>
    </header>

    <section class="selection-content">
      <p class="eyebrow">MY LEARNING SPACE</p>
      <h1>选择一门课程，开始学习</h1>
      <div class="intro-row">
        <p class="intro">课程、班级、任务和 AI 问答会以你当前选择的课程为上下文。</p>
        <button class="add-course" type="button" @click="adding = !adding">+ 添加课程</button>
      </div>

      <form v-if="adding" class="add-course-panel" @submit.prevent="addCourse">
        <label for="course-code">课程代码</label>
        <input id="course-code" v-model="courseCode" maxlength="50" placeholder="例如：MY001" autocomplete="off">
        <button type="submit" :disabled="submitting">{{ submitting ? '正在添加…' : '添加' }}</button>
      </form>

      <div v-if="loading" class="state-card">正在加载你的课程…</div>
      <div v-else-if="courses.length === 0" class="state-card">暂未加入课程，请联系教师或管理员为你添加班级。</div>
      <div v-else class="course-grid">
        <article v-for="course in courses" :key="course.classId" class="course-card">
          <div class="course-card-top"><span class="course-code">{{ course.code }}</span><span class="semester">{{ course.semester || '本学期' }}</span></div>
          <h2>{{ course.name }}</h2>
          <p class="description">{{ course.description || '进入课程后查看学习任务、课堂互动和课程 AI。' }}</p>
          <dl>
            <div><dt>教学班</dt><dd>{{ course.className }}</dd></div>
            <div><dt>任课教师</dt><dd>{{ course.teacherName || '待安排' }}</dd></div>
          </dl>
          <button class="enter-course" type="button" @click="enterCourse(course)">进入课程 <span>→</span></button>
        </article>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { getStudentCourseSelection, joinStudentCourse } from '../../api/student.js'

const router = useRouter()
const courses = ref([])
const loading = ref(true)
const adding = ref(false)
const courseCode = ref('')
const submitting = ref(false)

onMounted(loadCourses)

async function loadCourses() {
  try {
    courses.value = await getStudentCourseSelection()
  } catch (error) {
    ElMessage.error(error.message || '课程加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function addCourse() {
  const code = courseCode.value.trim()
  if (!code) {
    ElMessage.warning('请输入课程代码')
    return
  }

  submitting.value = true
  try {
    const result = await joinStudentCourse(code)
    ElMessage.success(result.message || '课程添加成功')
    courseCode.value = ''
    adding.value = false
    await loadCourses()
  } catch (error) {
    ElMessage.error(error.message || '添加课程失败')
  } finally {
    submitting.value = false
  }
}

function enterCourse(course) {
  sessionStorage.setItem('sizheng-active-course', JSON.stringify({
    courseId: course.courseId,
    classId: course.classId,
    code: course.code,
    name: course.name,
    className: course.className,
    semester: course.semester
  }))
  router.replace('/student/dashboard')
}

function logout() {
  sessionStorage.removeItem('sizheng-user')
  sessionStorage.removeItem('sizheng-active-course')
  router.replace('/login')
}
</script>

<style scoped>
.course-selection-page { min-height: 100vh; color: #172a52; background: radial-gradient(circle at 82% 15%, #dfe9ff 0, transparent 28%), linear-gradient(135deg, #f4f8ff, #fff 52%, #edf4ff); }
.course-selection-header { height: 76px; display: flex; align-items: center; justify-content: space-between; padding: 0 clamp(24px, 6vw, 92px); border-bottom: 1px solid #dfe7f5; background: rgba(255,255,255,.74); }
.brand, .logout { border: 0; background: transparent; cursor: pointer; color: #1f3e78; font-size: 16px; font-weight: 700; }.brand { display: inline-flex; align-items: center; gap: 10px; font-size: 19px; }.brand-mark { display: inline-grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; color: #fff; font-size: 13px; background: linear-gradient(135deg, #396fc9, #173d81); }.logout { color: #60708e; font-size: 14px; font-weight: 600; }
.selection-content { width: min(1120px, calc(100% - 48px)); margin: 0 auto; padding: clamp(58px, 10vh, 110px) 0 72px; }.eyebrow { margin: 0 0 10px; color: #4b79cc; font-size: 13px; font-weight: 800; letter-spacing: .14em; }h1 { margin: 0; color: #122b59; font-size: clamp(30px, 4vw, 46px); letter-spacing: -.035em; }.intro-row { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin: 18px 0 24px; }.intro { margin: 0; color: #697996; font-size: 17px; }.add-course { flex: 0 0 auto; border: 1px solid #3973d1; border-radius: 10px; padding: 10px 14px; cursor: pointer; color: #3269c2; background: #f5f8ff; font-size: 15px; font-weight: 700; }.add-course:hover { background: #eaf1ff; }.add-course-panel { display: grid; grid-template-columns: auto minmax(160px, 300px) auto; align-items: center; gap: 12px; margin: 0 0 26px; border: 1px solid #dce6f6; border-radius: 14px; padding: 14px 16px; background: #fff; }.add-course-panel label { color: #536785; font-size: 14px; font-weight: 700; }.add-course-panel input { min-width: 0; border: 1px solid #ccd9ee; border-radius: 8px; padding: 10px 12px; color: #243d6b; font: inherit; }.add-course-panel input:focus { outline: 2px solid #b9d1fb; border-color: #5589dd; }.add-course-panel button { border: 0; border-radius: 8px; padding: 10px 17px; cursor: pointer; color: #fff; background: #3973d1; font-weight: 700; }.add-course-panel button:disabled { opacity: .65; cursor: wait; }
.course-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 22px; }.course-card, .state-card { border: 1px solid #dce6f6; border-radius: 20px; background: rgba(255,255,255,.92); box-shadow: 0 18px 45px rgba(37, 73, 134, .09); }.course-card { padding: 26px; display: flex; min-height: 292px; flex-direction: column; transition: transform .2s ease, box-shadow .2s ease; }.course-card:hover { transform: translateY(-4px); box-shadow: 0 24px 48px rgba(37, 73, 134, .15); }.course-card-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }.course-code { border-radius: 999px; padding: 5px 10px; color: #3165bd; background: #eaf2ff; font-size: 13px; font-weight: 800; }.semester { color: #8a98ad; font-size: 13px; }h2 { margin: 24px 0 11px; color: #172d5b; font-size: 23px; line-height: 1.35; }.description { margin: 0; color: #6d7e9c; font-size: 15px; line-height: 1.75; }
dl { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0 22px; }dl div { min-width: 0; }dt { margin-bottom: 5px; color: #99a6ba; font-size: 12px; }dd { margin: 0; overflow: hidden; color: #425577; font-size: 14px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }.enter-course { display: flex; align-items: center; justify-content: space-between; width: 100%; margin-top: auto; border: 0; border-radius: 11px; padding: 13px 16px; cursor: pointer; color: #fff; background: #3973d1; font-size: 16px; font-weight: 700; }.enter-course:hover { background: #2d63bb; }.enter-course span { font-size: 20px; line-height: 1; }.state-card { padding: 30px; color: #677895; font-size: 16px; }
@media (max-width: 600px) { .course-selection-header { padding: 0 20px; }.selection-content { width: min(100% - 32px, 1120px); padding-top: 52px; }.intro-row { align-items: flex-start; flex-direction: column; }.intro { font-size: 15px; }.add-course-panel { grid-template-columns: 1fr; }.course-card { padding: 22px; } }
</style>
