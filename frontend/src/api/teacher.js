import { demoCourse, teacherQueue, teachingSteps } from '../mock/data.js'
import { isMockMode, request } from './http.js'
import { mockAction, mockResolve } from './mockTransport.js'

const classInteractionPayload = {
  demoCourse,
  pptSlides: [
    { id: 1, title: '第三章：实践与认识及其发展规律', subtitle: '马克思主义基本原理 · 王老师', bullets: ['本章核心问题：人的认识从哪里来？', '学习目标：理解实践、认识、真理、价值的关系', '重点：实践对认识的决定作用'] },
    { id: 2, title: '一、实践的本质与特征', bullets: ['实践是人类能动地改造世界的社会性物质活动', '三个特征：客观物质性、自觉能动性、社会历史性', '实践 ≠ 个人经验，≠ 简单行动'] },
    { id: 3, title: '二、实践对认识的决定作用', bullets: ['实践是认识的来源——认识从实践中产生', '实践是认识发展的动力——实践推动认识深化', '实践是认识的目的——认识服务于实践', '实践是检验真理的唯一标准'] },
    { id: 4, title: '三、认识运动的辩证过程', bullets: ['第一次飞跃：从实践到认识（感性→理性）', '第二次飞跃：从认识到实践（检验→发展）', '认识运动的反复性和无限性'] },
    { id: 5, title: '案例分析：社区调研中的认识变化', bullets: ['调研前：对基层治理的初步看法（感性认识）', '调研中：访谈、观察、数据收集', '调研后：观点修正和深化（理性认识）', '启示：实践推动认识从表层走向深层'] },
    { id: 6, title: '四、真理的客观性与实践标准', bullets: ['真理是标志主观同客观相符合的哲学范畴', '实践是检验真理的唯一标准', '真理既有绝对性，也有相对性', '案例：天鹅的颜色——认识在实践扩展中被修正'] },
    { id: 7, title: '五、真理尺度与价值尺度的统一', bullets: ['真理尺度：尊重客观规律', '价值尺度：服务人的合理需要', '在尊重客观规律的基础上实现价值追求', '反对"有用即真理"的实用主义'] },
    { id: 8, title: '课堂讨论', bullets: ['你是否有过"实践后发现自己原来的想法错了"的经历？', '这个经历如何体现了实践对认识的检验作用？', '请用1-2个关键词在右侧AI助手中提问'] }
  ],
  pptKeywords: ['实践', '认识', '真理检验', '感性认识', '理性认识', '价值尺度'],
  currentSlide: 0,
  statusCards: [
    { label: '当前问题', value: '如何理解实践是检验真理的唯一标准？', desc: '围绕教材第三章与社会实践案例展开', tag: '进行中', tagType: 'warning' },
    { label: '互动状态', value: '41 人参与', desc: '待点评回答 6 条，聚类观点 4 类', tag: '实时', tagType: 'success' }
  ],
  currentQuestion: {
    title: '如何理解实践是检验真理的唯一标准？',
    status: '进行中',
    statusType: 'warning',
    participantCount: 41,
    pendingCommentCount: 6,
    remainingSeconds: 30
  },
  messages: [
    { role: '教师', text: '请围绕“社会实践和认识深化”生成一个追问。' },
    { role: 'AI', text: '可追问：大学生社会调研如何帮助我们修正对基层治理的原有判断？', type: 'ai' },
    { role: '教师', text: '开启30秒抢答，并把回答按观点聚类。' }
  ],
  answers: [
    { viewpoint: '实践标准切入', content: '多数学生提到实践能把主观判断放到现实中检验', count: '18人', action: '可点评' },
    { viewpoint: '社会调研切入', content: '结合社区治理、乡村振兴、公共服务展开', count: '14人', action: '可展示' },
    { viewpoint: '待教师点评', content: 'AI标出表达完整、观点有偏差和案例新颖回答', count: '6条', action: '优先点评' },
    { viewpoint: '课堂后续动作', content: '可把典型回答沉淀为案例或生成巩固题', count: '可用', action: '生成题目' }
  ],
  suggestions: [
    '用“社会调研前后判断变化”作为追问案例。',
    '展示一条观点完整但案例不足的回答，现场补充论证链条。',
    '将“实践标准 vs 多数意见”转成随堂微测。'
  ]
}

