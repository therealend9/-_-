from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Iterable, Optional

from b_module.paragraph_builder.service import build_paragraphs
from b_module.role_recognizer.service import should_skip_for_segmentation
from b_module.schemas.types import OCRPageResult, QuestionCandidate
from b_module.text_utils import join_context_parts, join_text_parts, normalize_inline_text

from .review_rules import evaluate_candidate_review_flags


QUESTION_PATTERNS = [
    re.compile(r"^\s*(\d{1,3})\s*[\.、．]\s*"),
    re.compile(r"^\s*[\(（](\d{1,3})[\)）]\s*"),
]

TRAILING_NOISE_PATTERNS = [
    re.compile(r"^\s*\[IMAGE:[^\]]+\]\s*$", re.IGNORECASE),
    re.compile(r"^\s*\[IMAGE_OCR_FAILED:[^\]]+\].*$", re.IGNORECASE),
    re.compile(r"^\s*图片结束[。\.、]?\s*$"),
    re.compile(r"^\s*图像结束[。\.、]?\s*$"),
    re.compile(r"^\s*本页用于测试.*$"),
    re.compile(r"^\s*下图为.*$"),
    re.compile(r"^\s*下面是.*图片.*$"),
]


def split_free_layout_questions_v3(
    file_id: str,
    page_ocr_results: Iterable[OCRPageResult],
) -> dict[str, Any]:
    """Split free-layout OCR into question candidates via a paragraph layer."""
    normalized_pages = list(page_ocr_results)
    filtered_pages, duplicate_page_notes = _filter_duplicate_pages(normalized_pages)
    paragraph_result = build_paragraphs(file_id=file_id, page_ocr_results=filtered_pages)
    paragraphs = paragraph_result["paragraphs"]
    _resolve_type_heading_candidates(paragraphs)

    question_candidates: list[QuestionCandidate] = []
    sections: list[dict[str, Any]] = []
    seen_question_nos: dict[str, int] = {}
    current_state: Optional[dict[str, Any]] = None
    carry_over_question_no: Optional[str] = None
    last_confirmed_question_no: Optional[str] = None
    current_section_no: Optional[str] = None
    current_section_label: Optional[str] = None
    current_section_context_parts: list[str] = []
    current_section_context_block_ids: list[str] = []
    current_section_record: Optional[dict[str, Any]] = None
    section_sequence = 0

    for paragraph in paragraphs:
        heading_question_no = paragraph.get("heading_question_no")
        heading_confidence = float(paragraph.get("heading_confidence", 0.0) or 0.0)
        role = paragraph.get("role", "answer_like")
        semantic_role = str(paragraph.get("semantic_role", "") or "")

        if semantic_role == "section_heading":
            if current_state is not None:
                _finish_candidate(file_id, question_candidates, current_state, seen_question_nos)
                current_state = None
            section_sequence += 1
            current_section_no = str(paragraph.get("section_no") or section_sequence)
            current_section_label = str(paragraph.get("section_label") or _type_heading_label(paragraph))
            current_section_context_parts = []
            current_section_context_block_ids = []
            seen_question_nos = {}
            carry_over_question_no = None
            last_confirmed_question_no = None
            current_section_record = {
                "section_no": current_section_no,
                "section_label": current_section_label,
                "heading_text": _normalize_text(paragraph.get("text", "")),
                "heading_paragraph_id": paragraph.get("paragraph_id"),
                "page_no": paragraph.get("page_no"),
                "context_text": "",
                "context_paragraph_ids": [],
                "context_block_ids": [],
                "context_page_nos": [],
            }
            sections.append(current_section_record)
            continue

        if should_skip_for_segmentation(paragraph):
            continue

        if current_state is not None and paragraph["page_no"] != current_state["page_no"] and heading_question_no is None:
            # Preserve page-level candidates here. The dedicated cross-page
            # merger decides whether two adjacent parts are one question.
            _finish_candidate(file_id, question_candidates, current_state, seen_question_nos)
            current_state = None

        if heading_question_no and heading_confidence >= 0.65:
            if current_state is not None:
                _finish_candidate(file_id, question_candidates, current_state, seen_question_nos)

            current_state = _start_candidate_state(
                file_id=file_id,
                paragraph=paragraph,
                question_no=heading_question_no,
                initial_flags=_heading_flags(heading_confidence, paragraph),
                section_no=current_section_no,
                section_label=current_section_label,
                section_context=join_context_parts(current_section_context_parts),
                section_context_block_ids=current_section_context_block_ids,
            )
            if seen_question_nos.get(heading_question_no, 0) > 0:
                current_state["issue_flags"].append("repeated_question_no")
            carry_over_question_no = heading_question_no
            last_confirmed_question_no = heading_question_no
            continue

        if _should_infer_question_from_uncertain_heading(paragraph, last_confirmed_question_no):
            if current_state is not None:
                _finish_candidate(file_id, question_candidates, current_state, seen_question_nos)

            inferred_question_no = _infer_next_question_no(last_confirmed_question_no)
            current_state = _start_candidate_state(
                file_id=file_id,
                paragraph=paragraph,
                question_no=inferred_question_no,
                initial_flags=["ocr_heading_error_inferred", "low_heading_confidence", "needs_semantic_boundary_review"],
                heading_confidence=0.42,
                heading_source="uncertain_ocr_heading",
                section_no=current_section_no,
                section_label=current_section_label,
                section_context=join_context_parts(current_section_context_parts),
                section_context_block_ids=current_section_context_block_ids,
            )
            carry_over_question_no = inferred_question_no
            last_confirmed_question_no = inferred_question_no
            continue

        if current_state is None:
            if (
                carry_over_question_no is not None
                and paragraph.get("is_page_top_paragraph")
                and role == "answer_like"
            ):
                current_state = _start_candidate_state(
                    file_id=file_id,
                    paragraph=paragraph,
                    question_no=carry_over_question_no,
                    initial_flags=["continuation_without_heading"],
                    heading_confidence=0.0,
                    heading_source="carry_over",
                    section_no=current_section_no,
                    section_label=current_section_label,
                    section_context=join_context_parts(current_section_context_parts),
                    section_context_block_ids=current_section_context_block_ids,
                )
                if not paragraph.get("continued_from_previous_page"):
                    current_state["issue_flags"].append("weak_page_boundary_signal")
                continue
            if current_section_record is not None and _is_section_context_paragraph(paragraph):
                context_text = _normalize_text(paragraph.get("text", ""))
                if context_text:
                    current_section_context_parts.append(context_text)
                current_section_context_block_ids.extend(paragraph.get("block_ids", []))
                current_section_record["context_text"] = join_context_parts(current_section_context_parts)
                current_section_record["context_paragraph_ids"].append(paragraph.get("paragraph_id"))
                current_section_record["context_block_ids"] = list(current_section_context_block_ids)
                page_no = int(paragraph.get("page_no", 0) or 0)
                if page_no and page_no not in current_section_record["context_page_nos"]:
                    current_section_record["context_page_nos"].append(page_no)
            continue

        if _is_trailing_noise_paragraph(paragraph, current_state):
            current_state["issue_flags"].append("suppressed_trailing_noise")
            continue

        _extend_candidate_state(current_state, paragraph)

    if current_state is not None:
        _finish_candidate(file_id, question_candidates, current_state, seen_question_nos)

    _mark_sequence_anomalies(question_candidates)

    return {
        "file_id": file_id,
        "route_type": "free_layout_homework",
        "paragraph_result": paragraph_result,
        "section_result": {"file_id": file_id, "sections": sections},
        "question_candidates": question_candidates,
        "duplicate_page_notes": duplicate_page_notes,
    }


