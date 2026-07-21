from __future__ import annotations

"""Extract protected identity fields without adding them to answer output."""

from collections.abc import Iterable
from typing import Any

from page_alignment.service import align_page_to_template
from region_extractor.service import crop_region
from region_ocr.service import run_ocr_on_region
from template_registry.service import IDENTITY_CONTENT_TYPES


IDENTITY_FIELD_LABELS = {
    "student_name": "姓名",
    "student_no": "学号",
    "major": "专业",
    "college": "学院",
    "grade": "年级",
}
IDENTITY_REVIEW_THRESHOLD = 0.75


def extract_identity_fields(
    file_id: str,
    template: dict[str, Any],
    normalized_pages: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Crop and OCR configured identity regions into an internal binding record.

    The returned object is for protected persistence only. It must not be added
    to the public ``exam-document.v1`` answer result.
    """
    pages_by_no = {int(page["page_no"]): page for page in normalized_pages}
    fields: dict[str, dict[str, Any]] = {}
    for template_page in template.get("pages", []):
        page_no = int(template_page["page_no"])
        page = pages_by_no.get(page_no)
        for region in _identity_regions(template_page):
            field_name = str(region["content_type"])
            if field_name in fields:
                fields[field_name]["needs_review"] = True
                fields[field_name]["risk_flags"].append("duplicate_identity_region")
                continue
            if page is None:
                fields[field_name] = _missing_field(field_name, page_no, "page_missing")
                continue
            fields[field_name] = _extract_one_identity_field(
                file_id=file_id,
                page_no=page_no,
                region=region,
                page=page,
                template=template,
            )

    missing_required = [
        field for field in ("student_name", "student_no") if field not in fields
    ]
    if missing_required:
        for field in missing_required:
            fields[field] = _missing_field(field, None, "identity_region_missing")

    needs_review = any(item["needs_review"] for item in fields.values())
    return {
        "status": "needs_review" if needs_review else "recognized",
        "fields": fields,
    }


def _identity_regions(template_page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        region
        for region in template_page.get("regions", [])
        if region.get("content_type") in IDENTITY_CONTENT_TYPES
    ]


def _extract_one_identity_field(
    file_id: str,
    page_no: int,
    region: dict[str, Any],
    page: dict[str, Any],
    template: dict[str, Any],
) -> dict[str, Any]:
    field_name = str(region["content_type"])
    result = {
        "label": IDENTITY_FIELD_LABELS.get(field_name, field_name),
        "value": "",
        "confidence": 0.0,
        "page_no": page_no,
        "needs_review": False,
        "risk_flags": [],
    }
    try:
        alignment = align_page_to_template(
            page=page,
            template_page=template_page_for_page(template, page_no),
            template_dir=template.get("_template_dir"),
        )
        crop = crop_region(
            aligned_image_path=alignment["image_path"],
            bbox=list(region["bbox"]),
            output_stem=f"{file_id}_identity_{field_name}_p{page_no:03d}",
        )
        ocr_mode = str(region.get("ocr_mode", "handwriting"))
        if ocr_mode == "excluded":
            # Backward-compatible templates used ``excluded`` only to keep
            # identity regions out of answer OCR. Identity extraction now has
            # its own route, so those regions use handwriting OCR by default.
            ocr_mode = "handwriting"
        ocr = run_ocr_on_region(
            file_id=file_id,
            page_no=page_no,
            image_path=crop["image_path"],
            ocr_mode=ocr_mode,
        )
        confidence = float(ocr.get("ocr_confidence", 0.0) or 0.0)
        value = str(ocr.get("ocr_text", "") or "").strip()
        result.update({
            "value": value,
            "confidence": confidence,
            "crop_path": crop.get("image_path"),
            "ocr_engine": ocr.get("ocr_engine"),
            "needs_review": confidence < IDENTITY_REVIEW_THRESHOLD or not value,
        })
        if confidence < IDENTITY_REVIEW_THRESHOLD:
            result["risk_flags"].append("low_identity_ocr_confidence")
        if not value:
            result["risk_flags"].append("identity_value_empty")
    except Exception:
        result["needs_review"] = True
        result["risk_flags"].append("identity_region_processing_failed")
    return result


def template_page_for_page(template: dict[str, Any], page_no: int) -> dict[str, Any]:
    for page in template.get("pages", []):
        if int(page["page_no"]) == page_no:
            return page
    raise ValueError(f"template page not found: {page_no}")


def _missing_field(field_name: str, page_no: int | None, flag: str) -> dict[str, Any]:
    return {
        "label": IDENTITY_FIELD_LABELS.get(field_name, field_name),
        "value": "",
        "confidence": 0.0,
        "page_no": page_no,
        "needs_review": True,
        "risk_flags": [flag],
    }
