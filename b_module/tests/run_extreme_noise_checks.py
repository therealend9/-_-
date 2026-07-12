from __future__ import annotations

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from b_module.question_segmenter.free_layout_pipeline import split_free_layout_questions_v2


def _run_case(
    name: str,
    page_ocr_results: list[dict],
    expected_block_ids: list[str],
    expected_text_excludes: list[str],
) -> None:
    result = split_free_layout_questions_v2(file_id=name, page_ocr_results=page_ocr_results)
    candidates = result["question_candidates"]
    assert len(candidates) == 1, f"{name}: expected 1 candidate, got {len(candidates)}"
    candidate = candidates[0]
    text = candidate["text"]
    assert candidate["block_ids"] == expected_block_ids, f"{name}: unexpected block ids {candidate['block_ids']}"
    for excluded in expected_text_excludes:
        assert excluded not in text, f"{name}: unexpected trailing noise kept: {excluded}"
    assert candidate["needs_review"] is False, f"{name}: should not require review"
    print(f"[PASS] {name}")


def main() -> int:
    footer_noise_case = [
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
                    "block_id": "blk_footer_0001",
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
                    "block_id": "blk_footer_0002",
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
                    "block_id": "blk_footer_0003",
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

    image_end_case = [
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
                    "block_id": "blk_image_end_0001",
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
                    "block_id": "blk_image_end_0002",
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
                    "block_id": "blk_image_end_0003",
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

    legit_continuation_case = [
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
                    "block_id": "blk_legit_0001",
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
                    "block_id": "blk_legit_0002",
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
                    "block_id": "blk_legit_0003",
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

    _run_case(
        name="footer_noise_case",
        page_ocr_results=footer_noise_case,
        expected_block_ids=["blk_footer_0001"],
        expected_text_excludes=["OCRPageResult", "reading_order", "bbox", "confidence"],
    )
    _run_case(
        name="image_end_case",
        page_ocr_results=image_end_case,
        expected_block_ids=["blk_image_end_0001", "blk_image_end_0002"],
        expected_text_excludes=["图片结束"],
    )
    _run_case(
        name="legit_continuation_case",
        page_ocr_results=legit_continuation_case,
        expected_block_ids=["blk_legit_0001", "blk_legit_0002", "blk_legit_0003"],
        expected_text_excludes=[],
    )
    print("All extreme noise checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