def _resolve_type_heading_candidates(paragraphs: list[dict[str, Any]]) -> None:
    """Resolve common non-numeric type headings with one-step context.

    A paragraph such as "思考题：" is ambiguous by itself:
    - followed by numbered headings -> section_heading
    - followed by normal text / image content -> question_heading
    - followed by nothing useful -> uncertain_heading

    This keeps the rule simple for answer extraction while avoiding the common
    mistake of turning "思考题" / "简答题" section names into standalone questions.
    """
    for index, paragraph in enumerate(paragraphs):
        if paragraph.get("semantic_role") != "type_heading_candidate":
            continue

        next_paragraph = _find_next_effective_paragraph(paragraphs, index + 1)
        if next_paragraph is None:
            _mark_type_heading_as_uncertain(paragraph, "type_heading_without_following_content")
            continue

        if _is_numbered_question_paragraph(next_paragraph):
            _mark_type_heading_as_section(paragraph, "followed_by_numbered_question")
            continue

        if _is_body_or_image_paragraph(next_paragraph):
            _mark_type_heading_as_question(paragraph, "followed_by_body_or_image_content")
            continue

        _mark_type_heading_as_uncertain(paragraph, "ambiguous_following_context")


def _find_next_effective_paragraph(
    paragraphs: list[dict[str, Any]],
    start_index: int,
) -> Optional[dict[str, Any]]:
    for paragraph in paragraphs[start_index:]:
        semantic_role = str(paragraph.get("semantic_role", "") or "")
        if semantic_role in {"header_footer", "student_info", "noise", "section_heading"}:
            continue
        text = _normalize_text(paragraph.get("text", ""))
        if not text and semantic_role not in {"image_marker", "image_ocr"}:
            continue
        return paragraph
    return None


