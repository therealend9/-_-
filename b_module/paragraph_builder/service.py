from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable, Optional, Tuple

from b_module.schemas.types import OCRPageResult
from b_module.role_recognizer.service import classify_block_role, classify_paragraph_role
from b_module.text_utils import join_text_parts, normalize_inline_text

QUESTION_PATTERNS = [
    re.compile(r"^\s*(\d{1,3})\s*[\.、．]\s*"),
    re.compile(r"^\s*[\(（](\d{1,3})[\)）]\s*"),
    re.compile(r"^\s*第\s*(\d{1,3})\s*题(?:[\s:：、.．]|$)"),
    re.compile(r"^\s*([一二三四五六七八九十百零两]{1,6})\s*[、.．]\s*"),
    re.compile(r"^\s*第\s*([一二三四五六七八九十百零两]{1,6})\s*题(?:[\s:：、.．]|$)"),
]

UNCERTAIN_HEADING_PATTERNS = [
    re.compile(r"^\s*[A-Za-z][\.\)、]\s*"),
    re.compile(r"^\s*[?？][\.\)、]?\s*"),
]

CHINESE_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def build_paragraphs(
    file_id: str,
    page_ocr_results: Iterable[OCRPageResult],
) -> dict[str, Any]:
    """Build paragraph-like units before question segmentation."""
    paragraphs: list[dict[str, Any]] = []
    previous_last_paragraph: Optional[dict[str, Any]] = None

    ordered_pages = sorted(page_ocr_results, key=lambda item: item["page_no"])
    repeated_noise_ids, filtered_noise_blocks = _find_repeated_page_noise(ordered_pages)

    for page in ordered_pages:
        page_height = int(page.get("height", 0) or 0)
        page_width = int(page.get("width", 0) or 0)
        raw_blocks = [
            block
            for block in page["blocks"]
            if str(block.get("block_id", "")) not in repeated_noise_ids
        ]
        if _is_docx_mixed_page(raw_blocks):
            # DOCX mixed 的 reading_order 由 A 模块按“文本 -> 图片标记 -> 图片 OCR -> 后续文本”生成。
            # 不能再按 bbox 重新排序，否则图片内部 OCR 的 y 坐标会跑到 marker/text 前面。
            ordered_blocks = sorted(raw_blocks, key=lambda block: int(block.get("reading_order", 0) or 0))
        else:
            ordered_blocks = sorted(raw_blocks, key=lambda block: _reading_key(block, page_width))
        page_paragraphs: list[dict[str, Any]] = []

        for block_index, block in enumerate(ordered_blocks, start=1):
            block_meta = _classify_block(block, page_height)
            if page_paragraphs and _should_merge_into_paragraph(page_paragraphs[-1], block, block_meta, page_height):
                _append_block_to_paragraph(page_paragraphs[-1], block, block_meta)
                continue

            page_paragraphs.append(
                _create_paragraph(
                    file_id=file_id,
                    page=page,
                    block=block,
                    block_meta=block_meta,
                    block_index=block_index,
                )
            )

        effective_paragraphs = [
            paragraph
            for paragraph in page_paragraphs
            if paragraph.get("semantic_role") not in {"header_footer", "student_info", "noise", "section_heading"}
        ]
        if previous_last_paragraph and effective_paragraphs:
            first_paragraph = effective_paragraphs[0]
            if _is_cross_page_continuation(previous_last_paragraph, first_paragraph):
                first_paragraph["continued_from_previous_page"] = True
                first_paragraph["continuation_confidence"] = 0.83
                first_paragraph["continuation_reason"] = "page_boundary_geometry_match"
            else:
                first_paragraph["continued_from_previous_page"] = False

        if effective_paragraphs:
            previous_last_paragraph = effective_paragraphs[-1]
            previous_last_paragraph["is_page_bottom_paragraph"] = _bbox_bottom(previous_last_paragraph["bbox"]) / max(page_height, 1) >= 0.72

        paragraphs.extend(page_paragraphs)

    return {
        "file_id": file_id,
        "paragraphs": paragraphs,
        "filtered_noise_blocks": filtered_noise_blocks,
    }


def _is_docx_mixed_page(blocks: Iterable[dict[str, Any]]) -> bool:
    source_modes = {str(block.get("source_mode", "") or "") for block in blocks}
    block_types = {str(block.get("block_type", "") or "") for block in blocks}
    return (
        "text_extract" in source_modes
        or "image_marker" in source_modes
        or "image_marker" in block_types
        or "image_ocr" in block_types
    )


