from __future__ import annotations

from typing import Any, Iterable

from b_module.pipeline.service import process_b_module


def run_demo_pipeline(
    file_task: dict[str, Any],
    normalized_pages: Iterable[dict[str, Any]],
    page_ocr_results: Iterable[dict[str, Any]],
    assignment_type: str = "homework",
) -> dict[str, Any]:
    """Run the current non-LLM demo pipeline with stable defaults."""
    return process_b_module(
        file_task=file_task,
        normalized_pages=normalized_pages,
        page_ocr_results=page_ocr_results,
        assignment_type=assignment_type,
        review_results=[],
        llm_enabled=False,
    )


def run_demo_case(case: dict[str, Any], assignment_type: str = "homework") -> dict[str, Any]:
    return run_demo_pipeline(
        file_task={
            "file_id": case["file_id"],
            "task_status": "ocr_done",
        },
        normalized_pages=case.get("normalized_pages", []),
        page_ocr_results=case["page_ocr_results"],
        assignment_type=assignment_type,
    )


def format_demo_summary(result: dict[str, Any]) -> dict[str, Any]:
    split_result = result["split_result"]
    merge_result = result["merge_result"]
    export_result = result["export_result"]
    risk_result = result.get("risk_result", {})

    return {
        "file_id": result["file_id"],
        "route_type": result["route_decision"]["route_type"],
        "candidate_count": len(split_result["question_candidates"]),
        "merged_count": len(merge_result["merged_questions"]),
        "result_count": len(export_result["question_level_results"]),
        "high_risk_candidates": risk_result.get("risk_summary", {}).get("high_risk_candidates", 0),
        "questions": [
            {
                "question_no": item["question_no"],
                "page_nos": item["page_nos"],
                "final_text": item["final_text"],
                "needs_review": item["needs_review"],
                "decision_source": item.get("decision_source", "rule"),
            }
            for item in export_result["question_level_results"]
        ],
    }