const liveQuizPayload = {
  config: {
    chapter: '第三章 实践与认识及其发展规律',
    count: 5,
    ratio: 'balanced',
    difficulty: 'medium'
  },
  chapters: ['第一章 导论', '第二章 世界的物质性及发展规律', '第三章 实践与认识及其发展规律', '第四章 人类社会及其发展规律'],
  pushStatus: {
    label: '未推送',
    percentage: 0,
    participantCount: 0,
    durationMinutes: 5,
    statusType: 'info'
  },
  questions: [
    { id: 1, type: '单选', typeCode: 'single', stem: '下列关于实践与认识关系的说法，正确的是？', options: [{ key: 'A', text: '认识可以脱离实践独立产生' }, { key: 'B', text: '实践是认识的来源和发展动力' }, { key: 'C', text: '真理由多数意见决定' }], answer: 'B', source: '教材第三章' },
    { id: 2, type: '单选', typeCode: 'single', stem: '实践是检验真理的唯一标准，主要因为实践能够？', options: [{ key: 'A', text: '连接主观认识和客观对象' }, { key: 'B', text: '代替全部理论学习' }, { key: 'C', text: '取消价值判断' }], answer: 'A', source: '教材第三章' },
    { id: 3, type: '多选', typeCode: 'multiple', stem: '认识运动通常包括哪些环节？', options: [{ key: 'A', text: '从实践到认识' }, { key: 'B', text: '从感性认识到理性认识' }, { key: 'C', text: '从认识回到实践' }, { key: 'D', text: '脱离实践自我循环' }], answer: 'ABC', source: '教材第三章' },
    { id: 4, type: '单选', typeCode: 'single', stem: '大学生社会调研后修正原有判断，体现了什么观点？', options: [{ key: 'A', text: '实践推动认识深化' }, { key: 'B', text: '认识只来自书本' }, { key: 'C', text: '理论不需要检验' }], answer: 'A', source: '案例库：社会实践调研' },
    { id: 5, type: '多选', typeCode: 'multiple', stem: '分析现实问题时，真理尺度与价值尺度要求我们？', options: [{ key: 'A', text: '尊重客观规律' }, { key: 'B', text: '关注人民需要' }, { key: 'C', text: '用愿望替代事实' }, { key: 'D', text: '把理论运用于实践' }], answer: 'ABD', source: '教材第三章' }
  ]
}

const gradingReviewPayload = {
  reviewCols: [
    {
      title: '原始答卷图像',
      items: ['第 2 页 / 第 3 题区域已定位', '低置信度片段高亮标注', '可放大、旋转、重新框选'],
      actions: ['放大', '旋转', '重新框选']
    },
    {
      title: 'OCR与答案文本',
      items: ['学生答案已跨页合并', '红色标记疑似识别错误', '教师可直接修订文本内容'],
      actions: ['编辑文本', '查看原图', '标记']
    },
    {
      title: 'AI批改建议',
      items: ['建议得分：14/20', '问题：理论概念准确但案例论证不足', '可接受、修改或退回重批'],
      actions: ['接受', '修改分数', '退回']
    }
  ],
  reviewQueue: [
    { name: '李明哲 第3题', desc: 'OCR低置信度 2 处，建议人工确认', tag: '优先', type: 'danger' },
    { name: '陈雨涵 第5题', desc: 'AI分数与规则差异较大，需复核', tag: '异常', type: 'warning' }
  ],
  activeStep: 1
}

