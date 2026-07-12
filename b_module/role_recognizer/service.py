from __future__ import annotations

import re
from typing import Any, Optional

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

TYPE_HEADING_WORDS = [
    "思考题",
    "问答题",
    "简答题",
    "论述题",
    "分析题",
    "综合题",
    "附加题",
    "拓展题",
    "讨论题",
    "实验题",
    "材料题",
    "最后一题",
]

TYPE_HEADING_PATTERN = re.compile(
    r"^\s*(?P<label>"
    + "|".join(re.escape(word) for word in TYPE_HEADING_WORDS)
    + r")\s*"
    + r"(?P<paren>[（(][^）)]*[）)])?\s*"
    + r"(?:(?P<colon>[:：])\s*(?P<after>.*))?\s*$"
)

SECTION_HEADING_PATTERN = re.compile(
    r"^\s*(?P<section>[一二三四五六七八九十百零两]{1,6}|\d{1,3})\s*[、.．]\s*"
    r"(?P<label>"
    + "|".join(re.escape(word) for word in TYPE_HEADING_WORDS)
    + r")\s*(?:[（(][^）)]*[）)])?\s*(?:[:：].*)?$"
)

STUDENT_INFO_PATTERNS = [
    re.compile(r"姓名\s*[:：]"),
    re.compile(r"学号\s*[:：]"),
    re.compile(r"班级\s*[:：]"),
    re.compile(r"专业\s*[:：]"),
    re.compile(r"学院\s*[:：]"),
    re.compile(r"^\s*(?:姓名|学号|班级|专业|学院|分数|成绩)\s*$"),
]

HEADER_FOOTER_PATTERNS = [
    re.compile(r"^\s*第\s*\d+\s*页\s*$"),
    re.compile(r"^\s*第?\s*[一二三四五六七八九十百零两\d]+\s*页\s*[:：].*$"),
    re.compile(r"^\s*[一二三四五六七八九十百零两]+\s*页\s*[:：].*$"),
    re.compile(r"^\s*page\s*\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*page\s*\d+\s*[:：].*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
    re.compile(r"^.*(?:QQ|微信|公众号|搜集整理|资料自用|版权所有|禁止转载|仅供学习).*$", re.IGNORECASE),
]

NOISE_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"^\s*图片结束[。\.、]?\s*$"),
    re.compile(r"^\s*图像结束[。\.、]?\s*$"),
    re.compile(r"^\s*本页用于测试.*$"),
    re.compile(r"^\s*ocrpageresult.*$", re.IGNORECASE),
    re.compile(r"^\s*reading_order\s*[:：]?.*$", re.IGNORECASE),
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

SKIP_SEGMENTATION_ROLES = {"header_footer", "student_info", "noise", "section_heading"}


