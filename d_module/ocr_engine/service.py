from __future__ import annotations
"""OCR 服务。

当前策略：
- PDF / JPG / PNG：页面图片 -> PaddleOCR -> OCRPageResult。
- DOCX：可编辑文本直接转 text block；内嵌图片先插入 image_marker block，再对图片 OCR，
  将图片 OCR block 插入到 marker 后面，保持文档阅读顺序。
"""

from typing import Iterable, List

from d_module import config
from d_module.constants import (
    BBOX_SOURCE_ESTIMATED,
    BBOX_SOURCE_OCR,
    BBOX_SOURCE_RENDERED,
    BLOCK_TYPE_IMAGE_MARKER,
    BLOCK_TYPE_IMAGE_OCR,
    BLOCK_TYPE_TEXT,
    SOURCE_MODE_IMAGE_MARKER,
    SOURCE_MODE_OCR,
    SOURCE_MODE_TEXT_EXTRACT,
)
from d_module.ocr_engine.paddle_ocr_client import run_paddle_ocr
from d_module.ocr_engine.result_normalizer import normalize_paddle_result
from d_module.schemas.normalized_page import NormalizedPage
from d_module.schemas.ocr_block import OCRBlock
from d_module.schemas.ocr_page_result import OCRPageResult
from d_module.utils.id_generator import generate_block_id
from d_module.utils.image_utils import get_image_size


def run_ocr_on_page(
    file_id: str,
    page: NormalizedPage,
    ocr_engine: str = config.DEFAULT_OCR_ENGINE,
    low_confidence_threshold: float = config.LOW_CONFIDENCE_THRESHOLD,
) -> OCRPageResult:
    """对单页图片执行 OCR，并标准化为 OCRPageResult。"""
    if ocr_engine != "paddleocr":
        raise ValueError(f"第一版仅支持 paddleocr，当前传入: {ocr_engine}")

    raw_result = run_paddle_ocr(page.effective_image_path)
    return normalize_paddle_result(
        file_id=file_id,
        page=page,
        raw_result=raw_result,
        ocr_engine=ocr_engine,
        low_confidence_threshold=low_confidence_threshold,
    )


def run_ocr_on_pages(
    file_id: str,
    pages: Iterable[NormalizedPage],
    ocr_engine: str = config.DEFAULT_OCR_ENGINE,
    low_confidence_threshold: float = config.LOW_CONFIDENCE_THRESHOLD,
) -> List[OCRPageResult]:
    """批量对页面图片执行 OCR。"""
    return [
        run_ocr_on_page(
            file_id=file_id,
            page=page,
            ocr_engine=ocr_engine,
            low_confidence_threshold=low_confidence_threshold,
        )
        for page in pages
    ]


def build_pdf_text_ocr_result(
    file_id: str,
    page: NormalizedPage,
    extracted_page: dict,
) -> OCRPageResult:
    """Build an OCR-compatible result from a PDF text layer.

    PyMuPDF coordinates are PDF points. They are scaled onto the already
    rendered page image so downstream bbox/reading-order logic stays unchanged.
    """
    pdf_width = max(float(extracted_page.get("page_width", 0.0) or 0.0), 1.0)
    pdf_height = max(float(extracted_page.get("page_height", 0.0) or 0.0), 1.0)
    scale_x = page.processed_width / pdf_width
    scale_y = page.processed_height / pdf_height
    blocks: List[OCRBlock] = []

    for index, item in enumerate(extracted_page.get("blocks", []), start=1):
        text = str(item.get("text", "") or "").strip()
        bbox = item.get("bbox") or [0.0, 0.0, 0.0, 0.0]
        if not text or len(bbox) != 4:
            continue
        scaled_bbox = [
            max(0.0, min(float(bbox[0]) * scale_x, page.processed_width)),
            max(0.0, min(float(bbox[1]) * scale_y, page.processed_height)),
            max(0.0, min(float(bbox[2]) * scale_x, page.processed_width)),
            max(0.0, min(float(bbox[3]) * scale_y, page.processed_height)),
        ]
        blocks.append(
            OCRBlock(
                block_id=generate_block_id(file_id, page.page_no, index),
                bbox=scaled_bbox,
                bbox_source=BBOX_SOURCE_RENDERED,
                source_mode=SOURCE_MODE_TEXT_EXTRACT,
                text=text,
                confidence=1.0,
                line_index=index,
                reading_order=index,
                is_low_confidence=False,
                block_type=BLOCK_TYPE_TEXT,
            )
        )

    return OCRPageResult(
        file_id=file_id,
        page_no=page.page_no,
        image_path=page.effective_image_path,
        width=page.processed_width,
        height=page.processed_height,
        dpi=page.dpi,
        coordinate_base=page.coordinate_base,
        ocr_engine="pdf_text_layer",
        overall_confidence=1.0 if blocks else None,
        blocks=blocks,
    )


def _estimated_bbox(reading_order: int, page_width: int) -> List[float]:
    """为 DOCX 文本/图片标记生成估算 bbox。

    这些 bbox 只用于让 B 保持顺序和调试，不表示真实页面坐标。
    """
    x_min = 60
    x_max = max(120, page_width - 60)
    y_min = 80 + (reading_order - 1) * 48
    y_max = y_min + 36
    return [x_min, y_min, x_max, y_max]


def _make_text_block(
    file_id: str,
    page: NormalizedPage,
    index: int,
    text: str,
) -> OCRBlock:
    return OCRBlock(
        block_id=generate_block_id(file_id, page.page_no, index),
        bbox=_estimated_bbox(index, page.processed_width),
        bbox_source=BBOX_SOURCE_ESTIMATED,
        source_mode=SOURCE_MODE_TEXT_EXTRACT,
        text=text or "",
        confidence=1.0,
        line_index=index,
        reading_order=index,
        is_low_confidence=False,
        block_type=BLOCK_TYPE_TEXT,
    )


