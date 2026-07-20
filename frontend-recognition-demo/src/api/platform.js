import {
  adminInfo,
  adminReminders,
  demoCourse,
  studentInfo,
  studentNotifications,
  teacherInfo,
  teacherReminders
} from '../mock/data.js'
import { isMockMode, request } from './http.js'
import { mockResolve } from './mockTransport.js'

export function getStudentShell() {
  if (!isMockMode()) {
    return request('/student/shell')
  }

  return mockResolve({
    info: studentInfo,
    notices: studentNotifications
  })
}

export function getTeacherShell() {
  if (!isMockMode()) {
    return request('/teacher/shell')
  }

  return mockResolve({
    info: teacherInfo,
    notices: teacherReminders
  })
}

export function getAdminShell() {
  if (!isMockMode()) {
    return request('/admin/shell')
  }

  return mockResolve({
    info: {
      ...adminInfo,
      course: '全校思政课程',
      semester: demoCourse.semester
    },
    notices: adminReminders
  })
}
