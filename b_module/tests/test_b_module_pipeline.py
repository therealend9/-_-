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
    with (BASE_DIR / "mock_data" / filename).open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def test_basic_free_layout_split() -> None:
    case = _load_case("free_layout_case_basic.json")
    result = split_free_layout_questions_v2(
        file_id=case["file_id"],
        page_ocr_results=case["page_ocr_results"],
    )
    assert len(result["question_candidates"]) == 2
    assert result["question_candidates"][0]["question_no"] == "1"
    assert result["question_candidates"][1]["question_no"] == "2"
    assert "start_anchor_bbox" in result["question_candidates"][0]


def test_cross_page_merge() -> None:
    case = _load_case("free_layout_case_cross_page.json")
    split_result = split_free_layout_questions_v2(
        file_id=case["file_id"],
        page_ocr_results=case["page_ocr_results"],
    )
    merge_result = merge_cross_page_answers(
        file_id=case["file_id"],
        route_type="free_layout_homework",
        question_candidates=split_result["question_candidates"],
    )
    assert len(merge_result["merged_questions"]) == 1
    merged = merge_result["merged_questions"][0]
    assert merged["question_no"] == "2"
    assert merged["from_pages"] == [1, 2]
    assert "continuation_without_heading" in merged["merge_evidence"]


def test_multi_page_complex_a_should_keep_heading_and_answer_together() -> None:
    case = _load_case("free_layout_case_multi_page_complex_a.json")
    split_result = split_free_layout_questions_v2(
        file_id=case["file_id"],
        page_ocr_results=case["page_ocr_results"],
    )
    candidates = split_result["question_candidates"]
    assert len(candidates) == 5
    question_two = [item for item in candidates if item["question_no"] == "2"]
    assert len(question_two) == 2
    assert all("第二题答案" in item["text"] for item in question_two)
    assert candidates[0]["paragraph_ids"]


def test_export_result_uses_ocr_text_without_review() -> None:
    case = _load_case("free_layout_case_basic.json")
    split_result = split_free_layout_questions_v2(
        file_id=case["file_id"],
        page_ocr_results=case["page_ocr_results"],
    )
    merge_result = merge_cross_page_answers(
        file_id=case["file_id"],
        route_type="free_layout_homework",
        question_candidates=split_result["question_candidates"],
    )
    export_result = export_question_level_results(
        file_id=case["file_id"],
        route_type="free_layout_homework",
        merged_questions=merge_result["merged_questions"],
        review_results=[],
    )
    assert len(export_result["question_level_results"]) == 2
    assert export_result["question_level_results"][0]["final_text"] == export_result["question_level_results"][0]["ocr_text"]


def test_non_continuation_same_question_should_not_merge() -> None:
    candidates = [
        {
            "file_id": "file_mock_gap",
            "route_type": "free_layout_homework",
            "question_no": "3",
            "page_no": 1,
            "block_ids": ["blk_1"],
            "text": "3. 第一页答案内容",
            "split_confidence": 0.92,
            "needs_review": False,
            "start_block_id": "blk_1",
            "end_block_id": "blk_1",
            "start_anchor_bbox": [100, 150, 600, 220],
            "end_anchor_bbox": [100, 300, 1800, 520],
            "page_height": 3508,
            "issue_flags": [],
        },
        {
            "file_id": "file_mock_gap",
            "route_type": "free_layout_homework",
            "question_no": "3",
            "page_no": 2,
            "block_ids": ["blk_2"],
            "text": "3. 新起一题，但题号重复",
            "split_confidence": 0.9,
            "needs_review": True,
            "start_block_id": "blk_2",
            "end_block_id": "blk_2",
            "start_anchor_bbox": [100, 1300, 700, 1380],
            "end_anchor_bbox": [100, 1300, 1800, 1550],
            "page_height": 3508,
            "issue_flags": ["repeated_question_no"],
        },
    ]
    merge_result = merge_cross_page_answers(
        file_id="file_mock_gap",
        route_type="free_layout_homework",
        question_candidates=candidates,
    )
    assert len(merge_result["merged_questions"]) == 2


