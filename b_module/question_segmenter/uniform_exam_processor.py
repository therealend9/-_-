from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from page_alignment.service import align_page_to_template
from region_extractor.service import crop_region
from region_ocr.service import detect_blank_region, run_ocr_on_region


def split_uniform_exam_questions(
    file_id: str,
    template_id: str,
    question_regions: Iterable[dict],
    normalized_pages: Iterable[dict[str, Any]] | None = None,
    template: dict[str, Any] | None = None,
    document_role: str = "answer_sheet",
) -> dict:
    """Extract fixed answer regions and export one result for each question.

    Legacy callers may still use this function with precomputed regions only;
    those regions are returned unchanged. The fixed-answer-sheet route supplies
    a template and normalized pages, which enables the full crop/OCR flow.
    """
    if template and normalized_pages:
        return _extract_fixed_answer_regions(
            file_id=file_id,
            template_id=template_id,
            template=template,
            normalized_pages=normalized_pages,
            document_role=document_role,
        )

    normalized_regions = []
    for region in question_regions:
        normalized_regions.append(
            {
                "file_id": file_id,
                "route_type": "uniform_exam",
                "template_id": template_id,
                "question_no": str(region["question_no"]),
                "question_id": str(region.get("question_id") or region["question_no"]),
                "page_no": int(region["page_no"]),
                "bbox": region["bbox"],
                "region_confidence": float(region.get("region_confidence", 1.0)),
                "needs_review": bool(region.get("needs_review", False)),
            }
        )

    return {
        "file_id": file_id,
        "route_type": "uniform_exam",
        "template_id": template_id,
        "question_regions": normalized_regions,
    }


def _extract_fixed_answer_regions(
    file_id: str,
    template_id: str,
    template: dict[str, Any],
    normalized_pages: Iterable[dict[str, Any]],
    document_role: str,
) -> dict[str, Any]:
    if document_role not in {"question_paper", "answer_sheet"}:
        raise ValueError("document_role must be 'question_paper' or 'answer_sheet'")
    target_content_type = "question" if document_role == "question_paper" else "answer"
    pages_by_no = {int(page["page_no"]): page for page in normalized_pages}
    template_pages = list(template.get("pages", []))
    page_count_ok = len(pages_by_no) == len(template_pages)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for template_page in template_pages:
        page_no = int(template_page["page_no"])
        page = pages_by_no.get(page_no)
        if page is None:
            for region in _regions_for_role(template_page, target_content_type):
                grouped[str(region["question_id"])].append(_missing_region(region, page_no, "page_missing"))
            continue
        alignment = align_page_to_template(
            page=page,
            template_page=template_page,
            template_dir=template.get("_template_dir"),
        )
        for region in _regions_for_role(template_page, target_content_type):
            grouped[str(region["question_id"])].append(
                _extract_one_region(file_id, page_no, region, alignment, document_role)
            )

    question_level_results = []
    for question_id, parts in grouped.items():
        parts.sort(key=lambda item: (item["order"], item["page_no"]))
        question_level_results.append(_merge_question_parts(file_id, question_id, parts, page_count_ok))
    question_level_results.sort(key=lambda item: _question_sort_key(item["question_no"]))
    return {
        "file_id": file_id,
        "route_type": "uniform_exam",
        "template_id": template_id,
        "template_version": template.get("version"),
        "document_role": document_role,
        "status": "ready",
        "question_level_results": question_level_results,
    }