def _create_paragraph(
    file_id: str,
    page: OCRPageResult,
    block: dict[str, Any],
    block_meta: dict[str, Any],
    block_index: int,
) -> dict[str, Any]:
    bbox = _safe_bbox(block)
    text = _normalize_text(block["text"])
    return {
        "paragraph_id": f"para_{file_id}_p{int(page['page_no']):03d}_{block_index:03d}",
        "file_id": file_id,
        "page_no": int(page["page_no"]),
        "page_height": int(page.get("height", 0) or 0),
        "page_width": int(page.get("width", 0) or 0),
        "block_ids": [block["block_id"]],
        "texts": [text],
        "text": text,
        "bbox": bbox,
        "start_anchor_bbox": bbox,
        "end_anchor_bbox": bbox,
        "heading_question_no": block_meta["question_no"],
        "heading_confidence": block_meta["heading_confidence"],
        "heading_source": block_meta["heading_source"],
        "section_no": block_meta.get("section_no"),
        "section_label": block_meta.get("section_label"),
        "role": block_meta["role"],
        "semantic_role": block_meta.get("semantic_role", block_meta["role"]),
        "role_confidence": float(block_meta.get("role_confidence", block_meta.get("heading_confidence", 0.0)) or 0.0),
        "role_reason": block_meta.get("role_reason", block_meta.get("heading_source", "none")),
        "block_roles": [block_meta.get("semantic_role", block_meta["role"])],
        "role_reasons": [block_meta.get("role_reason", block_meta.get("heading_source", "none"))],
        "continued_from_previous_page": False,
        "continuation_confidence": 0.0,
        "continuation_reason": "",
        "reading_orders": [int(block["reading_order"])],
        "source_modes": [block.get("source_mode", "ocr")],
        "bbox_sources": [block.get("bbox_source", "ocr")],
        "block_types": [block.get("block_type", "text")],
        "has_estimated_bbox": block.get("bbox_source") == "estimated",
        "has_rendered_bbox": block.get("bbox_source") == "rendered",
        "has_low_confidence_block": bool(block.get("is_low_confidence")),
        "has_image_marker_block": block.get("block_type") == "image_marker",
        "block_count": 1,
        "is_page_top_paragraph": _bbox_top(bbox) / max(int(page.get("height", 0) or 0), 1) <= 0.22,
        "is_page_bottom_paragraph": False,
    }


def _append_block_to_paragraph(paragraph: dict[str, Any], block: dict[str, Any], block_meta: dict[str, Any]) -> None:
    previous_text = str(paragraph.get("text", "") or "")
    previous_semantic_role = str(paragraph.get("semantic_role", "") or "")
    bbox = _safe_bbox(block)
    text = _normalize_text(block["text"])
    paragraph["block_ids"].append(block["block_id"])
    paragraph["texts"].append(text)
    paragraph["text"] = join_text_parts(paragraph["texts"])
    paragraph["bbox"] = _merge_bbox(paragraph["bbox"], bbox)
    paragraph["end_anchor_bbox"] = bbox
    paragraph["reading_orders"].append(int(block["reading_order"]))
    paragraph["source_modes"].append(block.get("source_mode", "ocr"))
    paragraph["bbox_sources"].append(block.get("bbox_source", "ocr"))
    paragraph["block_types"].append(block.get("block_type", "text"))
    paragraph.setdefault("block_roles", []).append(block_meta.get("semantic_role", block_meta["role"]))
    paragraph.setdefault("role_reasons", []).append(block_meta.get("role_reason", block_meta.get("heading_source", "none")))
    paragraph["has_estimated_bbox"] = paragraph.get("has_estimated_bbox", False) or block.get("bbox_source") == "estimated"
    paragraph["has_rendered_bbox"] = paragraph.get("has_rendered_bbox", False) or block.get("bbox_source") == "rendered"
    paragraph["has_low_confidence_block"] = paragraph.get("has_low_confidence_block", False) or bool(block.get("is_low_confidence"))
    paragraph["has_image_marker_block"] = paragraph.get("has_image_marker_block", False) or block.get("block_type") == "image_marker"
    paragraph["block_count"] = len(paragraph["block_ids"])
    paragraph["role"] = _merge_role(paragraph["role"], block_meta["role"])
    paragraph_role = classify_paragraph_role(paragraph)
    paragraph["semantic_role"] = paragraph_role["semantic_role"]
    paragraph["role_confidence"] = paragraph_role["role_confidence"]
    paragraph["role_reason"] = paragraph_role["role_reason"]

    if (
        previous_semantic_role == "question_heading"
        and block_meta.get("semantic_role") == "answer_body"
        and not _ends_with_sentence_boundary(previous_text)
    ):
        paragraph["role"] = "heading_like"
        paragraph["semantic_role"] = "question_heading"
        paragraph["role_confidence"] = max(float(paragraph.get("role_confidence", 0.0) or 0.0), 0.9)
        paragraph["role_reason"] = "wrapped_question_heading_continuation"
        paragraph["wrapped_question_heading"] = True

    if paragraph.get("heading_question_no") is None and block_meta["question_no"] is not None:
        paragraph["heading_question_no"] = block_meta["question_no"]
        paragraph["heading_confidence"] = block_meta["heading_confidence"]
        paragraph["heading_source"] = block_meta["heading_source"]


