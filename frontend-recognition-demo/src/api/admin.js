import { adminQueue } from '../mock/data.js'
import { isMockMode, request } from './http.js'
import { mockResolve } from './mockTransport.js'

const userList = [
  {
    id: 1,
    userCode: 'U001',
    account: 'student01',
    name: '李明哲',
    role: '学生',
    roleCode: 'student',
    dept: '马克思主义学院',
    major: '思想政治教育',
    className: '2023级本科1班',
    course: '马克思主义基本原理',
    status: '正常',
    statusCode: 'active',
    statusType: 'success',
    lastLogin: '2026-07-07 09:15',
    createdAt: '2025-09-01',
    phone: '138****1024',
    email: 'limingzhe@example.edu.cn',
    loginCount: 128,
    dataScope: '本人学习数据',
    risk: '低风险',
    riskType: 'success'
  },
  {
    id: 2,
    userCode: 'U002',
    account: 'student02',
    name: '陈思源',
    role: '学生',
    roleCode: 'student',
    dept: '马克思主义学院',
    major: '思想政治教育',
    className: '2023级本科1班',
    course: '马克思主义基本原理',
    status: '正常',
    statusCode: 'active',
    statusType: 'success',
    lastLogin: '2026-07-07 08:42',
    createdAt: '2025-09-01',
    phone: '139****2048',
    email: 'chensiyuan@example.edu.cn',
    loginCount: 96,
    dataScope: '本人学习数据',
    risk: '低风险',
    riskType: 'success'
  },
  {
    id: 3,
    userCode: 'U003',
    account: 'teacher01',
    name: '王老师',
    role: '教师',
    roleCode: 'teacher',
    dept: '马克思主义学院',
    major: '马克思主义理论',
    className: '2023级本科1班',
    course: '马克思主义基本原理',
    status: '正常',
    statusCode: 'active',
    statusType: 'success',
    lastLogin: '2026-07-07 08:00',
    createdAt: '2025-08-20',
    phone: '137****6601',
    email: 'wanglaoshi@example.edu.cn',
    loginCount: 214,
    dataScope: '授课班级数据',
    risk: '低风险',
    riskType: 'success'
  },
  {
    id: 4,
    userCode: 'U004',
    account: 'student03',
    name: '周若涵',
    role: '学生',
    roleCode: 'student',
    dept: '马克思主义学院',
    major: '法学',
    className: '2023级本科2班',
    course: '中国近现代史纲要',
    status: '正常',
    statusCode: 'active',
    statusType: 'success',
    lastLogin: '2026-07-06 14:20',
    createdAt: '2025-09-01',
    phone: '136****3318',
    email: 'zhouruohan@example.edu.cn',
    loginCount: 73,
    dataScope: '本人学习数据',
    risk: '低风险',
    riskType: 'success'
  },
  {
    id: 5,
    userCode: 'U005',
    account: 'student04',
    name: '赵一鸣',
    role: '学生',
    roleCode: 'student',
    dept: '马克思主义学院',
    major: '公共管理',
    className: '2023级本科1班',
    course: '马克思主义基本原理',
    status: '禁用',
    statusCode: 'disabled',
    statusType: 'danger',
    lastLogin: '2026-05-20 10:00',
    createdAt: '2025-09-01',
    phone: '135****7810',
    email: 'zhaoyiming@example.edu.cn',
    loginCount: 22,
    dataScope: '本人学习数据',
    risk: '需复核',
    riskType: 'warning'
  },
  {
    id: 6,
    userCode: 'U006',
    account: 'teacher02',
    name: '李老师',
    role: '教师',
    roleCode: 'teacher',
    dept: '马克思主义学院',
    major: '中国近现代史',
    className: '2023级本科2班',
    course: '中国近现代史纲要',
    status: '正常',
    statusCode: 'active',
    statusType: 'success',
    lastLogin: '2026-07-07 07:30',
    createdAt: '2025-08-20',
    phone: '138****7789',
    email: 'lilaoshi@example.edu.cn',
    loginCount: 181,
    dataScope: '授课班级数据',
    risk: '低风险',
    riskType: 'success'
  },
  {
    id: 7,
    userCode: 'U007',
    account: 'admin01',
    name: '平台管理员',
    role: '管理员',
    roleCode: 'admin',
    dept: '教务处',
    major: '平台治理',
    className: '-',
    course: '全校思政课程',
    status: '正常',
    statusCode: 'active',
    statusType: 'warning',
    lastLogin: '2026-07-07 08:45',
    createdAt: '2025-08-01',
    phone: '139****9001',
    email: 'admin@example.edu.cn',
    loginCount: 318,
    dataScope: '全校平台数据',
    risk: '高权限',
    riskType: 'warning'
  }
]

const userBatchImportPayload = {
  stats: [
    { label: '待导入', value: '36', color: '#409EFF', desc: '本次名单行数' },
    { label: '可直接导入', value: '32', color: '#67C23A', desc: '字段完整且无冲突' },
    { label: '需处理', value: '3', color: '#E6A23C', desc: '院系或班级待确认' },
    { label: '重复账号', value: '1', color: '#F56C6C', desc: '需合并或跳过' }
  ],
  template: {
    name: '思政平台用户导入模板.xlsx',
    version: 'v1.2',
    updatedAt: '2026-07-07 16:20',
    requiredFields: ['账号', '姓名', '角色', '院系', '班级/部门', '关联课程']
  },
  mappings: [
    { source: '账号', target: 'username', rule: '唯一，建议使用学号/工号', status: '已匹配', statusType: 'success' },
    { source: '姓名', target: 'real_name', rule: '2-20 个字符', status: '已匹配', statusType: 'success' },
    { source: '角色', target: 'role', rule: '学生/教师/管理员', status: '已匹配', statusType: 'success' },
    { source: '院系', target: 'college', rule: '需匹配组织字典', status: '待确认', statusType: 'warning' },
    { source: '班级/部门', target: 'class_or_department', rule: '学生绑定班级，教师绑定部门', status: '待确认', statusType: 'warning' }
  ],
  previewRows: [
    { row: 2, account: 'student05', name: '刘予安', role: '学生', dept: '马克思主义学院', className: '2023级本科1班', course: '马克思主义基本原理', result: '可导入', resultType: 'success' },
    { row: 3, account: 'student06', name: '许佳宁', role: '学生', dept: '马克思主义学院', className: '2023级本科1班', course: '马克思主义基本原理', result: '可导入', resultType: 'success' },
    { row: 4, account: 'teacher03', name: '何老师', role: '教师', dept: '马克思主义学院', className: '2023级本科3班', course: '思想道德与法治', result: '班级待创建', resultType: 'warning' },
    { row: 5, account: 'student01', name: '李明哲', role: '学生', dept: '马克思主义学院', className: '2023级本科1班', course: '马克思主义基本原理', result: '账号重复', resultType: 'danger' }
  ],
  conflicts: [
    { type: '账号重复', count: 1, strategy: '保留原账号，跳过重复行', owner: '教务管理员' },
    { type: '班级不存在', count: 2, strategy: '导入前创建班级并绑定课程', owner: '课程管理员' },
    { type: '院系名称不一致', count: 1, strategy: '按组织字典归并为马克思主义学院', owner: '平台管理员' }
  ],
  steps: [
    { title: '上传模板', time: '已完成', desc: '已读取 36 行用户数据。' },
    { title: '字段映射', time: '已完成', desc: '账号、姓名、角色和课程字段已匹配。' },
    { title: '规则校验', time: '处理中', desc: '重复账号、角色合法性、班级存在性已完成预检。' },
    { title: '确认导入', time: '待执行', desc: '确认冲突处理策略后写入用户、班级和选课关系。' }
  ]
}

function findUser(id) {
  return userList.find((item) => String(item.id) === String(id) || item.userCode === id || item.account === id) || userList[0]
}

function buildUserDetail(id) {
  const user = findUser(id)
  const roleScopes = {
    student: ['查看本人学习任务', '提交预习问题', '查看作业反馈', '访问来源溯源'],
    teacher: ['发布导学任务', '查看授课班级学情', '复核 AI 批改', '管理教学资源'],
    admin: ['管理用户与角色', '审核 AI 内容', '维护知识库', '查看审计日志']
  }
  const courseBindings = user.roleCode === 'admin'
    ? [
        { course: '马克思主义基本原理', className: '全校范围', role: '平台治理', status: '可管理' },
        { course: '中国近现代史纲要', className: '全校范围', role: '平台治理', status: '可管理' }
      ]
    : [
        { course: user.course, className: user.className, role: user.role, status: user.status === '正常' ? '生效中' : '已停用' },
        { course: '形势与政策', className: user.roleCode === 'student' ? user.className : '2023级本科3班', role: user.role, status: '待开课' }
      ]

  return {
    user,
    stats: [
      { label: '账号状态', value: user.status, color: user.statusCode === 'active' ? '#67C23A' : '#F56C6C', desc: user.risk },
      { label: '角色', value: user.role, color: user.roleCode === 'admin' ? '#E6A23C' : '#409EFF', desc: user.dataScope },
      { label: '关联课程', value: String(courseBindings.length), color: '#409EFF', desc: '课程/班级关系' },
      { label: '登录次数', value: String(user.loginCount), color: '#909399', desc: `最近 ${user.lastLogin}` }
    ],
    security: [
      { name: '初始密码状态', result: user.loginCount > 1 ? '已修改' : '待修改', type: user.loginCount > 1 ? 'success' : 'warning', desc: '首次登录后要求修改默认密码。' },
      { name: '身份有效性', result: user.status, type: user.statusType, desc: '禁用后无法登录前端和调用业务接口。' },
      { name: '高权限校验', result: user.roleCode === 'admin' ? '需定期复核' : '普通权限', type: user.roleCode === 'admin' ? 'warning' : 'success', desc: '管理员账号建议按月复核权限范围。' }
    ],
    permissions: roleScopes[user.roleCode].map((name, index) => ({
      name,
      code: `${user.roleCode}:${index + 1}`,
      status: '已授权',
      type: 'success'
    })),
    courseBindings,
    timeline: [
      { title: '账号创建', time: user.createdAt, desc: `${user.dept} 创建 ${user.role} 账号。` },
      { title: '课程绑定', time: '2026-06-20 10:00', desc: `绑定到 ${user.course}。` },
      { title: '最近登录', time: user.lastLogin, desc: '通过统一登录入口进入平台。' },
      { title: '权限复核', time: '2026-07-07 09:30', desc: '平台完成角色与数据范围校验。' }
    ],
    auditLogs: [
      { action: 'update_user_scope', operator: '平台管理员', detail: `确认 ${user.name} 的数据范围为“${user.dataScope}”。`, time: '2026-07-07 09:30' },
      { action: 'sync_course_binding', operator: '系统', detail: `同步 ${user.course} 课程关系。`, time: '2026-07-07 08:10' }
    ]
  }
}

