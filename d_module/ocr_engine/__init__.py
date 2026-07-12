from __future__ import annotations
"""OCR 引擎封装模块。"""

from .service import build_docx_mixed_ocr_result, run_ocr_on_page, run_ocr_on_pages

__all__ = ["run_ocr_on_page", "run_ocr_on_pages", "build_docx_mixed_ocr_result"]