const classReportPayload = {
  classes: ['2023级1班', '2023级2班', '2023级3班'],
  overviewStats: [
    { label: '班级均分', value: '82.6', color: '#67C23A' },
    { label: '优秀率(≥85)', value: '38%', color: '#409EFF' },
    { label: '及格率', value: '94%', color: '#E6A23C' },
    { label: '互动参与率', value: '82%', color: '#2f2f2f' }
  ],
  studentScores: [
    { rank: 1, name: '陈晓婷', homework: 92, quiz: 90, interaction: 88, total: 90, trend: 5 },
    { rank: 2, name: '李明哲', homework: 88, quiz: 85, interaction: 90, total: 88, trend: 3 },
    { rank: 3, name: '王思远', homework: 85, quiz: 82, interaction: 85, total: 84, trend: -2 },
    { rank: 4, name: '张雨薇', homework: 78, quiz: 72, interaction: 80, total: 77, trend: 4 },
    { rank: 5, name: '赵一鸣', homework: 72, quiz: 65, interaction: 70, total: 69, trend: -5 }
  ],
  heatmap: [
    { name: '概念理解', rate: 88, color: '#67C23A' },
    { name: '案例分析', rate: 72, color: '#409EFF' },
    { name: '真理标准', rate: 68, color: '#E6A23C' },
    { name: '理论溯源', rate: 85, color: '#67C23A' },
    { name: '实践应用', rate: 76, color: '#409EFF' }
  ],
  aiSummary: [
    { label: '整体表现', color: '#67C23A', content: '班级整体学习态度积极，预习完成率76%在中上水平。课堂互动参与度较高，但部分学生在理论深度上需要加强。' },
    { label: '改进方向', color: '#E6A23C', content: '真理标准和案例分析得分相对偏低，建议增加社会实践案例讨论，引导学生用实践观点分析现实问题。' },
    { label: '教学建议', color: '#409EFF', content: '下次课可采用分组辨析形式，围绕“实践检验真理”主题展开讨论，同时为低分学生提供课后巩固题。' }
  ]
}

const resourceLibraryPayload = {
  categories: [
    { name: '案例库', count: 42 },
    { name: '课件模板', count: 18 },
    { name: '视频素材', count: 25 },
    { name: '政策文献', count: 30 },
    { name: '讨论题集', count: 55 },
    { name: '试卷库', count: 12 }
  ],
  resources: [
    { title: '实践与认识章节导学模板', fileType: '文档', chapter: '第三章', size: '2MB', uploadTime: '2026-05-20', category: '课件模板' },
    { title: '大学生社会调研案例集', fileType: '文档', chapter: '第三章', size: '12MB', uploadTime: '2026-05-18', category: '案例库' },
    { title: '实践检验真理专题课件', fileType: '课件', chapter: '第三章', size: '38MB', uploadTime: '2026-05-15', category: '课件模板' },
    { title: '认识运动两次飞跃板书结构', fileType: '文档', chapter: '第三章', size: '8MB', uploadTime: '2026-05-12', category: '课件模板' },
    { title: '大学生社会实践纪录片', fileType: '视频', chapter: '第三章', size: '480MB', uploadTime: '2026-05-10', category: '视频素材' },
    { title: '认识论课堂讨论题精选50例', fileType: '文档', chapter: '综合', size: '5MB', uploadTime: '2026-05-08', category: '讨论题集' }
  ]
}