const courseManagementPayload = {
  stats: [
    { label: '课程总数', value: '4', color: '#409EFF', desc: '当前学期已开课' },
    { label: '教学班级', value: '11', color: '#67C23A', desc: '覆盖全校思政课' },
    { label: '学习学生', value: '455', color: '#E6A23C', desc: '已完成账号绑定' },
    { label: '结构待完善', value: '1', color: '#F56C6C', desc: '需补章节与任务链' }
  ],
  courses: [
    { id: 1, code: 'MY001', name: '马克思主义基本原理', classCount: 2, studentCount: 90, chapterCount: 12, resourceCount: 8, semester: '2025-2026-2', status: '进行中', statusType: 'success' },
    { id: 2, code: 'SX001', name: '思想道德与法治', classCount: 2, studentCount: 88, chapterCount: 8, resourceCount: 12, semester: '2025-2026-2', status: '进行中', statusType: 'success' },
    { id: 3, code: 'ZG001', name: '中国近现代史纲要', classCount: 3, studentCount: 117, chapterCount: 10, resourceCount: 9, semester: '2025-2026-2', status: '进行中', statusType: 'success' },
    { id: 4, code: 'XS001', name: '形势与政策', classCount: 4, studentCount: 160, chapterCount: 6, resourceCount: 5, semester: '2025-2026-2', status: '待完善', statusType: 'warning' }
  ],
  classes: [
    { id: 1, courseId: 1, name: '2023级本科1班', teacher: '王老师', studentCount: 42, semester: '2025-2026-2', schedule: '周一 14:00-15:40', status: '进行中', statusType: 'success' },
    { id: 2, courseId: 1, name: '2023级本科2班', teacher: '李老师', studentCount: 48, semester: '2025-2026-2', schedule: '周三 14:00-15:40', status: '进行中', statusType: 'success' },
    { id: 3, courseId: 2, name: '2023级法学1班', teacher: '何老师', studentCount: 44, semester: '2025-2026-2', schedule: '周二 10:00-11:40', status: '进行中', statusType: 'success' },
    { id: 4, courseId: 2, name: '2023级公管1班', teacher: '何老师', studentCount: 44, semester: '2025-2026-2', schedule: '周四 10:00-11:40', status: '进行中', statusType: 'success' },
    { id: 5, courseId: 3, name: '2023级本科3班', teacher: '陈教授', studentCount: 39, semester: '2025-2026-2', schedule: '周五 08:00-09:40', status: '进行中', statusType: 'success' },
    { id: 6, courseId: 4, name: '全校混合1班', teacher: '平台排课', studentCount: 40, semester: '2025-2026-2', schedule: '线上异步', status: '待完善', statusType: 'warning' }
  ]
}

const courseStructurePayload = {
  course: {
    id: 1,
    code: 'MY001',
    name: '马克思主义基本原理',
    semester: '2025-2026-2',
    college: '马克思主义学院',
    owner: '王老师',
    status: '进行中',
    statusType: 'success',
    description: '面向大学生的马克思主义基本原理课程，当前重点建设“实践与认识及其发展规律”章节的导学、测评、反馈和来源溯源闭环。'
  },
  stats: [
    { label: '章节数量', value: '12', color: '#409EFF', desc: '已建立课程结构' },
    { label: '任务节点', value: '18', color: '#67C23A', desc: '导学、测评、作业' },
    { label: '资源绑定', value: '8', color: '#E6A23C', desc: '教材、课件、案例' },
    { label: '班级覆盖', value: '2', color: '#909399', desc: '当前学期教学班' }
  ],
  chapters: [
    { id: 1, order: 1, title: '导论', summary: '课程性质、基本问题与学习方法。', knowledgePoints: ['马克思主义整体性', '理论联系实际'], taskCount: 2, resourceCount: 1, status: '已配置', statusType: 'success' },
    { id: 2, order: 2, title: '世界的物质性及发展规律', summary: '物质、意识、联系、发展与矛盾分析法。', knowledgePoints: ['物质观', '矛盾分析法', '发展观'], taskCount: 3, resourceCount: 2, status: '已配置', statusType: 'success' },
    { id: 3, order: 3, title: '实践与认识及其发展规律', summary: '实践、认识、真理与价值的辩证关系。', knowledgePoints: ['实践', '认识', '真理标准', '真理与价值'], taskCount: 5, resourceCount: 3, status: '重点建设', statusType: 'warning' },
    { id: 4, order: 4, title: '人类社会及其发展规律', summary: '社会存在、社会意识与社会基本矛盾。', knowledgePoints: ['社会存在', '社会意识', '社会基本矛盾'], taskCount: 2, resourceCount: 1, status: '已配置', statusType: 'success' }
  ],
  taskChain: [
    { phase: '课前', title: '章节导学发布', owner: '教师', target: '学生阅读导学并提交问题', status: '已发布', statusType: 'success' },
    { phase: '课前', title: '预习小测', owner: '系统', target: '完成概念辨析题并生成弱点标签', status: '已配置', statusType: 'success' },
    { phase: '课中', title: '课堂互动指令', owner: '教师', target: '围绕高频困惑发问和抢答', status: '可用', statusType: 'success' },
    { phase: '课后', title: '材料分析作业', owner: '教师', target: '绑定评分量规和来源依据', status: '待复核', statusType: 'warning' },
    { phase: '治理', title: '来源与审核追踪', owner: '管理员', target: '检查知识来源、AI内容和审计记录', status: '已接入', statusType: 'success' }
  ],
  classCoverage: [
    { name: '2023级本科1班', teacher: '王老师', students: 42, progress: 76, quizAvg: 82.5, status: '进行中' },
    { name: '2023级本科2班', teacher: '李老师', students: 48, progress: 68, quizAvg: 79.2, status: '进行中' }
  ],
  resources: [
    { type: '教材', title: '《马克思主义基本原理》教材第三章', chapter: '实践与认识及其发展规律', indexStatus: '已索引', auditStatus: '已审核' },
    { type: '课件', title: '王老师第三章课堂讲义', chapter: '实践与认识及其发展规律', indexStatus: '已索引', auditStatus: '已审核' },
    { type: '案例', title: '大学生社会实践案例库', chapter: '实践与认识及其发展规律', indexStatus: '已索引', auditStatus: '已审核' }
  ],
  qualityChecks: [
    { name: '章节完整性', result: '通过', type: 'success', desc: '课程包含章节、摘要和知识点字段。' },
    { name: '任务链闭环', result: '已形成', type: 'success', desc: '课前、课中、课后和治理节点已可演示。' },
    { name: '来源绑定', result: '需持续补充', type: 'warning', desc: '重点章节已绑定来源，非重点章节资源仍需扩充。' },
    { name: '班级覆盖', result: '通过', type: 'success', desc: '当前课程已有教学班和教师绑定。' }
  ],
  timeline: [
    { title: '课程建档', time: '2025-09-01', desc: '创建课程基础信息与章节目录。' },
    { title: '章节结构同步', time: '2026-07-07 15:00', desc: '同步重点章节、任务链与资源索引。' },
    { title: '闭环检查', time: '2026-07-08 09:00', desc: '检查导学、测验、作业、反馈和来源治理链路。' }
  ]
}

function buildCourseStructure(id) {
  const course = courseManagementPayload.courses.find((item) => String(item.id) === String(id)) || courseManagementPayload.courses[0]

  return {
    ...courseStructurePayload,
    course: {
      ...courseStructurePayload.course,
      id: course.id,
      code: course.code,
      name: course.name,
      semester: course.semester,
      status: course.status,
      statusType: course.statusType
    },
    stats: [
      { label: '章节数量', value: String(course.chapterCount), color: '#409EFF', desc: '已建立课程结构' },
      { label: '任务节点', value: String(course.id === 4 ? 8 : 18), color: '#67C23A', desc: '导学、测评、作业' },
      { label: '资源绑定', value: String(course.resourceCount), color: '#E6A23C', desc: '教材、课件、案例' },
      { label: '班级覆盖', value: String(course.classCount), color: '#909399', desc: '当前学期教学班' }
    ],
    classCoverage: courseManagementPayload.classes
      .filter((item) => item.courseId === course.id)
      .map((item) => ({
        name: item.name,
        teacher: item.teacher,
        students: item.studentCount,
        progress: course.id === 4 ? 42 : 76,
        quizAvg: course.id === 4 ? 0 : 82.5,
        status: item.status
      }))
  }
}

const auditLogList = [
  { id: 1, time: '2026-07-08 09:15:32', operator: '平台管理员', role: '管理员', roleCode: 'admin', action: '审核', actionCode: 'approve_ai_content', actionType: 'warning', detail: '管理员审核通过 AI 教学设计。', targetType: 'ai_review', targetLabel: 'AI内容审核', targetId: 1, ip: '127.0.0.1', result: '成功', resultType: 'success' },
  { id: 2, time: '2026-07-08 09:02:10', operator: '王老师', role: '教师', roleCode: 'teacher', action: '发布', actionCode: 'publish_lesson_design', actionType: 'success', detail: '教师发布教学设计和预习任务。', targetType: 'lesson_design', targetLabel: '教学设计', targetId: 1, ip: '127.0.0.1', result: '成功', resultType: 'success' },
  { id: 3, time: '2026-07-08 08:45:10', operator: '平台管理员', role: '管理员', roleCode: 'admin', action: '修改', actionCode: 'update_user_scope', actionType: '', detail: '确认王老师的数据范围为“授课班级数据”。', targetType: 'user', targetLabel: '用户账号', targetId: 3, ip: '10.0.0.1', result: '成功', resultType: 'success' },
  { id: 4, time: '2026-07-07 20:35:18', operator: '李明哲', role: '学生', roleCode: 'student', action: '提交', actionCode: 'submit_quiz', actionType: '', detail: '提交实践与认识预习小测。', targetType: 'quiz_submission', targetLabel: '预习小测', targetId: 1, ip: '10.0.1.42', result: '成功', resultType: 'success' },
  { id: 5, time: '2026-07-07 15:00:00', operator: '系统', role: '系统', roleCode: 'system', action: '索引', actionCode: 'index_knowledge_source', actionType: 'success', detail: '资源完成解析、切片和向量索引。', targetType: 'knowledge_source', targetLabel: '知识来源', targetId: 1, ip: '127.0.0.1', result: '成功', resultType: 'success' },
  { id: 6, time: '2026-07-07 11:05:33', operator: '平台管理员', role: '管理员', roleCode: 'admin', action: '登录', actionCode: 'admin_login', actionType: '', detail: '管理端登录 - 账号密码登录。', targetType: 'session', targetLabel: '登录会话', targetId: 9001, ip: '10.0.0.1', result: '失败', resultType: 'danger' }
]

