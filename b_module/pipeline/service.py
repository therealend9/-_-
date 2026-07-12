from __future__ import annotations

from typing import Any, Iterable, Optional

from b_module.candidate_risk_scorer.service import evaluate_candidate_risk, summarize_candidate_risks
from b_module.cross_page_merger.service import merge_cross_page_answers
from b_module.layout_router.service import decide_layout_route
from b_module.question_segmenter.free_layout_pipeline_v3 import split_free_layout_questions_v3
from b_module.question_segmenter.uniform_exam_processor import split_uniform_exam_questions
from b_module.result_exporter.service import export_question_level_results
from b_module.semantic_segmenter.service import refine_candidates_with_llm, refine_cross_page_merge_with_llm


def build_b_module_context(
    file_task: dict[str, Any],
    normalized_pages: Iterable[dict[str, Any]],
    page_ocr_results: Iterable[dict[str, Any]],
    assignment_type: str,
    template_id: Optional[str] = None,
    question_regions: Optional[Iterable[dict[str, Any]]] = None,
    template: Optional[dict[str, Any]] = None,
    document_role: str = "question_paper",
) -> dict[str, Any]:
    """Build the stable A-to-B handoff context."""
    return {
        "file_task": file_task,
        "normalized_pages": list(normalized_pages or []),
        "page_ocr_results": list(page_ocr_results or []),
        "assignment_type": assignment_type,
        "template_id": template_id,
        "question_regions": list(question_regions or []),
        "template": template,
        "document_role": document_role,
    }


def process_b_module(
    file_task: dict[str, Any],
    normalized_pages: Iterable[dict[str, Any]],
    page_ocr_results: Iterable[dict[str, Any]],
    assignment_type: str,
    template_id: Optional[str] = None,
    question_regions: Optional[Iterable[dict[str, Any]]] = None,
    template: Optional[dict[str, Any]] = None,
    document_role: str = "question_paper",
    review_results: Optional[Iterable[dict[str, Any]]] = None,
    llm_enabled: bool = False,
) -> dict[str, Any]:
    """Orchestrate B-module processing with rule-first and LLM-refinement hooks."""
    context = build_b_module_context(
        file_task=file_task,
        normalized_pages=normalized_pages,
        page_ocr_results=page_ocr_results,
        assignment_type=assignment_type,
        template_id=template_id,
        question_regions=question_regions,
        template=template,
        document_role=document_role,
    )
    file_id = _resolve_file_id(context)

    route_decision = decide_layout_route(
        file_id=file_id,
        assignment_type=assignment_type,
        template_id=template_id,
        page_results=context["page_ocr_results"],
        normalized_pages=context["normalized_pages"],
    )

    if route_decision["route_type"] == "uniform_exam":
        uniform_result = _process_uniform_exam_route(
            file_id=file_id,
            template_id=template_id,
            question_regions=context["question_regions"],
            normalized_pages=context["normalized_pages"],
            template=context.get("template"),
            document_role=context["document_role"],
        )
        return {
            "file_id": file_id,
            "route_decision": route_decision,
            "context_status": "waiting_a_regions" if uniform_result.get("status") == "pending_a_output" else "ready",
            "uniform_result": uniform_result,
            "export_result": _build_uniform_export(file_id, uniform_result, context["document_role"]),
        }

    split_result = split_free_layout_questions_v3(
        file_id=file_id,
        page_ocr_results=context["page_ocr_results"],
    )
    risk_records = evaluate_candidate_risk(split_result["question_candidates"])
    risk_summary = summarize_candidate_risks(risk_records)
    semantic_split_result = refine_candidates_with_llm(
        question_candidates=split_result["question_candidates"],
        risk_records=risk_records,
        llm_enabled=llm_enabled,
    )
    merge_result = merge_cross_page_answers(
        file_id=file_id,
        route_type=route_decision["route_type"],
        question_candidates=semantic_split_result["question_candidates"],
    )
    semantic_merge_result = refine_cross_page_merge_with_llm(
        merged_questions=merge_result["merged_questions"],
        llm_enabled=llm_enabled,
    )
    export_result = export_question_level_results(
        file_id=file_id,
        route_type=route_decision["route_type"],
        merged_questions=semantic_merge_result["merged_questions"],
        review_results=review_results or [],
    )

    return {
        "file_id": file_id,
        "route_decision": route_decision,
        "context_status": "ready",
        "llm_enabled": llm_enabled,
        "paragraph_result": split_result.get("paragraph_result", {}),
        "split_result": split_result,
        "risk_result": {
            "risk_records": risk_records,
            "risk_summary": risk_summary,
        },
        "semantic_split_result": semantic_split_result,
        "merge_result": merge_result,
        "semantic_merge_result": semantic_merge_result,
        "export_result": export_result,
    }


