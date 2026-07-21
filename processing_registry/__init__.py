"""Persistent processing-result and internal task helpers."""

from processing_registry.service import (
    ensure_task_from_result,
    finalize_submission,
    get_answer_records,
    get_cached_result,
    get_result,
    get_review_records,
    get_task,
    mark_task_failed,
    save_result,
    start_task,
)

__all__ = [
    "ensure_task_from_result",
    "finalize_submission",
    "get_answer_records",
    "get_cached_result",
    "get_result",
    "get_review_records",
    "get_task",
    "mark_task_failed",
    "save_result",
    "start_task",
]
