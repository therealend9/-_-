"""Persistent answer-sheet template and exam binding helpers."""

from template_registry.service import (
    TemplateNotBoundError,
    bind_exam_template,
    create_exam,
    get_exam,
    get_exam_questions,
    list_exams,
    get_exam_template,
    get_answer_sheet_submission,
    get_template,
    publish_template,
    review_template,
    record_answer_sheet_submission,
    save_exam_questions,
    save_template,
    set_exam_status,
    validate_template,
)

__all__ = [
    "TemplateNotBoundError",
    "bind_exam_template",
    "create_exam",
    "get_exam",
    "get_exam_questions",
    "list_exams",
    "get_exam_template",
    "get_answer_sheet_submission",
    "get_template",
    "publish_template",
    "review_template",
    "record_answer_sheet_submission",
    "save_exam_questions",
    "save_template",
    "set_exam_status",
    "validate_template",
]
