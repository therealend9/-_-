# 考试文件识别 API 接口文档

## 1. 基本信息

- 服务地址：`http://127.0.0.1:8000`
- OpenAPI 页面：`/docs`
- 输出 JSON Schema：[exam-document.v1.schema.json](../contracts/exam-document.v1.schema.json)
- 正式处理结果版本：`exam-document.v1`
- 完整调用顺序和工作流消费规则：[工作流接入指南](考试文件识别模块工作流接入指南.md)

所有 JSON 请求使用 `application/json`；文件上传接口使用 `multipart/form-data`。错误响应为：

```json
{
  "detail": "错误说明"
}
```

`/api/process` 在答题卡未绑定模板时返回：

```json
{
  "detail": {
    "error_code": "TEMPLATE_NOT_BOUND",
    "message": "TEMPLATE_NOT_BOUND: exam_id"
  }
}
```

## 2. 考试与题目目录

### 创建考试

`POST /api/exams`

```json
{
  "exam_id": "mayuan_1516",
  "exam_name": "马原15-16期末试卷",
  "status": "draft"
}
```

`exam_id` 是后端稳定标识；`exam_name` 仅用于展示。

### 查询考试

`GET /api/exams`，或 `GET /api/exams/{exam_id}`。

响应包含考试名称、状态、当前模板 ID、模板名称和模板版本。

### 查询题目目录

`GET /api/exams/{exam_id}/questions`

响应是题目数组。`question_id` 是试题卷、答题卡模板和最终答案之间唯一允许使用的关联键。

```json
[
  {
    "question_id": "2.1",
    "question_no": "2.1",
    "question_text": "题干内容",
    "order": 5
  }
]
```

### 发布考试

`PATCH /api/exams/{exam_id}/status`

```json
{ "status": "published" }
```

考试必须先绑定模板才能发布。发布后不能重新绑定或更换模板。

## 3. 模板接口

### 创建答题卡模板草稿

`POST /api/templates/drafts`

表单字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `file` | 文件 | 是 | 空白答题卡 PDF/JPG/PNG |
| `template_id` | 字符串 | 是 | 模板唯一 ID |
| `template_name` | 字符串 | 是 | 模板名称 |
| `version` | 整数 | 是 | 正整数模板版本 |
| `exam_id` | 字符串 | 是 | 已有题目目录的考试 ID |

后端按区域阅读顺序映射题目目录 ID。答题卡上印刷的题号保存为 `template_label`，不是最终关联键。

### 读取、复核和发布模板

- `GET /api/templates/{template_id}`：获取模板及其页面、候选区域。
- `PUT /api/templates/{template_id}/review`：请求体为 `{ "pages": [...], "publish": false }`，保存人工复核后的完整页面数组。
- `POST /api/templates/{template_id}/publish`：发布模板。
- `POST /api/exams/{exam_id}/template`：请求体为 `{ "template_id": "tpl_mayuan_1516_v1" }`，绑定已发布模板。

绑定时后端强制检查：考试存在且为 `draft`、模板已发布且版本明确、模板答案区域 ID 与题目目录 ID 一致；答题卡已有成功提交时不能更换模板。

## 4. 文件处理

### 请求

`POST /api/process`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `file` | 文件 | 是 | PDF、JPG、PNG 或 DOCX |
| `document_role` | 枚举 | 是 | `question_paper` 或 `answer_sheet` |
| `exam_id` | 字符串 | 条件必填 | 答题卡必填；需要保存试题题目目录时，试题卷也必须传入 |
| `submission_id` | 字符串 | 否 | 调用方幂等标识；省略时由服务生成 |

答题卡请求不传 `template_id`，服务端按 `exam_id` 解析已绑定模板。

### 共同响应字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `schema_version` | 字符串 | 固定为 `exam-document.v1` |
| `submission_id` | 字符串 | 本次处理标识 |
| `exam_id` | 字符串或 `null` | 考试标识 |
| `exam_name` | 字符串或 `null` | 考试名称 |
| `document_role` | 枚举 | 文件角色 |
| `layout_type` | 枚举 | `free` 或 `fixed` |

### 试题卷成功响应

当 `document_role=question_paper` 时，响应含 `questions[]`：

```json
{
  "schema_version": "exam-document.v1",
  "submission_id": "paper_001",
  "exam_id": "mayuan_1516",
  "exam_name": "马原15-16期末试卷",
  "document_role": "question_paper",
  "layout_type": "free",
  "questions": [
    {
      "question_id": "2.1",
      "question_no": "2.1",
      "question_text": "题干内容",
      "page_nos": [2],
      "confidence": 0.96,
      "needs_review": false,
      "risk_flags": []
    }
  ]
}
```

### 答题卡成功响应

当 `document_role=answer_sheet` 时，响应含模板信息和 `answers[]`：

```json
{
  "schema_version": "exam-document.v1",
  "submission_id": "student_001",
  "exam_id": "mayuan_1516",
  "exam_name": "马原15-16期末试卷",
  "document_role": "answer_sheet",
  "layout_type": "fixed",
  "template_id": "tpl_mayuan_1516_v1",
  "template_name": "马原15-16答题卡",
  "template_version": 1,
  "answers": [
    {
      "question_id": "2.1",
      "question_no": "2.1",
      "answer_text": "学生作答文本",
      "is_blank": false,
      "page_nos": [1],
      "confidence": 0.83,
      "needs_review": false,
      "risk_flags": []
    }
  ]
}
```

`question_id` 必须用于与试题卷的 `questions[].question_id` 关联。`question_no` 仅用于显示，不应作为跨模块关联键。

## 5. 兼容性规则

- `exam-document.v1` 内只新增可选字段，不删除或改变既有字段类型。
- 需要删除字段、改变字段类型或改变字段语义时，发布新的 `schema_version`，例如 `exam-document.v2`。
- 接入方应拒绝或显式降级处理不认识的主版本，而不是假定格式兼容。