function buildAuditLogDetail(id) {
  const log = auditLogList.find((item) => String(item.id) === String(id)) || auditLogList[0]
  const isFailed = log.result !== '成功'
  const changeRows = {
    approve_ai_content: [
      { field: 'review_status', before: 'pending', after: 'approved', desc: '审核状态从待审核变为已通过。' },
      { field: 'reviewer_id', before: '未分配', after: log.operator, desc: '记录人工审核人。' }
    ],
    publish_lesson_design: [
      { field: 'lesson_status', before: 'approved', after: 'published', desc: '教学设计发布给学生端。' },
      { field: 'prestudy_task', before: 'draft', after: 'published', desc: '同步发布预习任务。' }
    ],
    update_user_scope: [
      { field: 'data_scope', before: '未确认', after: '授课班级数据', desc: '确认用户可访问的数据范围。' },
      { field: 'permission_reviewed_at', before: '-', after: log.time, desc: '记录权限复核时间。' }
    ],
    index_knowledge_source: [
      { field: 'index_status', before: 'pending', after: 'indexed', desc: '知识来源进入检索索引。' },
      { field: 'chunk_count', before: '0', after: '3', desc: '生成可检索文本切片。' }
    ]
  }

  return {
    log: {
      ...log,
      risk: isFailed ? '需排查' : log.roleCode === 'admin' ? '高权限操作' : '低风险',
      riskType: isFailed || log.roleCode === 'admin' ? 'warning' : 'success'
    },
    stats: [
      { label: '执行结果', value: log.result, color: isFailed ? '#F56C6C' : '#67C23A', desc: isFailed ? '需复核原因' : '已完成' },
      { label: '操作类型', value: log.action, color: '#409EFF', desc: log.actionCode },
      { label: '目标对象', value: log.targetLabel, color: '#E6A23C', desc: `${log.targetType} #${log.targetId}` },
      { label: '风险标记', value: isFailed ? '异常' : '正常', color: isFailed ? '#F56C6C' : '#909399', desc: log.ip }
    ],
    actor: {
      name: log.operator,
      role: log.role,
      roleCode: log.roleCode,
      account: log.roleCode === 'admin' ? 'admin01' : log.roleCode === 'teacher' ? 'teacher01' : log.roleCode === 'student' ? 'student01' : 'system',
      dataScope: log.roleCode === 'admin' ? '全校平台数据' : log.roleCode === 'teacher' ? '授课班级数据' : log.roleCode === 'student' ? '本人学习数据' : '系统任务'
    },
    request: {
      method: log.actionCode.includes('login') ? 'POST' : 'GET/POST',
      route: `/api/${log.targetType}/${log.targetId}`,
      ip: log.ip,
      userAgent: 'Mozilla/5.0 · Chrome · Windows',
      sessionId: `${log.roleCode}-session-20260708`,
      traceId: `trace-${String(log.id).padStart(6, '0')}`
    },
    changes: changeRows[log.actionCode] || [
      { field: 'action', before: '-', after: log.actionCode, desc: log.detail }
    ],
    relatedRecords: [
      { type: log.targetLabel, id: log.targetId, title: log.detail, status: log.result },
      { type: '操作人', id: log.actorId || '-', title: `${log.operator} · ${log.role}`, status: '已识别' }
    ],
    timeline: [
      { title: '接收请求', time: log.time, desc: `来源 IP ${log.ip} 发起 ${log.action} 操作。` },
      { title: '权限校验', time: log.time, desc: `${log.operator} 具备 ${log.targetLabel} 相关权限。` },
      { title: '执行业务动作', time: log.time, desc: log.detail },
      { title: '写入审计日志', time: log.time, desc: isFailed ? '失败操作已记录，等待排查。' : '操作结果和上下文已归档。' }
    ],
    complianceChecks: [
      { name: '操作人识别', result: log.operator ? '通过' : '缺失', type: log.operator ? 'success' : 'danger', desc: '检查审计日志是否关联明确操作主体。' },
      { name: '目标对象定位', result: log.targetType ? '通过' : '缺失', type: log.targetType ? 'success' : 'danger', desc: '检查目标类型和目标 ID 是否可追踪。' },
      { name: '来源 IP 记录', result: log.ip ? '通过' : '缺失', type: log.ip ? 'success' : 'warning', desc: '检查请求来源是否记录。' },
      { name: '结果可解释性', result: isFailed ? '需补充' : '通过', type: isFailed ? 'warning' : 'success', desc: isFailed ? '失败日志建议补充失败原因码。' : '操作结果与详情一致。' }
    ],
    rawContext: {
      id: log.id,
      action: log.actionCode,
      target_type: log.targetType,
      target_id: log.targetId,
      operator: log.operator,
      ip: log.ip,
      result: log.result,
      created_at: log.time
    }
  }
}

const systemSettingsPayload = {
  stats: [
    { label: '配置项', value: '6', color: '#409EFF', desc: '当前可治理参数' },
    { label: '启用项', value: '5', color: '#67C23A', desc: '已生效配置' },
    { label: '需复核', value: '1', color: '#E6A23C', desc: '阈值较高或敏感' },
    { label: '最近变更', value: '3', color: '#909399', desc: '7 日内记录' }
  ],
  config: {
    platformName: '马原智学 Agent',
    semester: '2025-2026-2',
    aiModel: 'default',
    autoReviewThreshold: 80,
    loginLockAttempts: 5,
    sessionTimeout: 120
  },
  semesters: ['2025-2026-1', '2025-2026-2', '2026-2027-1'],
  configList: [
    { key: 'platformName', group: '平台基础', name: '平台名称', value: '马原智学 Agent', displayValue: '马原智学 Agent', type: '文本', status: '已启用', statusType: 'success', risk: '低', updatedAt: '2026-07-08 09:00' },
    { key: 'semester', group: '平台基础', name: '当前学期', value: '2025-2026-2', displayValue: '2025-2026-2', type: '枚举', status: '已启用', statusType: 'success', risk: '低', updatedAt: '2026-07-08 09:00' },
    { key: 'aiModel', group: '模型审核', name: 'AI 模型选择', value: 'default', displayValue: '默认模型', type: '枚举', status: '已启用', statusType: 'success', risk: '中', updatedAt: '2026-07-07 18:30' },
    { key: 'autoReviewThreshold', group: '模型审核', name: '自动审核阈值', value: 80, displayValue: '80 分', type: '数值', status: '需复核', statusType: 'warning', risk: '中', updatedAt: '2026-07-07 18:30' },
    { key: 'loginLockAttempts', group: '安全会话', name: '登录失败锁定', value: 5, displayValue: '5 次', type: '数值', status: '已启用', statusType: 'success', risk: '低', updatedAt: '2026-07-07 16:10' },
    { key: 'sessionTimeout', group: '安全会话', name: '会话超时', value: 120, displayValue: '120 分钟', type: '数值', status: '已启用', statusType: 'success', risk: '低', updatedAt: '2026-07-07 16:10' }
  ],
  sysStatus: [
    { label: '后端服务', value: '运行中', color: '#67C23A' },
    { label: '数据库连接', value: '已连接', color: '#67C23A' },
    { label: '索引状态', value: '已索引', color: '#67C23A' },
    { label: '审计日志', value: '开启', color: '#409EFF' },
    { label: 'Mock 切换', value: '可用', color: '#E6A23C' }
  ],
  maintenanceActions: [
    { key: 'cleanup_logs', name: '清理过期日志', desc: '清理超过保留周期的低风险日志。', level: '普通', type: 'info' },
    { key: 'backup_database', name: '备份数据库', desc: '导出课程、用户、知识库和审计表。', level: '推荐', type: 'success' },
    { key: 'rebuild_index', name: '重建搜索索引', desc: '重新解析知识来源并刷新向量索引。', level: '谨慎', type: 'warning' },
    { key: 'reset_system', name: '重置系统', desc: '高风险操作，仅限演示环境。', level: '高风险', type: 'danger' }
  ]
}

function buildSystemConfigDetail(key) {
  const configItem = systemSettingsPayload.configList.find((item) => item.key === key) || systemSettingsPayload.configList[0]
  const rules = {
    platformName: { range: '2-30 个字符', defaultValue: '马原智学 Agent', owner: '平台管理员', impact: '影响登录页、顶部导航和导出报表标题。' },
    semester: { range: '学年-学年-学期', defaultValue: '2025-2026-2', owner: '教务管理员', impact: '影响课程、班级、任务和学情统计的默认筛选。' },
    aiModel: { range: 'default / advanced', defaultValue: 'default', owner: '模型管理员', impact: '影响教案生成、问答和批改建议的模型路由。' },
    autoReviewThreshold: { range: '60-95 分', defaultValue: 80, owner: '审核管理员', impact: '影响 AI 内容和作业批改建议进入人工复核的比例。' },
    loginLockAttempts: { range: '3-10 次', defaultValue: 5, owner: '安全管理员', impact: '影响账号防暴力破解策略。' },
    sessionTimeout: { range: '15-480 分钟', defaultValue: 120, owner: '安全管理员', impact: '影响学生端、教师端和管理端登录会话时长。' }
  }
  const rule = rules[configItem.key] || rules.platformName

  return {
    config: {
      ...configItem,
      owner: rule.owner,
      range: rule.range,
      defaultValue: rule.defaultValue,
      impact: rule.impact
    },
    stats: [
      { label: '当前状态', value: configItem.status, color: configItem.statusType === 'warning' ? '#E6A23C' : '#67C23A', desc: configItem.group },
      { label: '风险等级', value: configItem.risk, color: configItem.risk === '中' ? '#E6A23C' : '#67C23A', desc: '配置变更风险' },
      { label: '变更次数', value: '3', color: '#409EFF', desc: '近 30 日' },
      { label: '生效范围', value: '三端', color: '#909399', desc: '学生/教师/管理端' }
    ],
    validationRules: [
      { name: '取值范围', result: rule.range, type: 'success', desc: '保存前校验配置值是否落在允许范围内。' },
      { name: '默认值', result: String(rule.defaultValue), type: 'info', desc: '恢复默认时使用该值。' },
      { name: '权限要求', result: rule.owner, type: 'warning', desc: '只有对应管理员或超级管理员可修改。' }
    ],
    changeHistory: [
      { version: 'v3', operator: '平台管理员', before: String(rule.defaultValue), after: String(configItem.displayValue), time: configItem.updatedAt, status: '已生效' },
      { version: 'v2', operator: '系统初始化', before: '-', after: String(rule.defaultValue), time: '2026-07-07 11:48', status: '已归档' },
      { version: 'v1', operator: '部署脚本', before: '-', after: '创建配置项', time: '2026-07-07 11:30', status: '已归档' }
    ],
    relatedModules: [
      { module: '登录与身份认证', usage: configItem.key.includes('login') || configItem.key.includes('session') ? '直接影响' : '间接影响', status: '已接入' },
      { module: 'AI 内容审核', usage: configItem.key.includes('ai') || configItem.key.includes('Review') ? '直接影响' : '间接影响', status: '已接入' },
      { module: '课程学情统计', usage: configItem.key === 'semester' ? '直接影响' : '间接影响', status: '已接入' }
    ],
    timeline: [
      { title: '读取当前配置', time: configItem.updatedAt, desc: `当前值为 ${configItem.displayValue}。` },
      { title: '校验配置规则', time: configItem.updatedAt, desc: `校验范围：${rule.range}。` },
      { title: '写入审计记录', time: configItem.updatedAt, desc: '配置变更会进入操作日志，支持追踪与回滚。' }
    ],
    rawConfig: {
      key: configItem.key,
      value: configItem.value,
      group: configItem.group,
      status: configItem.status,
      updated_at: configItem.updatedAt
    }
  }
}

