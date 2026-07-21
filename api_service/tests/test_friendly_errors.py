from __future__ import annotations

from api_service.friendly_errors import runtime_message, teacher_message


def test_duplicate_question_id_is_explained_for_teachers() -> None:
    message = teacher_message("Duplicate question_id: 1.2")

    assert "重复题目编号：1.2" in message
    assert "跨页题目没有合并" in message


def test_template_mismatch_is_explained_for_teachers() -> None:
    message = teacher_message("Template question_id mismatch; missing=['1.2'], unexpected=['2.1']")

    assert "题目编号与试题目录不一致" in message
    assert "模板缺少的题目" in message
    assert "模板多出的题目" in message


def test_unknown_internal_error_is_not_exposed() -> None:
    message = teacher_message(r"C:\internal\secret\parser-error")

    assert message == "操作未完成。请检查文件、模板或考试设置后重试；如果仍然失败，请联系管理员。"


def test_runtime_dependency_message_hides_technical_details() -> None:
    error_code, message, hint = runtime_message("OpenVINO model missing at C:\\internal\\model.xml")

    assert error_code == "HANDWRITING_OCR_DEPENDENCY_MISSING"
    assert "手写文字识别服务" in message
    assert "C:\\internal" not in message
    assert "管理员" in hint
