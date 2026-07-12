from __future__ import annotations
"""页面渲染服务。

当前策略：
- DOCX：文本+图片混合模式，只生成占位页面，真实文字/图片 OCR 在 ocr_engine 中处理。
- PDF：每页渲染成图片。
- JPG / PNG：作为单页图片。
"""

from typing import List

from d_module import config
from d_module.constants import (
    COORDINATE_BASE_PAGE_IMAGE,
    PARSE_MODE_DOCX_MIXED,
    PARSE_MODE_IMAGE,
    PARSE_MODE_PDF_IMAGE,
    PARSE_MODE_PDF_TEXT,
    TASK_STATUS_RENDERED,
)
from d_module.page_renderer.docx_renderer import create_docx_placeholder_page
from d_module.page_renderer.docx_pdf_renderer import can_render_docx_via_pdf, render_docx_pages_via_pdf
from d_module.page_renderer.image_loader import load_image_as_page
from d_module.page_renderer.pdf_renderer import render_pdf_pages
from d_module.schemas.file_task import FileTask
from d_module.schemas.normalized_page import NormalizedPage


def _build_normalized_page(file_id: str, item: dict) -> NormalizedPage:
    return NormalizedPage(
        file_id=file_id,
        page_no=item["page_no"],
        page_image_path=item["image_path"],
        preprocessed_image_path=None,
        original_width=item["width"],
        original_height=item["height"],
        processed_width=item["width"],
        processed_height=item["height"],
        dpi=item.get("dpi"),
        coordinate_base=COORDINATE_BASE_PAGE_IMAGE,
    )


def render_pages_to_images(file_task: FileTask, parse_result: dict, dpi: int = config.DEFAULT_DPI) -> List[NormalizedPage]:
    """将输入文件渲染 / 标准化为页面对象。"""
    config.ensure_storage_dirs()
    parse_mode = parse_result["parse_mode"]

    if parse_mode == PARSE_MODE_DOCX_MIXED:
        if _should_use_docx_pdf_route():
            try:
                page_items = render_docx_pages_via_pdf(
                    file_id=file_task.file_id,
                    docx_path=file_task.storage_path,
                    dpi=dpi,
                )
                parse_result["docx_render_mode"] = "pdf_rendered"
            except Exception:
                page_items = [
                    create_docx_placeholder_page(
                        file_id=file_task.file_id,
                        docx_elements=parse_result.get("docx_elements", []),
                    )
                ]
                parse_result["docx_render_mode"] = "mixed_placeholder_fallback"
        else:
            page_items = [
                create_docx_placeholder_page(
                    file_id=file_task.file_id,
                    docx_elements=parse_result.get("docx_elements", []),
                )
            ]
            parse_result["docx_render_mode"] = "mixed_placeholder"

    elif parse_mode == PARSE_MODE_IMAGE:
        page_items = [load_image_as_page(file_task.file_id, file_task.storage_path)]

    elif parse_mode in {PARSE_MODE_PDF_IMAGE, PARSE_MODE_PDF_TEXT}:
        page_items = render_pdf_pages(file_task.file_id, file_task.storage_path, dpi=dpi)

    else:
        raise ValueError(f"不支持的 parse_mode: {parse_mode}")

    pages = [_build_normalized_page(file_task.file_id, item) for item in page_items]
    file_task.page_count = len(pages)
    file_task.task_status = TASK_STATUS_RENDERED
    return pages


def _should_use_docx_pdf_route() -> bool:
    if config.DOCX_RENDER_MODE not in config.DOCX_RENDER_MODES:
        return False
    if config.DOCX_RENDER_MODE == "mixed":
        return False
    if config.DOCX_RENDER_MODE == "pdf":
        return can_render_docx_via_pdf()
    return can_render_docx_via_pdf()