const rolePermissionPayload = {
  roleDefinitions: [
    { id: 'role_admin', code: 'admin', name: '超级管理员', type: '系统', desc: '拥有平台所有功能权限', dataScope: '全校平台数据', owner: '平台管理员', status: '启用', statusType: 'warning', updatedAt: '2026-07-08 09:20', defaultUserCount: 2 },
    { id: 'role_teacher', code: 'teacher', name: '授课教师', type: '系统', desc: '课程教学、资源管理、学情分析', dataScope: '授课班级数据', owner: '教务管理员', status: '启用', statusType: 'success', updatedAt: '2026-07-08 09:10', defaultUserCount: 12 },
    { id: 'role_student', code: 'student', name: '学生', type: '系统', desc: '课程学习、作业提交、AI问答', dataScope: '本人学习数据', owner: '教务管理员', status: '启用', statusType: 'success', updatedAt: '2026-07-08 09:05', defaultUserCount: 1200 },
    { id: 'role_assistant', code: 'assistant', name: '教学助理', type: '自定义', desc: '辅助教师管理课程和批改作业', dataScope: '指定课程数据', owner: '课程管理员', status: '启用', statusType: 'success', updatedAt: '2026-07-07 18:30', defaultUserCount: 5 },
    { id: 'role_reviewer', code: 'reviewer', name: '内容审核员', type: '自定义', desc: '审核AI生成内容和知识库', dataScope: '内容治理数据', owner: '审核管理员', status: '复核中', statusType: 'warning', updatedAt: '2026-07-07 17:40', defaultUserCount: 3 }
  ],
  permissionCatalog: [
    {
      name: '用户管理',
      code: 'user',
      permissions: [
        { key: 'user_view', label: '查看用户', level: '读', desc: '查看账号、组织、课程绑定与账号状态。' },
        { key: 'user_create', label: '新增用户', level: '写', desc: '创建单个用户账号并绑定基础组织。' },
        { key: 'user_edit', label: '编辑用户', level: '写', desc: '调整账号状态、角色和数据范围。' },
        { key: 'user_delete', label: '删除用户', level: '高危', desc: '移除账号或解除平台访问。' },
        { key: 'user_import', label: '批量导入', level: '写', desc: '通过模板导入学生、教师和管理员账号。' }
      ]
    },
    {
      name: '课程管理',
      code: 'course',
      permissions: [
        { key: 'course_view', label: '查看课程', level: '读', desc: '查看课程、班级、教师和学生覆盖情况。' },
        { key: 'course_create', label: '新建课程', level: '写', desc: '创建课程、教学班和基础结构。' },
        { key: 'course_edit', label: '编辑课程', level: '写', desc: '维护课程章节、任务链和班级绑定。' },
        { key: 'course_archive', label: '归档课程', level: '高危', desc: '将课程从当前学期业务流转中归档。' }
      ]
    },
    {
      name: '内容治理',
      code: 'content',
      permissions: [
        { key: 'content_review', label: 'AI内容审核', level: '审核', desc: '复核教案、导学、题目和案例生成内容。' },
        { key: 'content_approve', label: '内容发布', level: '高危', desc: '确认内容可以进入学生端或教师端使用。' },
        { key: 'knowledge_edit', label: '知识库管理', level: '写', desc: '维护教材、课件、案例和题库来源。' },
        { key: 'assignment_view', label: '查看作业', level: '读', desc: '查看作业提交、AI建议评分和教师复核状态。' }
      ]
    },
    {
      name: '系统设置',
      code: 'system',
      permissions: [
        { key: 'settings_view', label: '查看设置', level: '读', desc: '查看平台基础、模型审核和安全会话配置。' },
        { key: 'settings_edit', label: '修改设置', level: '高危', desc: '修改会影响三端运行的系统级配置。' },
        { key: 'log_view', label: '查看日志', level: '审计', desc: '查看登录、审核、发布、索引和权限变更记录。' },
        { key: 'role_manage', label: '角色权限管理', level: '高危', desc: '维护角色权限矩阵和数据范围。' }
      ]
    }
  ],
  rolePermissionMap: {
    role_admin: [
      'user_view', 'user_create', 'user_edit', 'user_delete', 'user_import',
      'course_view', 'course_create', 'course_edit', 'course_archive',
      'content_review', 'content_approve', 'knowledge_edit', 'assignment_view',
      'settings_view', 'settings_edit', 'log_view', 'role_manage'
    ],
    role_teacher: ['course_view', 'course_edit', 'knowledge_edit', 'assignment_view', 'content_review'],
    role_student: ['course_view', 'assignment_view'],
    role_assistant: ['user_view', 'course_view', 'course_edit', 'knowledge_edit', 'assignment_view', 'content_review'],
    role_reviewer: ['course_view', 'content_review', 'content_approve', 'knowledge_edit', 'assignment_view', 'log_view']
  }
}

const roleCustomUsers = {
  role_assistant: [
    { id: 'A001', account: 'assistant01', name: '赵助教', dept: '马克思主义学院', status: '正常', statusType: 'success', lastLogin: '2026-07-08 08:40' },
    { id: 'A002', account: 'assistant02', name: '刘助教', dept: '马克思主义学院', status: '正常', statusType: 'success', lastLogin: '2026-07-07 18:20' }
  ],
  role_reviewer: [
    { id: 'R001', account: 'reviewer01', name: '内容审核员', dept: '教务处', status: '正常', statusType: 'success', lastLogin: '2026-07-08 09:10' },
    { id: 'R002', account: 'reviewer02', name: '知识库复核员', dept: '马克思主义学院', status: '待复核', statusType: 'warning', lastLogin: '2026-07-07 17:10' }
  ]
}

function roleDefinitionsWithCounts() {
  return rolePermissionPayload.roleDefinitions.map((role) => {
    const realCount = userList.filter((item) => item.roleCode === role.code).length
    const customCount = roleCustomUsers[role.id]?.length || 0

    return {
      ...role,
      userCount: realCount || customCount || role.defaultUserCount
    }
  })
}

function findRoleDefinition(roleId) {
  return roleDefinitionsWithCounts().find((item) => item.id === roleId || item.code === roleId) || roleDefinitionsWithCounts()[0]
}

function buildPermissionMatrix() {
  return rolePermissionPayload.permissionCatalog.map((group) => ({
    ...group,
    permissions: group.permissions.map((permission) => ({
      ...permission,
      grants: Object.fromEntries(rolePermissionPayload.roleDefinitions.map((role) => [
        role.id,
        rolePermissionPayload.rolePermissionMap[role.id]?.includes(permission.key) || false
      ]))
    }))
  }))
}

function buildRolePermissionGroups(roleId) {
  const grantedKeys = rolePermissionPayload.rolePermissionMap[roleId] || []

  return rolePermissionPayload.permissionCatalog.map((group) => ({
    ...group,
    permissions: group.permissions.map((permission) => {
      const granted = grantedKeys.includes(permission.key)

      return {
        ...permission,
        granted,
        status: granted ? '已授权' : '未授权',
        type: granted ? 'success' : 'info'
      }
    })
  }))
}

function assignedUsersForRole(roleId) {
  const role = findRoleDefinition(roleId)
  const users = userList
    .filter((item) => item.roleCode === role.code)
    .map((item) => ({
      id: item.userCode,
      account: item.account,
      name: item.name,
      dept: item.dept,
      status: item.status,
      statusType: item.statusType,
      lastLogin: item.lastLogin
    }))

  return users.length ? users : (roleCustomUsers[role.id] || [])
}

function buildRolePermissionList() {
  const roles = roleDefinitionsWithCounts()
  const allPermissionCount = rolePermissionPayload.permissionCatalog.reduce((sum, group) => sum + group.permissions.length, 0)
  const highRiskCount = rolePermissionPayload.permissionCatalog
    .flatMap((group) => group.permissions)
    .filter((item) => item.level === '高危').length

  return {
    stats: [
      { label: '角色数量', value: String(roles.length), color: '#409EFF', desc: '系统与自定义角色' },
      { label: '权限点', value: String(allPermissionCount), color: '#67C23A', desc: '当前权限矩阵' },
      { label: '高危权限', value: String(highRiskCount), color: '#E6A23C', desc: '需重点复核' },
      { label: '绑定用户', value: String(roles.reduce((sum, item) => sum + Number(item.userCount || 0), 0)), color: '#909399', desc: '按角色汇总' }
    ],
    roles,
    permissionGroups: buildPermissionMatrix()
  }
}

function buildRolePermissionDetail(roleId) {
  const role = findRoleDefinition(roleId)
  const permissionGroups = buildRolePermissionGroups(role.id)
  const grantedPermissions = permissionGroups.flatMap((group) => group.permissions.filter((item) => item.granted))
  const highRiskPermissions = grantedPermissions.filter((item) => item.level === '高危')
  const assignedUsers = assignedUsersForRole(role.id)

  return {
    role: {
      ...role,
      permissionCount: grantedPermissions.length
    },
    stats: [
      { label: '已授权权限', value: String(grantedPermissions.length), color: '#409EFF', desc: '当前角色权限点' },
      { label: '关联用户', value: String(role.userCount), color: '#67C23A', desc: '直接或配置绑定' },
      { label: '敏感权限', value: String(highRiskPermissions.length), color: highRiskPermissions.length ? '#E6A23C' : '#67C23A', desc: '高危操作需复核' },
      { label: '最近复核', value: role.updatedAt.slice(5, 10), color: '#909399', desc: role.updatedAt }
    ],
    permissionGroups,
    assignedUsers,
    changeHistory: [
      { version: 'v4', operator: role.owner, before: '权限矩阵复核', after: `${grantedPermissions.length} 个权限生效`, time: role.updatedAt, status: '已生效' },
      { version: 'v3', operator: '平台管理员', before: '旧版权限模板', after: '按管理端页面清单补齐详情入口', time: '2026-07-08 09:00', status: '已归档' },
      { version: 'v2', operator: '系统初始化', before: '-', after: '创建角色权限配置', time: '2026-07-07 11:48', status: '已归档' }
    ],
    complianceChecks: [
      { name: '最小权限原则', result: role.id === 'role_admin' ? '需定期复核' : '通过', type: role.id === 'role_admin' ? 'warning' : 'success', desc: '检查角色是否只保留当前职责必要权限。' },
      { name: '高危权限复核', result: highRiskPermissions.length ? `${highRiskPermissions.length} 项` : '无', type: highRiskPermissions.length ? 'warning' : 'success', desc: '删除、发布、系统配置和角色管理权限需要审计。' },
      { name: '数据范围匹配', result: '通过', type: 'success', desc: `角色数据范围为“${role.dataScope}”。` },
      { name: '用户绑定校验', result: assignedUsers.length ? '通过' : '待绑定', type: assignedUsers.length ? 'success' : 'info', desc: '检查是否存在已绑定用户或演示账号。' }
    ],
    rawPermissionConfig: {
      role_id: role.id,
      role_code: role.code,
      data_scope: role.dataScope,
      permission_keys: grantedPermissions.map((item) => item.key),
      high_risk_permission_keys: highRiskPermissions.map((item) => item.key),
      updated_at: role.updatedAt
    }
  }
}

