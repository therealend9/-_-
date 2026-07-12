from __future__ import annotations

from typing import Iterable, Optional

from b_module.schemas.types import MergedQuestion, QuestionLevelResult, ReviewResult


def export_question_level_results(
    file_id: str,
    route_type: str,
    merged_questions: Iterable[MergedQuestion],
    review_results: Optional[Iterable[ReviewResult]] = None,
) -> dict:
    """Export merged OCR results into final question-level records."""
    review_map = _build_review_map(review_results or [])
    question_level_results: list[QuestionLevelResult] = []

    for merged_question in merged_questions:
        review_key = _resolve_review_key(merged_question)
        reviewed = review_map.get(review_key)
        corrected_text = reviewed["after_text"] if reviewed else None
        final_text = corrected_text or merged_question["merged_text"]

        result: QuestionLevelResult = {
            "file_id": file_id,
            "merge_group_id": merged_question["merge_group_id"],
            "question_no": merged_question["question_no"],
            "question_id": merged_question.get("question_id", merged_question["question_no"]),
            "section_no": merged_question.get("section_no"),
            "section_label": merged_question.get("section_label"),
            "section_context": merged_question.get("section_context", ""),
            "section_context_block_ids": list(merged_question.get("section_context_block_ids", [])),
            "route_type": route_type,
            "page_nos": merged_question["from_pages"],
            "ocr_text": merged_question["merged_text"],
            "final_text": final_text,
            "confidence": merged_question["merge_confidence"],
            "needs_review": merged_question["needs_review"],
            "decision_source": merged_question.get("decision_source", "rule"),
            "semantic_confidence": merged_question.get("semantic_confidence", merged_question["merge_confidence"]),
            "semantic_reason": merged_question.get("semantic_reason", "rule result exported"),
            "risk_flags": merged_question.get("issue_flags", []),
        }
        result["merge_evidence"] = merged_question.get("merge_evidence", [])
        if corrected_text is not None:
            result["corrected_text"] = corrected_text

        question_level_results.append(result)

    return {
        "file_id": file_id,
        "question_level_results": question_level_results,
    }


def _resolve_review_key(merged_question: MergedQuestion) -> str:
    merge_group_id = merged_question.get("merge_group_id")
    if merge_group_id:
        return f"merge_group:{merge_group_id}"
    return f"question_no:{merged_question['question_no']}"


def _build_review_map(review_results: Iterable[ReviewResult]) -> dict[str, ReviewResult]:
    review_map: dict[str, ReviewResult] = {}
    for review in review_results:
        merge_group_id = review.get("merge_group_id")
        if merge_group_id:
            review_map[f"merge_group:{merge_group_id}"] = review
            continue
        review_map[f"question_no:{review['question_no']}"] = review
    return review_map
