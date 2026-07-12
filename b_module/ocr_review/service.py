from __future__ import annotations

from typing import Optional

from datetime import datetime, timezone

from b_module.schemas.types import ReviewResult


def submit_ocr_review(
    file_id: str,
    question_no: str,
    raw_text: str,
    corrected_text: str,
    operator_id: str,
    merge_group_id: Optional[str] = None,
    review_reason: Optional[str] = None,
    review_id: Optional[str] = None,
    review_time: Optional[str] = None,
) -> ReviewResult:
    """Create a persisted-style OCR review record."""
    resolved_review_id = review_id or _generate_review_id(file_id, merge_group_id or question_no)
    resolved_review_time = review_time or datetime.now(timezone.utc).astimezone().isoformat()
    result: ReviewResult = {
        "review_id": resolved_review_id,
        "file_id": file_id,
        "question_no": question_no,
        "before_text": raw_text,
        "after_text": corrected_text,
        "operator_id": operator_id,
        "review_time": resolved_review_time,
    }
    if merge_group_id:
        result["merge_group_id"] = merge_group_id
    if review_reason:
        result["review_reason"] = review_reason
    return result


def _generate_review_id(file_id: str, identity: str) -> str:
    compact_file_id = file_id.replace("-", "_")
    compact_identity = identity.replace("-", "_").replace(" ", "_")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"rv_{compact_file_id}_{compact_identity}_{timestamp}"
