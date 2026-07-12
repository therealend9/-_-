from __future__ import annotations

from typing import Iterable

from b_module.schemas.types import QuestionCandidate


RISK_WEIGHTS = {
    "continuation_without_heading": 0.34,
    "question_no_gap": 0.22,
    "question_no_out_of_order": 0.24,
    "repeated_question_no": 0.24,
    "ocr_heading_error_inferred": 0.28,
    "low_heading_confidence": 0.18,
    "needs_semantic_boundary_review": 0.2,
    "weak_page_boundary_signal": 0.12,
    "low_confidence_heading": 0.18,
    "contains_low_confidence_block": 0.14,
    "estimated_bbox_source": 0.12,
    "estimated_bbox_in_merge": 0.12,
    "contains_image_marker_block": 0.08,
    "very_short_answer": 0.12,
    "low_split_confidence": 0.18,
}


def evaluate_candidate_risk(question_candidates: Iterable[QuestionCandidate]) -> list[dict]:
    """Score question candidates and decide whether they need LLM refinement."""
    risk_records: list[dict] = []
    for index, candidate in enumerate(question_candidates):
        risk_flags = list(candidate.get("issue_flags", []))
        risk_score = _score_risk(candidate, risk_flags)
        risk_records.append(
            {
                "candidate_index": index,
                "question_no": candidate.get("question_no"),
                "risk_score": risk_score,
                "risk_flags": sorted(set(risk_flags)),
                "needs_llm": risk_score >= 0.4,
            }
        )
    return risk_records


def summarize_candidate_risks(risk_records: Iterable[dict]) -> dict:
    records = list(risk_records)
    high_risk = [item for item in records if item.get("needs_llm")]
    return {
        "total_candidates": len(records),
        "high_risk_candidates": len(high_risk),
        "max_risk_score": max((float(item.get("risk_score", 0.0)) for item in records), default=0.0),
    }


def _score_risk(candidate: QuestionCandidate, risk_flags: list[str]) -> float:
    score = 0.0
    for flag in risk_flags:
        score += RISK_WEIGHTS.get(flag, 0.08)

    block_count = len(candidate.get("block_ids", []))
    if block_count <= 1:
        score += 0.08
    if len((candidate.get("text") or "").strip()) < 12:
        score += 0.06
    if float(candidate.get("split_confidence", 1.0)) < 0.75:
        score += 0.12
    if float(candidate.get("heading_confidence", 1.0)) < 0.6:
        score += 0.14
    if len(candidate.get("paragraph_ids", [])) >= 3:
        score += 0.06

    return round(min(1.0, score), 2)
