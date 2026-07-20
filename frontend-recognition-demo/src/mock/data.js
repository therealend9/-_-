export const demoCourse = {
  name: '马克思主义基本原理',
  chapter: '实践与认识及其发展规律',
  semester: '2025-2026-2',
  college: '马克思主义学院',
  className: '2023级本科1班'
}

// ===== 学生端数据 =====
export const studentInfo = {
  name: '李明哲',
  grade: '2023级',
  course: demoCourse.name,
  semester: demoCourse.semester,
  college: demoCourse.college
}

export const studentTasks = [
  { title: '阅读章节导学', desc: demoCourse.chapter, status: '进行中', time: '预计 8 分钟' },
  { title: '完成预习小测', desc: '5 道概念辨析题', status: '待完成', time: '截止周四 22:00' },
  { title: '提交课前问题', desc: '围绕真理标准或实践观点', status: '待完成', time: '课前 12 小时前' },
  { title: '查看上次反馈', desc: '认识论材料分析已批改', status: '已完成', score: 88 }
]

export const studentNotifications = [
  { content: '《实践与认识及其发展规律》导学已发布', time: '今天' },
  { content: '本周预习任务截止周四 22:00', time: '昨天' },
  { content: 'AI问答已接入教材来源溯源', time: '3天前' }
]

export const learningPath = [
  { step: 1, title: '读导学', desc: '先看本节课目标、重点和学习路线', active: true },
  { step: 2, title: '学概念', desc: '理解实践、认识、真理、价值', active: false },
  { step: 3, title: '做小测', desc: '完成 5 道题并查看解析', active: false },
  { step: 4, title: '提问题', desc: '提交一个真实困惑给教师', active: false }
]

// ===== 教师端数据 =====
export const teacherInfo = {
  name: '王老师',
  course: demoCourse.name,
  semester: demoCourse.semester,
  college: demoCourse.college
}

export const teacherQueue = [
  { title: 'AI教案待审核', count: 4, level: '优先', color: '#E6A23C' },
  { title: '学生困惑待聚类', count: 18, level: '处理中', color: '#409EFF' },
  { title: '作业复核待完成', count: 12, level: '优先', color: '#E6A23C' }
]

export const teacherReminders = [
  '《实践与认识及其发展规律》教案待审核 4 条',
  '本节课 14:00 开始',
  '课前问题聚类已生成 5 类'
]

export const teachingSteps = [
  { step: 1, title: '备课', desc: '生成教学设计、案例、讨论题' },
  { step: 2, title: '发布', desc: '审核导学和预习小测' },
  { step: 3, title: '课堂', desc: '发问、抢答、随堂测' },
  { step: 4, title: '课后', desc: '复核批改并发布反馈' }
]

// ===== 管理端数据 =====
export const adminInfo = {
  name: '平台管理员',
  college: demoCourse.college
}

export const adminQueue = [
  { title: 'AI内容待审核', count: 18, level: '优先', color: '#F56C6C' },
  { title: '敏感表达命中记录', count: 3, level: '警告', color: '#E6A23C' },
  { title: '作业批改异常', count: 2, level: '待处理', color: '#409EFF' }
]

export const adminReminders = [
  'AI内容待审核 18 条',
  '来源追溯规则本周已更新',
  '作业批改异常待处理 2 项'
]

// ===== AI 问答数据 =====
export const knowledgeSources = [
  { id: 1, type: '教材', title: '教材：《马克思主义基本原理》', desc: '第三章 实践与认识及其发展规律', tag: '主来源', status: '已审核' },
  { id: 2, type: '课件', title: '课件：王老师第三章课堂讲义', desc: '页码 12-18 · 实践对认识的决定作用', tag: '已引用', status: '已审核' },
  { id: 3, type: '案例', title: '案例库：大学生社会实践调研', desc: '用于说明实践推动认识深化', tag: '推荐', status: '已审核' }
]

export const chatHistory = [
  { role: '我', content: '为什么说实践是检验真理的唯一标准？' },
  { role: 'AI', content: '因为真理性不是由主观愿望或多数意见决定，而要看认识能否在实践中得到验证。实践把主观认识和客观对象联系起来，是检验认识是否符合客观实际的根本途径。' },
  { role: '我', content: '能结合大学生社会实践举个例子吗？' },
  { role: 'AI', content: '例如学生做乡村调研前可能只停留在材料理解，真正进入基层访谈、观察和整理数据后，才能检验原有判断是否准确，并形成更具体的认识。' }
]

export const relatedTopics = [
  '实践的基本特征',
  '认识运动的两次飞跃',
  '真理尺度与价值尺度',
  '理论联系实际'
]

export const suggestedQuestions = [
  '感性认识和理性认识有什么区别？',
  '为什么认识要回到实践中接受检验？',
  '如何用实践观点分析大学生科研训练？'
]