def _make_image_marker_block(
    file_id: str,
    page: NormalizedPage,
    index: int,
    image_id: str,
    image_path: str,
) -> OCRBlock:
    return OCRBlock(
        block_id=generate_block_id(file_id, page.page_no, index),
        bbox=_estimated_bbox(index, page.processed_width),
        bbox_source=BBOX_SOURCE_ESTIMATED,
        source_mode=SOURCE_MODE_IMAGE_MARKER,
        text=f"[IMAGE:{image_id}]",
        confidence=1.0,
        line_index=index,
        reading_order=index,
        is_low_confidence=False,
        block_type=BLOCK_TYPE_IMAGE_MARKER,
        image_id=image_id,
        image_path=image_path or None,
    )


def _ocr_inline_image_blocks(
    file_id: str,
    page: NormalizedPage,
    image_id: str,
    image_path: str,
    parent_block_id: str,
    start_index: int,
    ocr_engine: str,
    low_confidence_threshold: float,
) -> List[OCRBlock]:
    """对 DOCX 内嵌图片 OCR，并把结果转为 image_ocr blocks。"""
    if not image_path:
        return []

    raw_result = run_paddle_ocr(image_path)
    image_width, image_height = get_image_size(image_path)

    # 复用标准 normalizer，先得到图片内部 OCR 结果。
    image_page = NormalizedPage(
        file_id=file_id,
        page_no=page.page_no,
        page_image_path=image_path,
        preprocessed_image_path=None,
        original_width=image_width,
        original_height=image_height,
        processed_width=image_width,
        processed_height=image_height,
        dpi=None,
        coordinate_base=page.coordinate_base,
    )
    image_result = normalize_paddle_result(
        file_id=file_id,
        page=image_page,
        raw_result=raw_result,
        ocr_engine=ocr_engine,
        low_confidence_threshold=low_confidence_threshold,
    )

    blocks: List[OCRBlock] = []
    for offset, block in enumerate(image_result.blocks):
        new_index = start_index + offset
        blocks.append(
            OCRBlock(
                block_id=generate_block_id(file_id, page.page_no, new_index),
                bbox=block.bbox,
                bbox_source=BBOX_SOURCE_OCR,
                source_mode=SOURCE_MODE_OCR,
                text=block.text,
                confidence=block.confidence,
                line_index=new_index,
                reading_order=new_index,
                is_low_confidence=block.is_low_confidence,
                block_type=BLOCK_TYPE_IMAGE_OCR,
                image_id=image_id,
                image_path=image_path,
                parent_block_id=parent_block_id,
            )
        )
    return blocks


def build_docx_mixed_ocr_result(
    file_id: str,
    page: NormalizedPage,
    docx_elements: List[dict],
    ocr_engine: str = config.DEFAULT_OCR_ENGINE,
    low_confidence_threshold: float = config.LOW_CONFIDENCE_THRESHOLD,
) -> OCRPageResult:
    """将 DOCX 文本+内嵌图片转为统一 OCRPageResult。"""
    blocks: List[OCRBlock] = []
    next_index = 1

    for element in docx_elements:
        element_type = element.get("type")

        if element_type == "text":
            text = str(element.get("text", "")).strip()
            if not text:
                continue
            blocks.append(_make_text_block(file_id, page, next_index, text))
            next_index += 1
            continue

        if element_type == "image":
            image_id = element.get("image_id") or f"img_{next_index:03d}"
            image_path = element.get("image_path") or ""
            marker = _make_image_marker_block(file_id, page, next_index, image_id, image_path)
            blocks.append(marker)
            next_index += 1

            # 图片提取成功才 OCR；失败时保留 marker，B 仍知道原位置有图片。
            if image_path:
                try:
                    image_blocks = _ocr_inline_image_blocks(
                        file_id=file_id,
                        page=page,
                        image_id=image_id,
                        image_path=image_path,
                        parent_block_id=marker.block_id,
                        start_index=next_index,
                        ocr_engine=ocr_engine,
                        low_confidence_threshold=low_confidence_threshold,
                    )
                    blocks.extend(image_blocks)
                    next_index += len(image_blocks)
                except Exception as exc:
                    # 不让一张内嵌图片 OCR 失败导致整个 DOCX 文本结果失败。
                    # B 仍可以看到图片原位置和失败信息。
                    blocks.append(
                        OCRBlock(
                            block_id=generate_block_id(file_id, page.page_no, next_index),
                            bbox=_estimated_bbox(next_index, page.processed_width),
                            bbox_source=BBOX_SOURCE_ESTIMATED,
                            source_mode=SOURCE_MODE_IMAGE_MARKER,
                            text=f"[IMAGE_OCR_FAILED:{image_id}] {exc}",
                            confidence=0.0,
                            line_index=next_index,
                            reading_order=next_index,
                            is_low_confidence=True,
                            block_type=BLOCK_TYPE_IMAGE_MARKER,
                            image_id=image_id,
                            image_path=image_path,
                            parent_block_id=marker.block_id,
                        )
                    )
                    next_index += 1

    overall_confidence = None
    if blocks:
        overall_confidence = round(sum(block.confidence for block in blocks) / len(blocks), 4)

    return OCRPageResult(
        file_id=file_id,
        page_no=page.page_no,
        image_path=page.effective_image_path,
        width=page.processed_width,
        height=page.processed_height,
        dpi=page.dpi,
        coordinate_base=page.coordinate_base,
        ocr_engine="docx_mixed_wrapper+paddleocr",
        overall_confidence=overall_confidence,
        blocks=blocks,
    )
