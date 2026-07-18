from __future__ import annotations

import hashlib

import pytest

from processing_registry import service


def _configure_registry(tmp_path, monkeypatch) -> None:
    root = tmp_path / "results"
    monkeypatch.setattr(service, "RESULT_ROOT", root)
    monkeypatch.setattr(service, "RESULT_INDEX_FILE", root / "index.json")


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
