from __future__ import annotations

"""Filesystem-backed registry for fixed-layout answer-sheet templates.

The registry deliberately keeps the exam-to-template relationship separate from
student submissions. A caller supplies an ``exam_id``; the template is resolved
server-side so a submission cannot select an unrelated layout.
"""

import json
import os
from pathlib import Path
from typing import Any


TEMPLATE_ROOT = Path(os.getenv("ANSWER_SHEET_TEMPLATE_ROOT", "storage/templates"))
EXAM_BINDING_FILE = TEMPLATE_ROOT / "exam_bindings.json"
EXAMS_FILE = TEMPLATE_ROOT / "exams.json"
SUBMISSIONS_FILE = TEMPLATE_ROOT / "answer_sheet_submissions.json"
QUESTION_CONTENT_TYPES = {"question", "answer"}
IDENTITY_CONTENT_TYPES = {"student_name", "student_no", "major", "college", "grade"}
REQUIRED_IDENTITY_CONTENT_TYPES = {"student_name", "student_no"}
ALL_CONTENT_TYPES = QUESTION_CONTENT_TYPES | IDENTITY_CONTENT_TYPES


class TemplateNotBoundError(LookupError):
    """Raised when an exam has no published answer-sheet template."""


def create_exam(exam_id: str, exam_name: str, status: str = "draft") -> dict[str, Any]:
    """Create an exam record independent of its later template binding."""
    if not exam_id or not str(exam_id).strip():
        raise ValueError("exam_id is required")
    if not exam_name or not str(exam_name).strip():
        raise ValueError("exam_name is required")
    if status not in {"draft", "published"}:
        raise ValueError("exam status must be draft or published")
    TEMPLATE_ROOT.mkdir(parents=True, exist_ok=True)
    exams = _load_exams()
    key = str(exam_id)
    if key in exams:
        raise ValueError(f"Exam already exists: {exam_id}")
    record = {
        "exam_id": key,
        "exam_name": str(exam_name),
        "status": status,
        "template_id": None,
        "questions": [],
        "question_catalog_version": 0,
    }
    exams[key] = record
    _write_json(EXAMS_FILE, exams)
    return record


def get_exam(exam_id: str) -> dict[str, Any]:
    exam = _load_exams().get(str(exam_id))
    if not exam:
        raise FileNotFoundError(f"Exam not found: {exam_id}")
    return _enrich_exam(exam)


def list_exams() -> list[dict[str, Any]]:
    exams = sorted(_load_exams().values(), key=lambda item: str(item["exam_name"]))
    return [_enrich_exam(item) for item in exams]


def save_exam_questions(exam_id: str, questions: list[dict[str, Any]], source_submission_id: str) -> dict[str, Any]:
    """Save the canonical question catalog produced from the question paper."""
    exams = _load_exams()
    key = str(exam_id)
    if key not in exams:
        raise FileNotFoundError(f"Exam not found: {exam_id}")
    normalized = _normalize_question_catalog(questions)
    if not normalized:
        raise ValueError("Question paper did not produce any questions")
    exam = exams[key]
    # Once an answer-sheet template is bound, its regions are the source used
    # for final answers. Do not let a later question-paper upload silently
    # replace the catalog with IDs that no longer match those regions.
    if exam.get("template_id"):
        _validate_template_question_ids(get_template(exam["template_id"]), normalized)
        existing_questions = list(exam.get("questions") or [])
        if existing_questions and existing_questions != normalized:
            raise ValueError("Question catalog is frozen after an answer-sheet template is bound")
        if existing_questions == normalized:
            return _enrich_exam(exam)
    exam["questions"] = normalized
    exam["question_catalog_source_submission_id"] = str(source_submission_id)
    exam["question_catalog_version"] = int(exam.get("question_catalog_version", 0)) + 1
    _write_json(EXAMS_FILE, exams)
    return _enrich_exam(exam)


def get_exam_questions(exam_id: str) -> list[dict[str, Any]]:
    exam = _load_exams().get(str(exam_id))
    if not exam:
        raise FileNotFoundError(f"Exam not found: {exam_id}")
    return list(exam.get("questions") or [])


