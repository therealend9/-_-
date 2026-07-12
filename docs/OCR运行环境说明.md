# OCR 运行环境说明

扫描件、图片和手写答题卡必须使用 PaddleOCR。当前系统默认 `python` 是 Python
3.14，PaddlePaddle 不提供该版本的 Windows 包，因此不能用它启动 OCR 服务。

项目已配置独立运行环境：

```text
E:\ocr_runtime\python311\python.exe
<项目目录>\.venv-ocr\Scripts\python.exe
```

启动 API 时使用：

```powershell
.\scripts\start_api_ocr.ps1
```

或指定端口：

```powershell
.\scripts\start_api_ocr.ps1 -Port 8001
```

该环境包含 `paddlepaddle`、`paddleocr`、`opencv-contrib-python`、FastAPI 和项目
所需基础依赖。`GET /health` 中以下字段均为 `true` 时，扫描件和答题卡 OCR 可用：

```json
{
  "dependencies": {
    "paddleocr": true,
    "paddlepaddle": true,
    "opencv": true
  }
}
```

`python` 3.14 仍可用于不依赖 OCR 的文本型 PDF 试题卷处理，但不应用于 API OCR
服务。