const orgNodeDefinitions = [
  { id: 'org_root', parentId: '', name: '全校思政教学组织', type: '学校', level: 0, owner: '平台管理员', status: '运行中', statusType: 'success', desc: '承载全校思政课程、账号、班级和治理配置的根组织。', updatedAt: '2026-07-08 09:30' },
  { id: 'college_marxism', parentId: 'org_root', name: '马克思主义学院', type: '学院', level: 1, owner: '王老师', status: '运行中', statusType: 'success', desc: '负责马克思主义基本原理、中国近现代史纲要、思想道德与法治等课程建设。', updatedAt: '2026-07-08 09:20' },
  { id: 'dept_academic', parentId: 'org_root', name: '教务处', type: '部门', level: 1, owner: '平台管理员', status: '运行中', statusType: 'success', desc: '负责账号、课程开设、组织字典和数据治理复核。', updatedAt: '2026-07-08 09:10' },
  { id: 'dept_platform', parentId: 'org_root', name: '平台治理组', type: '部门', level: 1, owner: '平台管理员', status: '需复核', statusType: 'warning', desc: '负责系统设置、角色权限、审计日志和数据安全策略。', updatedAt: '2026-07-07 18:30' },
  { id: 'major_ideology', parentId: 'college_marxism', name: '思想政治教育', type: '专业', level: 2, owner: '王老师', status: '运行中', statusType: 'success', desc: '思政专业学生与课程教学组织。', updatedAt: '2026-07-08 09:00' },
  { id: 'major_law', parentId: 'college_marxism', name: '法学', type: '专业', level: 2, owner: '何老师', status: '运行中', statusType: 'success', desc: '法学专业思政课程班级与学生组织。', updatedAt: '2026-07-07 17:40' },
  { id: 'major_public', parentId: 'college_marxism', name: '公共管理', type: '专业', level: 2, owner: '李老师', status: '需复核', statusType: 'warning', desc: '公共管理专业账号和课程绑定需定期检查。', updatedAt: '2026-07-07 16:50' },
  { id: 'dept_teaching', parentId: 'college_marxism', name: '思政课程教研室', type: '部门', level: 2, owner: '王老师', status: '运行中', statusType: 'success', desc: '教师、教学助理和课程资源建设协同部门。', updatedAt: '2026-07-08 08:50' },
  { id: 'class_undergrad_1', parentId: 'major_ideology', name: '2023级本科1班', type: '班级', level: 3, owner: '王老师', status: '运行中', statusType: 'success', desc: '马克思主义基本原理课程重点演示班级。', updatedAt: '2026-07-08 08:30' },
  { id: 'class_undergrad_2', parentId: 'major_ideology', name: '2023级本科2班', type: '班级', level: 3, owner: '李老师', status: '运行中', statusType: 'success', desc: '中国近现代史纲要课程演示班级。', updatedAt: '2026-07-08 08:20' },
  { id: 'class_law_1', parentId: 'major_law', name: '2023级法学1班', type: '班级', level: 3, owner: '何老师', status: '运行中', statusType: 'success', desc: '思想道德与法治课程班级。', updatedAt: '2026-07-07 16:30' },
  { id: 'class_public_1', parentId: 'major_public', name: '2023级公管1班', type: '班级', level: 3, owner: '何老师', status: '待完善', statusType: 'warning', desc: '公共管理专业课程绑定待补齐。', updatedAt: '2026-07-07 16:10' }
]

function descendantOrgIds(nodeId) {
  const children = orgNodeDefinitions.filter((item) => item.parentId === nodeId)
  return children.flatMap((item) => [item.id, ...descendantOrgIds(item.id)])
}

function orgChildren(nodeId) {
  return orgNodeDefinitions.filter((item) => item.parentId === nodeId)
}

function orgTree(parentId = '') {
  return orgNodeDefinitions
    .filter((item) => item.parentId === parentId)
    .map((item) => ({
      ...item,
      children: orgTree(item.id)
    }))
}

function usersForOrgNode(node) {
  if (!node || node.id === 'org_root') return userList.slice(0, 8)
  if (node.type === '学院') return userList.filter((item) => item.dept === node.name)
  if (node.type === '专业') return userList.filter((item) => item.major === node.name)
  if (node.type === '班级') return userList.filter((item) => item.className === node.name)
  if (node.id === 'dept_academic' || node.id === 'dept_platform') return userList.filter((item) => item.roleCode === 'admin')
  if (node.id === 'dept_teaching') return userList.filter((item) => item.roleCode === 'teacher')

  return []
}

function classesForOrgNode(node) {
  if (!node || node.id === 'org_root' || node.type === '学院') return courseManagementPayload.classes
  if (node.type === '班级') return courseManagementPayload.classes.filter((item) => item.name === node.name)
  if (node.type === '专业') {
    const childNames = orgChildren(node.id).map((item) => item.name)
    return courseManagementPayload.classes.filter((item) => childNames.includes(item.name))
  }
  if (node.id === 'dept_teaching') {
    return courseManagementPayload.classes.filter((item) => ['王老师', '李老师', '何老师'].includes(item.teacher))
  }

  return []
}

function enrichOrgNode(node) {
  const scopeIds = [node.id, ...descendantOrgIds(node.id)]
  const scopedNodes = orgNodeDefinitions.filter((item) => scopeIds.includes(item.id))
  const members = usersForOrgNode(node)
  const classes = classesForOrgNode(node)
  const courseIds = new Set(classes.map((item) => item.courseId))

  return {
    ...node,
    childCount: scopedNodes.length - 1,
    userCount: members.length,
    studentCount: members.filter((item) => item.roleCode === 'student').length,
    teacherCount: members.filter((item) => item.roleCode === 'teacher').length,
    classCount: classes.length,
    courseCount: courseIds.size
  }
}

function buildOrgStructurePayload() {
  const nodes = orgNodeDefinitions.map(enrichOrgNode)
  const warningCount = nodes.filter((item) => item.statusType === 'warning').length

  return {
    stats: [
      { label: '组织节点', value: String(nodes.length), color: '#409EFF', desc: '学院、专业、班级、部门' },
      { label: '教学班级', value: String(nodes.filter((item) => item.type === '班级').length), color: '#67C23A', desc: '当前组织树' },
      { label: '绑定用户', value: String(userList.length), color: '#E6A23C', desc: '账号归属关系' },
      { label: '待复核节点', value: String(warningCount), color: warningCount ? '#F56C6C' : '#67C23A', desc: '组织或绑定待确认' }
    ],
    nodes,
    tree: orgTree(),
    recentChanges: [
      { action: '同步课程班级', operator: '系统', target: '2023级本科1班', time: '2026-07-08 09:30', status: '已完成' },
      { action: '复核组织字典', operator: '平台管理员', target: '平台治理组', time: '2026-07-08 09:10', status: '需复核' },
      { action: '更新专业绑定', operator: '教务管理员', target: '公共管理', time: '2026-07-07 16:50', status: '待确认' }
    ],
    qualityChecks: [
      { name: '账号归属完整性', result: '通过', type: 'success', desc: '用户均可映射到学院、专业、班级或部门。' },
      { name: '班级课程绑定', result: '需复核', type: 'warning', desc: '部分班级需确认课程与教师绑定。' },
      { name: '高权限部门', result: '需定期复核', type: 'warning', desc: '平台治理组关联系统设置、角色权限和审计数据。' }
    ]
  }
}

function buildOrgNodeDetail(nodeId) {
  const node = enrichOrgNode(orgNodeDefinitions.find((item) => item.id === nodeId) || orgNodeDefinitions[0])
  const children = orgChildren(node.id).map(enrichOrgNode)
  const members = usersForOrgNode(node).map((item) => ({
    id: item.userCode,
    account: item.account,
    name: item.name,
    role: item.role,
    dept: item.dept,
    major: item.major,
    className: item.className,
    status: item.status,
    statusType: item.statusType,
    lastLogin: item.lastLogin
  }))
  const boundClasses = classesForOrgNode(node).map((item) => ({
    ...item,
    course: courseManagementPayload.courses.find((course) => course.id === item.courseId)?.name || '-'
  }))
  const relatedCourses = courseManagementPayload.courses
    .filter((course) => boundClasses.some((item) => item.courseId === course.id) || node.id === 'org_root' || node.type === '学院')
    .map((course) => ({
      id: course.id,
      name: course.name,
      code: course.code,
      semester: course.semester,
      classCount: course.classCount,
      studentCount: course.studentCount,
      status: course.status,
      statusType: course.statusType
    }))

  return {
    node,
    stats: [
      { label: '子节点', value: String(node.childCount), color: '#409EFF', desc: '下级组织数量' },
      { label: '绑定用户', value: String(node.userCount), color: '#67C23A', desc: '当前节点范围' },
      { label: '教学班级', value: String(node.classCount), color: '#E6A23C', desc: '课程班级关系' },
      { label: '课程覆盖', value: String(node.courseCount), color: '#909399', desc: '关联课程数量' }
    ],
    children,
    members,
    boundClasses,
    relatedCourses,
    governanceRules: [
      { name: '组织归属', result: node.parentId ? '已绑定上级' : '根节点', type: 'success', desc: '检查节点是否存在明确上级组织。' },
      { name: '用户绑定', result: node.userCount ? '通过' : '待补充', type: node.userCount ? 'success' : 'info', desc: '检查节点范围内是否有关联用户。' },
      { name: '课程班级', result: node.classCount ? '已绑定' : '待绑定', type: node.classCount ? 'success' : 'warning', desc: '检查组织节点是否承载课程或教学班。' },
      { name: '治理状态', result: node.status, type: node.statusType, desc: '需复核节点应确认组织字典、账号归属和课程关系。' }
    ],
    timeline: [
      { title: '组织节点建档', time: '2026-07-07 11:48', desc: `创建 ${node.name} 节点并写入组织树。` },
      { title: '账号归属同步', time: '2026-07-08 09:10', desc: '同步用户角色、学院、专业、班级和部门归属。' },
      { title: '课程关系检查', time: node.updatedAt, desc: '检查课程、教师、班级和学生覆盖关系。' }
    ],
    rawNode: {
      id: node.id,
      parent_id: node.parentId,
      name: node.name,
      type: node.type,
      level: node.level,
      status: node.status,
      user_count: node.userCount,
      class_count: node.classCount,
      updated_at: node.updatedAt
    }
  }
}

