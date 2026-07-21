from __future__ import annotations

"""Filesystem-backed persistence for final document-processing results."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


RESULT_ROOT = Path(os.getenv("EXAM_PROCESSING_RESULT_ROOT", "storage/processing_results"))
RESULT_INDEX_FILE = RESULT_ROOT / "index.json"
REGISTRY_ROOT = Path(os.getenv("EXAM_PROCESSING_REGISTRY_ROOT", "storage/processing_registry"))
TASK_INDEX_FILE = REGISTRY_ROOT / "tasks.json"
ANSWER_INDEX_FILE = REGISTRY_ROOT / "answers.json"
REVIEW_INDEX_FILE = REGISTRY_ROOT / "reviews.json"


def get_cached_result(submission_id: str, fingerprint: dict[str, Any]) -> dict[str, Any] | None:
    """Return an idempotent result or reject reuse with different input."""
    records = _load_index()
    existing = records.get(str(submission_id))
    if existing is None:
        return None
    if existing.get("fingerprint") != fingerprint:
        raise ValueError("submission_id is already associated with a different processing request")
    return _read_result(existing)


def save_result(submission_id: str, fingerprint: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    """Persist a final response and make retries return the same response."""
    key = str(submission_id)
    records = _load_index()
    existing = records.get(key)
    if existing is not None:
        if existing.get("fingerprint") != fingerprint:
            raise ValueError("submission_id is already associated with a different processing request")
        return _read_result(existing)

    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    result_file = f"{hashlib.sha256(key.encode('utf-8')).hexdigest()}.json"
    result_path = RESULT_ROOT / result_file
    _write_json_atomic(result_path, result)
    records[key] = {
        "submission_id": key,
        "fingerprint": fingerprint,
        "result_file": result_file,
    }
    _write_json_atomic(RESULT_INDEX_FILE, records)
    return result


def get_result(submission_id: str) -> dict[str, Any]:
    """Read a previously persisted final response by submission ID."""
    record = _load_index().get(str(submission_id))
    if record is None:
        raise FileNotFoundError(f"Processing result not found: {submission_id}")
    return _read_result(record)


def start_task(submission_id: str, context: dict[str, Any]) -> dict[str, Any]:
    """Create or resume an internal processing task without changing public output."""
    key = str(submission_id)
    records = _load_registry(TASK_INDEX_FILE, "task registry")
    existing = records.get(key)
    if existing and existing.get("status") in {"completed", "needs_review"}:
        return dict(existing)

    now = _now()
    record = {
        "task_id": _task_id(key),
        "submission_id": key,
        "document_role": context.get("document_role"),
        "exam_id": context.get("exam_id"),
        "template_id": context.get("template_id"),
        "template_version": context.get("template_version"),
        "status": "processing",
        "output_count": 0,
        "needs_review_count": 0,
        "failed_count": 0,
        "error_code": None,
        "error_message": None,
        "created_at": existing.get("created_at", now) if existing else now,
        "updated_at": now,
    }
    records[key] = record
    _write_json_atomic(TASK_INDEX_FILE, records)
    return dict(record)


def mark_task_failed(submission_id: str, error_code: str, error_message: str) -> dict[str, Any]:
    """Persist a safe task failure summary for later teacher-facing queries."""
    key = str(submission_id)
    records = _load_registry(TASK_INDEX_FILE, "task registry")
    existing = records.get(key) or {
        "task_id": _task_id(key),
        "submission_id": key,
        "document_role": None,
        "exam_id": None,
        "template_id": None,
        "template_version": None,
        "output_count": 0,
        "needs_review_count": 0,
        "created_at": _now(),
    }
    existing.update({
        "status": "failed",
        "failed_count": 1,
        "error_code": str(error_code),
        "error_message": str(error_message),
        "updated_at": _now(),
    })
    records[key] = existing
    _write_json_atomic(TASK_INDEX_FILE, records)
    return dict(existing)


def finalize_submission(
    submission_id: str,
    result: dict[str, Any],
    review_records: Iterable[dict[str, Any]] | None = None,
    identity_needs_review: bool = False,
) -> dict[str, Any]:
    """Save internal answer/review summaries after a successful pipeline run.

    The public ``exam-document.v1`` response is deliberately stored unchanged.
    Identity values are never accepted here, preventing accidental exposure via
    the answer and review query routes.
    """
    key = str(submission_id)
    output_key = "answers" if result.get("document_role") == "answer_sheet" else "questions"
    outputs = list(result.get(output_key) or [])
    answer_records = _build_answer_records(key, result, outputs, output_key)
    answers = _load_registry(ANSWER_INDEX_FILE, "answer registry")
    answers[key] = answer_records
    _write_json_atomic(ANSWER_INDEX_FILE, answers)

    normalized_reviews = _normalize_review_records(key, review_records or [])
    if normalized_reviews:
        reviews = _load_registry(REVIEW_INDEX_FILE, "review registry")
        reviews[key] = normalized_reviews
        _write_json_atomic(REVIEW_INDEX_FILE, reviews)

    records = _load_registry(TASK_INDEX_FILE, "task registry")
    existing = records.get(key) or start_task(key, result)
    needs_review_count = sum(1 for item in outputs if item.get("needs_review"))
    task_needs_review = needs_review_count > 0 or bool(identity_needs_review)
    existing.update({
        "document_role": result.get("document_role"),
        "exam_id": result.get("exam_id"),
        "template_id": result.get("template_id"),
        "template_version": result.get("template_version"),
        "status": "needs_review" if task_needs_review else "completed",
        "output_count": len(outputs),
        "needs_review_count": needs_review_count + int(bool(identity_needs_review)),
        "failed_count": 0,
        "error_code": None,
        "error_message": None,
        "updated_at": _now(),
    })
    records[key] = existing
    _write_json_atomic(TASK_INDEX_FILE, records)
    return dict(existing)


def ensure_task_from_result(submission_id: str, result: dict[str, Any]) -> dict[str, Any]:
    """Backfill task metadata for results created before task tracking existed."""
    key = str(submission_id)
    records = _load_registry(TASK_INDEX_FILE, "task registry")
    existing = records.get(key)
    if existing and existing.get("status") in {"completed", "needs_review"}:
        return dict(existing)
    return finalize_submission(key, result)


def get_task(submission_id: str) -> dict[str, Any]:
    record = _load_registry(TASK_INDEX_FILE, "task registry").get(str(submission_id))
    if record is None:
        raise FileNotFoundError(f"Processing task not found: {submission_id}")
    return dict(record)


def get_answer_records(submission_id: str) -> list[dict[str, Any]]:
    records = _load_registry(ANSWER_INDEX_FILE, "answer registry").get(str(submission_id))
    if records is None:
        raise FileNotFoundError(f"Answer records not found: {submission_id}")
    return [dict(item) for item in records]


def get_review_records(submission_id: str) -> list[dict[str, Any]]:
    records = _load_registry(REVIEW_INDEX_FILE, "review registry").get(str(submission_id), [])
    return [dict(item) for item in records]


def _load_index() -> dict[str, dict[str, Any]]:
    if not RESULT_INDEX_FILE.is_file():
        return {}
    data = json.loads(RESULT_INDEX_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("processing result index must be an object")
    return data


def _load_registry(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")
    return data


def _read_result(record: dict[str, Any]) -> dict[str, Any]:
    result_file = record.get("result_file")
    if not result_file:
        raise ValueError("Processing result record is missing result_file")
    path = RESULT_ROOT / str(result_file)
    if not path.is_file():
        raise FileNotFoundError(f"Persisted processing result is missing: {record.get('submission_id')}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Persisted processing result must be an object")
    return data


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _build_answer_records(
    submission_id: str,
    result: dict[str, Any],
    outputs: list[dict[str, Any]],
    output_key: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    text_key = "answer_text" if output_key == "answers" else "question_text"
    for item in outputs:
        records.append({
            "submission_id": submission_id,
            "exam_id": result.get("exam_id"),
            "question_id": item.get("question_id"),
            "question_no": item.get("question_no"),
            "content_type": "answer" if output_key == "answers" else "question",
            "content_text": item.get(text_key, ""),
            "is_blank": item.get("is_blank") if output_key == "answers" else None,
            "page_nos": list(item.get("page_nos") or []),
            "confidence": item.get("confidence", 0.0),
            "needs_review": bool(item.get("needs_review", False)),
            "risk_flags": list(item.get("risk_flags") or []),
        })
    return records


def _normalize_review_records(submission_id: str, reviews: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in reviews:
        normalized.append({
            "submission_id": submission_id,
            "review_id": item.get("review_id"),
            "question_id": item.get("question_id"),
            "question_no": item.get("question_no"),
            "merge_group_id": item.get("merge_group_id"),
            "before_text": item.get("before_text", ""),
            "after_text": item.get("after_text", ""),
            "review_reason": item.get("review_reason"),
            "review_time": item.get("review_time"),
        })
    return normalized


def _task_id(submission_id: str) -> str:
    return f"task_{hashlib.sha256(submission_id.encode('utf-8')).hexdigest()[:16]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
