from __future__ import annotations

"""Generate reviewable fixed-answer-sheet template drafts from blank cards."""

import re
import shutil
from pathlib import Path
from typing import Any

from d_module.constants import PARSE_MODE_PDF_TEXT
from d_module.document_parser.service import classify_and_parse_document
from d_module.file_ingest.service import create_file_task
from d_module.ocr_engine.service import build_pdf_text_ocr_result, run_ocr_on_page
from d_module.page_renderer.docx_pdf_renderer import convert_docx_to_pdf
from d_module.page_renderer.service import render_pages_to_images
from template_registry.service import IDENTITY_CONTENT_TYPES, TEMPLATE_ROOT, get_exam_questions, save_template


QUESTION_LABEL_RE = re.compile(
    r"^\s*(?:第\s*)?(\d+(?:[.．、]\d+)?)(?:\s*[、．.）)]?\s*[:：]?\s*(?:答案)?\s*)?$"
)
IDENTITY_LABEL_PATTERNS = {
    "student_name": re.compile(r"\u59d3\u540d"),
    "student_no": re.compile(r"\u5b66\u53f7|\u5b66\u751f\u7f16\u53f7", re.IGNORECASE),
    "major": re.compile(r"\u4e13\u4e1a"),
    "college": re.compile(r"\u5b66\u9662|\u9662\u7cfb"),
    "grade": re.compile(r"\u5e74\u7ea7"),
}


def build_template_draft(
    template_id: str,
    template_name: str,
    source_path: str | Path,
    mime_type: str,
    version: int = 1,
    exam_id: str | None = None,
) -> dict[str, Any]:
    """Create a pending-review answer-sheet template from a blank source file.

    Candidate regions are inferred from table/rectangle borders first, then
    associated with printed labels when available. They are never
    auto-published; the template editor must review every rectangle.
    """
    source = Path(source_path)
    template_dir = TEMPLATE_ROOT / template_id
    template_dir.mkdir(parents=True, exist_ok=True)
    processing_source = source
    processing_mime_type = mime_type
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # DOCX table coordinates are document-flow coordinates, not physical
        # page coordinates. Render through Word/LibreOffice before detecting
        # answer boxes so normalized bbox values match later scanned pages.
        processing_source = convert_docx_to_pdf(source, template_dir / "source_pdf")
        processing_mime_type = "application/pdf"
    normalized_pages, ocr_page_results = _load_template_pages(
        submission_id=f"template_{template_id}",
        source_path=processing_source,
        mime_type=processing_mime_type,
    )
    pages = _build_pages(normalized_pages, ocr_page_results, template_dir)
    mapping_status = "not_requested"
    if exam_id:
        pages, mapping_status = _map_regions_to_exam_questions(pages, get_exam_questions(exam_id))
    template = {
        "template_id": template_id,
        "template_name": template_name,
        "version": version,
        "status": "pending_review",
        "auto_generated": True,
        "exam_id": exam_id,
        "question_mapping_status": mapping_status,
        "identity_protection": {"required": True, "status": "pending_review"},
        "page_count": len(pages),
        "pages": pages,
    }
    return save_template(template)