def classify_block_role(block: dict[str, Any], page_height: int = 0, page_width: int = 0) -> dict[str, Any]:
    """Classify one OCR block into a semantic role for B-module segmentation.

    This layer does not replace the existing heading/answer compatible roles.
    It adds a more explicit semantic_role so later stages can safely ignore
    student info, page headers/footers, and pure noise before question splitting.
    """
    text = _normalize_text(block.get("text", ""))
    block_type = str(block.get("block_type", "text") or "text")
    bbox = _safe_bbox(block)
    top_ratio = _bbox_top(bbox) / max(page_height, 1)
    bottom_ratio = _bbox_bottom(bbox) / max(page_height, 1)
    question_no = _extract_question_no(text)

    if block_type == "image_marker" or re.match(r"^\s*\[IMAGE:[^\]]+\]\s*$", text, re.IGNORECASE):
        return _role("image_marker", 0.98, "docx_image_marker", question_no=None)

    if block_type == "image_ocr":
        if question_no is not None:
            return _role("question_heading", 0.84, "image_ocr_question_heading", question_no=question_no)
        return _role("image_ocr", 0.86, "ocr_text_from_docx_image", question_no=None)

    if not text:
        return _role("noise", 0.96, "empty_text", question_no=None)

    section_heading = _extract_section_heading_info(text)
    if section_heading is not None:
        section_no, section_label = section_heading
        return _role(
            "section_heading",
            0.98,
            "explicit_numbered_type_section",
            question_no=None,
            section_no=section_no,
            section_label=section_label,
        )

    if question_no is not None:
        confidence = 0.95
        if block.get("is_low_confidence"):
            confidence -= 0.18
        return _role("question_heading", max(0.1, round(confidence, 2)), "regex_question_number", question_no=question_no)

    if _looks_like_student_info(text, top_ratio):
        return _role("student_info", 0.88, "student_info_pattern", question_no=None)

    if _looks_like_header_footer(text, top_ratio, bottom_ratio):
        return _role("header_footer", 0.86, "header_footer_pattern", question_no=None)

    if _looks_like_noise(text):
        return _role("noise", 0.85, "noise_pattern", question_no=None)

    type_heading = _extract_type_heading_info(text)
    if type_heading is not None:
        label, has_inline_content = type_heading
        if has_inline_content:
            return _role("question_heading", 0.88, "type_heading_with_inline_content", question_no=label)
        return _role("type_heading_candidate", 0.72, "type_heading_candidate_needs_context", question_no=label)

    if _looks_like_uncertain_heading(text, block, page_height):
        return _role("uncertain_heading", 0.42, "uncertain_heading_pattern", question_no=None)

    return _role("answer_body", 0.82, "default_answer_body", question_no=None)


def classify_paragraph_role(paragraph: dict[str, Any]) -> dict[str, Any]:
    """Classify a built paragraph from its block-level semantic roles."""
    roles = [str(role) for role in paragraph.get("block_roles", []) if role]
    if not roles:
        return _role("answer_body", 0.55, "missing_block_roles", question_no=paragraph.get("heading_question_no"))

    role_set = set(roles)
    if role_set == {"noise"}:
        return _role("noise", 0.92, "all_blocks_noise", question_no=None)
    if role_set == {"header_footer"}:
        return _role("header_footer", 0.9, "all_blocks_header_footer", question_no=None)
    if role_set == {"student_info"}:
        return _role("student_info", 0.9, "all_blocks_student_info", question_no=None)
    if role_set == {"image_marker"}:
        return _role("image_marker", 0.95, "all_blocks_image_marker", question_no=None)
    if role_set == {"image_ocr"}:
        return _role("image_ocr", 0.86, "all_blocks_image_ocr", question_no=None)
    if role_set == {"section_heading"}:
        return _role(
            "section_heading",
            0.98,
            "paragraph_explicit_section_heading",
            question_no=None,
            section_no=paragraph.get("section_no"),
            section_label=paragraph.get("section_label"),
        )
    if role_set == {"type_heading_candidate"}:
        return _role(
            "type_heading_candidate",
            0.72,
            "paragraph_type_heading_candidate",
            question_no=paragraph.get("heading_question_no"),
        )
    if "question_heading" in role_set and len(role_set) == 1:
        return _role("question_heading", 0.94, "paragraph_question_heading", question_no=paragraph.get("heading_question_no"))
    if "question_heading" in role_set:
        return _role("heading_answer_pair", 0.78, "heading_and_body_in_same_paragraph", question_no=paragraph.get("heading_question_no"))
    if "uncertain_heading" in role_set:
        return _role("uncertain_heading", 0.42, "paragraph_uncertain_heading", question_no=None)
    if role_set.intersection({"answer_body", "image_ocr", "image_marker"}):
        return _role("answer_body", 0.78, "paragraph_answer_body", question_no=None)
    return _role("mixed", 0.55, "mixed_roles", question_no=paragraph.get("heading_question_no"))


