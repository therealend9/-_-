from __future__ import annotations
"""A 负责人主流程入口。

当前主链路：
- DOCX：文本直接提取 + 内嵌图片标记/OCR -> OCRPageResult[]
- PDF：文本层 -> OCRPageResult[]；无可用文本的页面回退 PaddleOCR
- JPG/PNG：单页图片 -> 图像预处理 -> PaddleOCR -> OCRPageResult[]
"""

from pathlib import Path
from typing import Optional, Union

from d_module.constants import PARSE_MODE_DOCX_MIXED, PARSE_MODE_PDF_TEXT, TASK_STATUS_OCR_DONE
from d_module.document_parser.service import classify_and_parse_document
from d_module.file_ingest.service import create_file_task
from d_module.image_preprocess.service import preprocess_page_image, preprocess_pages
from d_module.ocr_engine.service import (
    build_docx_mixed_ocr_result,
    build_pdf_text_ocr_result,
    run_ocr_on_page,
    run_ocr_on_pages,
)
from d_module.page_renderer.service import render_pages_to_images
from d_module.utils.path_utils import relativize_paths_in_data


def process_file_to_ocr_results(
    submission_id: str,
    origin_name: str,
    mime_type: str,
    file_size: Optional[int] = None,
    source_path: Optional[Union[str, Path]] = None,
    file_bytes: Optional[bytes] = None,
    parse_strategy: str = "auto",
) -> dict:
    """完整处理链路，返回 A 输出给 B 的标准结果。"""
    file_task = create_file_task(
        submission_id=submission_id,
        origin_name=origin_name,
        mime_type=mime_type,
        file_size=file_size,
        source_path=source_path,
        file_bytes=file_bytes,
    )

    parse_result = classify_and_parse_document(file_task)
    pages = render_pages_to_images(file_task, parse_result)

    force_image_ocr = parse_strategy == "force_image_ocr"
    template_regions_only = parse_strategy == "template_regions_only"
    if parse_strategy not in {"auto", "force_image_ocr", "template_regions_only"}:
        raise ValueError("parse_strategy must be 'auto', 'force_image_ocr', or 'template_regions_only'")

    if template_regions_only:
        # Fixed answer cards are aligned and cropped by the template route.
        # Do not OCR the complete student page, which contains identity fields.
        pages = preprocess_pages(pages)
        ocr_results = []
    elif parse_result["parse_mode"] == PARSE_MODE_DOCX_MIXED:
        # DOCX 不对整页做 OCR，只对内嵌图片 OCR；文本直接来自 DOCX。
        ocr_results = [
            build_docx_mixed_ocr_result(
                file_id=file_task.file_id,
                page=pages[0],
                docx_elements=parse_result.get("docx_elements", []),
            )
        ]
    elif parse_result["parse_mode"] == PARSE_MODE_PDF_TEXT and not force_image_ocr:
        text_page_map = {
            int(item["page_no"]): item
            for item in parse_result.get("extracted_text_pages", [])
        }
        processed_pages = []
        ocr_results = []
        for page in pages:
            extracted_page = text_page_map.get(page.page_no)
            if extracted_page and extracted_page.get("usable"):
                result = build_pdf_text_ocr_result(file_task.file_id, page, extracted_page)
            else:
                page = preprocess_page_image(page)
                result = run_ocr_on_page(file_task.file_id, page)
            processed_pages.append(page)
            ocr_results.append(result)
        pages = processed_pages
    else:
        pages = preprocess_pages(pages)
        ocr_results = run_ocr_on_pages(file_task.file_id, pages)

    file_task.task_status = TASK_STATUS_OCR_DONE

    output = {
        "file_task": file_task.to_dict(),
        "parse_result": parse_result,
        "normalized_pages": [page.to_dict() for page in pages],
        "ocr_page_results": [result.to_dict() for result in ocr_results],
        "ocr_strategy": parse_strategy,
    }
    return relativize_paths_in_data(output)
