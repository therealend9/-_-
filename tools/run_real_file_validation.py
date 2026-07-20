from __future__ import annotations

"""Run repeatable validation against real files already retained in this repository.

The script deliberately uses an isolated registry/result directory so it cannot
change the development service's templates or persisted submissions.
"""

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "test_artifacts" / "validation_20260716"
TEMPLATE_ROOT = OUTPUT / "templates"
RESULT_ROOT = OUTPUT / "processing_results"
sys.path.insert(0, str(ROOT))

# These must be set before importing application services, which read them at
# module import time.
os.environ["ANSWER_SHEET_TEMPLATE_ROOT"] = str(TEMPLATE_ROOT)
os.environ["EXAM_PROCESSING_RESULT_ROOT"] = str(RESULT_ROOT)

from full_pipeline import process_file_to_question_results  # noqa: E402
from template_builder.service import build_template_draft  # noqa: E402
from template_registry.service import (  # noqa: E402
    bind_exam_template,
    create_exam,
    review_template,
    save_exam_questions,
)


def write_json(name: str, value: object) -> None:
    (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    blank_card = ROOT / "test_artifacts" / "answer_sheet_docx" / "答题纸.pdf"
    handwritten_card = ROOT / "test_artifacts" / "handwritten_politics_samples" / "politics_05_mayuan_handwritten_answer.jpg"
    student_essay = (
        ROOT
        / "test_artifacts"
        / "answer_sheet_desktop_v2"
        / "templates"
        / "tpl_desktop_answer_sheet_v2"
        / "source_pdf"
        / "2024级网络空间安全试验班2班2024302183019孙瑞杰.pdf"
    )
    for source in (blank_card, handwritten_card, student_essay):
        if not source.is_file():
            raise FileNotFoundError(source)

    manifest = {
        "run_date": "2026-07-16",
        "scope": "Real-file validation; no mock OCR responses are used.",
        "samples": [
            {
                "case": "blank_template_draft",
                "source": "answer_sheet_docx/答题纸.pdf",
                "sha256": sha256(blank_card),
                "purpose": "Create a real blank answer-card template draft and record automatic region proposals.",
            },
            {
                "case": "handwritten_fixed_answer_sheet",
                "source": "handwritten_politics_samples/politics_05_mayuan_handwritten_answer.jpg",
                "sha256": sha256(handwritten_card),
                "purpose": "Run page alignment, fixed-region crop, blank detection, handwriting OCR, and final answer output.",
                "limitation": "The source is a public completed answer card with objective areas and is used only as a technical handwriting/cropping sample, not as a final product benchmark for the subjective-only scenario.",
            },
            {
                "case": "free_layout_negative_control",
                "source": "answer_sheet_desktop_v2/student_essay.pdf",
                "sha256": sha256(student_essay),
                "purpose": "Verify a real free-layout student essay is not silently treated as a question paper.",
                "limitation": "This is a negative-control document, not a legitimate question-paper accuracy benchmark.",
            },
        ],
    }
    write_json("manifest.json", manifest)

    # Case 1: real blank template draft. The catalog is intentionally explicit
    # because a blank answer card alone cannot create question IDs.
    create_exam("real_blank_card_20260716", "真实空白答题卡模板测试")
    save_exam_questions(
        "real_blank_card_20260716",
        [
            {"question_id": "q01", "question_no": "1", "question_text": "人工核验题目 1"},
            {"question_id": "q02", "question_no": "2", "question_text": "人工核验题目 2"},
            {"question_id": "q03", "question_no": "3", "question_text": "人工核验题目 3"},
            {"question_id": "q04", "question_no": "4", "question_text": "人工核验题目 4"},
        ],
        "catalog_blank_card_20260716",
    )
    draft = build_template_draft(
        "tpl_real_blank_card_20260716",
        "真实空白答题卡自动草稿",
        blank_card,
        "application/pdf",
        version=1,
        exam_id="real_blank_card_20260716",
    )
    write_json("01_blank_template_draft.json", draft)

    # Case 2: use the real handwritten page as a fixed-layout technical sample.
    # The auto-generated reference image is retained by build_template_draft;
    # then the three visibly printed subjective regions are manually reviewed.
    create_exam("real_handwritten_20260716", "真实手写答题卡技术验证")
    questions = [
        {"question_id": "37", "question_no": "37", "question_text": "样本印刷题号 37"},
        {"question_id": "38", "question_no": "38", "question_text": "样本印刷题号 38"},
        {"question_id": "39", "question_no": "39", "question_text": "样本印刷题号 39"},
    ]
    save_exam_questions("real_handwritten_20260716", questions, "catalog_handwritten_20260716")
    handwritten_draft = build_template_draft(
        "tpl_real_handwritten_20260716",
        "真实手写样本复核模板",
        handwritten_card,
        "image/jpeg",
        version=1,
        exam_id="real_handwritten_20260716",
    )
    write_json("02_handwritten_auto_draft.json", handwritten_draft)

    reviewed_pages = handwritten_draft["pages"]
    reviewed_pages[0]["regions"] = [
        {
            "question_id": "37", "question_no": "37", "order": 1,
            "bbox": [0.355, 0.345, 0.690, 0.985], "coordinate_type": "normalized",
            "content_type": "answer", "ocr_mode": "handwriting", "region_source": "manual_review",
            "needs_review": False,
        },
        {
            "question_id": "38", "question_no": "38", "order": 1,
            "bbox": [0.695, 0.035, 0.995, 0.500], "coordinate_type": "normalized",
            "content_type": "answer", "ocr_mode": "handwriting", "region_source": "manual_review",
            "needs_review": False,
        },
        {
            "question_id": "39", "question_no": "39", "order": 1,
            "bbox": [0.695, 0.500, 0.995, 0.985], "coordinate_type": "normalized",
            "content_type": "answer", "ocr_mode": "handwriting", "region_source": "manual_review",
            "needs_review": False,
        },
    ]
    reviewed = review_template("tpl_real_handwritten_20260716", reviewed_pages, publish=True)
    binding = bind_exam_template("real_handwritten_20260716", "tpl_real_handwritten_20260716")
    write_json("03_handwritten_reviewed_template.json", reviewed)
    write_json("04_handwritten_binding.json", binding)

    answer_result = process_file_to_question_results(
        submission_id="real_handwritten_answer_20260716",
        origin_name=handwritten_card.name,
        mime_type="image/jpeg",
        file_size=handwritten_card.stat().st_size,
        source_path=handwritten_card,
        exam_id="real_handwritten_20260716",
        document_role="answer_sheet",
    )
    write_json("05_handwritten_answer_result.json", answer_result)

    # Case 3: a real student essay must not be reported as a question paper.
    negative_result = process_file_to_question_results(
        submission_id="free_layout_negative_20260716",
        origin_name="student_essay.pdf",
        mime_type="application/pdf",
        file_size=student_essay.stat().st_size,
        source_path=student_essay,
        document_role="question_paper",
    )
    write_json("06_free_layout_negative_result.json", negative_result)

    retry_result = process_file_to_question_results(
        submission_id="real_handwritten_answer_20260716",
        origin_name=handwritten_card.name,
        mime_type="image/jpeg",
        file_size=handwritten_card.stat().st_size,
        source_path=handwritten_card,
        exam_id="real_handwritten_20260716",
        document_role="answer_sheet",
    )
    summary = {
        "blank_template": {
            "page_count": draft["page_count"],
            "proposed_region_count": sum(len(page["regions"]) for page in draft["pages"]),
            "mapping_status": draft["question_mapping_status"],
        },
        "handwritten_answer_sheet": {
            "template_status": reviewed["status"],
            "answer_count": len(answer_result["answers"]),
            "answers": [
                {
                    "question_id": item["question_id"],
                    "is_blank": item["is_blank"],
                    "confidence": item["confidence"],
                    "needs_review": item["needs_review"],
                    "risk_flags": item["risk_flags"],
                    "answer_text_preview": item["answer_text"][:120],
                }
                for item in answer_result["answers"]
            ],
            "idempotent_retry_equal": answer_result == retry_result,
        },
        "free_layout_negative_control": {
            "question_count": len(negative_result["questions"]),
            "questions": [
                {"question_id": item["question_id"], "question_no": item["question_no"], "confidence": item["confidence"]}
                for item in negative_result["questions"]
            ],
        },
    }
    write_json("summary.json", summary)


if __name__ == "__main__":
    main()
