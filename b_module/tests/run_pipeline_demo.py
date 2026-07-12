from __future__ import annotations

import json
from pathlib import Path

from b_module.cross_page_merger.service import merge_cross_page_answers
from b_module.question_segmenter.free_layout_pipeline import split_free_layout_questions_v2
from b_module.result_exporter.service import export_question_level_results


BASE_DIR = Path(__file__).resolve().parents[1]
MOCK_DIR = BASE_DIR / "mock_data"


def load_case(filename: str) -> dict:
    with (MOCK_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


def run_case(filename: str) -> dict:
    case = load_case(filename)
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
    return {
        "split_result": split_result,
        "merge_result": merge_result,
        "export_result": export_result,
    }


def main() -> None:
    for filename in ("free_layout_case_basic.json", "free_layout_case_cross_page.json"):
        result = run_case(filename)
        print(f"=== {filename} ===")
        print(json.dumps(result["export_result"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
