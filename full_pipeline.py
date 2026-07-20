from __future__ import annotations

"""Stable single-file A -> B processing API."""

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from b_module.pipeline.service import process_b_module
from d_module.data_redaction import redact_and_record
from d_module.pipeline import process_file_to_ocr_results
from d_module.utils.path_utils import relativize_paths_in_data
from processing_registry.service import get_cached_result, save_result
from template_registry.service import (
    get_exam,
    get_exam_template,
    record_answer_sheet_submission,
    save_exam_questions,
)


OUTPUT_SCHEMA_VERSION = "exam-document.v1"


def process_file_to_question_results(
    submission_id: str,
    origin_name: str,
    mime_type: str,
    assignment_type: str = "homework",
    file_size: Optional[int] = None,
    source_path: Optional[Union[str, Path]] = None,
    file_bytes: Optional[bytes] = None,
    template_id: Optional[str] = None,
    question_regions: Optional[Iterable[dict[str, Any]]] = None,
    review_results: Optional[Iterable[dict[str, Any]]] = None,
    llm_enabled: bool = False,
    include_intermediate: bool = False,
    exam_id: Optional[str] = None,
    template: Optional[dict[str, Any]] = None,
    document_role: str = "question_paper",
) -> dict[str, Any]:
    """Run the complete file -> OCR -> question-level pipeline."""
    if document_role not in {"question_paper", "answer_sheet"}:
        raise ValueError("document_role must be 'question_paper' or 'answer_sheet'")
    active_template = template
    exam_name: Optional[str] = None
    if exam_id:
        # Student submissions select an exam, never a template directly.
        exam_name = get_exam(exam_id).get("exam_name")
        if document_role == "answer_sheet":
            active_template = get_exam_template(exam_id)
            template_id = active_template["template_id"]
            assignment_type = "uniform_exam"

    if active_template:
        template_id = active_template["template_id"]
        assignment_type = "uniform_exam"
        question_regions = _flatten_template_regions(active_template)
    elif document_role == "answer_sheet":
        raise ValueError("answer_sheet processing requires an exam-bound template")

    region_list = list(question_regions or [])
    review_result_list = list(review_results or [])
    fingerprint = _processing_fingerprint(
        document_role=document_role,
        exam_id=exam_id,
        template=active_template,
        source_path=source_path,
        file_bytes=file_bytes,
        mime_type=mime_type,
        assignment_type=assignment_type,
        question_regions=region_list,
        review_results=review_result_list,
        llm_enabled=llm_enabled,
        include_intermediate=include_intermediate,
    )
    cached = get_cached_result(submission_id, fingerprint)
    if cached is not None:
        return cached

    a_result = process_file_to_ocr_results(
        submission_id=submission_id,
        origin_name=origin_name,
        mime_type=mime_type,
        file_size=file_size,
        source_path=source_path,
        file_bytes=file_bytes,
        parse_strategy=(
            "template_regions_only"
            if active_template and document_role == "answer_sheet"
            else "force_image_ocr" if active_template else "auto"
        ),
    )
    b_result = process_b_module(
        file_task=a_result["file_task"],
        normalized_pages=a_result["normalized_pages"],
        page_ocr_results=a_result["ocr_page_results"],
        assignment_type=assignment_type,
        template_id=template_id,
        question_regions=region_list,
        template=active_template,
        document_role=document_role,
        review_results=review_result_list,
        llm_enabled=llm_enabled,
    )

    split_result = b_result.get("split_result") or {}
    export_result = b_result.get("export_result") or {}
    output: dict[str, Any] = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "submission_id": submission_id,
        "exam_id": exam_id,
        "exam_name": exam_name,
        "document_role": document_role,
        "layout_type": "fixed" if active_template else "free",
    }
    if document_role == "question_paper":
        question_records = export_result.get("questions") or [_question_record(item) for item in export_result.get("question_level_results", [])]
        output["questions"] = question_records
    else:
        output["answers"] = export_result.get("answers", [])
    if active_template:
        output["template_id"] = active_template["template_id"]
        output["template_name"] = active_template.get("template_name", active_template["template_id"])
        output["template_version"] = active_template["version"]
    if include_intermediate:
        output["normalized_pages"] = a_result["normalized_pages"]
        output["ocr_page_results"] = a_result["ocr_page_results"]
        output["b_result"] = b_result
    final_output = relativize_paths_in_data(output)
    redacted_output = redact_and_record(final_output, submission_id)
    if document_role == "question_paper" and exam_id:
        save_exam_questions(exam_id, redacted_output["questions"], submission_id)
    if document_role == "answer_sheet" and exam_id and active_template:
        record_answer_sheet_submission(exam_id, submission_id, active_template)
    return save_result(submission_id, fingerprint, redacted_output)


def _processing_fingerprint(
    document_role: str,
    exam_id: Optional[str],
    template: Optional[dict[str, Any]],
    source_path: Optional[Union[str, Path]],
    file_bytes: Optional[bytes],
    mime_type: str,
    assignment_type: str,
    question_regions: list[dict[str, Any]],
    review_results: list[dict[str, Any]],
    llm_enabled: bool,
    include_intermediate: bool,
) -> dict[str, Any]:
    if file_bytes is not None:
        source_bytes = file_bytes
    elif source_path is not None:
        source_bytes = None
    else:
        raise ValueError("source_path or file_bytes is required for processing")
    return {
        "document_role": document_role,
        "exam_id": str(exam_id) if exam_id is not None else None,
        "template_id": template.get("template_id") if template else None,
        "template_version": template.get("version") if template else None,
        "file_sha256": hashlib.sha256(source_bytes).hexdigest() if source_bytes is not None else _file_sha256(Path(source_path)),
        "mime_type": mime_type,
        "assignment_type": assignment_type,
        "template_sha256": _structured_sha256(_template_fingerprint_payload(template)) if template else None,
        "question_regions_sha256": _structured_sha256(question_regions),
        "review_results_sha256": _structured_sha256(review_results),
        "llm_enabled": bool(llm_enabled),
        "include_intermediate": bool(include_intermediate),
    }


def _structured_sha256(value: Any) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _template_fingerprint_payload(template: dict[str, Any]) -> dict[str, Any]:
    """Exclude runtime-only template resolution details from idempotency checks."""
    payload = dict(template)
    payload.pop("_template_dir", None)
    return payload


def _flatten_template_regions(template: dict[str, Any]) -> list[dict[str, Any]]:
    """Provide the legacy uniform-route handoff alongside the full template."""
    regions: list[dict[str, Any]] = []
    for page in template.get("pages", []):
        for region in page.get("regions", []):
            if region.get("content_type", "answer") != "answer":
                continue
            regions.append({
                "question_id": region["question_id"],
                "question_no": region["question_no"],
                "page_no": page["page_no"],
                "order": region["order"],
                "bbox": region["bbox"],
                "region_confidence": 1.0,
            })
    return regions


def _question_record(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": item.get("question_id", item["question_no"]),
        "question_no": item["question_no"],
        "question_text": item.get("final_text", ""),
        "page_nos": item.get("page_nos", []),
        "confidence": item.get("confidence", 0.0),
        "needs_review": item.get("needs_review", False),
        "risk_flags": item.get("risk_flags", []),
    }
