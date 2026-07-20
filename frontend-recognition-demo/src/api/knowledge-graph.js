import { isMockMode, request } from './http.js'
import { mockResolve } from './mockTransport.js'

// ============ Mock 数据 ============
const mockChapterGraph = {
  nodes: [
    { id: 1, name: '实践与认识及其发展规律', description: '本章围绕实践、认识、真理、价值四个核心范畴展开', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'basic', difficultyLabel: '基础', parentId: null, sortOrder: 1, color: '#409EFF', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 2, name: '实践', description: '人类能动地改造世界的社会性的物质活动', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'basic', difficultyLabel: '基础', parentId: 1, sortOrder: 1, color: '#67C23A', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 3, name: '认识', description: '在实践基础上主体对客体的能动反映', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'basic', difficultyLabel: '基础', parentId: 1, sortOrder: 2, color: '#E6A23C', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 4, name: '真理', description: '标志主观同客观相符合的哲学范畴', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'intermediate', difficultyLabel: '进阶', parentId: 1, sortOrder: 3, color: '#F56C6C', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 5, name: '价值', description: '客体对主体需要的满足关系', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'intermediate', difficultyLabel: '进阶', parentId: 1, sortOrder: 4, color: '#909399', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 6, name: '实践的基本特征', description: '客观物质性、自觉能动性、社会历史性', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'basic', difficultyLabel: '基础', parentId: 2, sortOrder: 1, color: '#67C23A', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 7, name: '实践的基本形式', description: '物质生产实践、社会政治实践、科学文化实践', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'basic', difficultyLabel: '基础', parentId: 2, sortOrder: 2, color: '#67C23A', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 8, name: '实践对认识的决定作用', description: '实践是认识的来源、动力、目的和检验标准', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'basic', difficultyLabel: '基础', parentId: 2, sortOrder: 3, color: '#E6A23C', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 9, name: '感性认识', description: '对事物现象和外部联系的认识', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'basic', difficultyLabel: '基础', parentId: 3, sortOrder: 1, color: '#E6A23C', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 10, name: '理性认识', description: '对事物本质和内部联系的认识', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'basic', difficultyLabel: '基础', parentId: 3, sortOrder: 2, color: '#E6A23C', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 11, name: '认识运动的两次飞跃', description: '从实践到认识、从认识到实践的辩证过程', nodeType: 'method', nodeTypeLabel: '方法论', difficulty: 'intermediate', difficultyLabel: '进阶', parentId: 3, sortOrder: 3, color: '#E6A23C', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 12, name: '真理的客观性', description: '真理的内容是客观的，检验真理的标准是客观的', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'intermediate', difficultyLabel: '进阶', parentId: 4, sortOrder: 1, color: '#F56C6C', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 13, name: '实践是检验真理的唯一标准', description: '只有实践才能把主观认识和客观对象联系起来加以对照', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'intermediate', difficultyLabel: '进阶', parentId: 4, sortOrder: 2, color: '#F56C6C', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 14, name: '真理的绝对性与相对性', description: '真理是绝对和相对的辩证统一', nodeType: 'core_concept', nodeTypeLabel: '核心概念', difficulty: 'advanced', difficultyLabel: '高级', parentId: 4, sortOrder: 3, color: '#F56C6C', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 15, name: '真理尺度与价值尺度', description: '认识和实践既要尊重客观规律，也要服务人的合理价值目标', nodeType: 'method', nodeTypeLabel: '方法论', difficulty: 'intermediate', difficultyLabel: '进阶', parentId: 5, sortOrder: 1, color: '#909399', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 16, name: '理论联系实际', description: '用科学理论指导实践，在实践中检验和发展理论', nodeType: 'application', nodeTypeLabel: '实践应用', difficulty: 'advanced', difficultyLabel: '高级', parentId: 5, sortOrder: 2, color: '#909399', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 17, name: '社会调研中的认识深化', description: '通过社区调研、访谈等方式观察实践如何推动认识变化', nodeType: 'case_study', nodeTypeLabel: '案例分析', difficulty: 'basic', difficultyLabel: '基础', parentId: 8, sortOrder: 1, color: '#409EFF', chapterTitle: '实践与认识及其发展规律', sources: [] },
    { id: 18, name: '科研训练中的实践检验', description: '在实验和数据分析中检验理论假设', nodeType: 'case_study', nodeTypeLabel: '案例分析', difficulty: 'intermediate', difficultyLabel: '进阶', parentId: 13, sortOrder: 1, color: '#F56C6C', chapterTitle: '实践与认识及其发展规律', sources: [] }
  ],
  edges: [
    { id: 1, source: 1, target: 2, relationType: 'contains', relationLabel: '核心范畴', weight: 1.0 },
    { id: 2, source: 1, target: 3, relationType: 'contains', relationLabel: '核心范畴', weight: 1.0 },
    { id: 3, source: 1, target: 4, relationType: 'contains', relationLabel: '核心范畴', weight: 1.0 },
    { id: 4, source: 1, target: 5, relationType: 'contains', relationLabel: '核心范畴', weight: 0.8 },
    { id: 5, source: 2, target: 6, relationType: 'contains', relationLabel: '基本特征', weight: 1.0 },
    { id: 6, source: 2, target: 7, relationType: 'contains', relationLabel: '基本形式', weight: 0.9 },
    { id: 7, source: 2, target: 8, relationType: 'contains', relationLabel: '对认识的作用', weight: 1.0 },
    { id: 8, source: 3, target: 9, relationType: 'contains', relationLabel: '初级阶段', weight: 1.0 },
    { id: 9, source: 3, target: 10, relationType: 'contains', relationLabel: '高级阶段', weight: 1.0 },
    { id: 10, source: 3, target: 11, relationType: 'contains', relationLabel: '辩证过程', weight: 1.0 },
    { id: 11, source: 4, target: 12, relationType: 'contains', relationLabel: '首要属性', weight: 1.0 },
    { id: 12, source: 4, target: 13, relationType: 'contains', relationLabel: '检验标准', weight: 1.0 },
    { id: 13, source: 4, target: 14, relationType: 'contains', relationLabel: '辩证属性', weight: 0.9 },
    { id: 14, source: 5, target: 15, relationType: 'contains', relationLabel: '双尺度统一', weight: 1.0 },
    { id: 15, source: 5, target: 16, relationType: 'contains', relationLabel: '方法论要求', weight: 0.9 },
    { id: 16, source: 9, target: 10, relationType: 'prerequisite', relationLabel: '从感性到理性', weight: 1.0 },
    { id: 17, source: 8, target: 13, relationType: 'prerequisite', relationLabel: '决定→检验', weight: 0.8 },
    { id: 18, source: 8, target: 17, relationType: 'derives', relationLabel: '实践→案例', weight: 0.7 },
    { id: 19, source: 13, target: 18, relationType: 'derives', relationLabel: '检验→案例', weight: 0.7 },
    { id: 20, source: 8, target: 11, relationType: 'related', relationLabel: '决定→飞跃', weight: 0.85 },
    { id: 21, source: 12, target: 13, relationType: 'related', relationLabel: '客观性→标准', weight: 0.9 },
    { id: 22, source: 15, target: 16, relationType: 'related', relationLabel: '尺度→方法', weight: 0.75 },
    { id: 23, source: 8, target: 17, relationType: 'applies', relationLabel: '原理→应用', weight: 0.8 },
    { id: 24, source: 13, target: 18, relationType: 'applies', relationLabel: '原理→应用', weight: 0.8 },
    { id: 25, source: 11, target: 17, relationType: 'applies', relationLabel: '飞跃→案例', weight: 0.7 }
  ],
  summary: { totalNodes: 18, totalEdges: 25, relationTypes: ['contains', 'prerequisite', 'related', 'derives', 'applies'] }
}