export function getTeacherDashboard() {
  if (!isMockMode()) {
    return request('/teacher/dashboard')
  }

  return mockResolve({
    currentCourse: {
      name: '马克思主义基本原理',
      chapter: '第三章：实践与认识及其发展规律',
      className: '2023级本科1班',
      time: '今天 14:00',
      progress: 65
    },
    modules: [
      { key: 'design', label: '教学设计', desc: 'AI 辅助教案生成 · 资源绑定', icon: 'Edit', route: '/teacher/lesson-design', status: '已生成', statusType: 'success' },
      { key: 'interaction', label: '课堂互动', desc: '快捷指令 · 发问 · 随堂微测', icon: 'ChatLineRound', route: '/teacher/class-interaction', status: '课中', statusType: 'warning' },
      { key: 'analytics', label: '学情分析', desc: '班级报告 · 学生排名 · 预警', icon: 'DataAnalysis', route: '/teacher/preclass-analytics', status: '可查看', statusType: 'info' },
      { key: 'grading', label: '批改复核', desc: 'AI 批改确认 · 教师终审', icon: 'Checked', route: '/teacher/grading-review', status: '12份待复核', statusType: 'danger' }
    ],
    stats: [
      { label: '今日课程', value: '14:00', desc: '第三章 · 本科1班', color: '#409EFF' },
      { label: '待审核', value: '22', desc: '教案+讨论题', color: '#E6A23C' },
      { label: '待批改', value: '12', desc: 'AI建议待确认', color: '#F56C6C' },
      { label: '学生提问', value: '18', desc: '课前问题汇总', color: '#909399' }
    ],
    recentActivity: [
      { type: 'ai', title: 'AI 教案已生成', desc: '第三章教学设计 + 5道随堂题', time: '今天 09:30' },
      { type: 'student', title: '学生提问聚类完成', desc: '实践检验真理相关问题 6 条', time: '昨天 20:00' },
      { type: 'warn', title: '预警提醒', desc: '张同学测验均分偏低，需关注', time: '昨天 15:00' },
      { type: 'system', title: '批改截止提醒', desc: '12 份作业复核截止 7/15', time: '前天 08:00' }
    ],
    quickActions: [
      { label: '进入备课', desc: '查看 / 生成教案', route: '/teacher/lesson-design' },
      { label: '开始上课', desc: '课堂互动 + 推送测验', route: '/teacher/class-interaction' },
      { label: '批改复核', desc: 'AI批改确认', route: '/teacher/grading-review' },
      { label: '题库管理', desc: '题目增删改查', route: '/teacher/quiz-bank' }
    ],
    teachingSteps,
    stateCols: [
      { title: '课前准备', items: ['预习完成率 76%', '高频困惑 5 类：实践标准/真理检验/价值判断...', '建议重点讲解：实践如何检验认识'] },
      { title: '批改复核', items: ['OCR 低置信度 9 处', 'AI 建议待确认 12 份', '异常分数 2 份需人工复核'] }
    ]
  })
}

export function getLessonDesign() {
  if (!isMockMode()) {
    return request('/teacher/lesson-design')
  }

  return mockResolve({
    demoCourse,
    contentCols: [
      {
        title: '三维目标',
        items: [
          '知识目标：理解实践、认识、真理和价值的基本含义',
          '能力目标：能用实践观点分析社会调研和科研训练',
          '价值目标：形成理论联系实际的学习方法'
        ]
      },
      {
        title: '课堂结构',
        items: [
          '导入：人的认识从哪里来',
          '讲授：实践对认识的决定作用',
          '辨析：真理标准与价值判断',
          '总结：从认识回到实践'
        ]
      },
      {
        title: '讨论与预习',
        items: [
          '讨论题：为什么实践是检验真理的唯一标准',
          '预习任务：阅读教材第三章相关内容',
          '小测题：5 道概念辨析题',
          '问题提交：学生匿名提交课前困惑'
        ]
      }
    ],
    caseMatches: [
      { theory: '实践是认识的来源', case: '大学生进入社区开展社会调研，从真实访谈中修正原有判断。', risk: '低风险' },
      { theory: '认识运动的两次飞跃', case: '科研训练中先提出假设，再通过实验或数据分析回到实践检验。', risk: '低风险' },
      { theory: '真理尺度与价值尺度', case: '乡村振兴议题分析中既要尊重客观规律，也要回应人民需求。', risk: '需教师确认' }
    ],
    sources: [
      { type: '教材', title: '《马克思主义基本原理》第三章', status: '已索引' },
      { type: '课件', title: '王老师第三章课堂讲义', status: '已索引' },
      { type: '案例', title: '大学生社会实践调研案例库', status: '已审核' }
    ]
  })
}

export function publishLessonDesign() {
  if (!isMockMode()) {
    return request('/teacher/lesson-design/publish', {
      method: 'POST'
    })
  }

  return mockAction({ success: true, message: '已发布给学生端，预习任务同步生效' })
}