def _is_numbered_question_paragraph(paragraph: dict[str, Any]) -> bool:
    question_no = paragraph.get("heading_question_no")
    if question_no is None:
        return False
    role = str(paragraph.get("role", "") or "")
    semantic_role = str(paragraph.get("semantic_role", "") or "")
    heading_source = str(paragraph.get("heading_source", "") or "")
    if semantic_role not in {"question_heading", "heading_answer_pair"} and role not in {"heading_like", "heading_answer_pair"}:
        return False
    # Numeric headings include Arabic numbers and Chinese numbers because the
    # upstream recognizer normalizes Chinese question numbers to digit strings.
    return str(question_no).isdigit() or "regex_question_number" in heading_source


def _is_body_or_image_paragraph(paragraph: dict[str, Any]) -> bool:
    semantic_role = str(paragraph.get("semantic_role", "") or "")
    role = str(paragraph.get("role", "") or "")
    if semantic_role in {"answer_body", "image_marker", "image_ocr", "mixed"}:
        return True
    if role in {"answer_like", "mixed"}:
        return True
    block_types = set(str(item) for item in paragraph.get("block_types", []))
    if block_types.intersection({"image_marker", "image_ocr"}):
        return True
    return False


def _mark_type_heading_as_question(paragraph: dict[str, Any], reason: str) -> None:
    label = _type_heading_label(paragraph)
    paragraph["semantic_role"] = "question_heading"
    paragraph["role"] = "heading_like"
    paragraph["heading_question_no"] = label
    paragraph["heading_confidence"] = max(float(paragraph.get("heading_confidence", 0.0) or 0.0), 0.74)
    paragraph["heading_source"] = reason
    paragraph["role_confidence"] = max(float(paragraph.get("role_confidence", 0.0) or 0.0), 0.74)
    paragraph["role_reason"] = reason
    paragraph["resolved_type_heading_role"] = "question_heading"


def _mark_type_heading_as_section(paragraph: dict[str, Any], reason: str) -> None:
    label = _type_heading_label(paragraph)
    paragraph["section_label"] = label
    paragraph["semantic_role"] = "section_heading"
    paragraph["role"] = "section_heading"
    paragraph["heading_question_no"] = None
    paragraph["heading_confidence"] = 0.0
    paragraph["heading_source"] = reason
    paragraph["role_confidence"] = max(float(paragraph.get("role_confidence", 0.0) or 0.0), 0.78)
    paragraph["role_reason"] = reason
    paragraph["resolved_type_heading_role"] = "section_heading"


def _mark_type_heading_as_uncertain(paragraph: dict[str, Any], reason: str) -> None:
    paragraph["semantic_role"] = "uncertain_heading"
    paragraph["role"] = "uncertain_heading_like"
    paragraph["heading_question_no"] = None
    paragraph["heading_confidence"] = 0.42
    paragraph["heading_source"] = reason
    paragraph["role_confidence"] = 0.42
    paragraph["role_reason"] = reason
    paragraph["resolved_type_heading_role"] = "uncertain_heading"


