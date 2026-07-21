from __future__ import annotations

import pytest

import full_pipeline
from d_module.data_redaction import service as redaction_service
from processing_registry import service as result_service


@pytest.fixture(autouse=True)
def _isolate_internal_registry(tmp_path, monkeypatch):
    root = tmp_path / "registry"
    monkeypatch.setattr(result_service, "REGISTRY_ROOT", root)
    monkeypatch.setattr(result_service, "TASK_INDEX_FILE", root / "tasks.json")
    monkeypatch.setattr(result_service, "ANSWER_INDEX_FILE", root / "answers.json")
    monkeypatch.setattr(result_service, "REVIEW_INDEX_FILE", root / "reviews.json")


def test_full_pipeline_reuses_persisted_result_for_identical_retry(tmp_path, monkeypatch) -> None:
    root = tmp_path / "results"
    monkeypatch.setattr(result_service, "RESULT_ROOT", root)
    monkeypatch.setattr(result_service, "RESULT_INDEX_FILE", root / "index.json")
    monkeypatch.setattr(redaction_service, "REDACTION_ROOT", tmp_path / "redaction")
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


def test_full_pipeline_persists_and_catalogs_redacted_question_result(tmp_path, monkeypatch) -> None:
    root = tmp_path / "results"
    monkeypatch.setattr(result_service, "RESULT_ROOT", root)
    monkeypatch.setattr(result_service, "RESULT_INDEX_FILE", root / "index.json")
    monkeypatch.setattr(redaction_service, "REDACTION_ROOT", tmp_path / "redaction")
    stored_questions = []
    calls = {"ocr": 0}

    def fake_ocr(**kwargs):
        calls["ocr"] += 1
        return {"file_task": {"file_id": "file_1"}, "normalized_pages": [], "ocr_page_results": []}

    monkeypatch.setattr(full_pipeline, "process_file_to_ocr_results", fake_ocr)
    monkeypatch.setattr(full_pipeline, "get_exam", lambda exam_id: {"exam_name": "马克思主义原理期末考试"})
    monkeypatch.setattr(full_pipeline, "save_exam_questions", lambda exam_id, questions, submission_id: stored_questions.extend(questions))
    monkeypatch.setattr(full_pipeline, "process_b_module", lambda **kwargs: {
        "export_result": {"questions": [{
            "question_id": "q1", "question_no": "1", "question_text": "联系电话：13800138000",
            "page_nos": [1], "confidence": 1.0, "needs_review": False, "risk_flags": [],
        }]},
    })
    request = {
        "submission_id": "sub_redacted",
        "origin_name": "paper.pdf",
        "mime_type": "application/pdf",
        "file_bytes": b"same document",
        "document_role": "question_paper",
        "exam_id": "mayuan_1516",
    }

    first = full_pipeline.process_file_to_question_results(**request)
    second = full_pipeline.process_file_to_question_results(**request)

    assert first == second
    assert calls["ocr"] == 1
    assert first["questions"][0]["question_text"] == "联系电话：[PHONE_REDACTED]"
    assert stored_questions[0]["question_text"] == "联系电话：[PHONE_REDACTED]"
    assert result_service.get_result("sub_redacted") == first


def test_redaction_audit_failure_prevents_result_persistence(tmp_path, monkeypatch) -> None:
    root = tmp_path / "results"
    monkeypatch.setattr(result_service, "RESULT_ROOT", root)
    monkeypatch.setattr(result_service, "RESULT_INDEX_FILE", root / "index.json")
    monkeypatch.setattr(full_pipeline, "process_file_to_ocr_results", lambda **kwargs: {
        "file_task": {"file_id": "file_1"}, "normalized_pages": [], "ocr_page_results": [],
    })
    monkeypatch.setattr(full_pipeline, "process_b_module", lambda **kwargs: {
        "export_result": {"questions": [{
            "question_id": "q1", "question_no": "1", "question_text": "Question",
            "page_nos": [1], "confidence": 1.0, "needs_review": False, "risk_flags": [],
        }]},
    })
    monkeypatch.setattr(full_pipeline, "redact_and_record", lambda result, submission_id: (_ for _ in ()).throw(OSError("audit unavailable")))

    with pytest.raises(OSError, match="audit unavailable"):
        full_pipeline.process_file_to_question_results(
            submission_id="sub_fail_closed",
            origin_name="paper.pdf",
            mime_type="application/pdf",
            file_bytes=b"same document",
            document_role="question_paper",
        )

    assert not root.exists()