export function getPreclassAnalytics() {
  if (!isMockMode()) {
    return request('/teacher/preclass-analytics')
  }

  return mockResolve({
    classes: ['2023级1班', '2023级2班', '2023级3班'],
    summary: [
      { label: '预习完成率', value: '76%', color: '#67C23A' },
      { label: '预习小测均分', value: '78.5', color: '#409EFF' },
      { label: '高频困惑', value: '5类', color: '#E6A23C' },
      { label: '建议重点讲', value: '3处', color: '#2f2f2f' }
    ],
    completionData: [
      { group: '全班整体', progress: 76, quizScore: '78.5', status: '进行中' },
      { group: '已完成学生', progress: 100, quizScore: '84.2', status: '已完成' },
      { group: '未完成学生', progress: 42, quizScore: '63.8', status: '进行中' },
      { group: '高频提问组', progress: 88, quizScore: '75.1', status: '已完成' },
      { group: '低分需关注组', progress: 58, quizScore: '61.5', status: '进行中' }
    ],
    weaknesses: [
      { topic: '为什么实践是检验真理的唯一标准', count: 18 },
      { topic: '感性认识与理性认识的区别', count: 15 },
      { topic: '认识为什么要回到实践', count: 12 },
      { topic: '真理尺度与价值尺度的关系', count: 10 },
      { topic: '如何用实践观点分析社会调研', count: 8 }
    ],
    scoreDist: [
      { range: '90-100', count: 8, height: 140, color: '#67C23A' },
      { range: '80-89', count: 15, height: 160, color: '#67C23A' },
      { range: '70-79', count: 10, height: 110, color: '#409EFF' },
      { range: '60-69', count: 5, height: 70, color: '#E6A23C' },
      { range: '<60', count: 2, height: 40, color: '#F56C6C' }
    ],
    suggestions: [
      '课堂导入用“社会调研前后判断变化”案例切入。',
      '增加 5 分钟“实践标准 vs 多数意见”概念辨析。',
      '随堂微测重点覆盖认识运动的两次飞跃。',
      '教师讲解时明确哪些内容来自教材，哪些是案例扩展。'
    ]
  })
}

export function getClassInteraction() {
  if (!isMockMode()) {
    return request('/teacher/class-interaction')
  }

  return mockResolve(classInteractionPayload)
}

export function sendClassInteractionCommand(commandText) {
  if (!isMockMode()) {
    return request('/teacher/class-interaction/command', {
      method: 'POST',
      body: JSON.stringify({ commandText })
    })
  }

  // 如果是请求教学建议，返回多条建议
  if (commandText.includes('教学建议') || commandText.includes('建议')) {
    return mockAction({
      success: true,
      message: '已生成教学建议',
      reply: `1.引导学生从"实践标准"切入，对比多数意见与客观检验的区别。
2.展示一条观点完整但案例不足的回答，现场补充论证链条。
3.将"实践标准 vs 多数意见"的讨论转成随堂微测题。`
    })
  }

  return mockAction({
    success: true,
    message: '指令已发送',
    reply: '可追问：如果多数人都认同一个判断，它是否一定是真理？请用实践标准说明。'
  })
}

export function getLiveInteractionState() {
  return request('/teacher/live-interaction')
}

export function publishLiveInteractionQuestion(questionText, durationSeconds) {
  return request('/teacher/live-interaction/questions', {
    method: 'POST',
    body: JSON.stringify({ questionText, durationSeconds })
  })
}

export function closeLiveInteractionQuestion(questionId) {
  return request(`/teacher/live-interaction/questions/${questionId}/close`, { method: 'POST' })
}

export function getLiveAnswers(questionId) {
  return request(`/teacher/live-interaction/questions/${questionId}/answers`)
}

export function highlightAnswer(answerId, highlighted = true) {
  return request(`/teacher/live-interaction/answers/${answerId}/highlight`, {
    method: 'POST', body: JSON.stringify({ highlighted })
  })
}

export function getLiveQuiz() {
  if (!isMockMode()) {
    return request('/teacher/live-quiz')
  }

  return mockResolve(liveQuizPayload)
}

export function generateLiveQuiz(config) {
  if (!isMockMode()) {
    return request('/teacher/live-quiz/generate', {
      method: 'POST',
      body: JSON.stringify(config)
    })
  }

  return mockAction({
    success: true,
    message: '已根据当前配置生成随堂测验',
    ...liveQuizPayload,
    config: {
      ...liveQuizPayload.config,
      ...config
    }
  })
}

