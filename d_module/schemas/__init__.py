from __future__ import annotations
"""A 负责人模块核心数据结构。"""

from .file_task import FileTask
from .normalized_page import NormalizedPage
from .ocr_block import OCRBlock
from .ocr_page_result import OCRPageResult
from .error_result import ErrorResult

__all__ = [
    "FileTask",
    "NormalizedPage",
    "OCRBlock",
    "OCRPageResult",
    "ErrorResult",
]