def set_exam_status(exam_id: str, status: str) -> dict[str, Any]:
    """Change the lifecycle state used to control template binding."""
    if status not in {"draft", "published"}:
        raise ValueError("exam status must be draft or published")
    exams = _load_exams()
    key = str(exam_id)
    if key not in exams:
        raise FileNotFoundError(f"Exam not found: {exam_id}")
    if status == "published" and not exams[key].get("template_id"):
        raise ValueError("Exam must bind a template before it can be published")
    exams[key]["status"] = status
    _write_json(EXAMS_FILE, exams)
    return _enrich_exam(exams[key])


def record_answer_sheet_submission(
    exam_id: str,
    submission_id: str,
    template: dict[str, Any],
    identity_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a successful answer-sheet submission for template-change guards."""
    if not submission_id:
        raise ValueError("submission_id is required")
    exams = _load_exams()
    key = str(exam_id)
    if key not in exams:
        raise FileNotFoundError(f"Exam not found: {exam_id}")
    expected_template_id = exams[key].get("template_id")
    if expected_template_id != template.get("template_id"):
        raise ValueError("Submission template does not match the exam binding")
    submissions = _load_submissions()
    submission_key = str(submission_id)
    record = {
        "submission_id": submission_key,
        "exam_id": key,
        "template_id": expected_template_id,
        "template_version": int(template["version"]),
    }
    if identity_fields is not None:
        record["identity_fields"] = identity_fields
    existing = submissions.get(submission_key)
    if existing and existing != record:
        raise ValueError(f"submission_id is already associated with another exam or template: {submission_id}")
    submissions[submission_key] = record
    _write_json(SUBMISSIONS_FILE, submissions)
    return record


def get_answer_sheet_submission(submission_id: str) -> dict[str, Any]:
    """Return the protected internal binding record for a submission."""
    record = _load_submissions().get(str(submission_id))
    if not record:
        raise FileNotFoundError(f"Answer-sheet submission not found: {submission_id}")
    return dict(record)


def _enrich_exam(exam: dict[str, Any]) -> dict[str, Any]:
    result = dict(exam)
    template_id = result.get("template_id")
    if template_id:
        try:
            template = get_template(template_id)
            result["template_name"] = template.get("template_name", template_id)
            result["template_version"] = template.get("version")
            result["template_status"] = template.get("status")
        except FileNotFoundError:
            result["template_status"] = "missing"
    else:
        result.setdefault("template_name", None)
        result.setdefault("template_status", None)
    return result


def _normalize_question_catalog(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(questions, start=1):
        question_id = str(item.get("question_id") or "").strip()
        question_no = str(item.get("question_no") or question_id).strip()
        question_text = str(item.get("question_text") or "").strip()
        if not question_id or not question_no or not question_text:
            raise ValueError("Each question requires question_id, question_no, and question_text")
        if question_id in seen:
            raise ValueError(f"Duplicate question_id: {question_id}")
        seen.add(question_id)
        normalized.append({
            "question_id": question_id,
            "question_no": question_no,
            "question_text": question_text,
            "order": index,
        })
    return normalized


def save_template(template: dict[str, Any]) -> dict[str, Any]:
    """Validate and persist a versioned template under its template ID."""
    normalized = validate_template(template)
    path = TEMPLATE_ROOT / normalized["template_id"] / "template.json"
    if path.is_file():
        persisted = validate_template(json.loads(path.read_text(encoding="utf-8")))
        if persisted.get("status") == "published" and persisted != normalized:
            raise ValueError("Published template is immutable; create a new template_id for changes")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized


def get_template(template_id: str) -> dict[str, Any]:
    path = TEMPLATE_ROOT / str(template_id) / "template.json"
    if not path.is_file():
        raise FileNotFoundError(f"Answer-sheet template not found: {template_id}")
    template = json.loads(path.read_text(encoding="utf-8"))
    template = validate_template(template)
    template["_template_dir"] = str(path.parent)
    return template


def bind_exam_template(exam_id: str, template_id: str, status: str = "published") -> dict[str, Any]:
    """Bind an immutable template version to an exam identifier."""
    if not exam_id:
        raise ValueError("exam_id is required")
    exams = _load_exams()
    key = str(exam_id)
    if key not in exams:
        raise FileNotFoundError(f"Exam not found: {exam_id}")
    exam = exams[key]
    if exam.get("status") != "draft":
        raise ValueError(f"Exam status does not allow template binding: {exam.get('status')}")
    template = get_template(template_id)
    if template.get("status") != "published":
        raise ValueError(f"Template must be published before binding: {template_id}")
    if "version" not in template or template.get("version") is None:
        raise ValueError("Template version must be explicit before binding")
    _validate_template_question_ids(template, list(exam.get("questions") or []))
    current_template_id = exam.get("template_id")
    if current_template_id and current_template_id != template["template_id"] and _has_answer_sheet_submissions(key):
        raise ValueError("Cannot change the template after answer-sheet submissions exist")
    TEMPLATE_ROOT.mkdir(parents=True, exist_ok=True)
    bindings = _load_bindings()
    record = {
        "exam_id": str(exam_id),
        "template_id": template["template_id"],
        "template_name": template.get("template_name", template["template_id"]),
        "template_version": template["version"],
        "status": status,
    }
    bindings[str(exam_id)] = record
    _write_json(EXAM_BINDING_FILE, bindings)
    exam["template_id"] = template["template_id"]
    exam["template_name"] = template.get("template_name", template["template_id"])
    exam["template_version"] = template["version"]
    _write_json(EXAMS_FILE, exams)
    return record


def get_exam_template(exam_id: str) -> dict[str, Any]:
    binding = _load_bindings().get(str(exam_id))
    if not binding or not binding.get("template_id"):
        raise TemplateNotBoundError(f"TEMPLATE_NOT_BOUND: {exam_id}")
    if binding.get("status") not in {None, "published"}:
        raise TemplateNotBoundError(f"TEMPLATE_NOT_BOUND: {exam_id}")
    template = get_template(binding["template_id"])
    if int(binding.get("template_version", template["version"])) != int(template["version"]):
        raise ValueError(f"Template version mismatch for exam: {exam_id}")
    return template


def validate_template(template: dict[str, Any]) -> dict[str, Any]:
    """Validate the portable template JSON schema used by the fixed route."""
    if not isinstance(template, dict):
        raise ValueError("template must be an object")
    result = dict(template)
    result.pop("_template_dir", None)
    template_id = str(result.get("template_id") or "").strip()
    if not template_id:
        raise ValueError("template_id is required")
    result["template_id"] = template_id
    if "version" not in result or result.get("version") is None:
        raise ValueError("template.version is required")
    result["version"] = int(result["version"])
    if result["version"] < 1:
        raise ValueError("template.version must be a positive integer")
    status = str(result.get("status", "draft"))
    if status not in {"draft", "pending_review", "published"}:
        raise ValueError("template.status must be draft, pending_review, or published")
    result["status"] = status
    pages = result.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("template.pages must be a non-empty list")
    if result.get("page_count") not in (None, len(pages)):
        raise ValueError("template.page_count does not match pages")
    result["page_count"] = len(pages)

    seen_pages: set[int] = set()
    seen_region_orders: set[tuple[str, str, int]] = set()
    normalized_pages: list[dict[str, Any]] = []
    for page in pages:
        item = dict(page)
        page_no = int(item.get("page_no", 0))
        if page_no < 1 or page_no in seen_pages:
            raise ValueError("template page_no values must be unique positive integers")
        seen_pages.add(page_no)
        width, height = int(item.get("reference_width", 0)), int(item.get("reference_height", 0))
        if width <= 0 or height <= 0:
            raise ValueError(f"template page {page_no} requires positive reference_width/reference_height")
        regions = item.get("regions")
        if not isinstance(regions, list):
            raise ValueError(f"template page {page_no}.regions must be a list")
        normalized_regions: list[dict[str, Any]] = []
        for region in regions:
            region_item = dict(region)
            ocr_mode = str(region_item.get("ocr_mode", "handwriting"))
            content_type = str(region_item.get("content_type") or ("answer" if ocr_mode == "handwriting" else "question"))
            if content_type not in ALL_CONTENT_TYPES:
                raise ValueError(
                    "region.content_type must be question, answer, student_name, student_no, major, college, or grade"
                )
            bbox = region_item.get("bbox")
            if not isinstance(bbox, list) or len(bbox) != 4:
                raise ValueError("region.bbox must be [x1, y1, x2, y2]")
            bbox = [float(value) for value in bbox]
            coordinate_type = str(region_item.get("coordinate_type", "normalized"))
            if coordinate_type != "normalized":
                raise ValueError("only normalized template bbox coordinates are supported")
            if not (0 <= bbox[0] < bbox[2] <= 1 and 0 <= bbox[1] < bbox[3] <= 1):
                raise ValueError("normalized region.bbox must be inside page bounds")
            if content_type in QUESTION_CONTENT_TYPES:
                question_id = str(region_item.get("question_id") or region_item.get("question_no") or "").strip()
                question_no = str(region_item.get("question_no") or question_id).strip()
                if not question_id or not question_no:
                    raise ValueError("question/answer regions require question_id and question_no")
                order = int(region_item.get("order", 1))
                key = (content_type, question_id, order)
                if key in seen_region_orders:
                    raise ValueError(f"duplicate region order for question_id={question_id}")
                seen_region_orders.add(key)
                region_item.update({"question_id": question_id, "question_no": question_no, "order": order})
            else:
                region_item.pop("question_id", None)
                region_item.pop("question_no", None)
                region_item.pop("order", None)
                ocr_mode = "excluded"
            region_item.update({
                "bbox": bbox,
                "coordinate_type": coordinate_type,
                "ocr_mode": ocr_mode,
                "content_type": content_type,
            })
            normalized_regions.append(region_item)
        item.update({"page_no": page_no, "reference_width": width, "reference_height": height, "regions": normalized_regions})
        normalized_pages.append(item)
    result["pages"] = sorted(normalized_pages, key=lambda value: value["page_no"])
    _normalize_identity_protection(result)
    _validate_identity_region_geometry(result)
    return result


def review_template(template_id: str, pages: list[dict[str, Any]], publish: bool = False) -> dict[str, Any]:
    """Persist a reviewer-edited page/region proposal.

    The caller sends the full reviewed pages payload after moving, deleting, or
    adding candidate boxes in the template editor. Publishing is explicit so a
    draft can never silently become available to student submissions.
    """
    template = get_template(template_id)
    if template.get("status") == "published":
        raise ValueError("Published template is immutable; create a new template_id for changes")
    template.pop("_template_dir", None)
    template["pages"] = pages
    template["page_count"] = len(pages)
    template["status"] = "pending_review"
    if template.get("identity_protection", {}).get("required"):
        template["identity_protection"]["status"] = "pending_review"
    saved = save_template(template)
    return publish_template(template_id) if publish else saved


def publish_template(template_id: str) -> dict[str, Any]:
    """Publish a reviewed template without modifying its regions."""
    template = get_template(template_id)
    template.pop("_template_dir", None)
    pending_regions = _pending_regions(template)
    if pending_regions:
        raise ValueError(f"Template has {len(pending_regions)} unreviewed region(s)")
    _validate_required_identity_regions(template)
    if template.get("identity_protection", {}).get("required"):
        template["identity_protection"]["status"] = "confirmed"
    template["status"] = "published"
    return save_template(template)


def _load_bindings() -> dict[str, dict[str, Any]]:
    if not EXAM_BINDING_FILE.is_file():
        return {}
    data = json.loads(EXAM_BINDING_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("exam_bindings.json must be an object")
    return data


def _load_exams() -> dict[str, dict[str, Any]]:
    if not EXAMS_FILE.is_file():
        return {}
    data = json.loads(EXAMS_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("exams.json must be an object")
    return data


def _load_submissions() -> dict[str, dict[str, Any]]:
    if not SUBMISSIONS_FILE.is_file():
        return {}
    data = json.loads(SUBMISSIONS_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("answer_sheet_submissions.json must be an object")
    return data


def _has_answer_sheet_submissions(exam_id: str) -> bool:
    return any(record.get("exam_id") == str(exam_id) for record in _load_submissions().values())


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _pending_regions(template: dict[str, Any]) -> list[dict[str, Any]]:
    regions = [region for page in template["pages"] for region in page["regions"]]
    if not regions:
        raise ValueError("Template must contain at least one region before publishing")
    return [region for region in regions if region.get("needs_review", False)]


def _normalize_identity_protection(template: dict[str, Any]) -> None:
    config = template.get("identity_protection")
    if config is None:
        return
    if not isinstance(config, dict):
        raise ValueError("identity_protection must be an object")
    required = config.get("required", False)
    if not isinstance(required, bool):
        raise ValueError("identity_protection.required must be boolean")
    status = str(config.get("status", "pending_review" if required else "not_required"))
    if status not in {"pending_review", "confirmed", "not_required"}:
        raise ValueError("identity_protection.status is invalid")
    template["identity_protection"] = {"required": required, "status": status}


def _identity_regions(template: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        region
        for page in template["pages"]
        for region in page["regions"]
        if region.get("content_type") in IDENTITY_CONTENT_TYPES
    ]


def _validate_required_identity_regions(template: dict[str, Any]) -> None:
    if not template.get("identity_protection", {}).get("required"):
        return
    regions = _identity_regions(template)
    for content_type in sorted(REQUIRED_IDENTITY_CONTENT_TYPES):
        matches = [region for region in regions if region["content_type"] == content_type]
        if len(matches) != 1:
            raise ValueError(f"Template requires exactly one {content_type} region")
        if matches[0].get("needs_review", False):
            raise ValueError(f"Template {content_type} region must be reviewed before publishing")
    for content_type in sorted(IDENTITY_CONTENT_TYPES - REQUIRED_IDENTITY_CONTENT_TYPES):
        matches = [region for region in regions if region["content_type"] == content_type]
        if len(matches) > 1:
            raise ValueError(f"Template allows at most one {content_type} region")
        if matches and matches[0].get("needs_review", False):
            raise ValueError(f"Template {content_type} region must be reviewed before publishing")


def _validate_identity_region_geometry(template: dict[str, Any]) -> None:
    for page in template["pages"]:
        identity = [region for region in page["regions"] if region["content_type"] in IDENTITY_CONTENT_TYPES]
        answer_or_question = [region for region in page["regions"] if region["content_type"] in QUESTION_CONTENT_TYPES]
        for region in identity:
            if any(_boxes_overlap(region["bbox"], other["bbox"]) for other in answer_or_question):
                raise ValueError("identity region must not overlap a question or answer region")
        if len(identity) > 1:
            for index, region in enumerate(identity):
                if any(_boxes_overlap(region["bbox"], other["bbox"]) for other in identity[index + 1:]):
                    raise ValueError("identity regions must not overlap")


def _boxes_overlap(first: list[float], second: list[float]) -> bool:
    return max(first[0], second[0]) < min(first[2], second[2]) and max(first[1], second[1]) < min(first[3], second[3])


def _validate_template_question_ids(template: dict[str, Any], questions: list[dict[str, Any]]) -> None:
    if not questions:
        raise ValueError("Exam must have a saved question catalog before binding an answer-sheet template")
    answer_regions = [
        region for page in template["pages"] for region in page["regions"]
        if region.get("content_type", "answer") == "answer"
    ]
    if not answer_regions:
        raise ValueError("Template must contain answer regions")
    expected = {str(question["question_id"]) for question in questions}
    actual = {str(region["question_id"]) for region in answer_regions}
    if expected != actual:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(f"Template question_id mismatch; missing={missing}, unexpected={unexpected}")
