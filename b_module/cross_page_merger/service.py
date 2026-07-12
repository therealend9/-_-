from __future__ import annotations

from typing import Iterable, Optional

from b_module.question_segmenter.review_rules import evaluate_merge_review_flags
from b_module.schemas.types import MergedQuestion, QuestionCandidate
from b_module.text_utils import join_text_parts


def merge_cross_page_answers(
    file_id: str,
    route_type: str,
    question_candidates: Iterable[QuestionCandidate],
) -> dict:
    """Merge adjacent candidates conservatively, preserving source traceability."""
    indexed_candidates = list(enumerate(question_candidates))
    ordered_candidates = sorted(
        indexed_candidates,
        key=lambda item: (
            item[1]["page_no"],
            _bbox_top(item[1].get("start_anchor_bbox")),
            item[1].get("start_block_id", ""),
            item[1]["question_no"],
        ),
    )

    merged_questions: list[MergedQuestion] = []
    current_group: list[tuple[int, QuestionCandidate]] = []

    for indexed_candidate in ordered_candidates:
        if not current_group:
            current_group = [indexed_candidate]
            continue

        previous = current_group[-1][1]
        candidate = indexed_candidate[1]
        merge_decision = _evaluate_merge(previous, candidate)
        if merge_decision["allow_merge"]:
            indexed_candidate[1]["merge_evidence"] = merge_decision["positive_evidence"]
            indexed_candidate[1]["merge_negative_evidence"] = merge_decision["negative_evidence"]
            current_group.append(indexed_candidate)
            continue

        merged_questions.append(_build_merged_question(file_id, route_type, current_group, len(merged_questions) + 1))
        current_group = [indexed_candidate]

    if current_group:
        merged_questions.append(_build_merged_question(file_id, route_type, current_group, len(merged_questions) + 1))

    return {
        "file_id": file_id,
        "merged_questions": merged_questions,
    }


def _evaluate_merge(previous: QuestionCandidate, current: QuestionCandidate) -> dict[str, object]:
    positive_evidence: list[str] = []
    negative_evidence: list[str] = []

    if previous["question_no"] != current["question_no"]:
        negative_evidence.append("question_no_changed")
    if str(previous.get("section_no") or "") != str(current.get("section_no") or ""):
        negative_evidence.append("section_changed")
    if current["page_no"] != previous["page_no"] + 1:
        negative_evidence.append("page_not_adjacent")
    if "repeated_question_no" in current.get("issue_flags", []):
        negative_evidence.append("repeated_question_no")
    if "question_no_out_of_order" in current.get("issue_flags", []):
        negative_evidence.append("question_no_out_of_order")
    if current.get("heading_confidence", 0.0) >= 0.85 and _current_starts_like_new_section(current):
        negative_evidence.append("strong_new_heading_restart")
    if not _is_top_boundary_candidate(current):
        negative_evidence.append("not_page_top_continuation")
    if not _geometry_is_similar(previous, current):
        negative_evidence.append("geometry_mismatch")

    if "continuation_without_heading" in current.get("issue_flags", []):
        positive_evidence.append("continuation_without_heading")
    if _is_bottom_to_top_continuation(previous, current):
        positive_evidence.append("page_boundary_continuation")
    if _geometry_is_similar(previous, current):
        positive_evidence.append("geometry_alignment")
    if _is_bottom_boundary_candidate(previous):
        positive_evidence.append("previous_page_tail_candidate")

    allow_merge = not negative_evidence and len(positive_evidence) >= 2
    return {
        "allow_merge": allow_merge,
        "positive_evidence": sorted(set(positive_evidence)),
        "negative_evidence": sorted(set(negative_evidence)),
    }