def _type_heading_label(paragraph: dict[str, Any]) -> str:
    label = paragraph.get("heading_question_no")
    if label:
        return str(label)
    text = _normalize_text(paragraph.get("text", ""))
    text = re.sub(r"[：:].*$", "", text)
    text = re.sub(r"[（(].*[）)]", "", text)
    return text.strip() or "非数字题头"


def split_free_layout_questions_v2(
    file_id: str,
    page_ocr_results: Iterable[OCRPageResult],
) -> dict[str, Any]:
    """Compatibility wrapper for the v2 entrypoint."""
    return split_free_layout_questions_v3(file_id=file_id, page_ocr_results=page_ocr_results)


def _start_candidate_state(
    file_id: str,
    paragraph: dict[str, Any],
    question_no: str,
    initial_flags: list[str],
    heading_confidence: Optional[float] = None,
    heading_source: Optional[str] = None,
    section_no: Optional[str] = None,
    section_label: Optional[str] = None,
    section_context: str = "",
    section_context_block_ids: Optional[Iterable[str]] = None,
) -> dict[str, Any]:
    text = _normalize_text(paragraph["text"])
    return {
        "file_id": file_id,
        "question_no": question_no,
        "question_id": _question_id(section_no, question_no),
        "section_no": section_no,
        "section_label": section_label,
        "section_context": section_context,
        "section_context_block_ids": list(section_context_block_ids or []),
        "page_no": int(paragraph["page_no"]),
        "page_height": int(paragraph.get("page_height", 0) or 0),
        "page_width": int(paragraph.get("page_width", 0) or 0),
        "paragraph_ids": [paragraph["paragraph_id"]],
        "paragraph_role": paragraph.get("role", "answer_like"),
        "paragraph_semantic_roles": [paragraph.get("semantic_role", paragraph.get("role", "answer_like"))],
        "paragraph_role_reasons": [paragraph.get("role_reason", "")],
        "block_ids": list(paragraph.get("block_ids", [])),
        "texts": [text] if text else [],
        "source_modes": list(paragraph.get("source_modes", [])),
        "bbox_sources": list(paragraph.get("bbox_sources", [])),
        "block_types": list(paragraph.get("block_types", [])),
        "has_estimated_bbox": bool(paragraph.get("has_estimated_bbox", False)),
        "has_low_confidence_block": bool(paragraph.get("has_low_confidence_block", False)),
        "has_image_marker_block": bool(paragraph.get("has_image_marker_block", False)),
        "start_block_id": paragraph["block_ids"][0],
        "end_block_id": paragraph["block_ids"][-1],
        "start_anchor_bbox": list(paragraph.get("start_anchor_bbox") or paragraph.get("bbox") or [0.0, 0.0, 0.0, 0.0]),
        "end_anchor_bbox": list(paragraph.get("end_anchor_bbox") or paragraph.get("bbox") or [0.0, 0.0, 0.0, 0.0]),
        "issue_flags": list(initial_flags),
        "heading_confidence": heading_confidence if heading_confidence is not None else float(paragraph.get("heading_confidence", 0.0) or 0.0),
        "heading_source": heading_source or str(paragraph.get("heading_source", "regex_numbering")),
    }


def _extend_candidate_state(state: dict[str, Any], paragraph: dict[str, Any]) -> None:
    text = _normalize_text(paragraph["text"])
    if text:
        state["texts"].append(text)
    state["paragraph_ids"].append(paragraph["paragraph_id"])
    state.setdefault("paragraph_semantic_roles", []).append(paragraph.get("semantic_role", paragraph.get("role", "answer_like")))
    state.setdefault("paragraph_role_reasons", []).append(paragraph.get("role_reason", ""))
    state["block_ids"].extend(paragraph.get("block_ids", []))
    state["source_modes"].extend(paragraph.get("source_modes", []))
    state["bbox_sources"].extend(paragraph.get("bbox_sources", []))
    state["block_types"].extend(paragraph.get("block_types", []))
    state["has_estimated_bbox"] = state.get("has_estimated_bbox", False) or bool(paragraph.get("has_estimated_bbox", False))
    state["has_low_confidence_block"] = state.get("has_low_confidence_block", False) or bool(paragraph.get("has_low_confidence_block", False))
    state["has_image_marker_block"] = state.get("has_image_marker_block", False) or bool(paragraph.get("has_image_marker_block", False))
    state["end_block_id"] = paragraph["block_ids"][-1]
    state["end_anchor_bbox"] = list(paragraph.get("end_anchor_bbox") or paragraph.get("bbox") or state["end_anchor_bbox"])
    if paragraph.get("continued_from_previous_page"):
        state["issue_flags"].append("continuation_without_heading")
    if paragraph.get("role") == "uncertain_heading_like":
        state["issue_flags"].append("uncertain_heading_inside_answer")


