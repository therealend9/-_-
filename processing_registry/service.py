from __future__ import annotations

"""Filesystem-backed persistence for final document-processing results."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any


RESULT_ROOT = Path(os.getenv("EXAM_PROCESSING_RESULT_ROOT", "storage/processing_results"))
RESULT_INDEX_FILE = RESULT_ROOT / "index.json"


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


def _load_index() -> dict[str, dict[str, Any]]:
    if not RESULT_INDEX_FILE.is_file():
        return {}
    data = json.loads(RESULT_INDEX_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("processing result index must be an object")
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