def test_ocr_heading_error_should_reduce_split_count_and_mark_risk() -> None:
    case = _load_case("free_layout_case_ocr_heading_error.json")
    split_result = split_free_layout_questions_v2(
        file_id=case["file_id"],
        page_ocr_results=case["page_ocr_results"],
    )
    assert len(split_result["question_candidates"]) == 2
    first_candidate, second_candidate = split_result["question_candidates"]
    assert first_candidate["question_no"] == "1"
    assert second_candidate["question_no"] == "2"
    assert "ocr_heading_error_inferred" in second_candidate["issue_flags"]


def test_cross_page_boundary_negative_should_not_merge() -> None:
    case = _load_case("free_layout_case_cross_page_boundary_negative.json")
    split_result = split_free_layout_questions_v2(
        file_id=case["file_id"],
        page_ocr_results=case["page_ocr_results"],
    )
    merge_result = merge_cross_page_answers(
        file_id=case["file_id"],
        route_type="free_layout_homework",
        question_candidates=split_result["question_candidates"],
    )
    assert len(merge_result["merged_questions"]) == 2


def test_multi_page_complex_b_should_block_wrong_cross_page_merge() -> None:
    case = _load_case("free_layout_case_multi_page_complex_b.json")
    split_result = split_free_layout_questions_v2(
        file_id=case["file_id"],
        page_ocr_results=case["page_ocr_results"],
    )
    merge_result = merge_cross_page_answers(
        file_id=case["file_id"],
        route_type="free_layout_homework",
        question_candidates=split_result["question_candidates"],
    )
    merged_questions = merge_result["merged_questions"]
    assert len(merged_questions) == 4
    assert any(item["question_no"] == "3" for item in merged_questions)


def test_trailing_ocr_footer_noise_should_be_suppressed() -> None:
    page_ocr_results = [
        {
            "file_id": "file_noise_footer",
            "page_no": 1,
            "image_path": "mock/page1.png",
            "width": 1240,
            "height": 1754,
            "dpi": 300,
            "coordinate_base": "page_image",
            "ocr_engine": "unit_test",
            "overall_confidence": 0.99,
            "blocks": [
                {
                    "block_id": "blk_file_noise_footer_p001_0001",
                    "bbox": [60, 200, 320, 240],
                    "bbox_source": "ocr",
                    "source_mode": "ocr",
                    "text": "1. 什么是虚拟内存？",
                    "confidence": 0.99,
                    "reading_order": 1,
                    "is_low_confidence": False,
                    "line_index": 1,
                    "block_type": "image_ocr",
                },
                {
                    "block_id": "blk_file_noise_footer_p001_0002",
                    "bbox": [90, 260, 1080, 300],
                    "bbox_source": "ocr",
                    "source_mode": "ocr",
                    "text": "虚拟内存用于扩展可用地址空间，并通过分页机制提升内存利用率。",
                    "confidence": 0.99,
                    "reading_order": 2,
                    "is_low_confidence": False,
                    "line_index": 2,
                    "block_type": "image_ocr",
                },
                {
                    "block_id": "blk_file_noise_footer_p001_0003",
                    "bbox": [90, 340, 1120, 380],
                    "bbox_source": "ocr",
                    "source_mode": "ocr",
                    "text": "注意：本页用于测试 OCRPageResult text bbox confidence reading_order",
                    "confidence": 0.98,
                    "reading_order": 3,
                    "is_low_confidence": False,
                    "line_index": 3,
                    "block_type": "image_ocr",
                },
            ],
        }
    ]

    split_result = split_free_layout_questions_v2(
        file_id="file_noise_footer",
        page_ocr_results=page_ocr_results,
    )
    candidates = split_result["question_candidates"]
    assert len(candidates) == 1
    assert "OCRPageResult" not in candidates[0]["text"]
    assert candidates[0]["needs_review"] is False