def test_answer_sheet_template_skips_whole_page_ocr_and_ignores_identity_regions(tmp_path, monkeypatch) -> None:
    root = tmp_path / "results"
    monkeypatch.setattr(result_service, "RESULT_ROOT", root)
    monkeypatch.setattr(result_service, "RESULT_INDEX_FILE", root / "index.json")
    monkeypatch.setattr(redaction_service, "REDACTION_ROOT", tmp_path / "redaction")
    captured = {}
    template = {
        "template_id": "tpl_1", "template_name": "Answer sheet", "version": 1,
        "pages": [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
            {"content_type": "student_name", "bbox": [0.1, 0.05, 0.4, 0.1]},
            {"content_type": "student_no", "bbox": [0.5, 0.05, 0.9, 0.1]},
            {"content_type": "answer", "question_id": "q1", "question_no": "1", "order": 1, "bbox": [0.1, 0.2, 0.9, 0.9]},
        ]}],
    }

    def fake_ocr(**kwargs):
        captured["parse_strategy"] = kwargs["parse_strategy"]
        return {"file_task": {"file_id": "file_1"}, "normalized_pages": [], "ocr_page_results": []}

    def fake_b_module(**kwargs):
        captured["question_regions"] = kwargs["question_regions"]
        return {"export_result": {"answers": [{
            "question_id": "q1", "question_no": "1", "answer_text": "Answer",
            "is_blank": False, "page_nos": [1], "confidence": 1.0, "needs_review": False, "risk_flags": [],
        }]}}

    monkeypatch.setattr(full_pipeline, "process_file_to_ocr_results", fake_ocr)
    monkeypatch.setattr(full_pipeline, "process_b_module", fake_b_module)
    result = full_pipeline.process_file_to_question_results(
        submission_id="sub_answer", origin_name="answer.png", mime_type="image/png",
        file_bytes=b"answer sheet", document_role="answer_sheet", template=template,
    )

    assert captured["parse_strategy"] == "template_regions_only"
    assert [region["question_id"] for region in captured["question_regions"]] == ["q1"]
    assert result["answers"][0]["answer_text"] == "Answer"


def test_review_records_are_redacted_before_internal_persistence(tmp_path, monkeypatch) -> None:
    root = tmp_path / "results"
    monkeypatch.setattr(result_service, "RESULT_ROOT", root)
    monkeypatch.setattr(result_service, "RESULT_INDEX_FILE", root / "index.json")
    monkeypatch.setattr(redaction_service, "REDACTION_ROOT", tmp_path / "redaction")
    monkeypatch.setattr(full_pipeline, "process_file_to_ocr_results", lambda **kwargs: {
        "file_task": {"file_id": "file_1"}, "normalized_pages": [], "ocr_page_results": [],
    })
    monkeypatch.setattr(full_pipeline, "process_b_module", lambda **kwargs: {
        "export_result": {"questions": [{
            "question_id": "q1", "question_no": "1", "question_text": "Question",
            "page_nos": [1], "confidence": 1.0, "needs_review": False, "risk_flags": [],
        }]},
    })

    full_pipeline.process_file_to_question_results(
        submission_id="sub_review_redaction",
        origin_name="paper.pdf",
        mime_type="application/pdf",
        file_bytes=b"same document",
        document_role="question_paper",
        review_results=[{
            "review_id": "review_1", "question_no": "1",
            "before_text": "姓名：张三", "after_text": "学号：202401001",
        }],
    )

    review = result_service.get_review_records("sub_review_redaction")[0]
    assert review["before_text"] == "姓名:[REDACTED]"
    assert review["after_text"] == "学号:[REDACTED]"
