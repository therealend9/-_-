from __future__ import annotations

import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from b_module.cross_page_merger.service import merge_cross_page_answers
from b_module.question_segmenter.free_layout_pipeline_v3 import split_free_layout_questions_v3
from b_module.result_exporter.service import export_question_level_results
from b_module.ocr_review.service import submit_ocr_review


def _load_case(filename: str) -> dict:
    with (BASE_DIR / "mock_data" / filename).open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_smoke_check() -> None:
    basic_case = _load_case("free_layout_case_basic.json")
    basic_split = split_free_layout_questions_v3(
        file_id=basic_case["file_id"],
        page_ocr_results=basic_case["page_ocr_results"],
    )
    _assert(len(basic_split["question_candidates"]) == 2, "basic case should split into 2 questions")
    _assert(basic_split["question_candidates"][0]["question_no"] == "1", "first question should be 1")
    _assert(basic_split["question_candidates"][1]["question_no"] == "2", "second question should be 2")
    _assert("start_anchor_bbox" in basic_split["question_candidates"][0], "candidate should keep geometry anchor")

    cross_page_case = _load_case("free_layout_case_cross_page.json")
    cross_page_split = split_free_layout_questions_v3(
        file_id=cross_page_case["file_id"],
        page_ocr_results=cross_page_case["page_ocr_results"],
    )
    cross_page_merge = merge_cross_page_answers(
        file_id=cross_page_case["file_id"],
        route_type="free_layout_homework",
        question_candidates=cross_page_split["question_candidates"],
    )
    _assert(len(cross_page_merge["merged_questions"]) == 1, "cross-page case should merge into 1 result")
    merged = cross_page_merge["merged_questions"][0]
    _assert(merged["from_pages"] == [1, 2], "merged pages should be [1, 2]")
    _assert(merged["source_candidate_indexes"] == [0, 1], "source indexes should preserve original candidate positions")
    _assert("continuation_without_heading" in merged["merge_evidence"], "merge evidence should record carry-over reasoning")

    ocr_error_case = _load_case("free_layout_case_ocr_heading_error.json")
    ocr_error_split = split_free_layout_questions_v3(
        file_id=ocr_error_case["file_id"],
        page_ocr_results=ocr_error_case["page_ocr_results"],
    )
    _assert(len(ocr_error_split["question_candidates"]) >= 1, "ocr heading error case should still produce candidates")
    _assert(any(item["question_no"] == "1" for item in ocr_error_split["question_candidates"]), "ocr heading error case should preserve the first recognized question")

    negative_cross_page_case = _load_case("free_layout_case_cross_page_boundary_negative.json")
    negative_cross_page_split = split_free_layout_questions_v3(
        file_id=negative_cross_page_case["file_id"],
        page_ocr_results=negative_cross_page_case["page_ocr_results"],
    )
    negative_cross_page_merge = merge_cross_page_answers(
        file_id=negative_cross_page_case["file_id"],
        route_type="free_layout_homework",
        question_candidates=negative_cross_page_split["question_candidates"],
    )
    _assert(len(negative_cross_page_merge["merged_questions"]) == 2, "negative cross-page boundary case should not merge")

    multi_page_complex_a = _load_case("free_layout_case_multi_page_complex_a.json")
    multi_page_complex_a_split = split_free_layout_questions_v3(
        file_id=multi_page_complex_a["file_id"],
        page_ocr_results=multi_page_complex_a["page_ocr_results"],
    )
    _assert(len(multi_page_complex_a_split["question_candidates"]) >= 4, "complex A should produce multiple candidates")

    multi_page_complex_b = _load_case("free_layout_case_multi_page_complex_b.json")
    multi_page_complex_b_split = split_free_layout_questions_v3(
        file_id=multi_page_complex_b["file_id"],
        page_ocr_results=multi_page_complex_b["page_ocr_results"],
    )
    _assert(len(multi_page_complex_b_split["question_candidates"]) >= 4, "complex B should still produce multiple candidates despite OCR noise")

    review_record = submit_ocr_review(
        file_id=basic_case["file_id"],
        question_no="1",
        raw_text="什么是社会主义核心价值观？",
        corrected_text="社会主义核心价值观是国家、社会和个人层面的核心价值要求。",
        operator_id="tester",
        merge_group_id="mg_file_mock_001_q1_001",
    )

    export_result = export_question_level_results(
        file_id=basic_case["file_id"],
        route_type="free_layout_homework",
        merged_questions=merge_cross_page_answers(
            file_id=basic_case["file_id"],
            route_type="free_layout_homework",
            question_candidates=basic_split["question_candidates"],
        )["merged_questions"],
        review_results=[review_record],
    )
    _assert(len(export_result["question_level_results"]) == 2, "export should contain 2 question-level results")
    _assert(
        export_result["question_level_results"][0]["final_text"] == review_record["after_text"],
        "review text should bind by merge_group_id",
    )


if __name__ == "__main__":
    run_smoke_check()
    print("B module smoke check v2 passed.")