def test_trailing_image_end_marker_should_be_suppressed() -> None:
    page_ocr_results = [
        {
            "file_id": "file_image_end",
            "page_no": 1,
            "image_path": "mock/page1.png",
            "width": 1240,
            "height": 1754,
            "dpi": 300,
            "coordinate_base": "page_image",
            "ocr_engine": "unit_test",
            "overall_confidence": 0.99,
            "blocks": [
                {
                    "block_id": "blk_file_image_end_p001_0001",
                    "bbox": [60, 200, 260, 240],
                    "bbox_source": "ocr",
                    "source_mode": "ocr",
                    "text": "2. 简述进程。",
                    "confidence": 0.99,
                    "reading_order": 1,
                    "is_low_confidence": False,
                    "line_index": 1,
                    "block_type": "image_ocr",
                },
                {
                    "block_id": "blk_file_image_end_p001_0002",
                    "bbox": [90, 260, 1060, 300],
                    "bbox_source": "ocr",
                    "source_mode": "ocr",
                    "text": "进程是程序的一次执行过程，是系统进行资源分配和调度的基本单位。",
                    "confidence": 0.99,
                    "reading_order": 2,
                    "is_low_confidence": False,
                    "line_index": 2,
                    "block_type": "image_ocr",
                },
                {
                    "block_id": "blk_file_image_end_p001_0003",
                    "bbox": [60, 320, 1180, 356],
                    "bbox_source": "estimated",
                    "source_mode": "text_extract",
                    "text": "图片结束",
                    "confidence": 1.0,
                    "reading_order": 3,
                    "is_low_confidence": False,
                    "line_index": 3,
                    "block_type": "text",
                },
            ],
        }
    ]

    split_result = split_free_layout_questions_v2(
        file_id="file_image_end",
        page_ocr_results=page_ocr_results,
    )
    candidates = split_result["question_candidates"]
    assert len(candidates) == 1
    assert "图片结束" not in candidates[0]["text"]
    assert candidates[0]["needs_review"] is False


def test_legitimate_ocr_continuation_should_not_be_suppressed() -> None:
    page_ocr_results = [
        {
            "file_id": "file_legit_continue",
            "page_no": 1,
            "image_path": "mock/page1.png",
            "width": 1240,
            "height": 1754,
            "dpi": 300,
            "coordinate_base": "page_image",
            "ocr_engine": "unit_test",
            "overall_confidence": 0.99,
            "blocks": [
                {
                    "block_id": "blk_file_legit_continue_p001_0001",
                    "bbox": [60, 200, 320, 240],
                    "bbox_source": "ocr",
                    "source_mode": "ocr",
                    "text": "3. 简述操作系统。",
                    "confidence": 0.99,
                    "reading_order": 1,
                    "is_low_confidence": False,
                    "line_index": 1,
                    "block_type": "image_ocr",
                },
                {
                    "block_id": "blk_file_legit_continue_p001_0002",
                    "bbox": [90, 260, 1080, 300],
                    "bbox_source": "ocr",
                    "source_mode": "ocr",
                    "text": "操作系统负责管理硬件与软件资源，",
                    "confidence": 0.99,
                    "reading_order": 2,
                    "is_low_confidence": False,
                    "line_index": 2,
                    "block_type": "image_ocr",
                },
                {
                    "block_id": "blk_file_legit_continue_p001_0003",
                    "bbox": [90, 306, 1000, 344],
                    "bbox_source": "ocr",
                    "source_mode": "ocr",
                    "text": "并为应用程序提供运行环境。",
                    "confidence": 0.99,
                    "reading_order": 3,
                    "is_low_confidence": False,
                    "line_index": 3,
                    "block_type": "image_ocr",
                },
            ],
        }
    ]

    split_result = split_free_layout_questions_v2(
        file_id="file_legit_continue",
        page_ocr_results=page_ocr_results,
    )
    candidates = split_result["question_candidates"]
    assert len(candidates) == 1
    assert "并为应用程序提供运行环境" in candidates[0]["text"]
    assert candidates[0]["needs_review"] is False
