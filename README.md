# 考试文件识别模块

当前版本负责两类文件处理：

- 自由版式试题卷识别，输出 `questions[]`。
- 固定模板答题卡识别，输出 `answers[]`。

输出统一遵循 `exam-document.v1`。

## 主要入口

启动 API：

```powershell
.\scripts\start_api_ocr.ps1
```

检查服务：

```powershell
curl.exe http://127.0.0.1:8000/health
```

命令行处理单个文件：

```powershell
.\.venv-ocr\Scripts\python.exe scripts\run_full_processor.py "试题或答题卡.pdf" `
  --document-role question_paper `
  --exam-id mayuan_1516 `
  --out outputs\result.json
```

模板草稿生成：

```powershell
.\.venv-ocr\Scripts\python.exe scripts\create_answer_sheet_template.py "空白答题卡.pdf" `
  --template-id tpl_mayuan_1516_v1 `
  --template-name "马原15-16答题卡" `
  --version 1 `
  --exam-id mayuan_1516
```

## 目录

- `api_service/`：FastAPI 服务入口。
- `full_pipeline.py`：单文件完整处理入口。
- `d_module/`：文件接收、解析、页面标准化和 OCR。
- `b_module/`：版式路由、分题、跨页合并、风险标记和结果导出。
- `template_builder/`：答题卡模板候选区域生成。
- `template_registry/`：考试、题目目录、模板、绑定和提交台账管理。
- `page_alignment/`、`region_extractor/`、`region_ocr/`：固定模板答题卡处理组件。
- `contracts/`：正式输出 JSON Schema。
- `docs/`：当前版本接口、工作流和运行说明。
- `揭榜挂帅_思政卷子/`：真实试卷样本，用于识别验证。

## 文档入口

工作流人员优先阅读：

1. [考试文件识别模块工作流接入指南](docs/考试文件识别模块工作流接入指南.md)
2. [考试文件识别 API 接口文档](docs/考试文件识别API接口文档.md)
3. [exam-document.v1 JSON Schema](contracts/exam-document.v1.schema.json)

开发和运行环境说明：

- [OCR 运行环境说明](docs/OCR运行环境说明.md)
- [标准答题卡固定区域使用说明](docs/标准答题卡固定区域使用说明.md)
- [考试文件识别模块剩余问题](docs/考试文件识别模块问题跟踪.md)

## 运行环境

扫描件、图片和手写答题卡使用项目内的 Python 3.11 OCR 环境：

```text
.venv-ocr\Scripts\python.exe
```

依赖清单见 `requirements-handoff.txt`。当前 API 依赖 PaddleOCR、PaddlePaddle、OpenCV、FastAPI 和项目基础依赖。
