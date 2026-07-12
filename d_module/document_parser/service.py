from __future__ import annotations
"""文档解析服务。

当前版本：
- DOCX：提取文本和内嵌图片元素，后续生成混合 OCRPageResult。
- PDF：文本层可用页直接提取，不可用页在主流程中单独回退 OCR。
- 图片：单页图片。
"""

from d_module.constants import (
    PARSE_MODE_DOCX_MIXED,
    PARSE_MODE_PDF_TEXT,
    SOURCE_TYPE_DOCX,
    SOURCE_TYPE_IMAGE,
    SOURCE_TYPE_PDF,
    TASK_STATUS_PARSED,
)
from d_module.document_parser.classifier import decide_parse_mode
from d_module.document_parser.docx_parser import extract_docx_mixed_elements
from d_module.document_parser.pdf_parser import extract_pdf_text_pages, get_pdf_page_count
from d_module.schemas.file_task import FileTask


def classify_and_parse_document(file_task: FileTask) -> dict:
    """判断解析路线，并准备后续处理需要的轻量解析结果。"""
    docx_elements = []
    extracted_text_pages = []
    pdf_has_text = False
    if file_task.source_type == SOURCE_TYPE_DOCX:
        # DOCX 不再整页图片化；这里直接提取文本和图片占位元素。
        docx_elements = extract_docx_mixed_elements(file_task.storage_path, file_task.file_id)
        page_count = 1
    elif file_task.source_type == SOURCE_TYPE_PDF:
        page_count = get_pdf_page_count(file_task.storage_path)
        extracted_text_pages = extract_pdf_text_pages(file_task.storage_path)
        pdf_has_text = any(page.get("usable") for page in extracted_text_pages)
    elif file_task.source_type == SOURCE_TYPE_IMAGE:
        page_count = 1
    else:
        page_count = None

    parse_mode = decide_parse_mode(file_task.source_type, pdf_has_text=pdf_has_text)
    file_task.page_count = page_count
    file_task.parse_mode = parse_mode
    file_task.task_status = TASK_STATUS_PARSED

    return {
        "file_id": file_task.file_id,
        "parse_mode": parse_mode,
        "page_count": page_count,
        "extracted_text_pages": extracted_text_pages,
        "docx_elements": docx_elements if parse_mode == PARSE_MODE_DOCX_MIXED else [],
        "docx_render_mode": "pending" if parse_mode == PARSE_MODE_DOCX_MIXED else None,
        "image_based": parse_mode not in {PARSE_MODE_DOCX_MIXED, PARSE_MODE_PDF_TEXT},
        "hybrid_mode": bool(
            extracted_text_pages
            and any(page.get("usable") for page in extracted_text_pages)
            and any(not page.get("usable") for page in extracted_text_pages)
        ),
        "text_extract_page_nos": [page["page_no"] for page in extracted_text_pages if page.get("usable")],
        "fallback_ocr_page_nos": [page["page_no"] for page in extracted_text_pages if not page.get("usable")],
    }