const rubricPayload = {
  stats: [
    { label: '量规总数', value: '2', color: '#409EFF', desc: '已建评分标准' },
    { label: '启用量规', value: '1', color: '#67C23A', desc: '可用于批改' },
    { label: '评分维度', value: '6', color: '#E6A23C', desc: '覆盖概念、案例、表达' },
    { label: '当前权重', value: '100%', color: '#67C23A', desc: '启用量规权重合计' }
  ],
  rubricList: [
    {
      id: 1,
      title: '实践与认识材料分析题评分量规',
      scenario: '课后材料分析作业',
      course: '马克思主义基本原理',
      owner: '王老师',
      itemCount: 4,
      totalScore: 100,
      totalWeight: 100,
      status: '启用中',
      statusType: 'success',
      updatedAt: '2026/07/07 15:00'
    },
    {
      id: 2,
      title: '课前预习小测简答题量规',
      scenario: '预习简答题',
      course: '马克思主义基本原理',
      owner: '王老师',
      itemCount: 2,
      totalScore: 20,
      totalWeight: 20,
      status: '草稿',
      statusType: 'info',
      updatedAt: '2026/07/07 15:00'
    }
  ],
  activeRubric: {
    id: 1,
    title: '实践与认识材料分析题评分量规',
    scenario: '课后材料分析作业',
    course: '马克思主义基本原理',
    owner: '王老师',
    totalScore: 100,
    status: '启用中',
    statusType: 'success',
    description: '用于约束 AI 批改建议和教师复核，重点检查概念准确、案例分析、论证结构与价值表达。',
    items: [
      {
        id: 1,
        name: '概念理解准确性',
        weight: 30,
        evidence: '检查学生是否准确使用实践、认识、真理、价值等核心概念。',
        levels: [
          { level: '优秀', score: 30, desc: '核心概念准确，能说明实践对认识的决定作用。' },
          { level: '合格', score: 22, desc: '主要概念基本正确，但辨析不够充分。' },
          { level: '待改进', score: 12, desc: '概念混淆或出现明显理论表述错误。' }
        ]
      },
      {
        id: 2,
        name: '理论联系实际',
        weight: 25,
        evidence: '检查学生是否能用实践观点分析社会调研、科研训练或现实案例。',
        levels: [
          { level: '优秀', score: 25, desc: '案例真实贴切，理论与案例对应清楚。' },
          { level: '合格', score: 18, desc: '能联系案例，但分析深度不足。' },
          { level: '待改进', score: 10, desc: '案例牵强或只复述材料。' }
        ]
      },
      {
        id: 3,
        name: '论证结构与表达',
        weight: 25,
        evidence: '检查答案是否有明确观点、分层论证和必要结论。',
        levels: [
          { level: '优秀', score: 25, desc: '观点明确，层次清晰，论证完整。' },
          { level: '合格', score: 18, desc: '结构基本完整，但论证略显松散。' },
          { level: '待改进', score: 9, desc: '观点不清或堆砌概念。' }
        ]
      },
      {
        id: 4,
        name: '价值导向与规范性',
        weight: 20,
        evidence: '检查表达是否符合课程规范，是否避免虚假引用和不当表述。',
        levels: [
          { level: '优秀', score: 20, desc: '表达稳妥，来源意识清楚，价值导向明确。' },
          { level: '合格', score: 14, desc: '总体规范，但来源或表达可进一步明确。' },
          { level: '待改进', score: 6, desc: '存在不准确引用或表达风险。' }
        ]
      }
    ]
  }
}

const assignmentDetailPayload = {
  assignment: {
    id: 1,
    title: '实践与认识及其发展规律学习心得',
    type: '课后材料分析作业',
    course: '马克思主义基本原理',
    chapter: '实践与认识及其发展规律',
    className: '2023级本科1班',
    deadline: '2026-07-15 22:00',
    publisher: '王老师',
    status: '批改中',
    statusType: 'warning',
    description: '围绕“实践与认识及其发展规律”章节，结合社会实践、实验课程或科研训练案例，分析实践如何推动认识深化。',
    rubricTitle: '实践与认识材料分析题评分量规'
  },
  stats: [
    { label: '提交人数', value: '38/42', color: '#409EFF', desc: '90% 已提交' },
    { label: '平均分', value: '82.0', color: '#67C23A', desc: '按当前提交统计' },
    { label: '待复核', value: '12', color: '#E6A23C', desc: '需教师确认' },
    { label: '低分预警', value: '3', color: '#F56C6C', desc: '低于 70 分' }
  ],
  rubric: rubricPayload.activeRubric,
  questions: [
    { id: 1, order: 1, type: '材料分析题', knowledgePoint: '实践与认识', stem: '结合一次实践活动，说明实践如何推动认识深化。', source: '已绑定知识来源', auditStatus: '已审核' },
    { id: 2, order: 2, type: '简答题', knowledgePoint: '真理标准', stem: '为什么说实践是检验真理的唯一标准？', source: '已绑定知识来源', auditStatus: '已审核' }
  ],
  submissions: [
    { studentId: 1, studentName: '李明哲', studentNo: 'student01', answered: '5/5', score: '100.0', submittedAt: '2026/07/07 20:35', status: '已提交', statusType: 'success', reviewStatus: '教师已确认', reviewType: 'success' },
    { studentId: 2, studentName: '陈思源', studentNo: 'student02', answered: '5/5', score: '86.0', submittedAt: '2026/07/07 19:50', status: '已提交', statusType: 'success', reviewStatus: 'AI建议待复核', reviewType: 'warning' },
    { studentId: 3, studentName: '周若涵', studentNo: 'student03', answered: '0/5', score: '待提交', submittedAt: '', status: '未提交', statusType: 'info', reviewStatus: '待提交', reviewType: 'info' }
  ],
  scoreDistribution: [
    { range: '90-100', count: 12, color: '#67C23A', height: 180 },
    { range: '80-89', count: 18, color: '#67C23A', height: 220 },
    { range: '70-79', count: 5, color: '#409EFF', height: 90 },
    { range: '60-69', count: 3, color: '#E6A23C', height: 70 },
    { range: '<60', count: 0, color: '#F56C6C', height: 40 }
  ],
  timeline: [
    { title: '作业发布', time: '2026-07-07 14:30', desc: '教师发布材料分析作业并绑定评分量规。' },
    { title: '学生提交', time: '2026-07-07 19:50', desc: '已有学生提交作答内容。' },
    { title: 'AI建议评分', time: '已生成', desc: '系统根据评分量规生成分项建议和风险提示。' },
    { title: '教师复核', time: '待复核', desc: '教师确认分数、评语和反馈发布状态。' }
  ]
}

const aiReviewDetailPayload = {
  review: {
    id: 1,
    title: '实践与认识及其发展规律教学设计方案',
    type: '教案',
    targetType: 'lesson_design',
    targetId: 1,
    risk: '低风险',
    riskType: 'success',
    status: '已通过',
    statusType: 'success',
    reviewer: '平台管理员',
    reviewComment: '内容符合课程目标，可进入教学使用。',
    createdAt: '2026/07/07 10:23',
    reviewedAt: '2026/07/07 10:35',
    contentPreview: 'AI 生成的章节教学设计，包含目标、案例和讨论题。'
  },
  target: {
    title: '实践与认识及其发展规律教学设计方案',
    type: '教案',
    course: '马克思主义基本原理',
    chapter: '实践与认识及其发展规律',
    owner: '王老师',
    status: 'published',
    version: 'v1',
    updatedAt: '2026/07/07 10:23',
    sections: [
      { title: '教学目标', content: '理解实践、认识、真理和价值的基本含义；能够用实践观点分析现实案例。' },
      { title: '重点知识', content: '实践的含义与特征、实践对认识的决定作用、认识运动的两次飞跃。' },
      { title: '课堂流程', content: '导入：人的认识从哪里来 / 讲授：实践对认识的决定作用 / 辨析：真理标准与价值判断 / 总结：从认识回到实践' },
      { title: '讨论问题', content: '为什么说实践是认识的来源？大学生社会实践如何推动认识深化？' }
    ],
    sources: [
      { type: '教材', title: '《马克思主义基本原理》教材第三章', status: '已绑定' },
      { type: '案例', title: '大学生社会实践案例库', status: '已绑定' }
    ]
  },
  stats: [
    { label: '审核状态', value: '已通过', color: '#67C23A', desc: '当前处理结果' },
    { label: '风险等级', value: '低风险', color: '#67C23A', desc: '模型初筛结果' },
    { label: '来源数量', value: '2', color: '#409EFF', desc: '已绑定依据' },
    { label: '处理记录', value: '1', color: '#909399', desc: '审核日志' }
  ],
  riskItems: [
    { level: '低', type: 'success', title: '内容安全与价值导向', evidence: '教学设计围绕教材第三章展开，未发现明显不当表述。', suggestion: '可按流程确认，发布前保留教师复核记录。' },
    { level: '低', type: 'success', title: '知识来源可追溯', evidence: '已绑定教材与案例库来源。', suggestion: '课堂使用时保留教材章节和案例库条目引用。' }
  ],
  decision: {
    recommendedAction: '可通过',
    reviewer: '平台管理员',
    comment: '内容符合课程目标，可进入教学使用。',
    actions: [
      { label: '通过', type: 'success', desc: '确认内容可用于教学或学生端展示。' },
      { label: '要求修改', type: 'warning', desc: '保留记录并退回生成/编辑环节修订。' },
      { label: '拒绝', type: 'danger', desc: '内容不适合发布或进入教学使用。' }
    ]
  },
  timeline: [
    { title: '内容生成', time: '2026/07/07 10:23', desc: '教案进入 AI 内容审核队列。' },
    { title: '风险初筛', time: '2026/07/07 10:23', desc: '系统标记为低风险。' },
    { title: '人工审核', time: '2026/07/07 10:35', desc: '平台管理员已处理该记录。' },
    { title: '审核日志', time: '2026/07/07 10:35', desc: '管理员审核通过 AI 教学设计。' }
  ],
  auditLogs: [
    { action: 'approve_ai_content', operator: '平台管理员', detail: '管理员审核通过 AI 教学设计。', time: '2026/07/07 10:35' }
  ]
}