def process_b_module_for_review(
    context: dict[str, Any],
    review_results: Optional[Iterable[dict[str, Any]]] = None,
    llm_enabled: bool = False,
) -> dict[str, Any]:
    """Replay B-module export with review results on an existing context."""
    return process_b_module(
        file_task=context["file_task"],
        normalized_pages=context["normalized_pages"],
        page_ocr_results=context["page_ocr_results"],
        assignment_type=context["assignment_type"],
        template_id=context.get("template_id"),
        question_regions=context.get("question_regions", []),
        template=context.get("template"),
        document_role=context.get("document_role", "question_paper"),
        review_results=review_results or [],
        llm_enabled=llm_enabled,
    )


def _process_uniform_exam_route(
    file_id: str,
    template_id: Optional[str],
    question_regions: list[dict[str, Any]],
    normalized_pages: list[dict[str, Any]],
    template: Optional[dict[str, Any]],
    document_role: str,
) -> dict[str, Any]:
    if not template_id:
        return {
            "status": "pending_a_output",
            "message": "uniform_exam route requires template_id from A module",
            "required_fields": ["template_id", "question_regions"],
        }
    if not question_regions:
        return {
            "status": "pending_a_output",
            "message": "uniform_exam route is reserved for A-provided question_regions",
            "required_fields": ["question_regions[].question_no", "question_regions[].page_no", "question_regions[].bbox"],
        }
    result = split_uniform_exam_questions(
        file_id=file_id,
        template_id=template_id,
        question_regions=question_regions,
        normalized_pages=normalized_pages,
        template=template,
        document_role=document_role,
    )
    result["status"] = "ready"
    return result


def _resolve_file_id(context: dict[str, Any]) -> str:
    file_task = context.get("file_task") or {}
    file_id = file_task.get("file_id")
    if not file_id:
        raise ValueError("file_task.file_id is required for B module processing")
    return str(file_id)


def _build_uniform_export(file_id: str, uniform_result: dict[str, Any], document_role: str) -> dict[str, Any]:
    records = list(uniform_result.get("question_level_results", []))
    if document_role == "question_paper":
        return {
            "file_id": file_id,
            "question_level_results": records,
            "questions": [_question_record(record) for record in records],
        }
    return {
        "file_id": file_id,
        "question_level_results": records,
        "answers": [_answer_record(record) for record in records],
    }


def _question_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": record["question_id"],
        "question_no": record["question_no"],
        "question_text": record.get("final_text", ""),
        "page_nos": record.get("page_nos", []),
        "confidence": record.get("confidence", 0.0),
        "needs_review": record.get("needs_review", False),
        "risk_flags": record.get("risk_flags", []),
    }


def _answer_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": record["question_id"],
        "question_no": record["question_no"],
        "answer_text": record.get("final_text", ""),
        "is_blank": record.get("is_blank", False),
        "page_nos": record.get("page_nos", []),
        "confidence": record.get("confidence", 0.0),
        "needs_review": record.get("needs_review", False),
        "risk_flags": record.get("risk_flags", []),
    }
