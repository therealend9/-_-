"""Teacher-facing messages for API errors.

Internal services can retain concise technical exceptions for code-level checks.
This module is the HTTP boundary that turns known failures into instructions a
teacher can act on, without exposing paths, stack traces, or parser details.
"""

from __future__ import annotations

import re


_DUPLICATE_QUESTION_ID = re.compile(r"^Duplicate question_id:\s*(?P<question_id>.+)$")
_QUESTION_ID_MISMATCH = re.compile(
    r"^Template question_id mismatch; missing=(?P<missing>.+), unexpected=(?P<unexpected>.+)$"
)
_UNREVIEWED_REGIONS = re.compile(r"^Template has (?P<count>\d+) unreviewed region\(s\)$")
_IDENTITY_REQUIRED = re.compile(r"^Template requires exactly one (?P<field>[a-z_]+) region$")
_IDENTITY_OPTIONAL_DUPLICATE = re.compile(r"^Template allows at most one (?P<field>[a-z_]+) region$")
_IDENTITY_UNREVIEWED = re.compile(r"^Template (?P<field>[a-z_]+) region must be reviewed before publishing$")

_IDENTITY_FIELD_LABELS = {
    "student_name": "姓名",
    "student_no": "学号",
    "major": "专业",
    "college": "学院",
    "grade": "年级",
}


def teacher_message(raw_message: str) -> str:
    """Return a safe, actionable Chinese message for known API failures."""
    message = str(raw_message or "").strip()

    duplicate = _DUPLICATE_QUESTION_ID.match(message)
    if duplicate:
        question_id = duplicate.group("question_id")
        return (
            f"发现重复题目编号：{question_id}。这道题可能被重复识别，"
            "或跨页题目没有合并。请检查试题切分结果后再提交。"
        )

    mismatch = _QUESTION_ID_MISMATCH.match(message)
    if mismatch:
        return (
            "答题卡模板中的题目编号与试题目录不一致。"
            f"模板缺少的题目：{mismatch.group('missing')}；"
            f"模板多出的题目：{mismatch.group('unexpected')}。"
            "请检查试题卷和答题卡模板是否属于同一场考试。"
        )

    unreviewed = _UNREVIEWED_REGIONS.match(message)
    if unreviewed:
        return (
            f"答题卡模板还有 {unreviewed.group('count')} 个区域没有确认。"
            "请在模板复核页面检查区域位置后再发布。"
        )

    required = _IDENTITY_REQUIRED.match(message)
    if required:
        label = _IDENTITY_FIELD_LABELS.get(required.group("field"), required.group("field"))
        return f"模板中必须有一个{label}区域。请在模板复核页面补充并确认该区域。"

    optional_duplicate = _IDENTITY_OPTIONAL_DUPLICATE.match(message)
    if optional_duplicate:
        label = _IDENTITY_FIELD_LABELS.get(optional_duplicate.group("field"), optional_duplicate.group("field"))
        return f"模板中{label}区域重复。请只保留一个{label}区域。"

    identity_unreviewed = _IDENTITY_UNREVIEWED.match(message)
    if identity_unreviewed:
        label = _IDENTITY_FIELD_LABELS.get(identity_unreviewed.group("field"), identity_unreviewed.group("field"))
        return f"{label}区域还没有完成确认。请在模板复核页面检查位置后再发布。"

    known_messages = {
        "Question paper did not produce any questions": "没有识别出题目。请确认上传的是清晰完整的试题卷后重新识别。",
        "Question catalog is frozen after an answer-sheet template is bound": (
            "题目目录已经和答题卡模板绑定，不能直接更换题目编号。"
            "请确认上传的是同一场考试的试题卷。"
        ),
        "Each question requires question_id, question_no, and question_text": (
            "题目信息不完整。请检查试题识别结果是否包含题号和题目内容。"
        ),
        "Exam must bind a template before it can be published": (
            "考试尚未绑定答题卡模板。请先完成模板复核和绑定，再发布考试。"
        ),
        "Cannot change the template after answer-sheet submissions exist": (
            "已经有学生答题卡使用了当前模板，不能直接更换模板。"
            "请新建一个考试或联系管理员处理。"
        ),
        "Published template is immutable; create a new template_id for changes": (
            "答题卡模板已经发布，不能直接修改。请复制后创建新版本再调整。"
        ),
        "Exam must have a saved question catalog before binding an answer-sheet template": (
            "请先完成试题卷识别并保存题目目录，再绑定答题卡模板。"
        ),
        "Template must contain answer regions": (
            "答题卡模板中没有答题区域。请在模板复核页面划分每道题的答题区域。"
        ),
        "identity region must not overlap a question or answer region": (
            "姓名或学号区域与答题区域重叠。请调整区域位置后重新保存模板。"
        ),
        "student_name and student_no regions must not overlap": (
            "姓名区域和学号区域重叠。请调整两个区域的位置后重新保存模板。"
        ),
        "identity regions must not overlap": (
            "姓名、学号、专业、学院或年级区域之间发生重叠。请调整区域位置后重新保存模板。"
        ),
        "answer_sheet processing requires an exam-bound template": (
            "该考试尚未绑定可用的答题卡模板。请先创建、复核并发布模板。"
        ),
    }
    if message in known_messages:
        return known_messages[message]

    if message.startswith("Exam not found:"):
        return "未找到所选考试。请确认考试是否已经创建，或重新选择考试。"
    if message.startswith("Answer-sheet template not found:"):
        return "未找到答题卡模板。请确认模板是否存在，或重新创建模板。"
    if message.startswith("Exam status does not allow template binding:"):
        return "当前考试状态不允许更换答题卡模板。请确认考试尚未发布且没有学生提交。"
    if message.startswith("Template must be published before binding:"):
        return "答题卡模板尚未发布。请完成区域复核并发布模板后再绑定考试。"
    if message.startswith("duplicate region order for question_id="):
        question_id = message.split("=", maxsplit=1)[1]
        return f"题目 {question_id} 的答题区域顺序重复。请重新调整区域顺序。"
    if message == "question/answer regions require question_id and question_no":
        return "答题区域缺少题目编号。请在模板复核页面为该区域选择对应题目。"

    return "操作未完成。请检查文件、模板或考试设置后重试；如果仍然失败，请联系管理员。"


def runtime_message(raw_message: str) -> tuple[str, str, str]:
    """Return error code, teacher message, and teacher-facing solution."""
    message = str(raw_message or "")
    if "PaddleOCR" in message or "paddleocr" in message or "paddlepaddle" in message:
        return (
            "OCR_DEPENDENCY_MISSING",
            "文字识别服务暂时不可用。",
            "请联系管理员检查识别环境后重试。",
        )
    if "OpenVINO" in message or "openvino" in message or "Handwriting OCR model" in message:
        return (
            "HANDWRITING_OCR_DEPENDENCY_MISSING",
            "手写文字识别服务暂时不可用。",
            "请联系管理员检查手写识别模型和运行环境后重试。",
        )
    return (
        "PROCESSING_FAILED",
        "文件处理没有完成。",
        "请检查文件是否清晰、完整且属于当前考试；如果仍然失败，请联系管理员。",
    )
