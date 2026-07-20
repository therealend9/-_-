import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: () => import('../views/login/LoginView.vue') },
    { path: '/register', component: () => import('../views/login/RegisterView.vue') },
    { path: '/forgot-password', component: () => import('../views/login/ForgotPassword.vue') },
    { path: '/student/course-selection', component: () => import('../views/student/CourseSelection.vue') },

    // ===== 学生端 =====
    {
      path: '/student',
      component: () => import('../layouts/StudentLayout.vue'),
      children: [
        { path: '', redirect: '/student/dashboard' },
        { path: 'dashboard', component: () => import('../views/student/StudentDashboard.vue') },
        { path: 'pre-study', component: () => import('../views/student/PreStudyCenter.vue') },
        { path: 'pre-study/:chapterId', component: () => import('../views/student/PreStudyDetail.vue') },
	        { path: 'pre-study-quiz', component: () => import('../views/student/PreStudyQuiz.vue') },
	        { path: 'pre-study-demo', component: () => import('../views/student/PreStudyDemo.vue') },
        { path: 'class-interaction', component: () => import('../views/student/ClassInteractionCenter.vue') },
        { path: 'in-class-quiz', component: () => import('../views/student/InClassQuiz.vue') },
        { path: 'ai-qa', component: () => import('../views/student/AiQa.vue') },
        { path: 'source/:sourceId', component: () => import('../views/student/SourceTraceDetail.vue') },
        { path: 'feedback', component: () => import('../views/student/FeedbackCenter.vue') },
        { path: 'feedback/:assignmentId', component: () => import('../views/student/FeedbackDetail.vue') },
        { path: 'grading/:submissionId', component: () => import('../views/student/GradingDetail.vue') },
        { path: 'learning-report', component: () => import('../views/student/LearningReport.vue') },
        { path: 'notifications', component: () => import('../views/student/Notifications.vue') },
        { path: 'profile', component: () => import('../views/student/Profile.vue') },
        { path: 'knowledge-graph', component: () => import('../views/student/KnowledgeGraph.vue') }
      ]
    },

    // ===== 教师端 =====
    {
      path: '/teacher',
      component: () => import('../layouts/TeacherLayout.vue'),
      children: [
        { path: '', redirect: '/teacher/dashboard' },
        { path: 'dashboard', component: () => import('../views/teacher/TeacherDashboard.vue') },
        { path: 'lesson-design', component: () => import('../views/teacher/LessonDesign.vue') },
        { path: 'preclass-analytics', component: () => import('../views/teacher/PreClassAnalytics.vue') },
        { path: 'class-interaction', component: () => import('../views/teacher/ClassInteraction.vue') },
        { path: 'live-quiz', component: () => import('../views/teacher/LiveQuizGeneration.vue') },
        { path: 'grading-review', component: () => import('../views/teacher/GradingReview.vue') },
        { path: 'class-report', component: () => import('../views/teacher/ClassLearningReport.vue') },
        { path: 'resource-library', component: () => import('../views/teacher/ResourceLibrary.vue') },
        { path: 'knowledge-graph', component: () => import('../views/student/KnowledgeGraph.vue'), props: { mode: 'teacher' } },
        { path: 'quiz-bank', component: () => import('../views/teacher/QuizBank.vue') }
      ]
    },

    // ===== 管理端 =====
    {
      path: '/admin',
      component: () => import('../layouts/AdminLayout.vue'),
      children: [
        { path: '', redirect: '/admin/dashboard' },
        { path: 'dashboard', component: () => import('../views/admin/AdminDashboard.vue') },
        { path: 'user-management', component: () => import('../views/admin/UserManagement.vue') },
        { path: 'org-structure', component: () => import('../views/admin/OrgStructure.vue') },
        { path: 'org-structure/:nodeId', component: () => import('../views/admin/OrgNodeDetail.vue') },
        { path: 'users/batch', component: () => import('../views/admin/UserBatchImport.vue') },
        { path: 'users/:userId', component: () => import('../views/admin/UserDetail.vue') },
        { path: 'course-management', component: () => import('../views/admin/CourseClassManagement.vue') },
        { path: 'courses/:courseId/structure', component: () => import('../views/admin/CourseStructureDetail.vue') },
        { path: 'knowledge-base', component: () => import('../views/admin/KnowledgeBase.vue') },
        { path: 'knowledge-base/:sourceId', component: () => import('../views/admin/KnowledgeSourceDetail.vue') },
        { path: 'ai-review', component: () => import('../views/admin/AiReview.vue') },
        { path: 'ai-review/:reviewId', component: () => import('../views/admin/AiReviewDetail.vue') },
        { path: 'rubrics', component: () => import('../views/admin/RubricManagement.vue') },
        { path: 'assignment-management', component: () => import('../views/admin/AssignmentManagement.vue') },
        { path: 'assignments/:assignmentId', component: () => import('../views/admin/AssignmentDetail.vue') },
        { path: 'analytics', component: () => import('../views/admin/Analytics.vue') },
        { path: 'audit-log', component: () => import('../views/admin/AuditLog.vue') },
        { path: 'audit-log/:logId', component: () => import('../views/admin/AuditLogDetail.vue') },
        { path: 'system-settings', component: () => import('../views/admin/SystemSettings.vue') },
        { path: 'system-settings/:configKey', component: () => import('../views/admin/SystemConfigDetail.vue') },
        { path: 'role-permission', component: () => import('../views/admin/RolePermission.vue') },
        { path: 'role-permission/:roleId/permissions', component: () => import('../views/admin/RolePermissionDetail.vue') },
        { path: 'knowledge-graph', component: () => import('../views/admin/KnowledgeGraphManage.vue') }
      ]
    }
  ]
})

function readStoredUser() {
  try {
    return JSON.parse(sessionStorage.getItem('sizheng-user') || 'null')
  } catch {
    return null
  }
}

function routeRole(path) {
  const role = path.split('/').filter(Boolean)[0]
  return ['student', 'teacher', 'admin'].includes(role) ? role : ''
}

router.beforeEach((to) => {
  const user = readStoredUser()
  const requiredRole = routeRole(to.path)

  if (to.path === '/register') {
    return true
  }

  if (to.path === '/login') {
    return true
  }

  if (to.path === '/forgot-password') {
    return true
  }

  if (!requiredRole) return true

  if (!user?.token || !user?.role) {
    return {
      path: '/login',
      query: { redirect: to.fullPath }
    }
  }

  if (user.role !== requiredRole) {
    return `/${user.role}/dashboard`
  }

  return true
})

export default router