def _build_candidate(file_id: str, state: dict[str, Any]) -> QuestionCandidate:
    text = join_text_parts(state["texts"])
    deduped_flags = sorted(set(state.get("issue_flags", [])))
    split_confidence = _score_candidate(
        block_count=len(state["block_ids"]),
        issue_flags=deduped_flags,
        heading_confidence=float(state.get("heading_confidence", 0.0) or 0.0),
    )
    final_flags = evaluate_candidate_review_flags(
        issue_flags=deduped_flags,
        split_confidence=split_confidence,
        text=text,
        block_count=len(state["block_ids"]),
        has_estimated_bbox=bool(state.get("has_estimated_bbox", False)),
        has_low_confidence_block=bool(state.get("has_low_confidence_block", False)),
        has_image_marker_block=bool(state.get("has_image_marker_block", False)),
        source_modes=state.get("source_modes", []),
        bbox_sources=state.get("bbox_sources", []),
    )
    return {
        "file_id": file_id,
        "route_type": "free_layout_homework",
        "question_no": state["question_no"],
        "question_id": state.get("question_id", state["question_no"]),
        "section_no": state.get("section_no"),
        "section_label": state.get("section_label"),
        "section_context": state.get("section_context", ""),
        "section_context_block_ids": list(state.get("section_context_block_ids", [])),
        "page_no": state["page_no"],
        "paragraph_ids": state["paragraph_ids"],
        "paragraph_role": state["paragraph_role"],
        "paragraph_semantic_roles": list(state.get("paragraph_semantic_roles", [])),
        "paragraph_role_reasons": list(state.get("paragraph_role_reasons", [])),
        "block_ids": state["block_ids"],
        "text": text,
        "split_confidence": _score_candidate(
            block_count=len(state["block_ids"]),
            issue_flags=final_flags,
            heading_confidence=float(state.get("heading_confidence", 0.0) or 0.0),
        ),
        "needs_review": bool(final_flags),
        "start_block_id": state["start_block_id"],
        "end_block_id": state["end_block_id"],
        "start_anchor_bbox": state["start_anchor_bbox"],
        "end_anchor_bbox": state["end_anchor_bbox"],
        "page_height": state["page_height"],
        "page_width": state["page_width"],
        "heading_confidence": float(state.get("heading_confidence", 0.0) or 0.0),
        "heading_source": state.get("heading_source", "regex_numbering"),
        "source_modes": list(state.get("source_modes", [])),
        "bbox_sources": list(state.get("bbox_sources", [])),
        "issue_flags": final_flags,
        "risk_flags": final_flags,
        "decision_source": "rule",
        "semantic_confidence": split_confidence,
        "semantic_reason": "rule-based free-layout segmentation",
    }


def _append_candidate(question_candidates: list[QuestionCandidate], candidate: QuestionCandidate) -> None:
    question_candidates.append(candidate)


def _finish_candidate(
    file_id: str,
    question_candidates: list[QuestionCandidate],
    state: dict[str, Any],
    seen_question_nos: dict[str, int],
) -> None:
    _append_candidate(question_candidates, _build_candidate(file_id, state))
    question_no = str(state["question_no"])
    seen_question_nos[question_no] = seen_question_nos.get(question_no, 0) + 1


