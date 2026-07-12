from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from b_module.pipeline.service import process_b_module


def _load_case(filename: str) -> dict:
    with (BASE_DIR / "mock_data" / filename).open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_pipeline_interface_smoke() -> None:
    free_case = _load_case("free_layout_case_basic.json")
    free_result = process_b_module(
        file_task={"file_id": free_case["file_id"], "task_status": "ocr_done"},
        normalized_pages=free_case.get("normalized_pages", []),
        page_ocr_results=free_case["page_ocr_results"],
        assignment_type="homework",
    )
    _assert(free_result["context_status"] == "ready", "free route should be ready")
    _assert(free_result["route_decision"]["route_type"] == "free_layout_homework", "free route should go to free_layout_homework")
    _assert(len(free_result["export_result"]["question_level_results"]) == 2, "free route should export 2 results")

    uniform_pending = process_b_module(
        file_task={"file_id": "file_uniform_001", "task_status": "ocr_done"},
        normalized_pages=[],
        page_ocr_results=[],
        assignment_type="uniform_exam",
        template_id="tpl_001",
        question_regions=[],
    )
    _assert(uniform_pending["context_status"] == "waiting_a_regions", "uniform route should wait for A regions when absent")
    _assert(uniform_pending["uniform_result"]["status"] == "pending_a_output", "uniform route placeholder status should be pending_a_output")


if __name__ == "__main__":
    run_pipeline_interface_smoke()
    print("B module pipeline interface smoke passed.")