def _extract_one_region(
    file_id: str, page_no: int, region: dict[str, Any], alignment: dict[str, Any], document_role: str,
) -> dict[str, Any]:
    base = {
        "question_id": str(region["question_id"]),
        "question_no": str(region["question_no"]),
        "order": int(region.get("order", 1)),
        "page_no": page_no,
        "alignment_confidence": float(alignment["alignment_confidence"]),
        "risk_flags": list(alignment.get("risk_flags", [])),
        "needs_review": bool(alignment.get("needs_review", False)),
    }
    try:
        crop = crop_region(
            aligned_image_path=alignment["image_path"],
            bbox=list(region["bbox"]),
            output_stem=f"{file_id}_q{region['question_id']}_p{page_no:03d}_o{int(region.get('order', 1)):02d}",
        )
        template_crop_path = None
        if document_role == "answer_sheet" and alignment.get("reference_image_path"):
            template_crop = crop_region(
                aligned_image_path=alignment["reference_image_path"],
                bbox=list(region["bbox"]),
                output_stem=f"{file_id}_template_q{region['question_id']}_p{page_no:03d}_o{int(region.get('order', 1)):02d}",
            )
            template_crop_path = template_crop["image_path"]
        blank = (
            detect_blank_region(crop["image_path"], template_crop_path=template_crop_path)
            if document_role == "answer_sheet"
            else {"is_blank": False, "ink_ratio": None}
        )
        base.update({"bbox": crop["bbox"], "crop_path": crop["image_path"], "is_blank": blank["is_blank"], "ink_ratio": blank["ink_ratio"]})
        if blank["is_blank"]:
            base.update({"ocr_text": "", "ocr_confidence": 1.0, "ocr_blocks": []})
            return base
        ocr = run_ocr_on_region(
            file_id=file_id,
            page_no=page_no,
            image_path=crop["image_path"],
            ocr_mode=str(region.get("ocr_mode", "handwriting")),
        )
        base.update(ocr)
        if float(ocr["ocr_confidence"]) < 0.75:
            base["needs_review"] = True
            base["risk_flags"].append("low_ocr_confidence")
        return base
    except Exception as exc:
        base.update({
            "bbox": None,
            "crop_path": None,
            "is_blank": False,
            "ocr_text": "",
            "ocr_confidence": 0.0,
            "ocr_blocks": [],
            "needs_review": True,
            "risk_flags": base["risk_flags"] + ["region_processing_failed"],
            "error": str(exc),
        })
        return base


def _missing_region(region: dict[str, Any], page_no: int, flag: str) -> dict[str, Any]:
    return {
        "question_id": str(region["question_id"]), "question_no": str(region["question_no"]),
        "order": int(region.get("order", 1)), "page_no": page_no, "bbox": None,
        "crop_path": None, "is_blank": False, "ocr_text": "", "ocr_confidence": 0.0,
        "ocr_blocks": [], "alignment_confidence": 0.0, "needs_review": True, "risk_flags": [flag],
    }


def _merge_question_parts(file_id: str, question_id: str, parts: list[dict[str, Any]], page_count_ok: bool) -> dict[str, Any]:
    flags = sorted({flag for part in parts for flag in part["risk_flags"]})
    if not page_count_ok:
        flags.append("page_count_mismatch")
    text_parts = [part["ocr_text"] for part in parts if part["ocr_text"]]
    confidence = min(
        min(float(part["alignment_confidence"]), float(part["ocr_confidence"]))
        for part in parts
    ) if parts else 0.0
    is_blank = bool(parts) and all(part["is_blank"] for part in parts)
    needs_review = bool(flags) or any(part["needs_review"] for part in parts)
    return {
        "file_id": file_id,
        "merge_group_id": f"uniform_{file_id}_{question_id}",
        "question_id": question_id,
        "question_no": parts[0]["question_no"] if parts else question_id,
        "route_type": "uniform_exam",
        "page_nos": sorted({part["page_no"] for part in parts}),
        "region_bboxes": [part["bbox"] for part in parts if part["bbox"] is not None],
        "ocr_text": "\n".join(text_parts),
        "final_text": "\n".join(text_parts),
        "is_blank": is_blank,
        "alignment_confidence": min((float(part["alignment_confidence"]) for part in parts), default=0.0),
        "ocr_confidence": min((float(part["ocr_confidence"]) for part in parts), default=0.0),
        "confidence": round(confidence, 4),
        "needs_review": needs_review,
        "risk_flags": flags,
        "region_results": parts,
    }


def _question_sort_key(question_no: str) -> tuple[int, str]:
    try:
        return (0, f"{int(question_no):08d}")
    except ValueError:
        return (1, question_no)


def _regions_for_role(template_page: dict[str, Any], content_type: str) -> list[dict[str, Any]]:
    return [
        region for region in template_page.get("regions", [])
        if str(region.get("content_type", "answer")) == content_type
    ]
