from __future__ import annotations

from typing import Iterable

from b_module.schemas.types import MergedQuestion, QuestionCandidate


def refine_candidates_with_llm(
    question_candidates: Iterable[QuestionCandidate],
    risk_records: Iterable[dict],
    llm_enabled: bool = False,
) -> dict:
    """Reserved LLM refinement entrypoint for page-level question segmentation.

    The current implementation keeps rule results intact and emits structured
    placeholder decisions so the pipeline can be upgraded later without further
    interface churn.
    """
    candidates = list(question_candidates)
    records = list(risk_records)
    decisions: list[dict] = []

    for record in records:
        if not record.get("needs_llm"):
            continue
        decisions.append(
            {
                "decision_id": f"llm_seg_candidate_{record['candidate_index']:03d}",
                "scope_type": "intra_page",
                "decision_source": "llm" if llm_enabled else "rule_fallback",
                "candidate_index": record["candidate_index"],
                "input_block_ids": candidates[record["candidate_index"]].get("block_ids", []),
                "decision": "keep",
                "decision_confidence": 0.55 if llm_enabled else 0.0,
                "reason": "LLM refinement interface reserved; current pipeline keeps rule segmentation.",
                "model_name": "pending_runtime" if llm_enabled else "not_enabled",
            }
        )

    refined_candidates: list[QuestionCandidate] = []
    for index, candidate in enumerate(candidates):
        updated = dict(candidate)
        decision = next((item for item in decisions if item["candidate_index"] == index), None)
        updated["decision_source"] = decision["decision_source"] if decision else "rule"
        updated["semantic_confidence"] = decision["decision_confidence"] if decision else candidate.get("split_confidence", 1.0)
        updated["semantic_reason"] = decision["reason"] if decision else "rule segmentation accepted"
        updated["risk_flags"] = next((item["risk_flags"] for item in records if item["candidate_index"] == index), candidate.get("issue_flags", []))
        refined_candidates.append(updated)

    return {
        "question_candidates": refined_candidates,
        "llm_decisions": decisions,
    }


def refine_cross_page_merge_with_llm(
    merged_questions: Iterable[MergedQuestion],
    llm_enabled: bool = False,
) -> dict:
    """Reserved LLM refinement entrypoint for cross-page merge decisions."""
    merged_questions = list(merged_questions)
    decisions: list[dict] = []
    refined: list[MergedQuestion] = []

    for index, merged_question in enumerate(merged_questions):
        updated = dict(merged_question)
        needs_semantic_review = "continuation_without_heading" in merged_question.get("merge_evidence", []) or merged_question.get("needs_review", False)
        if needs_semantic_review:
            decision = {
                "decision_id": f"llm_seg_merge_{index:03d}",
                "scope_type": "cross_page",
                "decision_source": "llm" if llm_enabled else "rule_fallback",
                "merge_group_id": merged_question.get("merge_group_id"),
                "input_block_ids": [],
                "decision": "merge",
                "decision_confidence": 0.6 if llm_enabled else 0.0,
                "reason": "Cross-page LLM refinement interface reserved; current pipeline keeps rule merge.",
                "model_name": "pending_runtime" if llm_enabled else "not_enabled",
            }
            decisions.append(decision)
            updated["decision_source"] = decision["decision_source"]
            updated["semantic_confidence"] = decision["decision_confidence"]
            updated["semantic_reason"] = decision["reason"]
        else:
            updated["decision_source"] = "rule"
            updated["semantic_confidence"] = merged_question.get("merge_confidence", 1.0)
            updated["semantic_reason"] = "rule merge accepted"
        refined.append(updated)

    return {
        "merged_questions": refined,
        "llm_decisions": decisions,
    }