const mockNodeDetail = {
  node: {
    id: 8,
    courseId: 1,
    courseName: '马克思主义基本原理',
    chapterId: 1,
    chapterTitle: '实践与认识及其发展规律',
    name: '实践对认识的决定作用',
    description: '实践是认识的来源、动力、目的和检验标准',
    nodeType: 'core_concept',
    nodeTypeLabel: '核心概念',
    difficulty: 'basic',
    difficultyLabel: '基础',
    parentId: 2,
    sortOrder: 3,
    color: '#E6A23C'
  },
  parent: { id: 2, name: '实践', nodeType: 'core_concept', color: '#67C23A' },
  children: [
    { id: 17, name: '社会调研中的认识深化', nodeType: 'case_study', difficulty: 'basic', color: '#409EFF' }
  ],
  edges: [
    { id: 7, source: 2, sourceName: '实践', target: 8, targetName: '实践对认识的决定作用', relationType: 'contains', relationLabel: '对认识的作用', weight: 1.0 },
    { id: 17, source: 8, sourceName: '实践对认识的决定作用', target: 13, targetName: '实践是检验真理的唯一标准', relationType: 'prerequisite', relationLabel: '决定→检验', weight: 0.8 },
    { id: 20, source: 8, sourceName: '实践对认识的决定作用', target: 11, targetName: '认识运动的两次飞跃', relationType: 'related', relationLabel: '决定→飞跃', weight: 0.85 },
    { id: 23, source: 8, sourceName: '实践对认识的决定作用', target: 17, targetName: '社会调研中的认识深化', relationType: 'applies', relationLabel: '原理→应用', weight: 0.8 }
  ],
  sources: []
}

