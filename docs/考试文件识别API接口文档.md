# 考试文件识别 API 接口文档

## 1. 范围

当前版本只处理三类输入：

1. 自由版式试题卷，输出 `questions[]`。
2. 空白答题卡，用于生成和复核固定模板。
3. 学生答题卡，按已发布模板裁剪并识别手写作答，输出 `answers[]`。

本模块不接收或保存独立的标准答案文件，不支持 `document_role=answer_key`，也不负责评分和答案比对。

服务地址：`http://127.0.0.1:8000`，OpenAPI：`/docs`，输出版本：`exam-document.v1`。

## 2. 考试与题目目录

### `POST /api/exams`

```json
{
  "exam_id": "mayuan_1516",
  "exam_name": "马原15-16期末试卷",
  "status": "draft"
}
```

### `GET /api/exams`、`GET /api/exams/{exam_id}`

查询考试、名称、状态和已绑定模板信息。

### `GET /api/exams/{exam_id}/questions`

查询已保存的题目目录。`question_id` 是试题、答题卡模板和学生答题结果之间唯一的关联键。

### `PATCH /api/exams/{exam_id}/status`

请求体：`{"status":"published"}`。考试发布前必须已经绑定已发布模板。

## 3. 空白答题卡模板

### `POST /api/templates/drafts`

使用 `multipart/form-data`：

| 字段 | 必填 | 说明 |
|---|---:|---|
| `file` | 是 | 空白答题卡 PDF/JPG/PNG/DOCX |
| `template_id` | 是 | 模板 ID |
| `template_name` | 是 | 前端展示名称 |
| `version` | 是 | 正整数版本 |
| `exam_id` | 是 | 已建立题目目录的考试 ID |

服务自动提出书写区域，返回 `pending_review` 模板草稿。前端必须允许老师调整区域并确认 `question_id`。

### 模板维护接口

- `GET /api/templates/{template_id}`：读取模板草稿。
- `PUT /api/templates/{template_id}/review`：保存人工复核后的完整 `pages`。
- `POST /api/templates/{template_id}/publish`：发布模板。
- `POST /api/exams/{exam_id}/template`：把已发布模板绑定到考试。

绑定强制校验：考试存在且状态允许、模板已发布、版本明确、模板区域的 `question_id` 与题目目录完全一致；已有学生答题卡提交后不能更换模板。

## 4. 文件处理接口

### `POST /api/process`

请求类型为 `multipart/form-data`：

| 字段 | 必填 | 取值或说明 |
|---|---:|---|
| `file` | 是 | PDF、JPG、PNG 或 DOCX |
| `document_role` | 是 | `question_paper` 或 `answer_sheet` |
| `exam_id` | 条件必填 | 试题卷保存题目目录、答题卡读取绑定模板时必填 |
| `submission_id` | 否 | 调用方生成的稳定幂等标识 |

不再接受 `answer_key`，也不接受 `answer_key_version`。

成功结果会按 `submission_id` 持久化。相同 `submission_id`、相同文件内容、相同考试和模板版本再次提交时，服务直接返回已保存的结果，不重复执行 OCR；若相同 `submission_id` 对应的文件或上下文不同，返回 `422`。

### `GET /api/submissions/{submission_id}`

读取一次成功 `POST /api/process` 的已保存最终结果。响应结构与原处理接口完全一致。

### 试题卷

`document_role=question_paper`，使用自由版式识别，成功响应包含：

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

提交 `exam_id` 时，服务端同时保存题目目录。

### 学生答题卡

`document_role=answer_sheet`，必须传 `exam_id`，服务端自动查询考试绑定的固定模板，不允许调用方直接指定模板：

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

处理顺序为：页面对齐、固定区域裁剪、空白检测、手写 OCR、同题多区域合并。`question_id` 必须与题目目录一致；`question_no` 仅用于展示。

## 5. 错误与兼容

上传文件会先进入安全隔离区，只有通过真实类型和资源限制校验后才会进入 OCR。成功响应格式保持 `exam-document.v1` 不变。安全校验失败时，`detail` 使用结构化错误：

```json
{
  "error_code": "FILE_SIGNATURE_MISMATCH",
  "message": "文件扩展名与真实内容不一致",
  "retryable": false,
  "file_id": null
}
```

- `413`：文件超过大小限制。
- `415`：扩展名或客户端 MIME 不允许。
- `422`：文件签名、图片像素、PDF 页数或渲染像素、DOCX 压缩包安全校验失败。
- `503`：安全校验所需的图片或 PDF 组件不可用。

- `400`：文件为空或类型不支持。
- `404`：考试或模板不存在。
- `422`：模板未绑定、模板未发布、题目 ID 不一致或角色不支持。
- `503`：OCR 运行依赖缺失。

机器校验定义见 [exam-document.v1.schema.json](../contracts/exam-document.v1.schema.json)。