const knowledgeSourceDetailPayload = {
  source: {
    id: 1,
    title: '《马克思主义基本原理》教材全文',
    type: '教材',
    typeCode: 'textbook',
    course: '马克思主义基本原理',
    semester: '2025-2026-2',
    chapter: '实践与认识及其发展规律',
    chapterOrder: 3,
    description: '用于解释实践、认识、真理和价值等核心概念。',
    citation: '教材第三章相关内容',
    fileUrl: '',
    indexStatus: '已索引',
    indexType: 'success',
    auditStatus: '已审核',
    auditType: 'success',
    createdAt: '2026/07/07 14:30',
    updatedAt: '2026/07/07 15:00'
  },
  stats: [
    { label: '索引切片', value: '3', color: '#409EFF', desc: '可检索文本块' },
    { label: '关联题目', value: '4', color: '#67C23A', desc: '题库绑定数量' },
    { label: '审核记录', value: '1', color: '#E6A23C', desc: 'AI内容治理记录' },
    { label: '引用场景', value: '3', color: '#909399', desc: '问答、反馈、题库' }
  ],
  chunks: [
    { id: '1-1', title: '核心概念原文', locator: '第三章 · 教材概念段', content: '实践是认识的来源、动力、目的，也是检验认识真理性的唯一标准。', tokenCount: 120, embeddingStatus: '已向量化', quality: '高', usedBy: 'AI问答 / 作业反馈 / 题目解析' },
    { id: '1-2', title: '理论说明', locator: '第三章 · 认识运动', content: '认识从实践中产生，又回到实践中接受检验和发展。', tokenCount: 156, embeddingStatus: '已向量化', quality: '中', usedBy: 'AI问答' },
    { id: '1-3', title: '使用提示', locator: '平台引用规范', content: '引用教材观点时，应说明教材章节和理论命题。', tokenCount: 192, embeddingStatus: '已向量化', quality: '中', usedBy: '作业反馈' }
  ],
  indexJobs: [
    { step: '资源解析', status: '已完成', statusType: 'success', desc: '提取标题、说明、引用和章节信息。', time: '2026/07/07 15:00' },
    { step: '文本切片', status: '已完成', statusType: 'success', desc: '生成 3 个可检索片段。', time: '2026/07/07 15:00' },
    { step: '向量索引', status: '已索引', statusType: 'success', desc: '写入检索索引，供问答、反馈和题目解析调用。', time: '2026/07/07 15:00' },
    { step: '质量审核', status: '已审核', statusType: 'success', desc: '确认来源可用于教学场景。', time: '2026/07/07 15:00' }
  ],
  relatedQuestions: [
    { id: 1, type: '单选题', knowledgePoint: '实践与认识', stem: '下列关于实践与认识关系的说法，正确的是哪一项？', auditStatus: '已审核' },
    { id: 2, type: '单选题', knowledgePoint: '真理标准', stem: '为什么说实践是检验真理的唯一标准？', auditStatus: '已审核' }
  ],
  aiReviews: [
    { id: 1, title: '教材来源审核', risk: '低风险', riskType: 'success', status: '已通过', statusType: 'success', time: '2026/07/07 15:00' }
  ],
  usageRecords: [
    { scene: 'AI问答', target: '实践为什么是检验真理的唯一标准', status: '已引用', time: '2026/07/07 15:00' },
    { scene: '课后反馈', target: '实践与认识学习心得反馈依据', status: '已引用', time: '2026/07/07 15:00' },
    { scene: '题库', target: '2 道题目绑定该来源', status: '已绑定', time: '2026/07/07 15:00' }
  ],
  auditLogs: [
    { action: 'index_knowledge_source', operator: '系统', detail: '资源完成解析、切片和向量索引。', time: '2026/07/07 15:00' }
  ],
  qualityChecks: [
    { name: '来源完整性', result: '通过', type: 'success', desc: '检查说明、引用、课程和章节字段。' },
    { name: '索引可用性', result: '已索引', type: 'success', desc: '确认资源已经进入检索范围。' },
    { name: '审核合规', result: '已审核', type: 'success', desc: '确认资源可用于教学、问答和反馈。' },
    { name: '题目绑定', result: '已绑定', type: 'success', desc: '检查该来源是否支撑题库和练习。' }
  ]
}

const analyticsPayload = {
  metrics: [
    { label: '平台总用户', value: '1,280', color: '#67C23A', change: '↑ 12% 较上月' },
    { label: '月活用户', value: '856', color: '#409EFF', change: '↑ 8% 较上月' },
    { label: 'AI交互次数', value: '4,520', color: '#E6A23C', change: '↑ 25% 较上月' },
    { label: '待处理告警', value: '3', color: '#F56C6C', change: '↓ 2 较上月' }
  ],
  trendData: [
    { month: '1月', value: 320, color: '#e0ded8' },
    { month: '2月', value: 280, color: '#d5d3cd' },
    { month: '3月', value: 450, color: '#c9c7c0' },
    { month: '4月', value: 520, color: '#bdbab3' },
    { month: '5月', value: 610, color: '#b0ada5' },
    { month: '6月', value: 720, color: '#2f2f2f' }
  ],
  rankings: [
    { name: '毛泽东思想和中国特色社会主义理论体系概论', teacher: '陈教授', active: '92%' },
    { name: '中国近现代史纲要', teacher: '李老师', active: '85%' },
    { name: '马克思主义基本原理', teacher: '王教授', active: '78%' },
    { name: '形势与政策', teacher: '张老师', active: '72%' }
  ]
}

const assignmentManagementPayload = {
  courses: ['马克思主义基本原理', '中国近现代史纲要', '毛泽东思想和中国特色社会主义理论体系概论'],
  summary: [
    { label: '总作业数', value: '24', color: '#67C23A' },
    { label: '待批改', value: '42', color: '#E6A23C' },
    { label: '已完成', value: '18', color: '#409EFF' },
    { label: '逾期未交', value: '15', color: '#F56C6C' }
  ],
  assignments: [
    { id: 1, title: '实践与认识及其发展规律学习心得', course: '马克思主义基本原理', class: '2023级1班', submitCount: '38/42', avgScore: 82, deadline: '2026-06-01', status: '批改中' },
    { id: 2, title: '课堂讨论总结', course: '马克思主义基本原理', class: '2023级2班', submitCount: '36/38', avgScore: 85, deadline: '2026-05-28', status: '已完成' },
    { id: 3, title: '近代史人物评述', course: '中国近现代史纲要', class: '2023级1班', submitCount: '40/42', avgScore: 78, deadline: '2026-06-05', status: '进行中' },
    { id: 4, title: '社会实践与认识深化分析', course: '马克思主义基本原理', class: '2023级3班', submitCount: '32/40', avgScore: 80, deadline: '2026-05-30', status: '批改中' }
  ]
}

export function getAdminDashboard() {
  if (!isMockMode()) {
    return request('/admin/dashboard')
  }

  return mockResolve({
    adminQueue,
    statusCards: [
      { label: '内容治理队列', value: '18 条待审', desc: 'AI内容待审核 18 条，被拦截 3 条', tag: '优先', tagType: 'danger' },
      { label: '教学治理队列', value: '14 人待分配', desc: '新任课教师 14 人待分配课程', tag: '处理中', tagType: 'warning' }
    ],
    entries: [
      { title: '账号与教学组织', desc: '15-18 / 31-34 用户、课程、组织', tag: '管理', route: '/admin/user-management' },
      { title: '知识与内容治理', desc: '19-22 知识来源与 AI 审核', tag: '审核', route: '/admin/knowledge-base' },
      { title: '知识图谱管理', desc: '知识点关系可视化编辑与绑定', tag: '图谱', route: '/admin/knowledge-graph' }
    ],
    coreStats: [
      { label: '待处理', value: '18', desc: '内容治理优先', color: '#F56C6C' },
      { label: '告警', value: '3', desc: '建议今天处理', color: '#E6A23C' }
    ]
  })
}

export function getAnalytics() {
  if (!isMockMode()) {
    return request('/admin/analytics')
  }

  return mockResolve({
    users: { total: 5, students: 3, teachers: 1, admins: 1, activeToday: 2 },
    courses: { total: 1 },
    quizzes: { totalSubmissions: 25, avgScore: 78 },
    aiChat: { sessions: 3, messages: 18 },
    knowledgeSources: { total: 8, approved: 6, pending: 2 },
    aiReviews: { total: 12, pending: 3, approved: 9 }
  })
}

export function getPlatformAnalytics() {
  return getAnalytics()
}

export function getAssignmentManagement() {
  if (!isMockMode()) {
    return request('/admin/assignments')
  }

  return mockResolve(assignmentManagementPayload)
}

export function remindAssignment(id) {
  if (!isMockMode()) {
    return request(`/admin/assignments/${id}/remind`, {
      method: 'POST'
    })
  }

  return mockResolve({
    success: true,
    message: '已向未提交学生发送催交通知',
    ...assignmentManagementPayload
  })
}

export function getAiReviewList() {
  if (!isMockMode()) {
    return request('/admin/ai-review')
  }

  return mockResolve({
    stats: [
      { label: '待审核', value: '18', color: '#F56C6C', desc: '需要人工审核' },
      { label: '已通过', value: '142', color: '#67C23A', desc: '本周累计通过' },
      { label: '已拒绝', value: '6', color: '#909399', desc: '含违规内容' },
      { label: '被拦截', value: '3', color: '#E6A23C', desc: '敏感词自动拦截' }
    ],
    reviewList: [
      { id: 1, title: '实践与认识及其发展规律教学设计方案', type: '教案', source: '教材第三章 + 教师修订版课件', author: '系统生成', time: '今天 10:23', risk: '低风险', riskType: 'success', status: '已通过', statusType: 'success' },
      { id: 2, title: '大学生社会实践案例讨论', type: '案例', source: '案例库 + 教材第三章', author: '系统生成', time: '今天 09:15', risk: '低风险', riskType: 'success', status: '已通过', statusType: 'success' },
      { id: 3, title: '真理标准与认识发展导学卡', type: '导学', source: '教材 + AI整合', author: '系统生成', time: '昨天 16:42', risk: '待审查', riskType: 'warning', status: '待审核', statusType: 'warning' },
      { id: 4, title: '关于认识论方法训练的讨论题', type: '题目', source: '教材第三章', author: '王老师', time: '昨天 14:08', risk: '低风险', riskType: 'success', status: '待审核', statusType: 'warning' },
      { id: 5, title: '实践案例引用来源缺失内容', type: '案例', source: 'AI生成未标注来源', author: '系统生成', time: '昨天 11:30', risk: '高风险', riskType: 'danger', status: '需修改', statusType: 'info' }
    ]
  })
}

export function getAiReviewDetail(id) {
  if (!isMockMode()) {
    return request(`/admin/ai-review/${id}`)
  }

  return mockResolve({
    ...aiReviewDetailPayload,
    review: {
      ...aiReviewDetailPayload.review,
      id: Number(id) || 1
    }
  })
}

