from __future__ import annotations

from typing import Iterable

from .free_layout_pipeline_v3 import split_free_layout_questions_v3


def split_free_layout_questions(file_id: str, page_ocr_results: Iterable[dict]) -> dict:
    """Compatibility wrapper for legacy imports."""
    return split_free_layout_questions_v3(file_id=file_id, page_ocr_results=page_ocr_results)