def _classify_block(block: dict[str, Any], page_height: int) -> dict[str, Any]:
    role_info = classify_block_role(block, page_height=page_height)
    semantic_role = role_info["semantic_role"]
    question_no = role_info.get("question_no")

    if semantic_role == "question_heading":
        return {
            "role": "heading_like",
            "semantic_role": semantic_role,
            "question_no": question_no,
            "heading_confidence": float(role_info.get("role_confidence", 0.95)),
            "heading_source": role_info.get("role_reason", "regex_question_number"),
            "role_confidence": float(role_info.get("role_confidence", 0.95)),
            "role_reason": role_info.get("role_reason", "regex_question_number"),
        }

    if semantic_role == "type_heading_candidate":
        return {
            "role": "type_heading_candidate_like",
            "semantic_role": semantic_role,
            "question_no": question_no,
            "heading_confidence": float(role_info.get("role_confidence", 0.72)),
            "heading_source": role_info.get("role_reason", "type_heading_candidate_needs_context"),
            "role_confidence": float(role_info.get("role_confidence", 0.72)),
            "role_reason": role_info.get("role_reason", "type_heading_candidate_needs_context"),
        }

    if semantic_role == "section_heading":
        return {
            "role": "section_heading",
            "semantic_role": semantic_role,
            "question_no": None,
            "section_no": role_info.get("section_no"),
            "section_label": role_info.get("section_label"),
            "heading_confidence": 0.0,
            "heading_source": role_info.get("role_reason", "explicit_section_heading"),
            "role_confidence": float(role_info.get("role_confidence", 0.98)),
            "role_reason": role_info.get("role_reason", "explicit_section_heading"),
        }

    if semantic_role == "uncertain_heading":
        return {
            "role": "uncertain_heading_like",
            "semantic_role": semantic_role,
            "question_no": None,
            "heading_confidence": 0.42,
            "heading_source": role_info.get("role_reason", "uncertain_heading_pattern"),
            "role_confidence": float(role_info.get("role_confidence", 0.42)),
            "role_reason": role_info.get("role_reason", "uncertain_heading_pattern"),
        }

    if semantic_role in {"header_footer", "student_info", "noise"}:
        return {
            "role": "non_question_noise",
            "semantic_role": semantic_role,
            "question_no": None,
            "heading_confidence": 0.0,
            "heading_source": "none",
            "role_confidence": float(role_info.get("role_confidence", 0.8)),
            "role_reason": role_info.get("role_reason", semantic_role),
        }

    return {
        "role": "answer_like",
        "semantic_role": semantic_role,
        "question_no": None,
        "heading_confidence": 0.0,
        "heading_source": "none",
        "role_confidence": float(role_info.get("role_confidence", 0.75)),
        "role_reason": role_info.get("role_reason", "answer_body"),
    }


