from __future__ import annotations

import json

from d_module.data_redaction import service


def test_redacts_explicit_personal_data_without_mutating_source() -> None:
    source = {
        "schema_version": "exam-document.v1",
        "submission_id": "sub_1",
        "answers": [{
            "question_id": "q1",
            "question_no": "1",
            "answer_text": "姓名：张三；学号：202615001；电话：138 0013 8000；邮箱：student@example.com",
            "is_blank": False,
            "page_nos": [1],
            "confidence": 0.9,
            "needs_review": False,
            "risk_flags": [],
        }],
    }

    redacted, report = service.redact_result(source)
    answer = redacted["answers"][0]["answer_text"]

    assert "张三" not in answer
    assert "202615001" not in answer
    assert "138 0013 8000" not in answer
    assert "student@example.com" not in answer
    assert set(report["redacted_fields"]) == {"email", "phone", "student_name", "student_number"}
    assert source["answers"][0]["answer_text"].startswith("姓名：张三")


def test_redacts_email_when_ocr_concatenates_the_following_chinese_label() -> None:
    source = {"answers": [{"answer_text": "邮箱：test.student@example.com身份证号：11010519491231002X"}]}

    redacted, report = service.redact_result(source)

    assert redacted["answers"][0]["answer_text"] == "邮箱：[EMAIL_REDACTED]身份证号:[REDACTED]"
    assert set(report["redacted_fields"]) == {"email", "id_card"}


def test_redacts_path_and_filename_but_preserves_normal_question_content() -> None:
    source = {
        "origin_name": "student_001.pdf",
        "source_path": r"C:\Users\admin\storage\accepted\file_1\original.pdf",
        "questions": [{
            "question_id": "q1",
            "question_no": "1",
            "question_text": "请结合实际说明社会存在与社会意识的关系。",
            "page_nos": [1],
            "confidence": 0.9,
            "needs_review": False,
            "risk_flags": [],
        }],
    }

    redacted, report = service.redact_result(source)

    assert redacted["origin_name"] == "[REDACTED]"
    assert redacted["source_path"] == "[PATH_REDACTED]"
    assert redacted["questions"][0]["question_text"] == source["questions"][0]["question_text"]
    assert set(report["redacted_fields"]) == {"filename", "path"}


def test_audit_record_contains_no_original_content(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(service, "REDACTION_ROOT", tmp_path / "redaction")
    source = {
        "submission_id": "sub_1",
        "answers": [{"answer_text": "姓名：李四", "risk_flags": []}],
    }

    redacted = service.redact_and_record(source, "sub_1")
    report_path = next((tmp_path / "redaction").glob("*.json"))
    report_text = report_path.read_text(encoding="utf-8")
    report = json.loads(report_text)

    assert redacted["answers"][0]["answer_text"] == "姓名:[REDACTED]"
    assert "李四" not in report_text
    assert report["redaction_status"] == "redacted"
    assert report["source_result_sha256"] != report["redacted_result_sha256"]


def test_unlabeled_name_is_not_claimed_as_identifiable() -> None:
    source = {"answers": [{"answer_text": "我认为张三的观点需要进一步讨论。", "risk_flags": []}]}

    redacted, report = service.redact_result(source)

    assert redacted == source
    assert report["redaction_status"] == "clean"
