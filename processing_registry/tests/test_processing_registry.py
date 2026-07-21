from __future__ import annotations

import hashlib

import pytest

from processing_registry import service


def _configure_registry(tmp_path, monkeypatch) -> None:
    root = tmp_path / "results"
    monkeypatch.setattr(service, "RESULT_ROOT", root)
    monkeypatch.setattr(service, "RESULT_INDEX_FILE", root / "index.json")
    registry_root = tmp_path / "registry"
    monkeypatch.setattr(service, "REGISTRY_ROOT", registry_root)
    monkeypatch.setattr(service, "TASK_INDEX_FILE", registry_root / "tasks.json")
    monkeypatch.setattr(service, "ANSWER_INDEX_FILE", registry_root / "answers.json")
    monkeypatch.setattr(service, "REVIEW_INDEX_FILE", registry_root / "reviews.json")


def test_result_is_persisted_and_retrievable(tmp_path, monkeypatch) -> None:
    _configure_registry(tmp_path, monkeypatch)
    fingerprint = {"document_role": "question_paper", "file_sha256": "abc"}
    result = {"schema_version": "exam-document.v1", "submission_id": "sub_1", "questions": []}

    service.save_result("sub_1", fingerprint, result)

    assert service.get_result("sub_1") == result
    assert service.get_cached_result("sub_1", fingerprint) == result


def test_submission_id_cannot_be_reused_for_different_input(tmp_path, monkeypatch) -> None:
    _configure_registry(tmp_path, monkeypatch)
    service.save_result("sub_1", {"file_sha256": "first"}, {"submission_id": "sub_1"})

    with pytest.raises(ValueError, match="different processing request"):
        service.get_cached_result("sub_1", {"file_sha256": "second"})


def test_internal_task_answer_and_review_records_do_not_change_final_result(tmp_path, monkeypatch) -> None:
    _configure_registry(tmp_path, monkeypatch)
    result = {
        "schema_version": "exam-document.v1",
        "submission_id": "sub_1",
        "exam_id": "exam_1",
        "document_role": "answer_sheet",
        "answers": [{
            "question_id": "1.1", "question_no": "1", "answer_text": "脱敏后的答案",
            "is_blank": False, "page_nos": [1], "confidence": 0.6,
            "needs_review": True, "risk_flags": ["low_ocr_confidence"],
        }],
    }

    service.start_task("sub_1", {"document_role": "answer_sheet", "exam_id": "exam_1"})
    task = service.finalize_submission(
        "sub_1",
        result,
        review_records=[{"review_id": "review_1", "question_no": "1", "after_text": "教师确认后的答案"}],
    )

    assert task["status"] == "needs_review"
    assert task["needs_review_count"] == 1
    assert service.get_answer_records("sub_1")[0]["content_text"] == "脱敏后的答案"
    assert service.get_review_records("sub_1")[0]["after_text"] == "教师确认后的答案"
    assert "task_id" not in result
    assert "identity_fields" not in result