export function publishLiveQuiz(questionIds) {
  if (!isMockMode()) {
    return request('/teacher/live-quiz/publish', {
      method: 'POST',
      body: JSON.stringify({ questionIds })
    })
  }

  return mockAction({
    success: true,
    message: '已推送至学生端',
    pushStatus: {
      label: '已推送',
      percentage: 100,
      participantCount: 41,
      durationMinutes: 5,
      statusType: 'success'
    }
  })
}

export function closeLiveQuiz(quizId) {
  if (!isMockMode()) {
    return request('/teacher/live-quiz/close', {
      method: 'POST',
      body: JSON.stringify({ quizId })
    })
  }

  return mockAction({ success: true, message: '已关闭测验' })
}

export function getGradingReview() {
  if (!isMockMode()) {
    return request('/teacher/grading-review')
  }

  return mockResolve(gradingReviewPayload)
}

export function confirmGradingReview(action = 'publish') {
  if (!isMockMode()) {
    return request('/teacher/grading-review/confirm', {
      method: 'POST',
      body: JSON.stringify({ action })
    })
  }

  return mockAction({ success: true, message: action === 'return' ? '已退回重批' : '已确认发布学生反馈' })
}

export function getClassLearningReport() {
  if (!isMockMode()) {
    return request('/teacher/class-report')
  }

  return mockResolve(classReportPayload)
}

export function getTeacherResourceLibrary() {
  if (!isMockMode()) {
    return request('/teacher/resource-library')
  }

  return mockResolve(resourceLibraryPayload)
}

/** 获取班级学情分析（教师端） */
export function getClassAnalytics() {
  if (!isMockMode()) {
    return request('/teacher/class-analytics')
  }

  return mockResolve({
    classStats: [
      { label: '班级均分', value: '76', color: '#67C23A' },
      { label: '优秀率(≥80)', value: '38%', color: '#409EFF' },
      { label: '及格率(≥60)', value: '92%', color: '#67C23A' },
      { label: '预警人数', value: '2', color: '#F56C6C' }
    ],
    studentScores: [
      { rank: 1, name: '李明哲', total: 88, avgScore: 85, quizRate: 90, riskLevel: 'normal', trend: 3 },
      { rank: 2, name: '陈雨涵', total: 82, avgScore: 80, quizRate: 85, riskLevel: 'normal', trend: 2 },
      { rank: 3, name: '王晓丽', total: 78, avgScore: 75, quizRate: 70, riskLevel: 'normal', trend: -1 },
      { rank: 4, name: '赵志远', total: 65, avgScore: 68, quizRate: 60, riskLevel: 'attention', trend: -2 },
      { rank: 5, name: '张同学', total: 45, avgScore: 42, quizRate: 30, riskLevel: 'warning', trend: -5 }
    ],
    heatmap: [
      { name: '概念理解', rate: 82, color: '#67C23A' },
      { name: '案例分析', rate: 68, color: '#E6A23C' },
      { name: '互动参与', rate: 75, color: '#409EFF' },
      { name: '来源意识', rate: 70, color: '#409EFF' },
      { name: '表达结构', rate: 78, color: '#67C23A' }
    ],
    warningList: [
      { name: '张同学', total: 45, reason: '测验均分偏低，尚未主动提问', riskLevel: 'warning' },
      { name: '刘同学', total: 50, reason: '学习天数不足，零互动', riskLevel: 'warning' }
    ],
    attentionList: [
      { name: '赵志远', total: 65, reason: '案例分析能力偏弱，建议加强练习', riskLevel: 'attention' }
    ],
    summary: {
      label: '需重点关注',
      color: '#E6A23C',
      content: '班级均分 76，存在 2 名预警学生。案例分析是整体薄弱环节，建议增加社会调研类讨论题，并为低分学生提供课后巩固材料。'
    }
  })
}

