from __future__ import annotations

"""Generate reviewable fixed-answer-sheet template drafts from blank cards."""

import re
import shutil
from pathlib import Path
from typing import Any

from d_module.pipeline import process_file_to_ocr_results
from template_registry.service import TEMPLATE_ROOT, get_exam_questions, save_template


QUESTION_LABEL_RE = re.compile(r"^\s*(?:第\s*)?(\d+(?:[.．、]\d+)?)(?:\s*[、．.）)])?\s*$")


def build_template_draft(
    template_id: str,
    template_name: str,
    source_path: str | Path,
    mime_type: str,
    version: int = 1,
    exam_id: str | None = None,
) -> dict[str, Any]:
    """Create a pending-review answer-sheet template from a blank source file.

    Candidate regions are inferred from printed question labels and are never
    auto-published. The template editor must review the generated rectangles.
    """
    source = Path(source_path)
    a_result = process_file_to_ocr_results(
        submission_id=f"template_{template_id}",
        origin_name=source.name,
        mime_type=mime_type,
        file_size=source.stat().st_size,
        source_path=source,
        # A blank PDF frequently has a usable text layer for printed labels.
        # Keeping auto mode avoids requiring OCR merely to build a draft.
        parse_strategy="auto",
    )
    template_dir = TEMPLATE_ROOT / template_id
    template_dir.mkdir(parents=True, exist_ok=True)
    pages = _build_pages(a_result["normalized_pages"], a_result["ocr_page_results"], template_dir)
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
        "page_count": len(pages),
        "pages": pages,
    }
    return save_template(template)


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
    proposals = propose_regions_from_ocr_pages(normalized_pages, ocr_page_results)
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
        })
    return labels


def _map_regions_to_exam_questions(
    pages: list[dict[str, Any]], questions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    """Map answer boxes to canonical question IDs by physical reading order."""
    regions: list[dict[str, Any]] = []
    for page in pages:
        for region in page["regions"]:
            regions.append({"page_no": page["page_no"], "region": region})
    regions.sort(key=lambda item: (item["page_no"], item["region"]["bbox"][1], item["region"]["bbox"][0]))
    if not questions:
        raise ValueError("Exam must have question paper results before creating an answer-sheet template")
    if len(regions) != len(questions):
        for item in regions:
            item["region"]["needs_review"] = True
            item["region"]["question_mapping_error"] = "question_count_mismatch"
        return pages, "count_mismatch"
    for item, question in zip(regions, questions):
        region = item["region"]
        region["template_label"] = region["question_no"]
        region["question_id"] = question["question_id"]
        region["question_no"] = question["question_no"]
        region["question_id_source"] = "exam_question_catalog"
    return pages, "mapped"
