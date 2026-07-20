from __future__ import annotations

"""Run synthetic handwritten samples through OCR and the real final pipeline."""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SAMPLE_DIR = ROOT / "test_artifacts" / "redaction_handwriting_20260719" / "samples"
ARTIFACT_ROOT = ROOT / "test_artifacts" / "redaction_handwriting_20260719" / "runs"

EXPECTED_BY_SAMPLE = {
    "handwriting_sensitive_clear.png": [
        "测试甲",
        "TEST20260719001",
        "13900000000",
        "test.student@example.com",
        "11010519491231002X",
    ],
    "handwriting_sensitive_spaced.png": [
        "测试乙",
        "202615001",
        "138 0013 8000",
        "tester@example.com",
    ],
    "handwriting_non_sensitive.png": [],
}

PHONE_RE = re.compile(r"(?<!\d)1[3-9](?:[ -]?\d){9}(?!\d)")
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b")
ID_CARD_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")


def _string_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [item for child in value.values() for item in _string_values(child)]
    if isinstance(value, list):
        return [item for child in value for item in _string_values(child)]
    return [value] if isinstance(value, str) else []


def _scan_final_result(result: dict[str, Any], expected_values: list[str]) -> dict[str, list[str]]:
    text_values = _string_values(result)
    joined = "\n".join(text_values)
    return {
        "expected_values": [value for value in expected_values if value in joined],
        "phone_patterns": PHONE_RE.findall(joined),
        "email_patterns": EMAIL_RE.findall(joined),
        "id_card_patterns": ID_CARD_RE.findall(joined),
    }


def _ocr_texts(ocr_output: dict[str, Any]) -> list[str]:
    pages = ocr_output.get("ocr_page_results", [])
    return [
        str(block.get("text", ""))
        for page in pages
        for block in page.get("blocks", [])
        if str(block.get("text", ""))
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("terminal_%Y%m%dT%H%M%SZ"))
    args = parser.parse_args()

    run_dir = ARTIFACT_ROOT / args.run_id
    runtime_dir = run_dir / "runtime"
    os.environ["D_MODULE_STORAGE_ROOT"] = str(runtime_dir / "storage")
    os.environ["EXAM_PROCESSING_RESULT_ROOT"] = str(runtime_dir / "processing_results")
    os.environ["EXAM_PROCESSING_REDACTION_ROOT"] = str(runtime_dir / "redaction")

    from d_module.pipeline import process_file_to_ocr_results
    from full_pipeline import process_file_to_question_results

    run_dir.mkdir(parents=True, exist_ok=False)
    records = []
    for index, path in enumerate(sorted(SAMPLE_DIR.glob("*.png")), start=1):
        raw_ocr = process_file_to_ocr_results(
            submission_id=f"raw_{args.run_id}_{index}",
            origin_name=path.name,
            mime_type="image/png",
            source_path=path,
        )
        final_result = process_file_to_question_results(
            submission_id=f"final_{args.run_id}_{index}",
            origin_name=path.name,
            mime_type="image/png",
            source_path=path,
            document_role="question_paper",
            include_intermediate=True,
        )
        expected = EXPECTED_BY_SAMPLE[path.name]
        leaks = _scan_final_result(final_result, expected)
        records.append({
            "sample": path.name,
            "raw_ocr_texts": _ocr_texts(raw_ocr),
            "final_result": final_result,
            "sensitive_values_found_in_final_result": leaks,
            "passed": not any(leaks.values()),
        })

    report = {
        "run_id": args.run_id,
        "engine": "PaddleOCR via full_pipeline.process_file_to_question_results",
        "samples": records,
        "passed": all(record["passed"] for record in records),
    }
    output_path = run_dir / "terminal_validation_report.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_path)
    print(json.dumps({
        "run_id": args.run_id,
        "passed": report["passed"],
        "sample_results": [
            {"sample": item["sample"], "passed": item["passed"], "leaks": item["sensitive_values_found_in_final_result"]}
            for item in records
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