/** AI 生成教案 */
export function generateLessonDesign(chapterId, config = {}) {
  if (!isMockMode()) {
    return request('/teacher/lesson-design/generate', {
      method: 'POST',
      body: JSON.stringify({ chapterId, config })
    })
  }
  return mockResolve({
    success: true,
    design: {
      chapter: { id: 1, title: '实践与认识及其发展规律', chapterOrder: 3, courseName: '马克思主义基本原理', semester: '2025-2026-2', summary: '围绕实践、认识、真理、价值的关系展开' },
      config: { focusAreas: ['理论基础', '案例分析', '价值引导'], classHours: 2, includeQuiz: true, includeDiscussion: true },
      teachingObjectives: [
        { type: '知识目标', content: '理解实践与认识及其发展规律的核心概念和基本原理。' },
        { type: '能力目标', content: '能够运用相关理论分析现实问题，培养理论联系实际的能力。' },
        { type: '价值目标', content: '增强对马克思主义理论的认同，形成科学的思维方法。' }
      ],
      keyPoints: ['核心概念与理论框架', '理论与实践的结合点', '常见误区辨析', '与其他章节的逻辑关联'],
      classStructure: [
        { phase: '导入（5分钟）', content: '以社会热点或生活案例切入，引出本章核心问题。', method: '案例导入 + 问题驱动' },
        { phase: '讲授（40分钟）', content: '系统讲解基本概念、理论框架和逻辑关系。', method: '讲授 + 板书 + PPT辅助' },
        { phase: '互动讨论（15分钟）', content: '分组讨论理论相关的现实问题。', method: '分组讨论 + 代表发言' },
        { phase: '总结（10分钟）', content: '回顾知识框架，提炼方法论启示。', method: '思维导图 + 课后任务' }
      ],
      discussionQuestions: ['结合本章理论，分析一个你身边的社会现象。', '理论基础在我们日常生活中有哪些体现？'],
      quizQuestions: [
        { stem: '下列关于实践与认识关系的说法，正确的是？', type: 'single', knowledgePoint: '实践与认识' },
        { stem: '实践是检验真理的唯一标准，主要因为？', type: 'single', knowledgePoint: '真理标准' }
      ],
      caseRecommendations: [{ title: '大学生社会实践案例', type: '案例', usage: '引导学生用理论分析该案例。' }],
      sourceRefs: [{ id: 1, type: 'textbook', title: '《马克思主义基本原理》教材第三章', citation: '实践与认识相关段落' }],
      generatedAt: new Date().toISOString()
    }
  })
}

/** 保存 AI 教案为草稿 */
export function saveLessonDesignDraft(chapterId, design) {
  if (!isMockMode()) {
    return request('/teacher/lesson-design/save', {
      method: 'POST',
      body: JSON.stringify({ chapterId, design })
    })
  }
  return mockResolve({ success: true, id: Date.now(), status: 'draft' })
}

/** AI 批改提交 */
export function aiGradeSubmission(submissionId, answerText, rubricId) {
  if (!isMockMode()) {
    return request('/teacher/grading-review/ai-grade', {
      method: 'POST',
      body: JSON.stringify({ submissionId, answerText, rubricId })
    })
  }
  return mockResolve({
    submission: { id: submissionId, studentName: '李明哲', stem: '实践与认识材料分析题', knowledgePoint: '实践与认识' },
    rubricItems: [
      { id: 1, name: '概念理解准确性', weight: 30, aiScore: 88, level: '优秀', evidence: '是否准确使用核心概念', comment: '概念使用稳定，能说明实践对认识的决定作用。' },
      { id: 2, name: '理论联系实际', weight: 25, aiScore: 72, level: '合格', evidence: '能否用理论分析现实问题', comment: '有案例但深度可以加强。' },
      { id: 3, name: '论证结构与表达', weight: 25, aiScore: 84, level: '优秀', evidence: '论证是否有清晰结构', comment: '观点明确，层次清晰。' },
      { id: 4, name: '价值导向与规范性', weight: 20, aiScore: 90, level: '优秀', evidence: '表达是否符合课程规范', comment: '表达稳妥，来源意识较好。' }
    ],
    totalScore: 83,
    confidence: 92,
    suggestions: ['可以在案例分析深度上继续提升。', '尝试用不同角度案例论证同一观点。'],
    riskFlags: []
  })
}

