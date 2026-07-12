from __future__ import annotations

import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from b_module.cross_page_merger.service import merge_cross_page_answers
from b_module.question_segmenter.free_layout_pipeline import split_free_layout_questions_v2
from b_module.result_exporter.service import export_question_level_results


def _load_case(filename: str) -> dict:
    with (BASE_DIR / "mock_data" / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_smoke_check() -> None:
    basic_case = _load_case("free_layout_case_basic.json")
    basic_split = split_free_layout_questions_v2(
        file_id=basic_case["file_id"],
        page_ocr_results=basic_case["page_ocr_results"],
    )
    _assert(len(basic_split["question_candidates"]) == 2, "basic case should split into 2 questions")
    _assert(basic_split["question_candidates"][0]["question_no"] == "1", "first question should be 1")
    _assert(basic_split["question_candidates"][1]["question_no"] == "2", "second question should be 2")

    cross_page_case = _load_case("free_layout_case_cross_page.json")
    cross_page_split = split_free_layout_questions_v2(
        file_id=cross_page_case["file_id"],
        page_ocr_results=cross_page_case["page_ocr_results"],
    )
    cross_page_merge = merge_cross_page_answers(
        file_id=cross_page_case["file_id"],
        route_type="free_layout_homework",
        question_candidates=cross_page_split["question_candidates"],
    )
    _assert(len(cross_page_merge["merged_questions"]) == 1, "cross-page case should merge into 1 result")
    _assert(cross_page_merge["merged_questions"][0]["from_pages"] == [1, 2], "merged pages should be [1, 2]")

    export_result = export_question_level_results(
        file_id=basic_case["file_id"],
        route_type="free_layout_homework",
        merged_questions=merge_cross_page_answers(
            file_id=basic_case["file_id"],
            route_type="free_layout_homework",
            question_candidates=basic_split["question_candidates"],
        )["merged_questions"],
        review_results=[],
    )
    _assert(len(export_result["question_level_results"]) == 2, "export should contain 2 question-level results")


if __name__ == "__main__":
    run_smoke_check()
    print("B module smoke check passed.")
