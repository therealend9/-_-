from __future__ import annotations
"""A 负责人模块配置。

当前版本采用混合策略：
- PDF：文本层优先；无可用文本的页面回退到图片 OCR。
- DOCX：可编辑文本直接提取；内嵌图片按出现位置插入标记，并对图片 OCR。
- JPG / PNG：直接作为单页图片 OCR。
"""

from pathlib import Path
import os
import shutil
from typing import Optional


BASE_STORAGE_DIR = Path(os.getenv("D_MODULE_STORAGE_ROOT", "storage"))

RAW_DIR = BASE_STORAGE_DIR / "raw"
CONVERTED_DIR = BASE_STORAGE_DIR / "converted"
PAGE_DIR = BASE_STORAGE_DIR / "pages"
PREPROCESSED_DIR = BASE_STORAGE_DIR / "preprocessed"
EXTRACTED_IMAGE_DIR = BASE_STORAGE_DIR / "docx_images"

DEFAULT_DPI = int(os.getenv("D_MODULE_DEFAULT_DPI", "300"))
DEFAULT_OCR_ENGINE = os.getenv("D_MODULE_OCR_ENGINE", "paddleocr")
LOW_CONFIDENCE_THRESHOLD = float(os.getenv("D_MODULE_LOW_CONFIDENCE_THRESHOLD", "0.75"))

# 旧的 DOCX->PDF 路线仍保留配置兼容，但当前默认 DOCX 采用“文本+内嵌图片 OCR”混合路线。
# 如果后续要恢复 DOCX 全页图片化，可以继续使用该配置。
LIBREOFFICE_BIN = os.getenv("D_MODULE_LIBREOFFICE_BIN", "libreoffice")
DOCX_RENDER_MODE = os.getenv("D_MODULE_DOCX_RENDER_MODE", "auto").strip().lower()
DOCX_RENDER_MODES = {"mixed", "pdf", "auto"}

# 第一版限制：避免超大文件拖垮服务。
MAX_FILE_SIZE_BYTES = int(os.getenv("D_MODULE_MAX_FILE_SIZE_BYTES", str(50 * 1024 * 1024)))

ALLOWED_EXTENSIONS = {"docx", "pdf", "jpg", "jpeg", "png"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
}

# DOCX 混合模式下没有真实页面渲染图，所以创建一张占位页用于满足 B 的 image_path 字段。
DOCX_PLACEHOLDER_WIDTH = int(os.getenv("D_MODULE_DOCX_PLACEHOLDER_WIDTH", "1240"))
DOCX_PLACEHOLDER_HEIGHT = int(os.getenv("D_MODULE_DOCX_PLACEHOLDER_HEIGHT", "1754"))

# 第一版联调约束：PDF/图片预处理尽量不改变最终图像尺寸。
KEEP_IMAGE_SIZE_AFTER_PREPROCESS = True


def resolve_libreoffice_bin() -> Optional[str]:
    """Resolve a usable LibreOffice/soffice executable path if present."""
    candidates = []

    env_value = os.getenv("D_MODULE_LIBREOFFICE_BIN")
    if env_value:
        candidates.append(env_value)

    candidates.extend(
        [
            "soffice",
            "libreoffice",
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    )

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        if Path(candidate).exists():
            return str(Path(candidate))
    return None


def ensure_storage_dirs() -> None:
    """创建模块运行需要的存储目录。"""
    for directory in (RAW_DIR, CONVERTED_DIR, PAGE_DIR, PREPROCESSED_DIR, EXTRACTED_IMAGE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
