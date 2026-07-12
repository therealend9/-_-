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


def run_pipeline_llm_migration_smoke() -> None:
    case = _load_case("free_layout_case_cross_page.json")
    result = process_b_module(
        file_task={"file_id": case["file_id"], "task_status": "ocr_done"},
        normalized_pages=case.get("normalized_pages", []),
        page_ocr_results=case["page_ocr_results"],
        assignment_type="homework",
        llm_enabled=False,
    )

    _assert(result["context_status"] == "ready", "pipeline should complete in rule-fallback mode")
    _assert(result["risk_result"]["risk_summary"]["high_risk_candidates"] >= 1, "cross-page sample should produce at least one high-risk candidate")
    _assert(len(result["semantic_split_result"]["llm_decisions"]) >= 1, "rule-fallback path should emit reserved semantic decisions")
    _assert(len(result["semantic_merge_result"]["llm_decisions"]) >= 1, "cross-page merge should emit reserved semantic merge decisions")

    final_result = result["export_result"]["question_level_results"][0]
    _assert(final_result["decision_source"] in {"rule_fallback", "rule", "llm"}, "export should preserve decision source")
    _assert("semantic_reason" in final_result, "export should preserve semantic reason")


if __name__ == "__main__":
    run_pipeline_llm_migration_smoke()
    print("B module LLM migration smoke passed.")