def _heading_flags(heading_confidence: float, paragraph: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if heading_confidence < 0.72:
        flags.append("low_heading_confidence")
    if paragraph.get("role") in {"heading_answer_pair", "uncertain_heading_pair"}:
        flags.append("heading_answer_pair")
    return flags


def _should_infer_question_from_uncertain_heading(
    paragraph: dict[str, Any],
    last_confirmed_question_no: Optional[str],
) -> bool:
    if paragraph.get("role") not in {"uncertain_heading_like", "uncertain_heading_pair"}:
        return False
    if last_confirmed_question_no is None or not last_confirmed_question_no.isdigit():
        return False
    text = _normalize_text(paragraph.get("text", ""))
    return len(text) >= 8


def _infer_next_question_no(last_confirmed_question_no: Optional[str]) -> str:
    if last_confirmed_question_no and last_confirmed_question_no.isdigit():
        return str(int(last_confirmed_question_no) + 1)
    return "1"


def _normalize_text(text: str) -> str:
    return normalize_inline_text(text)


def _question_id(section_no: Optional[str], question_no: str) -> str:
    return f"{section_no}.{question_no}" if section_no else str(question_no)


def _is_section_context_paragraph(paragraph: dict[str, Any]) -> bool:
    return str(paragraph.get("semantic_role", "") or "") in {
        "answer_body",
        "image_marker",
        "image_ocr",
        "mixed",
    } or str(paragraph.get("role", "") or "") in {"answer_like", "mixed"}


def _extract_question_no(text: str) -> Optional[str]:
    for pattern in QUESTION_PATTERNS:
        match = pattern.match(text or "")
        if not match:
            continue
        question_no = match.group(1)
        if question_no.isdigit():
            return str(int(question_no))
    return None


def _is_trailing_noise_paragraph(paragraph: dict[str, Any], current_state: dict[str, Any]) -> bool:
    text = _normalize_text(paragraph.get("text", ""))
    if not text:
        return False

    if paragraph.get("heading_question_no") is not None:
        return False

    if paragraph.get("semantic_role") in {"noise", "header_footer", "student_info"}:
        return True

    if paragraph.get("role") not in {"answer_like", "mixed"}:
        return False

    source_modes = set(paragraph.get("source_modes", []))
    block_types = set(paragraph.get("block_types", []))
    current_modes = set(current_state.get("source_modes", []))

    if _is_strong_trailing_noise(text):
        return True

    matches_noise = any(pattern.match(text) for pattern in TRAILING_NOISE_PATTERNS)
    if not matches_noise:
        return False

    # Suppress especially when a weak estimated/text marker is appended after a stable OCR answer.
    if "ocr" in current_modes and ("text_extract" in source_modes or "image_marker" in source_modes):
        return True

    if "image_marker" in block_types:
        return True

    return False


def _is_strong_trailing_noise(text: str) -> bool:
    normalized = text.strip().lower()
    return (
        "ocrpageresult" in normalized
        or "reading_order" in normalized
        or "bbox" in normalized
        or "confidence" in normalized
        or "本页用于测试" in normalized
    )


def _mark_sequence_anomalies(question_candidates: list[QuestionCandidate]) -> None:
    previous_numeric: Optional[int] = None
    previous_section: Optional[str] = None
    for candidate in question_candidates:
        current_section = str(candidate.get("section_no") or "")
        if previous_section is not None and current_section != previous_section:
            previous_numeric = None
        current_numeric = int(candidate["question_no"]) if candidate["question_no"].isdigit() else None
        if previous_numeric is not None and current_numeric is not None:
            if current_numeric > previous_numeric + 1:
                _append_issue(candidate, "question_no_gap")
            elif current_numeric < previous_numeric:
                _append_issue(candidate, "question_no_out_of_order")
        if current_numeric is not None:
            previous_numeric = current_numeric
        previous_section = current_section


def _append_issue(candidate: QuestionCandidate, issue_flag: str) -> None:
    flags = set(candidate.get("issue_flags", []))
    flags.add(issue_flag)
    candidate["issue_flags"] = sorted(flags)
    candidate["needs_review"] = True
    candidate["split_confidence"] = _score_candidate(
        len(candidate["block_ids"]),
        candidate["issue_flags"],
        float(candidate.get("heading_confidence", 0.0) or 0.0),
    )


def _should_keep_cross_page_open(current_state: dict[str, Any], paragraph: dict[str, Any]) -> bool:
    if not paragraph.get("is_page_top_paragraph"):
        return False
    if paragraph.get("heading_question_no") is not None:
        return False

    current_bottom = current_state.get("end_anchor_bbox") or [0.0, 0.0, 0.0, 0.0]
    previous_page_height = max(int(current_state.get("page_height", 0) or 0), 1)
    current_page_height = max(int(paragraph.get("page_height", 0) or 0), 1)
    previous_bottom_ratio = float(current_bottom[3]) / previous_page_height
    next_top_ratio = float((paragraph.get("start_anchor_bbox") or [0.0, 0.0, 0.0, 0.0])[1]) / current_page_height

    same_question_signal = current_state.get("question_no") is not None
    geometry_signal = previous_bottom_ratio >= 0.72 and next_top_ratio <= 0.18
    width_signal = abs(
        float((current_state.get("end_anchor_bbox") or [0.0, 0.0, 0.0, 0.0])[2] - (current_state.get("end_anchor_bbox") or [0.0, 0.0, 0.0, 0.0])[0])
        - float((paragraph.get("start_anchor_bbox") or [0.0, 0.0, 0.0, 0.0])[2] - (paragraph.get("start_anchor_bbox") or [0.0, 0.0, 0.0, 0.0])[0])
    ) <= max(120.0, float(paragraph.get("page_width", 0) or 0) * 0.28)

    return same_question_signal and geometry_signal and width_signal


def _score_candidate(block_count: int, issue_flags: Iterable[str], heading_confidence: float) -> float:
    score = 0.95
    if block_count == 1:
        score -= 0.06
    score -= 0.06 * len(set(issue_flags))
    if heading_confidence and heading_confidence < 0.75:
        score -= 0.12
    return max(0.1, min(1.0, round(score, 2)))


def _filter_duplicate_pages(
    page_ocr_results: list[OCRPageResult],
) -> tuple[list[OCRPageResult], list[dict[str, Any]]]:
    if not page_ocr_results:
        return [], []

    kept_pages: list[OCRPageResult] = []
    duplicate_notes: list[dict[str, Any]] = []
    previous_signature: Optional[dict[str, Any]] = None

    for page in sorted(page_ocr_results, key=lambda item: item["page_no"]):
        signature = _build_page_signature(page)
        if previous_signature and _is_near_duplicate_page(previous_signature, signature):
            duplicate_notes.append(
                {
                    "skipped_page_no": page["page_no"],
                    "reference_page_no": previous_signature["page_no"],
                    "reason": "near_duplicate_page_detected",
                    "similarity": round(signature["similarity_to_previous"], 4),
                }
            )
            continue
        kept_pages.append(page)
        previous_signature = signature

    return kept_pages, duplicate_notes


def _build_page_signature(page: OCRPageResult) -> dict[str, Any]:
    blocks = page.get("blocks", [])
    texts = [_normalize_text(block.get("text", "")) for block in blocks]
    joined = " ".join(part for part in texts if part)
    headings = [
        _extract_question_no(text)
        for text in texts
        if _extract_question_no(text) is not None
    ]
    return {
        "page_no": page["page_no"],
        "text": joined,
        "heading_sequence": headings[:10],
        "block_count": len(blocks),
        "similarity_to_previous": 0.0,
    }


def _is_near_duplicate_page(previous_signature: dict[str, Any], current_signature: dict[str, Any]) -> bool:
    previous_text = previous_signature.get("text", "")
    current_text = current_signature.get("text", "")
    if not previous_text or not current_text:
        return False

    similarity = SequenceMatcher(None, previous_text, current_text).ratio()
    current_signature["similarity_to_previous"] = similarity
    same_heading_sequence = previous_signature.get("heading_sequence") == current_signature.get("heading_sequence")
    similar_block_count = abs(int(previous_signature.get("block_count", 0)) - int(current_signature.get("block_count", 0))) <= 1
    return similarity >= 0.9 and same_heading_sequence and similar_block_count