def _load_template_pages(
    submission_id: str,
    source_path: Path,
    mime_type: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Render a blank card without expensive whole-page OCR.

    Template construction needs geometry, not handwritten text. PDF text blocks
    are retained when present for label association; scanned files continue with
    empty labels and rely on rectangle detection plus human review.
    """
    file_task = create_file_task(
        submission_id=submission_id,
        origin_name=source_path.name,
        mime_type=mime_type,
        file_size=source_path.stat().st_size,
        source_path=source_path,
    )
    parse_result = classify_and_parse_document(file_task)
    pages = render_pages_to_images(file_task, parse_result)
    text_by_page = {
        int(item["page_no"]): item
        for item in parse_result.get("extracted_text_pages", [])
    }
    ocr_page_results: list[dict[str, Any]] = []
    for page in pages:
        extracted = text_by_page.get(page.page_no)
        if parse_result["parse_mode"] == PARSE_MODE_PDF_TEXT and extracted and extracted.get("usable"):
            ocr_page_results.append(build_pdf_text_ocr_result(file_task.file_id, page, extracted).to_dict())
        else:
            # A blank scanned answer card has no PDF text layer. OCR is used
            # once during template setup to find printed identity labels; a
            # failed optional proposal leaves manual template review available.
            try:
                ocr_page_results.append(run_ocr_on_page(file_task.file_id, page).to_dict())
            except Exception:
                ocr_page_results.append({
                    "file_id": file_task.file_id,
                    "page_no": page.page_no,
                    "blocks": [],
                })
    return [page.to_dict() for page in pages], ocr_page_results


def propose_regions_from_ocr_pages(
    normalized_pages: list[dict[str, Any]],
    ocr_page_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Produce answer-region proposals using printed labels and vertical layout.

    This intentionally errs toward review: the inferred boxes are broad, carry
    ``needs_review``, and are only suitable for vertically ordered answer cards.
    """
    ocr_by_page = {int(item["page_no"]): item for item in ocr_page_results}
    proposals: list[dict[str, Any]] = []
    for page in normalized_pages:
        page_no = int(page["page_no"])
        width = float(page["processed_width"])
        height = float(page["processed_height"])
        labels = _find_question_labels((ocr_by_page.get(page_no) or {}).get("blocks", []), width, height)
        for index, label in enumerate(labels):
            next_top = labels[index + 1]["top"] if index + 1 < len(labels) else 0.96
            top = min(max(label["bottom"] + 0.012, 0.04), 0.94)
            bottom = min(max(next_top - 0.012, top + 0.05), 0.98)
            if bottom <= top:
                continue
            proposals.append({
                "page_no": page_no,
                "question_id": label["question_id"],
                "question_no": label["question_no"],
                "order": 1,
                "bbox": [0.10, round(top, 6), 0.94, round(bottom, 6)],
                "coordinate_type": "normalized",
                "content_type": "answer",
                "ocr_mode": "handwriting",
                "region_source": "auto_label_layout",
                "needs_review": True,
                "label_bbox": label["bbox"],
            })
    return proposals


def _build_pages(
    normalized_pages: list[dict[str, Any]],
    ocr_page_results: list[dict[str, Any]],
    template_dir: Path,
) -> list[dict[str, Any]]:
    proposals = propose_regions_from_page_layout(normalized_pages, ocr_page_results)
    proposals.extend(propose_identity_regions_from_ocr_pages(normalized_pages, ocr_page_results))
    regions_by_page: dict[int, list[dict[str, Any]]] = {}
    for region in proposals:
        regions_by_page.setdefault(int(region.pop("page_no")), []).append(region)
    pages: list[dict[str, Any]] = []
    for page in normalized_pages:
        page_no = int(page["page_no"])
        source_image = Path(page.get("preprocessed_image_path") or page["page_image_path"])
        reference_name = f"page_{page_no:03d}.png"
        shutil.copy2(source_image, template_dir / reference_name)
        pages.append({
            "page_no": page_no,
            "reference_width": int(page["processed_width"]),
            "reference_height": int(page["processed_height"]),
            "reference_image_path": reference_name,
            "regions": regions_by_page.get(page_no, []),
        })
    return pages


def propose_identity_regions_from_ocr_pages(
    normalized_pages: list[dict[str, Any]],
    ocr_page_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Propose editable identity fields beside printed student-information labels."""
    ocr_by_page = {int(item["page_no"]): item for item in ocr_page_results}
    proposals: list[dict[str, Any]] = []
    for page in normalized_pages:
        page_no = int(page["page_no"])
        width = float(page["processed_width"])
        height = float(page["processed_height"])
        found: set[str] = set()
        blocks = (ocr_by_page.get(page_no) or {}).get("blocks", [])
        for block in sorted(blocks, key=lambda item: (item.get("bbox", [0, 0])[1], item.get("bbox", [0, 0])[0])):
            text = str(block.get("text", "") or "").strip()
            bbox = block.get("bbox") or []
            if len(bbox) != 4:
                continue
            content_type = next((
                value for value, pattern in IDENTITY_LABEL_PATTERNS.items()
                if value not in found and pattern.search(text)
            ), None)
            if content_type is None:
                continue
            left = max(0.0, min(float(bbox[2]) / width + 0.01, 0.94))
            top = max(0.0, min(float(bbox[1]) / height - 0.015, 0.94))
            right = 0.94
            bottom = max(top + 0.035, min(float(bbox[3]) / height + 0.045, 0.98))
            if right <= left or bottom <= top:
                continue
            proposals.append({
                "page_no": page_no,
                "bbox": [round(left, 6), round(top, 6), round(right, 6), round(bottom, 6)],
                "coordinate_type": "normalized",
                "content_type": content_type,
                "ocr_mode": "handwriting",
                "region_source": "auto_identity_label",
                "needs_review": True,
                "label_bbox": [round(float(value), 2) for value in bbox],
            })
            found.add(content_type)
    return proposals


def propose_regions_from_page_layout(
    normalized_pages: list[dict[str, Any]],
    ocr_page_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find printed answer rectangles before falling back to label-only boxes."""
    ocr_by_page = {int(item["page_no"]): item for item in ocr_page_results}
    proposals: list[dict[str, Any]] = []
    for page in normalized_pages:
        page_no = int(page["page_no"])
        width = float(page["processed_width"])
        height = float(page["processed_height"])
        image_path = Path(page.get("preprocessed_image_path") or page["page_image_path"])
        boxes = _find_answer_boxes(image_path, width, height)
        if not boxes:
            continue
        labels = _find_question_labels((ocr_by_page.get(page_no) or {}).get("blocks", []), width, height)
        for index, box in enumerate(boxes, start=1):
            label = _label_for_box(labels, box)
            label_value = label["question_no"] if label else f"region_{page_no}_{index}"
            proposals.append({
                "page_no": page_no,
                "question_id": label_value,
                "question_no": label_value,
                "template_label": label_value,
                "order": 1,
                "bbox": box,
                "coordinate_type": "normalized",
                "content_type": "answer",
                "ocr_mode": "handwriting",
                "region_source": "auto_rectangle_layout",
                "needs_review": True,
                "label_bbox": label["bbox"] if label else None,
            })
    return proposals or propose_regions_from_ocr_pages(normalized_pages, ocr_page_results)


def _find_answer_boxes(image_path: Path, width: float, height: float) -> list[list[float]]:
    """Detect large printed rectangular writing areas with OpenCV line morphology."""
    try:
        import cv2
    except ImportError:
        return []
    import numpy as np
    image_bytes = np.fromfile(str(image_path), dtype=np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return []
    page_height, page_width = image.shape[:2]
    binary = cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 12,
    )
    horizontal = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, page_width // 32), 1)),
    )
    vertical = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, page_height // 32))),
    )
    lines = cv2.bitwise_or(horizontal, vertical)
    lines = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
    contours, _ = cv2.findContours(lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[list[float]] = []
    for contour in contours:
        x, y, box_width, box_height = cv2.boundingRect(contour)
        width_ratio, height_ratio = box_width / page_width, box_height / page_height
        area_ratio = width_ratio * height_ratio
        if width_ratio < 0.20 or height_ratio < 0.15 or area_ratio < 0.045 or area_ratio > 0.82:
            continue
        if x <= page_width * 0.01 and y <= page_height * 0.01:
            continue
        candidates.append([
            round(max(0.0, x / page_width), 6),
            round(max(0.0, y / page_height), 6),
            round(min(1.0, (x + box_width) / page_width), 6),
            round(min(1.0, (y + box_height) / page_height), 6),
        ])
    return _deduplicate_boxes(candidates)


def _deduplicate_boxes(boxes: list[list[float]]) -> list[list[float]]:
    kept: list[list[float]] = []
    for box in sorted(boxes, key=lambda value: (value[1], value[0], -(value[2] - value[0]) * (value[3] - value[1]))):
        if any(_intersection_over_union(box, existing) >= 0.85 for existing in kept):
            continue
        kept.append(box)
    return kept


def _intersection_over_union(first: list[float], second: list[float]) -> float:
    left, top = max(first[0], second[0]), max(first[1], second[1])
    right, bottom = min(first[2], second[2]), min(first[3], second[3])
    if right <= left or bottom <= top:
        return 0.0
    overlap = (right - left) * (bottom - top)
    first_area = (first[2] - first[0]) * (first[3] - first[1])
    second_area = (second[2] - second[0]) * (second[3] - second[1])
    return overlap / max(first_area + second_area - overlap, 1e-9)


def _label_for_box(labels: list[dict[str, Any]], box: list[float]) -> dict[str, Any] | None:
    for label in labels:
        center_x = (label["left"] + label["right"]) / 2
        center_y = (label["top"] + label["bottom"]) / 2
        if box[0] <= center_x <= box[2] and box[1] <= center_y <= min(box[3], box[1] + 0.16):
            return label
    return None


def _find_question_labels(blocks: list[dict[str, Any]], width: float, height: float) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block in sorted(blocks, key=lambda item: (item.get("bbox", [0, 0])[1], item.get("bbox", [0, 0])[0])):
        text = str(block.get("text", "") or "").strip()
        match = QUESTION_LABEL_RE.match(text)
        bbox = block.get("bbox") or []
        if not match or len(bbox) != 4:
            continue
        question_no = match.group(1).replace("．", ".").replace("、", ".")
        # A repeated label on another page is retained by page-level processing.
        if question_no in seen:
            continue
        seen.add(question_no)
        labels.append({
            "question_id": question_no,
            "question_no": question_no,
            "bbox": [round(float(value), 2) for value in bbox],
            "top": max(0.0, min(float(bbox[1]) / height, 1.0)),
            "bottom": max(0.0, min(float(bbox[3]) / height, 1.0)),
            "left": max(0.0, min(float(bbox[0]) / width, 1.0)),
            "right": max(0.0, min(float(bbox[2]) / width, 1.0)),
        })
    return labels


def _map_regions_to_exam_questions(
    pages: list[dict[str, Any]], questions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    """Map answer boxes to canonical question IDs by physical reading order."""
    regions: list[dict[str, Any]] = []
    for page in pages:
        for region in page["regions"]:
            if region.get("content_type", "answer") != "answer":
                continue
            regions.append({"page_no": page["page_no"], "region": region})
    regions = _sort_regions_in_reading_order(regions)
    if not questions:
        raise ValueError("Exam must have question paper results before creating an answer-sheet template")
    if len(regions) != len(questions):
        for item in regions:
            item["region"]["needs_review"] = True
            item["region"]["question_mapping_error"] = "question_count_mismatch"
        return pages, "count_mismatch"
    for item, question in zip(regions, questions):
        region = item["region"]
        region["template_label"] = region.get("template_label") or region["question_no"]
        region["question_id"] = question["question_id"]
        region["question_no"] = question["question_no"]
        region["question_id_source"] = "exam_question_catalog"
    # Keep the persisted page arrays in the same physical order used for the
    # canonical mapping.  This makes template review and API consumers see
    # left-to-right columns in the expected order as well.
    ordered_by_page: dict[int, list[dict[str, Any]]] = {}
    for item in regions:
        ordered_by_page.setdefault(int(item["page_no"]), []).append(item["region"])
    for page in pages:
        identity_regions = [
            region for region in page["regions"]
            if region.get("content_type") in IDENTITY_CONTENT_TYPES
        ]
        page["regions"] = ordered_by_page.get(int(page["page_no"]), []) + identity_regions
    return pages, "mapped"


def _sort_regions_in_reading_order(regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Read adjacent columns left-to-right before moving to the next row."""
    result: list[dict[str, Any]] = []
    by_page: dict[int, list[dict[str, Any]]] = {}
    for item in regions:
        by_page.setdefault(int(item["page_no"]), []).append(item)
    for page_no in sorted(by_page):
        rows: list[list[dict[str, Any]]] = []
        for item in sorted(by_page[page_no], key=lambda value: value["region"]["bbox"][1]):
            box = item["region"]["bbox"]
            matched_row = None
            for row in rows:
                row_box = row[0]["region"]["bbox"]
                overlap = min(box[3], row_box[3]) - max(box[1], row_box[1])
                min_height = min(box[3] - box[1], row_box[3] - row_box[1])
                if min_height > 0 and overlap / min_height >= 0.45:
                    matched_row = row
                    break
            if matched_row is None:
                rows.append([item])
            else:
                matched_row.append(item)
        rows.sort(key=lambda row: min(item["region"]["bbox"][1] for item in row))
        for row in rows:
            result.extend(sorted(row, key=lambda item: item["region"]["bbox"][0]))
    return result