/** OCR 模拟识别 */
export function ocrRecognize(imageUrl) {
  if (!isMockMode()) {
    return request('/teacher/grading-review/ocr', {
      method: 'POST',
      body: JSON.stringify({ imageUrl })
    })
  }
  return mockResolve({
    text: '在社区调研前，我对基层治理的理解主要来自教材和新闻材料...',
    confidence: 96,
    keywords: ['实践', '认识', '检验', '修正', '调研'],
    warnings: []
  })
}

// ===== 题库管理 =====
export function getQuizBank(params = {}) {
  if (!isMockMode()) {
    const qs = new URLSearchParams()
    if (params.chapterId) qs.set('chapterId', params.chapterId)
    if (params.type) qs.set('type', params.type)
    if (params.status) qs.set('status', params.status)
    if (params.keyword) qs.set('keyword', params.keyword)
    return request(`/teacher/quiz-bank?${qs.toString()}`)
  }
  return mockResolve([
    { id: 1, chapterId: 1, chapterTitle: '实践与认识及其发展规律', knowledgePoint: '实践与认识', questionType: 'single', stem: '下列关于实践与认识关系的说法，正确的是哪一项？', options: ['认识可以脱离实践独立产生', '实践是认识的来源和发展动力', '认识的目的只是形成理论', '真理主要由多数人的意见决定'], answer: [1], analysis: '实践是认识的来源、动力、目的，也是检验认识真理性的唯一标准。', auditStatus: 'approved' },
    { id: 2, chapterId: 1, chapterTitle: '实践与认识及其发展规律', knowledgePoint: '真理标准', questionType: 'single', stem: '为什么说实践是检验真理的唯一标准？', options: ['因为实践能连接主观认识和客观对象', '因为实践由少数专家决定', '因为实践可以替代全部理论学习', '因为实践不需要价值判断'], answer: [0], analysis: '实践能够把主观认识放到客观现实中接受检验。', auditStatus: 'approved' },
    { id: 3, chapterId: 1, chapterTitle: '实践与认识及其发展规律', knowledgePoint: '概念辨析', questionType: 'judge', stem: '认识的发展只需要从感性认识上升到理性认识，不需要再回到实践。', options: ['正确', '错误'], answer: [1], analysis: '认识运动包括从实践到认识、从认识再回到实践的过程。', auditStatus: 'approved' },
    { id: 4, chapterId: 1, chapterTitle: '实践与认识及其发展规律', knowledgePoint: '理论联系实际', questionType: 'single', stem: '大学生参加社会调研后修正原有判断，最能体现哪一观点？', options: ['理论可以脱离现实独立完成', '实践推动认识深化', '价值判断不需要事实依据', '认识只来自书本'], answer: [1], analysis: '社会调研作为实践活动，能够检验并推动原有认识发展。', auditStatus: 'approved' },
    { id: 5, chapterId: 1, chapterTitle: '实践与认识及其发展规律', knowledgePoint: '真理与价值', questionType: 'single', stem: '关于真理尺度与价值尺度的关系，下列说法更准确的是？', options: ['二者完全无关', '价值尺度可以取代真理尺度', '应在尊重客观规律基础上实现价值追求', '只要目的正当就不必考虑事实'], answer: [2], analysis: '认识和实践既要尊重客观规律，也要服务人的合理价值目标。', auditStatus: 'approved' }
  ])
}

export function createQuizQuestion(data) {
  if (!isMockMode()) {
    return request('/teacher/quiz-bank', { method: 'POST', body: JSON.stringify(data) })
  }
  return mockResolve({ id: Date.now() })
}

export function updateQuizQuestion(id, data) {
  if (!isMockMode()) {
    return request(`/teacher/quiz-bank/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  }
  return mockResolve({ success: true })
}

export function deleteQuizQuestion(id) {
  if (!isMockMode()) {
    return request(`/teacher/quiz-bank/${id}`, { method: 'DELETE' })
  }
  return mockResolve({ success: true })
}