def _should_merge_into_paragraph(
    paragraph: dict[str, Any],
    block: dict[str, Any],
    block_meta: dict[str, Any],
    page_height: int,
) -> bool:
    current_bbox = _safe_bbox(block)
    previous_bbox = paragraph["end_anchor_bbox"]
    if paragraph.get("semantic_role") == "section_heading" or block_meta.get("semantic_role") == "section_heading":
        return False
    if block_meta["role"] == "non_question_noise" or paragraph.get("role") == "non_question_noise":
        return False
    if block_meta["role"] in {"heading_like", "uncertain_heading_like", "type_heading_candidate_like"}:
        return False
    if _should_keep_source_mode_boundary(paragraph, block):
        return False

    vertical_gap = max(0.0, _bbox_top(current_bbox) - _bbox_bottom(previous_bbox))
    normalized_gap = vertical_gap / max(page_height, 1)
    left_delta = abs(_bbox_left(current_bbox) - _bbox_left(paragraph["bbox"]))
    width_delta = abs(_bbox_width(current_bbox) - _bbox_width(paragraph["bbox"]))
    left_tolerance = max(36.0, paragraph["page_width"] * 0.08)
    width_tolerance = max(120.0, paragraph["page_width"] * 0.28)

    if paragraph["role"] in {"heading_like", "uncertain_heading_like"}:
        return (
            normalized_gap <= 0.06
            and left_delta <= left_tolerance
            and width_delta <= width_tolerance
        )

    return (
        normalized_gap <= 0.05
        and left_delta <= left_tolerance
        and width_delta <= width_tolerance
    )


