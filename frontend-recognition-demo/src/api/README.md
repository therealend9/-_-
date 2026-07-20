# 前后端接口切换说明

当前前端默认使用本地模拟数据，可以直接运行和演示；后端完成后，只需要按本文件约定返回 JSON，再把环境变量切换到真实接口。

## 运行方式

```bash
npm install
npm run dev
```

本项目默认访问路径带有前缀：

```text
http://127.0.0.1:5173/sizheng-agent-frontend/
```

## 环境变量

复制 `.env.example` 为 `.env.local`，开发阶段保持：

```text
VITE_USE_MOCK=true
VITE_API_BASE_URL=http://localhost:8080/api
```

后端接口完成后改成：

```text
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8080/api
```

## 已预留接口

学生端：

```text
GET  /student/dashboard
GET  /student/shell
GET  /student/pre-study
GET  /student/pre-study/:chapterId
POST /student/pre-study/question
GET  /student/pre-study/quiz
POST /student/pre-study/quiz/submit
GET  /student/ai-qa
GET  /student/notifications
GET  /student/profile
GET  /student/learning-report
GET  /student/class-interaction
POST /student/class-interaction/answer
GET  /student/feedback
GET  /student/in-class-quiz
GET  /student/source/:sourceId
GET  /student/feedback/:assignmentId
GET  /student/grading/:submissionId
```

教师端：

```text
GET  /teacher/dashboard
GET  /teacher/shell
GET  /teacher/lesson-design
POST /teacher/lesson-design/publish
GET  /teacher/preclass-analytics
GET  /teacher/class-interaction
POST /teacher/class-interaction/command
GET  /teacher/live-quiz
POST /teacher/live-quiz/generate
POST /teacher/live-quiz/publish
GET  /teacher/grading-review
POST /teacher/grading-review/confirm
GET  /teacher/class-report
GET  /teacher/resource-library
```

管理端：

```text
GET /admin/shell
GET /admin/dashboard
GET /admin/analytics
GET /admin/ai-review
GET /admin/ai-review/:id
GET /admin/knowledge-sources
GET /admin/knowledge-sources/:id
GET /admin/rubrics
GET /admin/assignments
GET /admin/assignments/:id
GET /admin/users
GET /admin/users/:id
GET /admin/users/batch-import
GET /admin/courses
GET /admin/courses/:id/structure
GET /admin/audit-log
GET /admin/audit-log/:id
GET /admin/system-settings
GET /admin/system-settings/:configKey
GET /admin/role-permission
GET /admin/role-permission/:roleId/permissions
GET /admin/org-structure
GET /admin/org-structure/:nodeId
```

## 后端返回格式

前端页面现在直接消费 JSON 对象，不需要额外包一层。如果后端统一返回：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

则需要在 `src/api/http.js` 里把 `return response.json()` 改成先取 `data`。

## 修改原则

1. 页面组件只调用 `src/api/*.js` 中的函数。
2. 后端接口地址只写在 `src/api/*.js` 和 `src/api/http.js`。
3. 新增页面时，先在 `src/api/` 增加数据函数，再由页面调用，避免把接口地址散落在页面里。