const mockCourseGraph = {
  chapters: [
    { id: 1, title: '实践与认识及其发展规律', chapterOrder: 3, nodeCount: 18 }
  ],
  nodes: mockChapterGraph.nodes,
  edges: mockChapterGraph.edges
}

// ============ API 函数 ============

/** 学生端：获取章节知识图谱 */
export function getStudentKnowledgeGraph(chapterId) {
  if (!isMockMode()) {
    return request(`/student/knowledge-graph/${chapterId}`)
  }
  return mockResolve(mockChapterGraph)
}

/** 学生端：获取当前课程的章节列表（使用数据库真实主键） */
export function getStudentKnowledgeGraphChapters() {
  if (!isMockMode()) {
    return request('/student/knowledge-graph/chapters')
  }
  return mockResolve([
    { id: 1, chapterOrder: 3, title: '实践与认识及其发展规律' }
  ])
}

/** 学生端：获取知识点节点详情 */
export function getStudentNodeDetail(nodeId) {
  if (!isMockMode()) {
    return request(`/student/knowledge-graph/nodes/${nodeId}`)
  }
  return mockResolve({ ...mockNodeDetail, node: { ...mockNodeDetail.node, id: Number(nodeId) || 8 } })
}

/** 教师端：获取章节知识图谱 */
export function getTeacherKnowledgeGraph(chapterId) {
  if (!isMockMode()) {
    return request(`/teacher/knowledge-graph/${chapterId}`)
  }
  return mockResolve(mockChapterGraph)
}

export function getTeacherKnowledgeGraphChapters() {
  if (!isMockMode()) {
    return request('/teacher/knowledge-graph/chapters')
  }
  return getStudentKnowledgeGraphChapters()
}

/** 教师端：获取知识点节点详情 */
export function getTeacherNodeDetail(nodeId) {
  if (!isMockMode()) {
    return request(`/teacher/knowledge-graph/nodes/${nodeId}`)
  }
  return mockResolve({ ...mockNodeDetail, node: { ...mockNodeDetail.node, id: Number(nodeId) || 8 } })
}

/** 管理端：获取课程知识图谱概览 */
export function getAdminKnowledgeGraph(courseId) {
  if (!isMockMode()) {
    return request(`/admin/knowledge-graph/${courseId}`)
  }
  return mockResolve(mockCourseGraph)
}

/** 管理端：获取知识点节点详情 */
export function getAdminNodeDetail(nodeId) {
  if (!isMockMode()) {
    return request(`/admin/knowledge-graph/nodes/${nodeId}`)
  }
  return mockResolve({ ...mockNodeDetail, node: { ...mockNodeDetail.node, id: Number(nodeId) || 8 } })
}

/** 管理端：获取关系类型列表 */
export function getRelationTypes() {
  if (!isMockMode()) {
    return request('/admin/knowledge-graph/relation-types')
  }
  return mockResolve([
    { value: 'contains', label: '包含' },
    { value: 'prerequisite', label: '前置知识' },
    { value: 'related', label: '相关' },
    { value: 'derives', label: '派生' },
    { value: 'applies', label: '应用' },
    { value: 'contrasts', label: '对比' }
  ])
}

/** 管理端：获取节点类型列表 */
export function getNodeTypes() {
  if (!isMockMode()) {
    return request('/admin/knowledge-graph/node-types')
  }
  return mockResolve([
    { value: 'core_concept', label: '核心概念' },
    { value: 'method', label: '方法论' },
    { value: 'application', label: '实践应用' },
    { value: 'case_study', label: '案例分析' },
    { value: 'extension', label: '拓展延伸' }
  ])
}
