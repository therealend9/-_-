from __future__ import annotations

from typing import Iterable, Optional, Set


DOCX_ESTIMATED_SAFE_SOURCE_MODES = {"text_extract", "image_marker"}


def evaluate_candidate_review_flags(
    issue_flags: Optional[Iterable[str]],
    split_confidence: float,
    text: str,
    block_count: int,
    has_estimated_bbox: bool = False,
    has_low_confidence_block: bool = False,
    has_image_marker_block: bool = False,
    source_modes: Optional[Iterable[str]] = None,
    bbox_sources: Optional[Iterable[str]] = None,
) -> list[str]:
    """Return normalized review flags for a question candidate.

    规则重点：
    - DOCX mixed 路线中，正文文本来自 text_extract，图片占位来自 image_marker。
      这两类 block 的 bbox 本来就是 estimated，只表示坐标不精确，不能直接说明文本不可信。
    - 因此，只要 estimated bbox 来自 text_extract / image_marker 参与的 DOCX 混合链路，
      就不再自动追加 estimated_bbox_source，也不再因此触发 needs_review。
    - 如果某个 OCR block 自身 bbox_source=estimated，仍然保留 estimated_bbox_source 风险。
    """
    normalized_flags = set(issue_flags or [])
    source_mode_set = _to_clean_set(source_modes)
    bbox_source_set = _to_clean_set(bbox_sources)
    suppressible_flags = {"suppressed_trailing_noise"}

    if split_confidence < 0.75:
        normalized_flags.add("low_split_confidence")
    if not text.strip():
        normalized_flags.add("empty_candidate_text")
    if block_count <= 0:
        normalized_flags.add("empty_block_group")
    if len(text.strip()) < 4:
        normalized_flags.add("very_short_answer")

    if has_estimated_bbox and _should_flag_estimated_bbox_candidate(source_mode_set, bbox_source_set):
        normalized_flags.add("estimated_bbox_source")
    else:
        normalized_flags.discard("estimated_bbox_source")

    if has_low_confidence_block:
        normalized_flags.add("contains_low_confidence_block")
    if has_image_marker_block:
        # 图片占位说明 DOCX 原位置有图。它对 B 模块有价值，但不应天然触发人工复核。
        # 如果图片 OCR 失败或文本为空，其他规则会再单独触发。
        normalized_flags.discard("contains_image_marker_block")

    if "cross_page_candidate_extended" in normalized_flags and "continuation_without_heading" in normalized_flags:
        normalized_flags.discard("continuation_without_heading")
    if normalized_flags and normalized_flags.issubset(suppressible_flags):
        normalized_flags.clear()

    return sorted(normalized_flags)


def evaluate_merge_review_flags(
    issue_flags: Optional[Iterable[str]],
    merge_confidence: float,
    page_count: int,
    has_estimated_bbox: bool = False,
    source_modes: Optional[Iterable[str]] = None,
    bbox_sources: Optional[Iterable[str]] = None,
) -> list[str]:
    """Return normalized review flags for a merged question result.

    DOCX mixed 路线下，text_extract / image_marker 的 estimated bbox 只表示坐标不可信，
    不表示分题结果需要复核；因此不会生成 estimated_bbox_in_merge。
    """
    normalized_flags = set(issue_flags or [])
    source_mode_set = _to_clean_set(source_modes)
    bbox_source_set = _to_clean_set(bbox_sources)
    suppressible_flags = {"suppressed_trailing_noise"}

    if merge_confidence < 0.8:
        normalized_flags.add("low_merge_confidence")
    if page_count >= 3:
        normalized_flags.add("multi_page_long_answer")

    if has_estimated_bbox and _should_flag_estimated_bbox_merge(source_mode_set, bbox_source_set):
        normalized_flags.add("estimated_bbox_in_merge")
    else:
        normalized_flags.discard("estimated_bbox_in_merge")
        normalized_flags.discard("estimated_bbox_source")

    if normalized_flags and normalized_flags.issubset(suppressible_flags):
        normalized_flags.clear()

    return sorted(normalized_flags)


def infer_coordinate_text_trust(
    source_modes: Optional[Iterable[str]] = None,
    bbox_sources: Optional[Iterable[str]] = None,
    has_low_confidence_block: bool = False,
) -> dict[str, object]:
    """Infer non-review diagnostic trust labels.

    这个函数不直接决定 needs_review，只用于后续报告或调试：
    - DOCX 文本：text_trust 高，coordinate_trust 低；
    - OCR 文本：coordinate_trust 高，但 text_trust 受 OCR 置信度影响。
    """
    source_mode_set = _to_clean_set(source_modes)
    bbox_source_set = _to_clean_set(bbox_sources)
    notes: list[str] = []

    if "estimated" in bbox_source_set:
        coordinate_trust = "low"
        notes.append("coordinate_untrusted_estimated_bbox")
    else:
        coordinate_trust = "high"

    if source_mode_set and source_mode_set.issubset({"text_extract", "image_marker"}):
        text_trust = "high"
        notes.append("docx_text_extract_text_is_stable")
    elif "ocr" in source_mode_set and has_low_confidence_block:
        text_trust = "medium"
        notes.append("contains_low_confidence_ocr_block")
    elif "ocr" in source_mode_set:
        text_trust = "medium"
    else:
        text_trust = "unknown"

    return {
        "coordinate_trust": coordinate_trust,
        "text_trust": text_trust,
        "trust_notes": notes,
    }


def _should_flag_estimated_bbox_candidate(source_modes: Set[str], bbox_sources: Set[str]) -> bool:
    if "estimated" not in bbox_sources:
        return False

    # DOCX mixed 路线：text_extract / image_marker 的 estimated bbox 只是“坐标估计”，
    # 对分题文本本身不构成风险，不应直接触发 needs_review。
    if source_modes.intersection(DOCX_ESTIMATED_SAFE_SOURCE_MODES):
        return False

    # 其他来源仍然视为坐标风险。
    return True


def _should_flag_estimated_bbox_merge(source_modes: Set[str], bbox_sources: Set[str]) -> bool:
    if "estimated" not in bbox_sources:
        return False
    if source_modes.intersection(DOCX_ESTIMATED_SAFE_SOURCE_MODES):
        return False
    return True


def _to_clean_set(values: Optional[Iterable[str]]) -> Set[str]:
    return {str(value).strip() for value in (values or []) if str(value).strip()}
