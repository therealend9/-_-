<template>
  <div class="demo-root">
    <!-- 案例头部 -->
    <header class="demo-hero">
      <div class="hero-badge">📖 实现案例</div>
      <h1>"课前学习"模块 —— 完整学习旅程演示</h1>
      <p class="hero-sub">学生：李明哲 · 课程：马克思主义基本原理 · 2025-2026-2 学期 · 2023级本科1班</p>
      <div class="hero-stats">
        <div class="hero-stat"><strong>3</strong> 层页面</div>
        <div class="hero-stat"><strong>6</strong> 个课程章节</div>
        <div class="hero-stat"><strong>6</strong> 道预习小测</div>
        <div class="hero-stat"><strong>1</strong> 条完整学习路径</div>
      </div>
    </header>

    <!-- ==================== 阶段一：章节列表 ==================== -->
    <section class="stage" id="stage1">
      <div class="stage-header stage-center">
        <span class="stage-num">01</span>
        <div>
          <h2>课前学习中心 —— 章节列表与任务总览</h2>
          <p>路由：<code>/student/pre-study</code> · 组件：<code>PreStudyCenter.vue</code> · 数据：<code>getPreStudyContent()</code></p>
        </div>
      </div>

      <div class="stage-body">
        <!-- 数据来源说明 -->
        <div class="data-card">
          <div class="data-title">📦 API 返回数据结构</div>
          <pre class="code-block">{{ JSON.stringify(demoData.center.overview, null, 2) }}</pre>
        </div>

        <!-- 渲染效果：统计卡片 -->
        <div class="render-label">↓ 渲染为 ↓</div>

        <el-row :gutter="16" class="demo-row">
          <el-col :span="6" v-for="card in statCards" :key="card.label">
            <div class="demo-stat">
              <div class="demo-stat-icon" :style="{background:card.iconBg,color:card.iconColor}">
                <el-icon size="20"><component :is="card.icon" /></el-icon>
              </div>
              <div class="demo-stat-info">
                <div class="demo-stat-val">{{ card.value }}</div>
                <div class="demo-stat-label">{{ card.label }}</div>
                <div class="demo-stat-sub">{{ card.sub }}</div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 渲染效果：章节列表（截取3章展示） -->
        <div class="render-label">↓ 章节卡片渲染 ↓</div>
        <div class="chapter-demo-list">
          <div
            v-for="ch in demoChapters"
            :key="ch.id"
            class="demo-chapter"
            :class="'demo-chapter-' + ch.statusType"
          >
            <div class="dc-order" :class="'dc-order-' + ch.statusType">{{ ch.chapterOrder }}</div>
            <div class="dc-body">
              <div class="dc-top">
                <strong>{{ ch.title }}</strong>
                <el-tag size="small" :type="ch.statusType" :effect="ch.status === '进行中' ? 'dark' : 'light'">{{ ch.status }}</el-tag>
              </div>
              <div class="dc-question">❓ {{ ch.coreQuestion }}</div>
              <div class="dc-meta">
                <span>⏱ {{ ch.estimatedMinutes }}分钟</span>
                <span>📅 截止 {{ ch.deadline }}</span>
                <span>📋 {{ ch.completedTasks }}/{{ ch.totalTasks }} 项任务</span>
              </div>
              <el-progress :percentage="Math.round(ch.completedTasks/ch.totalTasks*100)" :stroke-width="4" :show-text="false" :color="ch.statusType==='success'?'#67C23A':ch.statusType==='warning'?'#409EFF':'#c9c9c9'" />
            </div>
            <div class="dc-arrow">→</div>
          </div>
        </div>

        <!-- 渲染效果：任务清单 + 快捷入口 -->
        <el-row :gutter="16" class="demo-row">
          <el-col :span="12">
            <div class="demo-side-card">
              <div class="dsc-title">📝 待完成预习任务 <el-tag size="small" type="warning">5 项</el-tag></div>
              <div v-for="(t,i) in demoData.center.tasks.slice(0,4)" :key="i" class="dsc-task">
                <span class="dot" :class="t.status==='已完成'?'dot-done':''"></span>
                <div class="dsc-task-info">
                  <div class="dsc-task-title">{{ t.title }}</div>
                  <div class="dsc-task-sub">{{ t.chapterTitle }}</div>
                </div>
                <el-tag size="small" :type="t.statusType">{{ t.status }}</el-tag>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="demo-side-card">
              <div class="dsc-title">🚀 快捷入口</div>
              <div class="dsc-entry" v-for="a in demoData.center.quickActions" :key="a.route">
                <span class="entry-dot">✏️</span>
                <div><strong>{{ a.label }}</strong><br><small>{{ a.desc }}</small></div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- 分隔线 -->
    <div class="stage-divider">
      <span>👇 点击第3章「实践与认识及其发展规律」→ 进入导学详情</span>
    </div>

    <!-- ==================== 阶段二：导学详情 ==================== -->
    <section class="stage" id="stage2">
      <div class="stage-header stage-detail">
        <span class="stage-num">02</span>
        <div>
          <h2>章节导学详情 —— 深度学习</h2>
          <p>路由：<code>/student/pre-study/1</code> · 组件：<code>PreStudyDetail.vue</code> · 数据：<code>getPreStudyDetail(1)</code></p>
        </div>
      </div>

      <div class="stage-body">
        <!-- 数据来源 -->
        <div class="data-card">
          <div class="data-title">📦 API 返回数据结构（关键字段）</div>
          <pre class="code-block">{
  chapter: { title: "实践与认识及其发展规律", chapterOrder: 3, status: "导学中", estimatedMinutes: 18 },
  stats: [ { label:"预计时长", value:"18 分钟" }, { label:"核心概念", value:"5" }, ... ],
  learningObjectives: [ { type:"知识目标", content:"..." }, { type:"能力目标", content:"..." }, { type:"价值目标", content:"..." } ],
  guideBlocks: [ { title:"导入问题", content:"..." }, { title:"学习主线", content:"..." }, { title:"案例提示", content:"..." } ],
  keyConcepts: [ { name:"实践", explain:"...", example:"...", misread:"..." }, ... ],
  taskSteps: [ { title:"阅读导学正文", status:"进行中" }, { title:"概念辨析", status:"待完成" }, ... ],
  sourceRefs: [ { title:"教材第三章", type:"教材" }, { title:"课堂讲义", type:"课件" }, ... ],
  quizPreview: [ { knowledgePoint:"实践与认识", type:"单选题", stem:"..." }, ... ],
  timeline: [ { title:"导学发布", time:"2026/07/07" }, { title:"学生阅读", time:"进行中" }, ... ]
}</pre>
        </div>

        <div class="render-label">↓ 渲染为 ↓</div>

        <!-- 统计卡片 -->
        <el-row :gutter="12" class="demo-row">
          <el-col :span="6" v-for="s in demoData.detail.stats" :key="s.label">
            <div class="detail-stat">
              <div class="ds-label">{{ s.label }}</div>
              <div class="ds-val" :style="{color:s.color}">{{ s.value }}</div>
              <div class="ds-desc">{{ s.desc }}</div>
            </div>
          </el-col>
        </el-row>

        <!-- 导学档案 -->
        <el-row :gutter="16" class="demo-row">
          <el-col :span="15">
            <div class="demo-card">
              <div class="demo-card-title">📋 导学档案</div>
              <div class="hero-box">
                <div class="hero-label">本节课先解决一个核心问题</div>
                <div class="hero-q">人的认识从哪里来，又怎样在实践中被检验和发展？</div>
                <p class="hero-summary">本章围绕实践、认识、真理、价值的关系展开，重点理解实践在认识形成、发展和检验中的基础作用。</p>
              </div>
              <div class="obj-grid">
                <div v-for="obj in demoData.detail.learningObjectives" :key="obj.type">
                  <span class="obj-type">{{ obj.type }}</span>
                  <strong>{{ obj.content }}</strong>
                </div>
              </div>
            </div>
          </el-col>
          <el-col :span="9">
            <div class="demo-card">
              <div class="demo-card-title">🔗 学习任务链</div>
              <div v-for="(ts,i) in demoData.detail.taskSteps" :key="i" class="task-step">
                <div class="ts-head">
                  <span class="ts-idx">{{ i+1 }}</span>
                  <strong>{{ ts.title }}</strong>
                  <el-tag size="small" :type="ts.statusType">{{ ts.status }}</el-tag>
                </div>
                <p class="ts-target">{{ ts.target }}</p>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 导学正文 + 概念卡片 + 来源引用 -->
        <el-row :gutter="16" class="demo-row">
          <el-col :span="12">
            <div class="demo-card">
              <div class="demo-card-title">📖 导学正文</div>
              <div v-for="block in demoData.detail.guideBlocks" :key="block.title" class="g-block">
                <strong>{{ block.title }}</strong>
                <p>{{ block.content }}</p>
              </div>
            </div>
            <div class="demo-card" style="margin-top:12px">
              <div class="demo-card-title">📚 来源引用</div>
              <div v-for="src in demoData.detail.sourceRefs" :key="src.id" class="src-item">
                <strong>{{ src.title }}</strong>
                <span class="src-tag">{{ src.type }} · {{ src.locator }}</span>
                <el-tag size="small" type="success">{{ src.status }}</el-tag>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="demo-card">
              <div class="demo-card-title">🧩 核心概念 <el-tag size="small" type="info">3 个</el-tag></div>
              <div v-for="c in demoData.detail.keyConcepts" :key="c.name" class="concept-demo">
                <div class="cd-head">
                  <strong>{{ c.name }}</strong>
                  <el-tag size="small" type="info">{{ c.source }}</el-tag>
                </div>
                <p>{{ c.explain }}</p>
                <div class="cd-example">📗 案例：{{ c.example }}</div>
                <div class="cd-misread">⚠️ 易错点：{{ c.misread }}</div>
              </div>
            </div>
            <div class="demo-card" style="margin-top:12px">
              <div class="demo-card-title">🕐 学习时间线</div>
              <div v-for="(tl,i) in demoData.detail.timeline" :key="i" class="tl-item">
                <div class="tl-dot" :class="{ active: i <= 1 }"></div>
                <div>
                  <strong>{{ tl.title }}</strong>
                  <div class="tl-time">{{ tl.time }}</div>
                  <div class="tl-desc">{{ tl.desc }}</div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 小测预览 + 问题提交 -->
        <el-row :gutter="16" class="demo-row">
          <el-col :span="12">
            <div class="demo-card">
              <div class="demo-card-title">📝 小测预览 <el-button size="small" type="primary" plain>开始小测 →</el-button></div>
              <table class="quiz-preview-table">
                <thead><tr><th>知识点</th><th>题型</th><th>题目</th><th>复习建议</th></tr></thead>
                <tbody>
                  <tr v-for="q in demoData.detail.quizPreview" :key="q.id">
                    <td>{{ q.knowledgePoint }}</td>
                    <td class="tc">{{ q.type }}</td>
                    <td>{{ q.stem }}</td>
                    <td>{{ q.review }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="demo-card">
              <div class="demo-card-title">❓ 课前问题提交 <el-tag size="small" type="warning">教师可见</el-tag></div>
              <div class="question-demo">
                <div class="qd-input-demo">为什么实践能成为检验真理的唯一标准？有没有反例可以说明？</div>
                <el-button type="primary" style="width:100%;margin-top:8px">提交问题</el-button>
                <p class="qd-hint">提交后会匿名汇总给教师，用于生成课前学情报告。</p>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- 分隔线 -->
    <div class="stage-divider">
      <span>👇 完成导学阅读后 → 进入预习小测检验理解</span>
    </div>

    <!-- ==================== 阶段三：预习小测 ==================== -->
    <section class="stage" id="stage3">
      <div class="stage-header stage-quiz">
        <span class="stage-num">03</span>
        <div>
          <h2>预习小测 —— 效果检验与查漏补缺</h2>
          <p>路由：<code>/student/pre-study-quiz</code> · 组件：<code>PreStudyQuiz.vue</code> · 数据：<code>getPreStudyQuiz()</code> → <code>submitPreStudyQuiz()</code></p>
        </div>
      </div>

      <div class="stage-body">
        <!-- 数据 -->
        <div class="data-card">
          <div class="data-title">📦 API 返回 & 提交数据结构</div>
          <pre class="code-block">// GET -> 6道题（含3种题型）
[
  { id:1, type:"单选题", tag:"实践与认识", title:"下列关于实践...", options:[...], correctIndex:1, answer:null },
  { id:4, type:"多选题", tag:"理论联系实际", title:"下列哪些属于...", 
    options:[...], correctIndices:[0,1,3], answer:[] },  // 多选用数组
  { id:3, type:"判断题", tag:"概念辨析", title:"认识的发展只需要...", 
    options:["正确","错误"], correctIndex:1, answer:null },
]

// POST -> 提交判分
submitPreStudyQuiz([
  { questionId:1, selectedIndex:1 },          // 单选 → 数字
  { questionId:4, selectedIndex:[0,1,3] },     // 多选 → 数组
  { questionId:3, selectedIndex:1 },           // 判断 → 数字
])
// → 返回 { score:83, results:[...], weakPoints:["真理与价值"] }</pre>
        </div>

        <div class="render-label">↓ 渲染为 ↓</div>

        <!-- 测验收题展示 -->
        <el-row :gutter="16" class="demo-row">
          <el-col :span="16">
            <!-- 题目1：单选题（已答对） -->
            <div class="quiz-card">
              <div class="qc-head">
                <span class="qc-num">1</span>
                <strong>单选题</strong>
                <el-tag size="small" type="success" style="margin-left:auto">回答正确</el-tag>
              </div>
              <div class="qc-title">下列关于实践与认识关系的说法，正确的是哪一项？</div>
              <div class="qc-options">
                <div class="qco">○ A. 认识可以脱离实践独立产生</div>
                <div class="qco selected correct">● B. 实践是认识的来源和发展动力 ✓</div>
                <div class="qco">○ C. 认识的目的只是形成理论</div>
                <div class="qco">○ D. 真理主要由多数人的意见决定</div>
              </div>
              <div class="qc-result success">
                <strong>✅ 回答正确</strong>
                <p>实践是认识的来源、动力、目的，也是检验认识真理性的唯一标准。</p>
                <span class="qc-review">📖 建议复习："实践对认识的决定作用"</span>
              </div>
            </div>

            <!-- 题目4：多选题（已答对） -->
            <div class="quiz-card">
              <div class="qc-head">
                <span class="qc-num">4</span>
                <strong>多选题</strong>
                <el-tag size="small" type="info" style="margin-left:auto">知识点：理论联系实际</el-tag>
              </div>
              <div class="qc-title">下列哪些属于实践对认识的决定作用表现？（多选）</div>
              <div class="qc-options">
                <div class="qco selected correct">☑ A. 实践是认识的来源 ✓</div>
                <div class="qco selected correct">☑ B. 实践是认识发展的动力 ✓</div>
                <div class="qco">☐ C. 实践可以替代所有理论学习</div>
                <div class="qco selected correct">☑ D. 实践是检验认识真理性的标准 ✓</div>
              </div>
              <div class="qc-result success">
                <strong>✅ 回答正确</strong>
                <p>实践对认识的决定作用表现在四个方面：来源、动力、目的和检验标准。</p>
                <span class="qc-review">📖 建议复习："实践对认识的决定作用"的四个方面</span>
              </div>
            </div>

            <!-- 题目5：单选题（答错了——重点展示） -->
            <div class="quiz-card error-card">
              <div class="qc-head">
                <span class="qc-num err">5</span>
                <strong>单选题</strong>
                <el-tag size="small" type="danger" style="margin-left:auto">需要复习</el-tag>
              </div>
              <div class="qc-title">关于真理尺度与价值尺度的关系，下列说法更准确的是？</div>
              <div class="qc-options">
                <div class="qco">○ A. 二者完全无关</div>
                <div class="qco selected wrong">● B. 价值尺度可以取代真理尺度 ← 你的回答（错误）</div>
                <div class="qco selected correct">● C. 应在尊重客观规律基础上实现价值追求 ← 正确答案</div>
                <div class="qco">○ D. 只要目的正当就不必考虑事实</div>
              </div>
              <div class="qc-result error">
                <strong>❌ 需要复习</strong>
                <p>认识和实践既要尊重客观规律，也要服务人的合理价值目标。</p>
                <span class="qc-review">📖 建议复习："真理尺度与价值尺度的统一"</span>
              </div>
            </div>
          </el-col>

          <el-col :span="8">
            <!-- 答题卡 -->
            <div class="demo-card">
              <div class="demo-card-title">📋 答题卡</div>
              <div class="answer-grid-demo">
                <div class="ag-cell done correct">1</div>
                <div class="ag-cell done correct">2</div>
                <div class="ag-cell done correct">3</div>
                <div class="ag-cell done correct">4</div>
                <div class="ag-cell done wrong">5</div>
                <div class="ag-cell done correct">6</div>
              </div>
              <div class="ag-legend">
                <span class="leg"><span class="leg-dot g"></span> 正确</span>
                <span class="leg"><span class="leg-dot r"></span> 需复习</span>
                <span class="leg"><span class="leg-dot gy"></span> 已答</span>
              </div>
            </div>

            <!-- 成绩结果 -->
            <div class="score-card">
              <div class="score-big">83<span>分</span></div>
              <div class="score-detail">共 6 题 · 正确 5 题</div>
              <div class="score-weak">薄弱点：真理与价值</div>
              <el-button type="warning" style="width:100%;margin-top:8px">🔄 重做错题 (1)</el-button>
            </div>

            <!-- 考试说明 -->
            <div class="demo-card" style="margin-top:12px">
              <div class="demo-card-title">📌 考试说明</div>
              <div class="info-line">⏱ 限时 15 分钟，超时可继续作答</div>
              <div class="info-line">📄 共 6 题：单选题 3 道、判断题 2 道、多选题 1 道</div>
              <div class="info-line">ℹ️ 提交后可查看解析和正确答案</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- ==================== 底部总结 ==================== -->
    <section class="summary-section">
      <h2>🎯 完整链路总结</h2>
      <div class="flow-diagram">
        <div class="flow-node">
          <div class="fn-icon">🏠</div>
          <strong>PreStudyCenter</strong>
          <p>章节总览<br>6章列表 + 进度 + 任务</p>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-node">
          <div class="fn-icon">📖</div>
          <strong>PreStudyDetail</strong>
          <p>深度学习<br>导学 + 概念 + 提问</p>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-node">
          <div class="fn-icon">✏️</div>
          <strong>PreStudyQuiz</strong>
          <p>效果检验<br>6题 + 判分 + 重做</p>
        </div>
      </div>

      <div class="summary-grid">
        <div class="sg-item">
          <h4>📁 涉及文件</h4>
          <ul>
            <li><code>views/student/PreStudyCenter.vue</code></li>
            <li><code>views/student/PreStudyDetail.vue</code></li>
            <li><code>views/student/PreStudyQuiz.vue</code></li>
            <li><code>api/student.js</code>（3个API + Mock数据）</li>
            <li><code>router/index.js</code>（3条路由）</li>
            <li><code>styles/global.css</code>（设计token）</li>
          </ul>
        </div>
        <div class="sg-item">
          <h4>🔄 数据流</h4>
          <ul>
            <li><code>getPreStudyContent()</code> → Center 页</li>
            <li><code>getPreStudyDetail(id)</code> → Detail 页</li>
            <li><code>getPreStudyQuiz()</code> → Quiz 页</li>
            <li><code>submitPreStudyQuiz()</code> → 判分</li>
            <li><code>submitPreStudyQuestion()</code> → 教师端</li>
          </ul>
        </div>
        <div class="sg-item">
          <h4>🎨 设计系统</h4>
          <ul>
            <li>CSS 变量：7 基础色 + 4 强调色</li>
            <li>缓动：<code>cubic-bezier(0.16,1,0.3,1)</code></li>
            <li>阴影：3级（sm/md/lg）</li>
            <li>微交互：hover上浮+过渡</li>
          </ul>
        </div>
      </div>
    </section>

    <footer class="demo-footer">
      <p>📌 本页为静态案例展示，所有数据来自 <code>src/api/student.js</code> Mock 数据层</p>
      <p>切换真实后端：设置 <code>VITE_USE_MOCK=false</code> + <code>VITE_API_BASE_URL</code></p>
    </footer>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { Checked, TrendCharts, Timer, AlarmClock } from '@element-plus/icons-vue'

const statCards = [
  { label: '已完成章节', value: '2/6', sub: '1 章进行中', icon: Checked, iconBg: '#f0f9eb', iconColor: '#67C23A' },
  { label: '整体完成进度', value: '33%', sub: '8/24 个任务', icon: TrendCharts, iconBg: '#ecf5ff', iconColor: '#409EFF' },
  { label: '预计总学习时长', value: '123 分钟', sub: '8/24 个任务已完成', icon: Timer, iconBg: '#fdf6ec', iconColor: '#E6A23C' },
  { label: '下次小测截止', value: '5 天 3 小时', sub: '2026/07/18 22:00', icon: AlarmClock, iconBg: '#fef0f0', iconColor: '#F56C6C' }
]

const demoChapters = [
  { id: 1, title: '实践与认识及其发展规律', chapterOrder: 3, status: '进行中', statusType: 'warning', coreQuestion: '人的认识从哪里来，又怎样在实践中被检验和发展？', deadline: '2026/07/15 22:00', completedTasks: 1, totalTasks: 4, estimatedMinutes: 18 },
  { id: 2, title: '物质世界及其发展规律', chapterOrder: 1, status: '已完成', statusType: 'success', coreQuestion: '世界的本质是什么？我们应该怎样理解世界的规律性？', deadline: '2026/07/01 22:00', completedTasks: 4, totalTasks: 4, estimatedMinutes: 20 },
  { id: 3, title: '资本主义的本质及规律', chapterOrder: 4, status: '未开始', statusType: 'info', coreQuestion: '为什么说劳动价值论是理解资本主义的基础？', deadline: '2026/07/22 22:00', completedTasks: 0, totalTasks: 4, estimatedMinutes: 25 }
]

const demoData = reactive({
  center: {
    overview: {
      totalChapters: 6, completedChapters: 2, inProgressChapters: 1,
      progressPercent: 33, totalTasks: 24, completedTasks: 8,
      totalStudyMinutes: 123, nextQuizDeadline: '2026/07/18 22:00'
    },
    tasks: [
      { chapterTitle: '实践与认识及其发展规律', title: '完成预习小测', desc: '系统会根据错题给出知识点解析', status: '待完成', statusType: 'warning' },
      { chapterTitle: '实践与认识及其发展规律', title: '提交课前困惑', desc: '问题会进入教师端课前学情聚类', status: '待完成', statusType: 'info' },
      { chapterTitle: '实践与认识及其发展规律', title: '阅读章节导学', desc: '先理解本章要解决的问题和学习路线', status: '已完成', statusType: 'success' },
      { chapterTitle: '实践与认识及其发展规律', title: '学习核心概念', desc: '重点区分实践、认识、真理和价值', status: '已完成', statusType: 'success' }
    ],
    quickActions: [
      { label: '进入预习小测', desc: '检验本章预习效果', route: '/student/pre-study-quiz' },
      { label: '向 AI 提问', desc: '不懂的地方问 AI 学伴', route: '/student/ai-qa' }
    ]
  },
  detail: {
    chapter: { title: '实践与认识及其发展规律', chapterOrder: 3, status: '导学中', estimatedMinutes: 18 },
    stats: [
      { label: '预计时长', value: '18 分钟', color: '#409EFF', desc: '导学与概念阅读' },
      { label: '核心概念', value: '5', color: '#67C23A', desc: '实践、认识、真理等' },
      { label: '来源引用', value: '3', color: '#E6A23C', desc: '教材、课件、案例' },
      { label: '学习任务', value: '4', color: '#909399', desc: '导学、小测、提问' }
    ],
    learningObjectives: [
      { type: '知识目标', content: '理解实践、认识、真理和价值的基本含义，能够说明实践对认识的决定作用。' },
      { type: '能力目标', content: '能够用实践观点分析社会调研、科研训练和专业学习中的认识变化。' },
      { type: '价值目标', content: '形成理论联系实际的学习方法，在实践中增长才干、服务社会。' }
    ],
    guideBlocks: [
      { title: '导入问题', content: '人的认识从哪里来，又怎样在实践中被检验和发展？阅读时先把问题放到真实学习、科研训练和社会实践中理解。' },
      { title: '学习主线', content: '先理解实践的基本特征，再分析认识如何从感性材料上升到理性认识，最后回到实践中接受检验。' },
      { title: '案例提示', content: '可以用一次社区调研、志愿服务或课程实验为例，观察实践前后的判断变化。' }
    ],
    keyConcepts: [
      { name: '实践', explain: '实践是人类能动地改造世界的社会性的物质活动，是认识产生和发展的基础。', example: '学生进入社区访谈、观察、整理材料，是把理论问题放到现实中检验。', misread: '实践不等于个人经验，也不等于简单行动。', source: '教材第三章' },
      { name: '认识', explain: '认识是在实践基础上主体对客体的能动反映，经历从感性认识到理性认识的发展过程。', example: '调研前的初步看法会在事实材料中被修正和深化。', misread: '认识不是脱离现实的主观想象。', source: '教材第三章' },
      { name: '真理', explain: '真理是标志主观同客观相符合的哲学范畴，实践是检验真理的唯一标准。', example: '判断观点是否正确，要看它能否解释和指导现实实践。', misread: '真理不是由多数意见或个人偏好决定。', source: '教材第三章' }
    ],
    taskSteps: [
      { title: '阅读导学正文', target: '了解本章问题、目标和学习路径', status: '进行中', statusType: 'warning' },
      { title: '概念辨析', target: '区分实践、认识、真理和价值', status: '待完成', statusType: 'info' },
      { title: '完成预习小测', target: '提交 6 道概念题并查看解析', status: '待完成', statusType: 'info' },
      { title: '提交课前问题', target: '把困惑汇总给教师端课前学情', status: '待提交', statusType: 'warning' }
    ],
    sourceRefs: [
      { id: 1, title: '《马克思主义基本原理》教材第三章', type: '教材', locator: '实践与认识相关段落', status: '已审核' },
      { id: 2, title: '王老师第三章课堂讲义', type: '课件', locator: '认识运动两次飞跃', status: '已审核' },
      { id: 3, title: '大学生社会实践案例库', type: '案例', locator: '社区调研案例', status: '已审核' }
    ],
    quizPreview: [
      { id: 1, knowledgePoint: '实践与认识', type: '单选题', stem: '下列关于实践与认识关系的说法，正确的是哪一项？', review: '复习"实践对认识的决定作用"' },
      { id: 2, knowledgePoint: '真理标准', type: '单选题', stem: '为什么说实践是检验真理的唯一标准？', review: '复习"真理的客观性与实践标准"' },
      { id: 3, knowledgePoint: '概念辨析', type: '判断题', stem: '认识的发展只需要从感性认识上升到理性认识...', review: '复习"认识运动的两次飞跃"' }
    ],
    timeline: [
      { title: '导学发布', time: '2026/07/07 14:30', desc: '教师发布本章导学、概念卡和预习任务。' },
      { title: '学生阅读', time: '进行中', desc: '当前处于导学阅读阶段，建议先完成概念辨析。' },
      { title: '小测与提问', time: '待完成', desc: '完成预习小测并提交一个真实困惑。' },
      { title: '教师查看学情', time: '课前 12 小时', desc: '教师端将聚合问题和错题，用于调整课堂重点。' }
    ]
  }
})
</script>

<style scoped>
.demo-root {
  max-width: 1100px; margin: 0 auto; padding: 32px 24px 80px;
  font-family: "Microsoft YaHei","PingFang SC",sans-serif;
  color: #2f2f2f; background: #f7f6f2;
}

/* Hero */
.demo-hero {
  background: linear-gradient(135deg, #2f2f2f 0%, #4a4a4a 100%);
  color: #fcfcfa; border-radius: 20px; padding: 36px 40px; margin-bottom: 40px;
}
.hero-badge {
  display: inline-block; background: rgba(255,255,255,.12);
  padding: 4px 14px; border-radius: 20px; font-size: 13px; margin-bottom: 12px;
}
.demo-hero h1 { font-size: 28px; font-weight: 800; letter-spacing: -0.3px; margin-bottom: 8px; }
.hero-sub { font-size: 14px; color: rgba(255,255,255,.65); margin-bottom: 20px; }
.hero-stats { display: flex; gap: 32px; }
.hero-stat strong { display: block; font-size: 32px; font-weight: 800; }
.hero-stat { font-size: 12px; color: rgba(255,255,255,.55); }

/* Stage */
.stage { margin-bottom: 16px; }
.stage-header {
  display: flex; align-items: flex-start; gap: 16px;
  padding: 24px 28px; border-radius: 16px;
  margin-bottom: 20px;
}
.stage-center { background: #ecf5ff; border: 1px solid #90caf9; }
.stage-detail { background: #f0f9eb; border: 1px solid #a5d6a7; }
.stage-quiz { background: #fdf6ec; border: 1px solid #f5dab1; }
.stage-num {
  font-size: 40px; font-weight: 900; line-height: 1;
  opacity: 0.2; flex-shrink: 0;
}
.stage-header h2 { font-size: 20px; font-weight: 800; margin-bottom: 4px; }
.stage-header p { font-size: 13px; color: var(--muted); }
.stage-header code {
  background: rgba(0,0,0,.06); padding: 1px 6px; border-radius: 4px;
  font-size: 12px;
}
.stage-body { padding: 0 4px; }

/* Data card */
.data-card {
  background: #1e1e1e; color: #d4d4d4; border-radius: 12px;
  padding: 16px 20px; margin-bottom: 16px;
}
.data-title { font-size: 14px; font-weight: 700; color: #e0e0e0; margin-bottom: 10px; }
.code-block {
  font-family: "Cascadia Code","Fira Code",monospace;
  font-size: 12px; line-height: 1.55; overflow-x: auto;
  white-space: pre; color: #ce9178;
}
.render-label {
  text-align: center; font-size: 12px; color: var(--muted);
  margin: 16px 0 12px; font-weight: 600;
}

/* Demo stat cards */
.demo-row { margin-bottom: 16px; }
.demo-stat {
  display: flex; align-items: center; gap: 12px;
  background: #fcfcfa; border: 1px solid #c9c9c9;
  border-radius: 14px; padding: 14px 16px;
}
.demo-stat-icon {
  width: 42px; height: 42px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.demo-stat-info { flex: 1; min-width: 0; }
.demo-stat-val { font-size: 20px; font-weight: 800; line-height: 1.2; }
.demo-stat-label { font-size: 12px; color: #8a8a8a; margin-top: 2px; }
.demo-stat-sub { font-size: 11px; color: #8a8a8a; margin-top: 1px; }

/* Chapter demo list */
.chapter-demo-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.demo-chapter {
  display: flex; align-items: center; gap: 14px;
  background: #fcfcfa; border: 1px solid #c9c9c9; border-radius: 14px;
  padding: 14px 18px;
}
.demo-chapter-warning { border-left: 4px solid #409EFF; }
.demo-chapter-success { border-left: 4px solid #67C23A; }
.demo-chapter-info { border-left: 4px solid #c9c9c9; }
.dc-order {
  width: 38px; height: 38px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px; font-weight: 800; flex-shrink: 0;
}
.dc-order-warning { background: #ecf5ff; color: #409EFF; }
.dc-order-success { background: #f0f9eb; color: #67C23A; }
.dc-order-info { background: #efeee9; color: #8a8a8a; }
.dc-body { flex: 1; min-width: 0; }
.dc-top { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.dc-top strong { font-size: 14px; }
.dc-question { font-size: 12px; color: #8a8a8a; margin-bottom: 6px; }
.dc-meta { display: flex; gap: 14px; font-size: 11px; color: #8a8a8a; margin-bottom: 6px; }
.dc-arrow { color: #8a8a8a; font-size: 18px; }

/* Side cards */
.demo-side-card {
  background: #fcfcfa; border: 1px solid #c9c9c9;
  border-radius: 14px; padding: 16px;
}
.dsc-title { font-size: 14px; font-weight: 700; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
.dsc-task {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 0; border-bottom: 1px dashed #c9c9c9;
}
.dsc-task:last-child { border-bottom: none; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #8a8a8a; flex-shrink: 0; }
.dot-done { background: #67C23A; }
.dsc-task-info { flex: 1; min-width: 0; }
.dsc-task-title { font-size: 13px; font-weight: 600; }
.dsc-task-sub { font-size: 11px; color: #8a8a8a; margin-top: 1px; }
.dsc-entry {
  display: flex; align-items: center; gap: 10px;
  padding: 10px; border-radius: 8px; background: #efeee9; margin-bottom: 6px;
}
.dsc-entry strong { font-size: 13px; }
.dsc-entry small { font-size: 11px; color: #8a8a8a; }
.entry-dot { font-size: 18px; }

/* Stage divider */
.stage-divider {
  text-align: center; padding: 24px 0;
  font-size: 13px; color: #8a8a8a; font-weight: 600;
}
.stage-divider span {
  display: inline-block; background: #efeee9; border: 1px dashed #c9c9c9;
  border-radius: 20px; padding: 8px 20px;
}

/* Detail stage */
.detail-stat {
  background: #efeee9; border: 1px dashed #c9c9c9;
  border-radius: 14px; padding: 16px; text-align: center;
}
.ds-label { font-size: 12px; color: #8a8a8a; }
.ds-val { font-size: 26px; font-weight: 800; margin: 4px 0; }
.ds-desc { font-size: 11px; color: #8a8a8a; }

.demo-card {
  background: #fcfcfa; border: 1px solid #c9c9c9;
  border-radius: 14px; padding: 18px;
}
.demo-card-title {
  font-size: 15px; font-weight: 700; margin-bottom: 14px;
  display: flex; justify-content: space-between; align-items: center;
}

.hero-box {
  background: #e6e4de; border: 1px solid #606060;
  border-radius: 14px; padding: 18px; margin-bottom: 14px;
}
.hero-label { font-size: 11px; color: #8a8a8a; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.hero-q { font-size: 19px; font-weight: 800; margin: 6px 0; }
.hero-summary { font-size: 13px; color: #4d4d4d; line-height: 1.7; }
.obj-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; }
.obj-grid div { background: #efeee9; border-radius: 8px; padding: 10px; font-size: 12px; }
.obj-type { display: block; font-size: 11px; color: #8a8a8a; margin-bottom: 4px; }

.task-step { padding: 10px 0; border-bottom: 1px dashed #c9c9c9; }
.task-step:last-child { border-bottom: none; }
.ts-head { display: flex; align-items: center; gap: 8px; }
.ts-idx {
  width: 22px; height: 22px; border-radius: 6px; background: #e6e4de;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 800;
}
.ts-target { font-size: 12px; color: #8a8a8a; margin: 4px 0 2px 30px; }

.g-block {
  background: #efeee9; border-radius: 8px; padding: 12px; margin-bottom: 8px;
}
.g-block strong { font-size: 13px; display: block; margin-bottom: 4px; }
.g-block p { font-size: 12px; color: #4d4d4d; line-height: 1.65; margin: 0; }

.src-item {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 8px 0; border-bottom: 1px dashed #c9c9c9;
}
.src-item:last-child { border-bottom: none; }
.src-item strong { font-size: 13px; }
.src-tag { font-size: 11px; color: #8a8a8a; }

.concept-demo {
  background: #efeee9; border-radius: 10px; padding: 12px; margin-bottom: 10px;
}
.cd-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.concept-demo p { font-size: 12px; line-height: 1.6; margin: 6px 0; }
.cd-example { background: #f2fbf4; border: 1px solid #a5d6a7; border-radius: 8px; padding: 8px 10px; font-size: 11px; margin-bottom: 6px; }
.cd-misread { background: #fff7e6; border: 1px solid #f5dab1; border-radius: 8px; padding: 8px 10px; font-size: 11px; }

.tl-item {
  display: flex; gap: 12px; padding: 8px 0;
  border-bottom: 1px dashed #c9c9c9;
}
.tl-item:last-child { border-bottom: none; }
.tl-dot {
  width: 10px; height: 10px; border-radius: 50%; background: #c9c9c9;
  margin-top: 5px; flex-shrink: 0;
}
.tl-dot.active { background: #409EFF; }
.tl-time { font-size: 11px; color: #8a8a8a; }
.tl-desc { font-size: 12px; color: #4d4d4d; }

.quiz-preview-table {
  width: 100%; font-size: 12px; border-collapse: collapse;
}
.quiz-preview-table th {
  text-align: left; padding: 8px 6px; border-bottom: 2px solid #c9c9c9;
  font-weight: 700; font-size: 11px; color: #8a8a8a;
}
.quiz-preview-table td {
  padding: 8px 6px; border-bottom: 1px dashed #c9c9c9;
}
.tc { text-align: center; }

.question-demo { padding: 8px 0; }
.qd-input-demo {
  background: #efeee9; border: 1px solid #c9c9c9; border-radius: 8px;
  padding: 12px; font-size: 13px; min-height: 60px;
}
.qd-hint { font-size: 11px; color: #8a8a8a; margin-top: 8px; }

/* Quiz cards */
.quiz-card {
  background: #fcfcfa; border: 1px solid #c9c9c9;
  border-radius: 14px; padding: 20px; margin-bottom: 16px;
}
.quiz-card.error-card { border-color: #ef9a9a; }
.qc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.qc-num {
  width: 26px; height: 26px; border-radius: 7px; background: #e6e4de;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 800;
}
.qc-num.err { background: #ffebee; color: #e57373; }
.qc-title { font-size: 14px; font-weight: 700; margin-bottom: 14px; line-height: 1.6; }
.qc-options { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.qco {
  padding: 8px 12px; border-radius: 8px; font-size: 13px;
  border: 1px solid transparent;
}
.qco.selected { background: #efeee9; border-color: #c9c9c9; }
.qco.correct { background: #f0f9eb; border-color: #a5d6a7; }
.qco.wrong { background: #ffebee; border-color: #ef9a9a; }
.qc-result {
  border-radius: 10px; padding: 12px 14px; font-size: 12px; line-height: 1.6;
}
.qc-result.success { background: #f0f9eb; border: 1px solid #a5d6a7; }
.qc-result.error { background: #ffebee; border: 1px solid #ef9a9a; }
.qc-result p { margin: 4px 0; }
.qc-review { font-size: 11px; color: #8a8a8a; }

.answer-grid-demo { display: flex; gap: 8px; flex-wrap: wrap; }
.ag-cell {
  width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;
  border-radius: 8px; font-size: 15px; font-weight: 700;
  border: 2px solid #c9c9c9; background: #fcfcfa;
}
.ag-cell.done { background: #e6e4de; border-color: #909090; }
.ag-cell.correct { background: #f0f9eb; border-color: #a5d6a7; color: #67C23A; }
.ag-cell.wrong { background: #ffebee; border-color: #ef9a9a; color: #e57373; }
.ag-legend { display: flex; gap: 14px; margin-top: 10px; font-size: 11px; color: #8a8a8a; }
.leg { display: flex; align-items: center; gap: 4px; }
.leg-dot { width: 8px; height: 8px; border-radius: 2px; }
.leg-dot.g { background: #67C23A; }
.leg-dot.r { background: #e57373; }
.leg-dot.gy { background: #909090; }

.score-card {
  background: linear-gradient(135deg, #f0f9eb, #e8f5e9);
  border: 1px solid #a5d6a7; border-radius: 14px;
  padding: 20px; text-align: center; margin-top: 12px;
}
.score-big { font-size: 48px; font-weight: 900; color: #67C23A; line-height: 1; }
.score-big span { font-size: 18px; font-weight: 600; }
.score-detail { font-size: 13px; color: #4d4d4d; margin-top: 6px; }
.score-weak { font-size: 12px; color: #e57373; margin-top: 4px; }

.info-line {
  padding: 8px 0; border-bottom: 1px dashed #c9c9c9;
  font-size: 12px; color: #8a8a8a;
}
.info-line:last-child { border-bottom: none; }

/* Summary */
.summary-section {
  background: #fcfcfa; border: 1px solid #c9c9c9;
  border-radius: 20px; padding: 36px; margin-top: 20px;
}
.summary-section h2 { font-size: 22px; font-weight: 800; text-align: center; margin-bottom: 24px; }
.flow-diagram {
  display: flex; align-items: center; justify-content: center;
  gap: 20px; margin-bottom: 32px;
}
.flow-node {
  background: #efeee9; border-radius: 14px;
  padding: 18px 24px; text-align: center; min-width: 160px;
}
.flow-node strong { font-size: 14px; }
.flow-node p { font-size: 11px; color: #8a8a8a; margin-top: 6px; line-height: 1.5; }
.fn-icon { font-size: 28px; margin-bottom: 6px; }
.flow-arrow { font-size: 24px; color: #8a8a8a; font-weight: 700; }

.summary-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; }
.sg-item { background: #efeee9; border-radius: 12px; padding: 18px; }
.sg-item h4 { font-size: 14px; margin-bottom: 10px; }
.sg-item ul { list-style: none; padding: 0; }
.sg-item li {
  font-size: 12px; color: #4d4d4d; padding: 4px 0;
  border-bottom: 1px dashed #c9c9c9;
}
.sg-item li:last-child { border-bottom: none; }
.sg-item code {
  background: rgba(0,0,0,.05); padding: 1px 5px; border-radius: 3px;
  font-size: 11px;
}

.demo-footer {
  text-align: center; margin-top: 32px; padding-top: 20px;
  border-top: 1px solid #c9c9c9;
}
.demo-footer p { font-size: 12px; color: #8a8a8a; margin-bottom: 4px; }
.demo-footer code {
  background: #efeee9; padding: 1px 6px; border-radius: 3px; font-size: 11px;
}
</style>
