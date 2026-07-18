from __future__ import annotations

import pytest

import full_pipeline
from processing_registry import service as result_service


def test_full_pipeline_reuses_persisted_result_for_identical_retry(tmp_path, monkeypatch) -> None:
    root = tmp_path / "results"
    monkeypatch.setattr(result_service, "RESULT_ROOT", root)
    monkeypatch.setattr(result_service, "RESULT_INDEX_FILE", root / "index.json")
    calls = {"ocr": 0}

    def fake_ocr(**kwargs):
        calls["ocr"] += 1
        return {"file_task": {"file_id": "file_1"}, "normalized_pages": [], "ocr_page_results": []}

    monkeypatch.setattr(full_pipeline, "process_file_to_ocr_results", fake_ocr)
    monkeypatch.setattr(full_pipeline, "process_b_module", lambda **kwargs: {
        "export_result": {"questions": [{
            "question_id": "q1", "question_no": "1", "question_text": "Question",
            "page_nos": [1], "confidence": 1.0, "needs_review": False, "risk_flags": [],
        }]},
    })
    request = {
        "submission_id": "sub_1",
        "origin_name": "paper.pdf",
        "mime_type": "application/pdf",
        "file_bytes": b"same document",
        "document_role": "question_paper",
    }

    first = full_pipeline.process_file_to_question_results(**request)
    second = full_pipeline.process_file_to_question_results(**request)

    assert first == second
    assert calls["ocr"] == 1
    assert result_service.get_result("sub_1") == first

    changed = dict(request)
    changed["file_bytes"] = b"different document"
    with pytest.raises(ValueError, match="different processing request"):
        full_pipeline.process_file_to_question_results(**changed)