def _build_merged_question(
    file_id: str,
    route_type: str,
    group: list[tuple[int, QuestionCandidate]],
    index: int,
) -> MergedQuestion:
    candidates = [item[1] for item in group]
    from_pages = sorted({item["page_no"] for item in candidates})
    issue_flags = sorted(
        {
            flag
            for item in candidates
            for flag in item.get("issue_flags", [])
        }
    )
    merged_text = join_text_parts(item["text"] for item in candidates if item["text"].strip())
    merge_confidence = round(
        sum(item["split_confidence"] for item in candidates) / max(len(candidates), 1),
        2,
    )
    if len(from_pages) != len(candidates):
        issue_flags.append("duplicate_question_same_page")
        merge_confidence = max(0.1, round(merge_confidence - 0.15, 2))

    merge_evidence = _collect_merge_evidence(group)
    has_estimated_bbox = any("estimated_bbox_source" in item.get("issue_flags", []) for item in candidates)
    source_modes = [
        mode
        for item in candidates
        for mode in item.get("source_modes", [])
    ]
    bbox_sources = [
        source
        for item in candidates
        for source in item.get("bbox_sources", [])
    ]
    if len(from_pages) > 1 and "page_boundary_continuation" not in merge_evidence:
        issue_flags.append("weak_cross_page_evidence")
        merge_confidence = max(0.1, round(merge_confidence - 0.1, 2))

    final_flags = evaluate_merge_review_flags(
        issue_flags=issue_flags,
        merge_confidence=merge_confidence,
        page_count=len(from_pages),
        has_estimated_bbox=has_estimated_bbox,
        source_modes=source_modes,
        bbox_sources=bbox_sources,
    )

    section_no = candidates[0].get("section_no")
    section_label = candidates[0].get("section_label")
    question_id = candidates[0].get("question_id") or (
        f"{section_no}.{candidates[0]['question_no']}" if section_no else candidates[0]["question_no"]
    )
    identity = str(question_id).replace("/", "_").replace(" ", "_")
    return {
        "file_id": file_id,
        "route_type": route_type,
        "merge_group_id": f"mg_{file_id}_q{identity}_{index:03d}",
        "question_no": candidates[0]["question_no"],
        "question_id": question_id,
        "section_no": section_no,
        "section_label": section_label,
        "section_context": candidates[0].get("section_context", ""),
        "section_context_block_ids": list(candidates[0].get("section_context_block_ids", [])),
        "from_pages": from_pages,
        "merged_text": merged_text,
        "merge_confidence": merge_confidence,
        "needs_review": bool(final_flags),
        "source_candidate_indexes": [item[0] for item in group],
        "merge_evidence": merge_evidence,
        "issue_flags": final_flags,
        "decision_source": "rule",
        "semantic_confidence": merge_confidence,
        "semantic_reason": "rule-based cross-page merge",
    }


def _collect_merge_evidence(group: list[tuple[int, QuestionCandidate]]) -> list[str]:
    evidence: set[str] = set()
    for previous_item, current_item in zip(group, group[1:]):
        decision = _evaluate_merge(previous_item[1], current_item[1])
        evidence.update(decision["positive_evidence"])
    return sorted(evidence)


def _current_starts_like_new_section(candidate: QuestionCandidate) -> bool:
    top_ratio = _bbox_top(candidate.get("start_anchor_bbox")) / max(int(candidate.get("page_height", 0) or 0), 1)
    return top_ratio > 0.22


def _is_top_boundary_candidate(candidate: QuestionCandidate) -> bool:
    top_ratio = _bbox_top(candidate.get("start_anchor_bbox")) / max(int(candidate.get("page_height", 0) or 0), 1)
    return top_ratio <= 0.22


def _is_bottom_boundary_candidate(candidate: QuestionCandidate) -> bool:
    bottom_ratio = _bbox_bottom(candidate.get("end_anchor_bbox")) / max(int(candidate.get("page_height", 0) or 0), 1)
    return bottom_ratio >= 0.76


def _geometry_is_similar(previous: QuestionCandidate, current: QuestionCandidate) -> bool:
    previous_bbox = previous.get("end_anchor_bbox")
    current_bbox = current.get("start_anchor_bbox")
    if not previous_bbox or not current_bbox:
        return False

    previous_width = _bbox_width(previous_bbox)
    current_width = _bbox_width(current_bbox)
    previous_left = _bbox_left(previous_bbox)
    current_left = _bbox_left(current_bbox)
    page_width = max(int(previous.get("page_width", 0) or 0), int(current.get("page_width", 0) or 0), 1)
    width_delta_ratio = abs(previous_width - current_width) / page_width
    left_delta_ratio = abs(previous_left - current_left) / page_width
    return width_delta_ratio <= 0.22 and left_delta_ratio <= 0.1


def _bbox_left(bbox: Optional[list[float]]) -> float:
    if not bbox or len(bbox) != 4:
        return float("inf")
    return float(bbox[0])


def _bbox_top(bbox: Optional[list[float]]) -> float:
    if not bbox or len(bbox) != 4:
        return float("inf")
    return float(bbox[1])


def _bbox_bottom(bbox: Optional[list[float]]) -> float:
    if not bbox or len(bbox) != 4:
        return float("-inf")
    return float(bbox[3])


def _bbox_width(bbox: Optional[list[float]]) -> float:
    if not bbox or len(bbox) != 4:
        return 0.0
    return max(0.0, float(bbox[2]) - float(bbox[0]))


def _is_bottom_to_top_continuation(previous: QuestionCandidate, current: QuestionCandidate) -> bool:
    previous_page_height = max(int(previous.get("page_height", 0) or 0), 1)
    current_page_height = max(int(current.get("page_height", 0) or 0), 1)
    previous_bottom_ratio = _bbox_bottom(previous.get("end_anchor_bbox")) / previous_page_height
    current_top_ratio = _bbox_top(current.get("start_anchor_bbox")) / current_page_height
    return previous_bottom_ratio >= 0.78 and current_top_ratio <= 0.18