export function decideAiReview(id, action, comment = '') {
  if (!isMockMode()) {
    return request(`/admin/ai-review/${id}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action, comment })
    })
  }

  const statusMap = {
    approve: { status: '已通过', statusType: 'success', message: '审核通过' },
    revision: { status: '需修改', statusType: 'info', message: '要求修改' },
    reject: { status: '已拒绝', statusType: 'danger', message: '审核拒绝' }
  }
  const next = statusMap[action] || statusMap.revision

  return mockResolve({
    success: true,
    message: next.message,
    ...aiReviewDetailPayload,
    review: {
      ...aiReviewDetailPayload.review,
      id: Number(id) || 1,
      status: next.status,
      statusType: next.statusType,
      reviewComment: comment || next.message
    }
  })
}

export function getRubrics() {
  if (!isMockMode()) {
    return request('/admin/rubrics')
  }

  return mockResolve(rubricPayload)
}

export function createRubric(payload) {
  if (!isMockMode()) {
    return request('/admin/rubrics', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  }

  return mockResolve({
    success: true,
    message: '量规草稿已保存',
    ...rubricPayload
  })
}

export function getAssignmentDetail(id) {
  if (!isMockMode()) {
    return request(`/admin/assignments/${id}`)
  }

  return mockResolve({
    ...assignmentDetailPayload,
    assignment: {
      ...assignmentDetailPayload.assignment,
      id: Number(id) || 1
    }
  })
}

export function getKnowledgeSources() {
  if (!isMockMode()) {
    return request('/admin/knowledge-sources')
  }

  return mockResolve({
    stats: [
      { label: '教材资源', value: '8', color: '#409EFF', desc: '已全部索引' },
      { label: '课件资源', value: '23', color: '#67C23A', desc: '21份已索引' },
      { label: '案例库', value: '128', color: '#E6A23C', desc: '128条已审核' },
      { label: '题库', value: '94', color: '#909399', desc: '86道已审核' }
    ],
    knowledgeList: [
      { id: 1, name: '《马克思主义基本原理》教材全文', type: '教材', course: '马克思主义基本原理', size: '12章', indexStatus: '已索引', audit: '已审核', auditType: 'success', updateTime: '2025-09-01' },
      { id: 2, name: '王老师思政课教学课件合集', type: '课件', course: '马克思主义基本原理', size: '16份', indexStatus: '已索引', audit: '已审核', auditType: 'success', updateTime: '2025-10-15' },
      { id: 3, name: '大学生社会实践案例集', type: '案例', course: '马克思主义基本原理', size: '32条', indexStatus: '已索引', audit: '已审核', auditType: 'success', updateTime: '2025-11-20' },
      { id: 4, name: '实践与认识及其发展规律讨论题库', type: '题库', course: '马克思主义基本原理', size: '45道', indexStatus: '已索引', audit: '已审核', auditType: 'success', updateTime: '2025-12-05' },
      { id: 5, name: '时事热点思政教学素材', type: '素材', course: '全校通用', size: '18条', indexStatus: '待索引', audit: '待审核', auditType: 'warning', updateTime: '2026-01-08' }
    ]
  })
}

export function getKnowledgeSourceDetail(id) {
  if (!isMockMode()) {
    return request(`/admin/knowledge-sources/${id}`)
  }

  return mockResolve({
    ...knowledgeSourceDetailPayload,
    source: {
      ...knowledgeSourceDetailPayload.source,
      id: Number(id) || 1
    }
  })
}

export function reindexKnowledgeSources() {
  if (!isMockMode()) {
    return request('/admin/knowledge-sources/reindex', {
      method: 'POST'
    })
  }

  return mockResolve({ success: true, message: '已重新索引 5 条知识来源' })
}

export function reindexKnowledgeSource(id) {
  if (!isMockMode()) {
    return request(`/admin/knowledge-sources/${id}/reindex`, {
      method: 'POST'
    })
  }

  return mockResolve({
    success: true,
    message: '知识来源已重新索引',
    ...knowledgeSourceDetailPayload
  })
}

export function auditKnowledgeSource(id, action) {
  if (!isMockMode()) {
    return request(`/admin/knowledge-sources/${id}/audit`, {
      method: 'POST',
      body: JSON.stringify({ action })
    })
  }

  return mockResolve({
    success: true,
    message: action === 'approve' ? '知识来源已审核通过' : '知识来源已退回',
    ...knowledgeSourceDetailPayload
  })
}

export function getUsers() {
  if (!isMockMode()) {
    return request('/admin/users')
  }

  const activeCount = userList.filter((item) => item.statusCode === 'active').length
  const disabledCount = userList.length - activeCount
  const teacherCount = userList.filter((item) => item.roleCode === 'teacher').length
  const studentCount = userList.filter((item) => item.roleCode === 'student').length

  return mockResolve({
    stats: [
      { label: '用户总数', value: String(userList.length), color: '#409EFF', desc: '当前平台账号' },
      { label: '学生账号', value: String(studentCount), color: '#67C23A', desc: '已绑定班级' },
      { label: '教师账号', value: String(teacherCount), color: '#E6A23C', desc: '已绑定课程' },
      { label: '禁用账号', value: String(disabledCount), color: '#F56C6C', desc: '需定期清理' }
    ],
    users: userList,
    total: userList.length
  })
}

export function updateUserStatus(id, status) {
  if (!isMockMode()) {
    return request(`/admin/users/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    })
  }

  const user = userList.find((item) => String(item.id) === String(id))
  if (user) {
    user.statusCode = status === 'disabled' ? 'disabled' : 'active'
    user.status = user.statusCode === 'active' ? '正常' : '禁用'
    user.statusType = user.statusCode === 'active' ? 'success' : 'danger'
  }

  return mockResolve({
    success: true,
    message: status === 'disabled' ? '用户已禁用' : '用户已启用',
    user
  })
}

export function getUserDetail(id) {
  if (!isMockMode()) {
    return request(`/admin/users/${id}`)
  }

  return mockResolve(buildUserDetail(id))
}

export function getUserBatchImport() {
  if (!isMockMode()) {
    return request('/admin/users/batch-import')
  }

  return mockResolve(userBatchImportPayload)
}

export function confirmUserBatchImport() {
  if (!isMockMode()) {
    return request('/admin/users/batch-import/confirm', {
      method: 'POST'
    })
  }

  return mockResolve({
    success: true,
    message: '已导入 2 个用户，跳过 2 条记录',
    ...userBatchImportPayload
  })
}

/** 上传 Excel 批量导入用户 */
export async function uploadUserBatch(file) {
  if (!isMockMode()) {
    const token = (() => {
      try { return JSON.parse(sessionStorage.getItem('sizheng-user') || 'null')?.token || '' }
      catch { return '' }
    })()
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
    const form = new FormData()
    form.append('file', file)
    const resp = await fetch(`${API_BASE_URL}/admin/users/batch-import`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form
    })
    const data = await resp.json()
    if (!resp.ok) throw new Error(data.message || '导入失败')
    return data
  }
  // Mock
  return {
    total: 3, success: 2, failed: 1,
    errors: ['user03：账号已存在']
  }
}

/** 上传知识来源文件 */
export async function uploadKnowledgeFile(file, metadata = {}) {
  if (!isMockMode()) {
    const token = (() => {
      try { return JSON.parse(sessionStorage.getItem('sizheng-user') || 'null')?.token || '' }
      catch { return '' }
    })()
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
    const form = new FormData()
    form.append('file', file)
    if (metadata.title) form.append('title', metadata.title)
    if (metadata.sourceType) form.append('sourceType', metadata.sourceType)
    if (metadata.chapterId) form.append('chapterId', String(metadata.chapterId))
    if (metadata.courseId) form.append('courseId', String(metadata.courseId))
    if (metadata.description) form.append('description', metadata.description)
    if (metadata.citation) form.append('citation', metadata.citation)
    const resp = await fetch(`${API_BASE_URL}/admin/knowledge-sources/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form
    })
    const data = await resp.json()
    if (!resp.ok) throw new Error(data.message || '上传失败')
    return data
  }
  return { success: true, message: '文件已上传，等待审核', fileUrl: '/uploads/demo.pdf', originalName: file.name, size: file.size }
}

export function getCourses() {
  if (!isMockMode()) {
    return request('/admin/courses')
  }

  return mockResolve(courseManagementPayload)
}

export function getCourseStructureDetail(id) {
  if (!isMockMode()) {
    return request(`/admin/courses/${id}/structure`)
  }

  return mockResolve(buildCourseStructure(id))
}

export function getAuditLogs() {
  if (!isMockMode()) {
    return request('/admin/audit-log')
  }

  const failed = auditLogList.filter((item) => item.result !== '成功').length
  const adminActions = auditLogList.filter((item) => item.roleCode === 'admin').length

  return mockResolve({
    stats: [
      { label: '日志总数', value: String(auditLogList.length), color: '#409EFF', desc: '当前筛选范围' },
      { label: '成功操作', value: String(auditLogList.length - failed), color: '#67C23A', desc: '已完成动作' },
      { label: '失败操作', value: String(failed), color: '#F56C6C', desc: '需排查记录' },
      { label: '高权限操作', value: String(adminActions), color: '#E6A23C', desc: '管理员动作' }
    ],
    logs: auditLogList,
    total: auditLogList.length
  })
}

function csvCell(value) {
  const text = String(value ?? '')
  const guarded = /^[=+\-@]/.test(text) ? `'${text}` : text
  return `"${guarded.replace(/"/g, '""')}"`
}

function buildAuditCsv(logs) {
  const headers = ['时间', '操作人', '角色', '操作类型', '目标对象', '目标ID', '操作详情', 'IP地址', '结果']
  const rows = logs.map((log) => [
    log.time,
    log.operator,
    log.role,
    log.action,
    log.targetLabel,
    log.targetId || '',
    log.detail,
    log.ip,
    log.result
  ])

  return [headers, ...rows].map((row) => row.map(csvCell).join(',')).join('\r\n')
}

export function exportAuditLogs(filters = {}) {
  if (!isMockMode()) {
    return request('/admin/audit-log/export', {
      method: 'POST',
      body: JSON.stringify(filters)
    })
  }

  const logs = auditLogList
    .filter((item) => !filters.action || item.action === filters.action)
    .filter((item) => !filters.role || item.roleCode === filters.role)
    .filter((item) => !filters.result || item.result === filters.result)
  return mockResolve({
    success: true,
    message: `已导出 ${logs.length} 条日志`,
    filename: 'audit-logs-mock.csv',
    content: `\uFEFF${buildAuditCsv(logs)}`
  })
}

export function getAuditLogDetail(id) {
  if (!isMockMode()) {
    return request(`/admin/audit-log/${id}`)
  }

  return mockResolve(buildAuditLogDetail(id))
}

export function getSystemSettings() {
  if (!isMockMode()) {
    return request('/admin/system-config')
  }

  return mockResolve([
    { configKey: 'platform.name', configValue: '马原智学 Agent', description: '平台名称' },
    { configKey: 'platform.semester', configValue: '2025-2026-2', description: '当前学期' },
    { configKey: 'ai.model', configValue: 'deepseek-v4', description: 'AI 模型' },
    { configKey: 'ai.temperature', configValue: '0.7', description: 'AI 温度参数' },
    { configKey: 'quiz.default_duration', configValue: '5', description: '测验默认限时' },
    { configKey: 'security.session_timeout', configValue: '480', description: '会话超时(分钟)' }
  ])
}

export function saveSystemConfig(configKey, configValue) {
  if (!isMockMode()) {
    return request('/admin/system-config', {
      method: 'POST',
      body: JSON.stringify({ configKey, configValue })
    })
  }
  return mockResolve({ success: true })
}

export function saveSystemSettings(config) {
  if (!isMockMode()) {
    return request('/admin/system-settings', {
      method: 'POST',
      body: JSON.stringify(config)
    })
  }

  Object.assign(systemSettingsPayload.config, config)
  return mockResolve({
    success: true,
    message: '系统设置已保存',
    ...systemSettingsPayload
  })
}

export function getSystemConfigDetail(configKey) {
  if (!isMockMode()) {
    return request(`/admin/system-settings/${configKey}`)
  }

  return mockResolve(buildSystemConfigDetail(configKey))
}

export function getRolePermissions() {
  if (!isMockMode()) {
    return request('/admin/role-permission')
  }

  return mockResolve(buildRolePermissionList())
}

export function getRolePermissionDetail(roleId) {
  if (!isMockMode()) {
    return request(`/admin/role-permission/${roleId}/permissions`)
  }

  return mockResolve(buildRolePermissionDetail(roleId))
}

export function saveRolePermissions(roleId, permissionKeys) {
  if (!isMockMode()) {
    return request(`/admin/role-permission/${roleId}/permissions`, {
      method: 'POST',
      body: JSON.stringify({ permissionKeys })
    })
  }

  return mockResolve({
    success: true,
    message: '角色权限已保存',
    roleId,
    permissionKeys
  })
}

export function getOrgStructure() {
  if (!isMockMode()) {
    return request('/admin/org-structure')
  }

  return mockResolve(buildOrgStructurePayload())
}

export function getOrgNodeDetail(nodeId) {
  if (!isMockMode()) {
    return request(`/admin/org-structure/${nodeId}`)
  }

  return mockResolve(buildOrgNodeDetail(nodeId))
}