def _is_cross_page_continuation(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    if current["role"] in {"heading_like", "uncertain_heading_like", "type_heading_candidate_like", "section_heading", "non_question_noise"}:
        return False
    if current.get("semantic_role") in {"header_footer", "student_info", "noise"}:
        return False

    previous_bottom_ratio = _bbox_bottom(previous["bbox"]) / max(previous["page_height"], 1)
    current_top_ratio = _bbox_top(current["bbox"]) / max(current["page_height"], 1)
    if previous_bottom_ratio < 0.76 or current_top_ratio > 0.18:
        return False

    left_delta = abs(_bbox_left(previous["bbox"]) - _bbox_left(current["bbox"]))
    width_delta = abs(_bbox_width(previous["bbox"]) - _bbox_width(current["bbox"]))
    left_tolerance = max(42.0, previous["page_width"] * 0.10)
    width_tolerance = max(160.0, previous["page_width"] * 0.30)
    return left_delta <= left_tolerance and width_delta <= width_tolerance


def _merge_role(previous_role: str, current_role: str) -> str:
    if previous_role == current_role:
        return previous_role
    if "non_question_noise" in {previous_role, current_role}:
        return "non_question_noise"
    if "heading_like" in {previous_role, current_role}:
        return "heading_answer_pair"
    if "uncertain_heading_like" in {previous_role, current_role}:
        return "uncertain_heading_pair"
    if "type_heading_candidate_like" in {previous_role, current_role}:
        return "type_heading_candidate_pair"
    return "mixed"


def _should_keep_source_mode_boundary(paragraph: dict[str, Any], block: dict[str, Any]) -> bool:
    existing_modes = set(paragraph.get("source_modes", []))
    current_mode = str(block.get("source_mode", "ocr"))

    # Pure text-extract DOCX lines keep line boundaries so heading and answer are not
    # prematurely fused into a single paragraph.
    if existing_modes == {"text_extract"} and current_mode == "text_extract":
        return True

    # When OCR output and estimated/text-extract output meet, keep them split to avoid
    # contaminating a stable OCR paragraph with weaker estimated geometry.
    if current_mode not in existing_modes and (
        "text_extract" in existing_modes
        or current_mode == "text_extract"
        or "image_marker" in existing_modes
        or current_mode == "image_marker"
    ):
        return True

    return False


def _reading_key(block: dict[str, Any], page_width: int) -> Tuple[float, float, int]:
    bbox = _safe_bbox(block)
    row_bucket = round(_bbox_top(bbox) / 24.0)
    return (
        row_bucket,
        round(_bbox_left(bbox) / max(page_width / 30.0, 1.0), 2),
        int(block.get("reading_order", 0)),
    )


def _normalize_text(text: str) -> str:
    return normalize_inline_text(text)


def _ends_with_sentence_boundary(text: str) -> bool:
    return bool(re.search(r"[。！？?!；;：:]\s*$", text or ""))


def _find_repeated_page_noise(
    pages: list[OCRPageResult],
) -> tuple[set[str], list[dict[str, Any]]]:
    """Find repeated headers, footers and stable-position watermark blocks."""
    occurrences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    filtered_ids: set[str] = set()
    notes: list[dict[str, Any]] = []
    ad_pattern = re.compile(
        r"(?:QQ|微信|公众号|搜集整理|资料自用|版权所有|禁止转载|仅供学习)",
        re.IGNORECASE,
    )

    for page in pages:
        page_no = int(page.get("page_no", 0) or 0)
        page_width = max(float(page.get("width", 0) or 0), 1.0)
        page_height = max(float(page.get("height", 0) or 0), 1.0)
        for block in page.get("blocks", []):
            text = _normalize_text(block.get("text", ""))
            block_id = str(block.get("block_id", "") or "")
            if not text or not block_id:
                continue
            bbox = _safe_bbox(block)
            top_ratio = _bbox_top(bbox) / page_height
            bottom_ratio = _bbox_bottom(bbox) / page_height
            left_ratio = _bbox_left(bbox) / page_width
            signature = re.sub(r"\d+", "#", text.lower())
            signature = re.sub(r"[^\w\u4e00-\u9fff#]+", "", signature)
            if len(signature) >= 4:
                occurrences[signature].append(
                    {
                        "block_id": block_id,
                        "page_no": page_no,
                        "text": text,
                        "top_ratio": top_ratio,
                        "bottom_ratio": bottom_ratio,
                        "left_ratio": left_ratio,
                    }
                )
            if bottom_ratio >= 0.9 and ad_pattern.search(text):
                filtered_ids.add(block_id)
                notes.append({"block_id": block_id, "page_no": page_no, "text": text, "reason": "margin_advertisement"})

    for items in occurrences.values():
        if len({item["page_no"] for item in items}) < 2:
            continue
        all_in_margin = all(item["top_ratio"] <= 0.12 or item["bottom_ratio"] >= 0.88 for item in items)
        stable_position = (
            max(item["top_ratio"] for item in items) - min(item["top_ratio"] for item in items) <= 0.08
            and max(item["left_ratio"] for item in items) - min(item["left_ratio"] for item in items) <= 0.1
            and len(items[0]["text"]) >= 8
        )
        if not (all_in_margin or stable_position):
            continue
        reason = "repeated_margin_text" if all_in_margin else "repeated_watermark_text"
        for item in items:
            if item["block_id"] in filtered_ids:
                continue
            filtered_ids.add(item["block_id"])
            notes.append(
                {
                    "block_id": item["block_id"],
                    "page_no": item["page_no"],
                    "text": item["text"],
                    "reason": reason,
                }
            )

    return filtered_ids, notes


def _extract_question_no(text: str) -> Optional[str]:
    for pattern in QUESTION_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        question_no = match.group(1)
        if question_no.isdigit():
            return str(int(question_no))
        parsed = _parse_chinese_number(question_no)
        if parsed is not None:
            return str(parsed)
    return None


def _parse_chinese_number(text: str) -> Optional[int]:
    if not text:
        return None
    if text == "十":
        return 10
    if "百" in text:
        parts = text.split("百", 1)
        high = CHINESE_DIGITS.get(parts[0], 1 if parts[0] == "" else None)
        if high is None:
            return None
        tail = _parse_chinese_number(parts[1]) or 0
        return high * 100 + tail
    if "十" in text:
        parts = text.split("十", 1)
        tens = CHINESE_DIGITS.get(parts[0], 1 if parts[0] == "" else None)
        if tens is None:
            return None
        ones = CHINESE_DIGITS.get(parts[1], 0) if parts[1] else 0
        return tens * 10 + ones
    total = 0
    for char in text:
        value = CHINESE_DIGITS.get(char)
        if value is None:
            return None
        total = total * 10 + value
    return total


def _looks_like_uncertain_heading(text: str, block: dict[str, Any], page_height: int) -> bool:
    if not text:
        return False
    bbox = _safe_bbox(block)
    top_ratio = _bbox_top(bbox) / max(page_height, 1)
    short_line = len(text) <= 18
    low_conf = float(block.get("confidence", 1.0)) < 0.7 or bool(block.get("is_low_confidence"))
    if short_line and low_conf and top_ratio <= 0.3:
        return True
    return any(pattern.match(text) for pattern in UNCERTAIN_HEADING_PATTERNS)


def _safe_bbox(block: dict[str, Any]) -> list[float]:
    bbox = block.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4:
        return [0.0, 0.0, 0.0, 0.0]
    return [float(value) for value in bbox]


def _merge_bbox(left: list[float], right: list[float]) -> list[float]:
    return [
        min(left[0], right[0]),
        min(left[1], right[1]),
        max(left[2], right[2]),
        max(left[3], right[3]),
    ]


def _bbox_left(bbox: list[float]) -> float:
    return float(bbox[0])


def _bbox_top(bbox: list[float]) -> float:
    return float(bbox[1])


def _bbox_bottom(bbox: list[float]) -> float:
    return float(bbox[3])


def _bbox_width(bbox: list[float]) -> float:
    return max(0.0, float(bbox[2]) - float(bbox[0]))