def should_skip_for_segmentation(paragraph: dict[str, Any]) -> bool:
    """Return whether this paragraph should be excluded from question splitting."""
    semantic_role = str(paragraph.get("semantic_role", "") or "")
    return semantic_role in SKIP_SEGMENTATION_ROLES


def _role(
    semantic_role: str,
    confidence: float,
    reason: str,
    question_no: Any = None,
    section_no: Any = None,
    section_label: Any = None,
) -> dict[str, Any]:
    result = {
        "semantic_role": semantic_role,
        "role_confidence": round(float(confidence), 2),
        "role_reason": reason,
        "question_no": question_no,
    }
    if section_no is not None:
        result["section_no"] = str(section_no)
    if section_label is not None:
        result["section_label"] = str(section_label)
    return result


def _normalize_text(text: Any) -> str:
    return str(text or "").replace("\n", " ").strip()


def _extract_question_no(text: str) -> Optional[str]:
    for pattern in QUESTION_PATTERNS:
        match = pattern.match(text or "")
        if not match:
            continue
        raw = match.group(1)
        if raw.isdigit():
            return str(int(raw))
        parsed = _parse_chinese_number(raw)
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


def _extract_type_heading_info(text: str) -> Optional[tuple[str, bool]]:
    """Return (label, has_inline_content) for common non-numeric type headings.

    Examples:
    - 思考题：请说明... -> ("思考题", True)
    - 思考题：        -> ("思考题", False)
    - 思考题（共三大题，每题15分） -> ("思考题", False)

    This is only a candidate signal.  Single-line headings without inline
    content are resolved later in the question segmenter by looking at the
    next effective paragraph.
    """
    match = TYPE_HEADING_PATTERN.match(text or "")
    if not match:
        return None
    label = match.group("label")
    after = match.group("after")
    has_inline_content = after is not None and bool(after.strip())
    return label, has_inline_content


def _extract_section_heading_info(text: str) -> Optional[tuple[str, str]]:
    match = SECTION_HEADING_PATTERN.match(text or "")
    if not match:
        return None
    raw_section = match.group("section")
    if raw_section.isdigit():
        section_no = str(int(raw_section))
    else:
        parsed = _parse_chinese_number(raw_section)
        section_no = str(parsed) if parsed is not None else raw_section
    return section_no, match.group("label")


def _looks_like_student_info(text: str, top_ratio: float) -> bool:
    if top_ratio > 0.28:
        return False
    if len(text) > 80:
        return False
    return any(pattern.search(text) for pattern in STUDENT_INFO_PATTERNS)


def _looks_like_header_footer(text: str, top_ratio: float, bottom_ratio: float) -> bool:
    if len(text) > 60:
        return False
    if top_ratio > 0.18 and bottom_ratio < 0.82:
        return False
    return any(pattern.match(text) for pattern in HEADER_FOOTER_PATTERNS)


def _looks_like_noise(text: str) -> bool:
    return any(pattern.match(text) for pattern in NOISE_PATTERNS)


def _looks_like_uncertain_heading(text: str, block: dict[str, Any], page_height: int) -> bool:
    if not text:
        return False
    bbox = _safe_bbox(block)
    top_ratio = _bbox_top(bbox) / max(page_height, 1)
    short_line = len(text) <= 18
    low_conf = float(block.get("confidence", 1.0) or 1.0) < 0.7 or bool(block.get("is_low_confidence"))
    if short_line and low_conf and top_ratio <= 0.3:
        return True
    return any(pattern.match(text) for pattern in UNCERTAIN_HEADING_PATTERNS)


def _safe_bbox(block: dict[str, Any]) -> list[float]:
    bbox = block.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4:
        return [0.0, 0.0, 0.0, 0.0]
    return [float(value) for value in bbox]


def _bbox_top(bbox: list[float]) -> float:
    return float(bbox[1])


def _bbox_bottom(bbox: list[float]) -> float:
    return float(bbox[3])
