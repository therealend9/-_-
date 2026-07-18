from __future__ import annotations

from typing import Any, Iterable, Optional

from b_module.schemas.types import RouteDecision


def decide_layout_route(
    file_id: str,
    assignment_type: str,
    template_id: Optional[str],
    page_results: Optional[Iterable[dict[str, Any]]] = None,
    normalized_pages: Optional[Iterable[dict[str, Any]]] = None,
) -> RouteDecision:
    """Decide whether a submission should use the uniform or free-layout route."""
    normalized_assignment_type = (assignment_type or "").strip().lower()
    if template_id:
        return {
            "file_id": file_id,
            "route_type": "uniform_exam",
            "reason": "template_present",
            "template_id": template_id,
        }

    if normalized_assignment_type in {"uniform_exam", "template_exam"}:
        return {
            "file_id": file_id,
            "route_type": "uniform_exam",
            "reason": "assignment_type_marked_uniform",
            "template_id": None,
        }

    page_results = list(page_results or [])
    normalized_pages = list(normalized_pages or [])

    low_conf_pages = 0
    for page in page_results:
        # OCR engines may explicitly return null when a page has no usable
        # confidence aggregate. Treat that as unknown quality and let the
        # free-layout route continue to perform its own review checks.
        confidence = page.get("overall_confidence")
        if confidence is not None and float(confidence) < 0.8:
            low_conf_pages += 1
    text_extract_pages = sum(
        1
        for page in page_results
        for block in page.get("blocks", [])
        if block.get("source_mode") == "text_extract"
    )
    transformed_pages = sum(
        1
        for page in normalized_pages
        if page.get("rotation_degree") not in (None, 0) or page.get("has_perspective_fix")
    )

    if low_conf_pages == 0 and text_extract_pages == 0 and transformed_pages == 0:
        return {
            "file_id": file_id,
            "route_type": "free_layout_homework",
            "reason": "stable_page_quality_without_template",
            "template_id": None,
        }

    return {
        "file_id": file_id,
        "route_type": "free_layout_homework",
        "reason": "quality_or_layout_variation_detected",
        "template_id": None,
    }
