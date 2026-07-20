from __future__ import annotations

"""Conservative, local-only redaction for final document-processing results.

This module does not identify students. It only removes data that has a
high-confidence format or an explicit label in an already-recognized result.
The audit output contains metadata and hashes only, never source OCR text.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REDACTION_VERSION = "data-redaction.v1"
REDACTION_ROOT = Path(os.getenv("EXAM_PROCESSING_REDACTION_ROOT", "storage/redaction"))

# OCR segmentation can concatenate an email and the following Chinese label.
# Python's Unicode ``\b`` treats Chinese characters as word characters, so use
# explicit ASCII email boundaries instead of a generic Unicode word boundary.
_EMAIL_RE = re.compile(
    r"(?i)(?<![A-Z0-9._%+\-])[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}(?![A-Z0-9._%+\-])"
)
_PHONE_RE = re.compile(r"(?<!\d)1[3-9](?:[ -]?\d){9}(?!\d)")
_ID_CARD_RE = re.compile(r"(?<!\d)(?:\d{17}[\dXx]|\d{15})(?!\d)")
_NAME_LABEL_RE = re.compile(
    r"(?P<label>\u59d3\u540d|\u5b66\u751f\u59d3\u540d)\s*[:\uff1a]\s*"
    r"(?P<value>[\u4e00-\u9fff]{2,4})"
)
_STUDENT_NO_LABEL_RE = re.compile(
    r"(?P<label>\u5b66\u53f7|\u5b66\u751f\u7f16\u53f7|student[ _-]*id)\s*[:\uff1a]\s*"
    r"(?P<value>[A-Za-z0-9][A-Za-z0-9-]{3,23})",
    re.IGNORECASE,
)
_ID_LABEL_RE = re.compile(
    r"(?P<label>\u8eab\u4efd\u8bc1(?:\u53f7|\u53f7\u7801)?)\s*[:\uff1a]\s*"
    r"(?P<value>[0-9Xx -]{15,22})"
)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b\u200c\u200d\ufeff\u202a-\u202e]")
_ABSOLUTE_PATH_RE = re.compile(r"(?i)^(?:[A-Z]:[\\/]|\\\\|/).*")
_SENSITIVE_KEY_RE = re.compile(
    r"(?i)^(?:student[_-]?(?:name|no|id)|phone|mobile|email|id[_-]?card|"
    r"origin[_-]?name|original[_-]?filename|source[_-]?filename|filename)$"
)
_PATH_KEY_RE = re.compile(r"(?i)(?:path|directory|dir)$")


def redact_result(result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create a redacted copy without changing the result's JSON shape."""
    if not isinstance(result, dict):
        raise TypeError("processing result must be an object")

    categories: set[str] = set()
    count = 0

    def visit(value: Any, key: str | None = None, field_path: str = "$") -> Any:
        nonlocal count
        if isinstance(value, dict):
            return {
                item_key: visit(item_value, str(item_key), f"{field_path}.{item_key}")
                for item_key, item_value in value.items()
            }
        if isinstance(value, list):
            return [visit(item, None, f"{field_path}[{index}]") for index, item in enumerate(value)]
        if isinstance(value, str):
            replacement, matched_categories = _redact_string(value, key)
            if replacement != value:
                count += 1
                categories.update(matched_categories)
            return replacement
        if value is None or isinstance(value, (bool, int, float)):
            return value
        raise TypeError(f"unsupported result value at {field_path}: {type(value).__name__}")

    redacted = visit(result)
    report = {
        "submission_id": str(result.get("submission_id", "")),
        "redaction_version": REDACTION_VERSION,
        "redaction_status": "redacted" if count else "clean",
        "redacted_fields": sorted(categories),
        "redaction_count": count,
        "source_result_sha256": _sha256_json(result),
        "redacted_result_sha256": _sha256_json(redacted),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return redacted, report


def redact_and_record(result: dict[str, Any], submission_id: str) -> dict[str, Any]:
    """Redact before persistence and record metadata-only audit evidence."""
    redacted, report = redact_result(result)
    report["submission_id"] = str(submission_id)
    _write_report(str(submission_id), report)
    return redacted


def _redact_string(value: str, key: str | None) -> tuple[str, set[str]]:
    key_text = key or ""
    if _SENSITIVE_KEY_RE.match(key_text):
        return "[REDACTED]", {_key_category(key_text)}
    if _PATH_KEY_RE.search(key_text) or _ABSOLUTE_PATH_RE.match(value.strip()):
        return "[PATH_REDACTED]", {"path"}

    categories: set[str] = set()
    text = _CONTROL_RE.sub("", value)
    if text != value:
        categories.add("control_character")

    text, replaced = _replace_labeled(text, _ID_LABEL_RE, "id_card")
    if replaced:
        categories.add("id_card")
    text, replaced = _replace_labeled(text, _NAME_LABEL_RE, "student_name")
    if replaced:
        categories.add("student_name")
    text, replaced = _replace_labeled(text, _STUDENT_NO_LABEL_RE, "student_number")
    if replaced:
        categories.add("student_number")

    text, replacements = _EMAIL_RE.subn("[EMAIL_REDACTED]", text)
    if replacements:
        categories.add("email")
    text, replacements = _PHONE_RE.subn("[PHONE_REDACTED]", text)
    if replacements:
        categories.add("phone")
    text, replacements = _ID_CARD_RE.subn(_replace_id_card, text)
    if replacements:
        categories.add("id_card")
    return text, categories


def _replace_labeled(text: str, pattern: re.Pattern[str], _category: str) -> tuple[str, int]:
    return pattern.subn(lambda match: f"{match.group('label')}:[REDACTED]", text)


def _replace_id_card(match: re.Match[str]) -> str:
    value = match.group(0)
    if len(value) == 18 and _is_valid_id_card(value):
        return "[ID_CARD_REDACTED]"
    if len(value) == 15:
        return "[ID_CARD_REDACTED]"
    return value


def _is_valid_id_card(value: str) -> bool:
    if not re.fullmatch(r"\d{17}[\dXx]", value):
        return False
    weights = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
    checks = "10X98765432"
    checksum = sum(int(item) * weight for item, weight in zip(value[:17], weights)) % 11
    return checks[checksum] == value[-1].upper()


def _key_category(key: str) -> str:
    lowered = key.lower()
    if "name" in lowered:
        return "filename" if "origin" in lowered or "file" in lowered else "student_name"
    if "email" in lowered:
        return "email"
    if "phone" in lowered or "mobile" in lowered:
        return "phone"
    if "student" in lowered:
        return "student_number"
    return "id_card"


def _sha256_json(value: Any) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _write_report(submission_id: str, report: dict[str, Any]) -> None:
    if not submission_id:
        raise ValueError("submission_id is required for redaction audit")
    REDACTION_ROOT.mkdir(parents=True, exist_ok=True)
    report_name = f"{hashlib.sha256(submission_id.encode('utf-8')).hexdigest()}.json"
    destination = REDACTION_ROOT / report_name
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(destination)
