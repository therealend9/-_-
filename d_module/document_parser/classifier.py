from __future__ import annotations
"""文件类型和解析路线判断。

当前版本：
- docx -> docx_mixed：文本直接提取，内嵌图片 OCR，并在原位置插入图片标记。
- pdf  -> pdf_text / pdf_image：文本层可用时优先提取，不可用页回退 OCR。
- jpg/png -> image：作为单页图片 OCR。
"""

from d_module.constants import (
    PARSE_MODE_DOCX_MIXED,
    PARSE_MODE_IMAGE,
    PARSE_MODE_PDF_IMAGE,
    PARSE_MODE_PDF_TEXT,
    SOURCE_TYPE_DOCX,
    SOURCE_TYPE_IMAGE,
    SOURCE_TYPE_PDF,
)


def classify_source_type(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    if ext == "docx":
        return SOURCE_TYPE_DOCX
    if ext == "pdf":
        return SOURCE_TYPE_PDF
    if ext in {"jpg", "jpeg", "png"}:
        return SOURCE_TYPE_IMAGE
    raise ValueError(f"不支持的扩展名: {ext}")


def decide_parse_mode(source_type: str, pdf_has_text: bool = False) -> str:
    """根据文件类型决定解析模式。"""
    if source_type == SOURCE_TYPE_DOCX:
        return PARSE_MODE_DOCX_MIXED
    if source_type == SOURCE_TYPE_PDF:
        return PARSE_MODE_PDF_TEXT if pdf_has_text else PARSE_MODE_PDF_IMAGE
    if source_type == SOURCE_TYPE_IMAGE:
        return PARSE_MODE_IMAGE
    raise ValueError(f"非法 source_type: {source_type}")
