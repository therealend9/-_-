from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from b_module.question_segmenter import uniform_exam_processor
from b_module.pipeline.service import _build_uniform_export
from full_pipeline import OUTPUT_SCHEMA_VERSION
from region_extractor import service as region_extractor_service
from region_ocr.service import detect_blank_region
from template_builder.service import _map_regions_to_exam_questions
from template_registry import service as template_service


def _write_image(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def test_region_processing_supports_non_ascii_paths(tmp_path: Path, monkeypatch) -> None:
    source_dir = tmp_path / "学生答卷"
    output_dir = tmp_path / "识别输出"
    source_dir.mkdir()
    student_path = source_dir / "答题卡.png"
    reference_path = source_dir / "空白模板.png"
    student = Image.new("RGB", (100, 100), "white")
    ImageDraw.Draw(student).rectangle((20, 20, 50, 50), fill="black")
    _write_image(student_path, student)
    _write_image(reference_path, Image.new("RGB", (100, 100), "white"))
    monkeypatch.setattr(region_extractor_service.config, "PREPROCESSED_DIR", output_dir)

    student_crop = region_extractor_service.crop_region(str(student_path), [0.1, 0.1, 0.9, 0.9], "学生答案")
    reference_crop = region_extractor_service.crop_region(str(reference_path), [0.1, 0.1, 0.9, 0.9], "空白答案")

    assert Path(student_crop["image_path"]).is_file()
    result = detect_blank_region(student_crop["image_path"], reference_crop["image_path"])
    assert result["is_blank"] is False


def test_template_validation_and_exam_binding(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(template_service, "TEMPLATE_ROOT", tmp_path / "templates")
    monkeypatch.setattr(template_service, "EXAM_BINDING_FILE", tmp_path / "templates" / "exam_bindings.json")
    monkeypatch.setattr(template_service, "EXAMS_FILE", tmp_path / "templates" / "exams.json")
    template = {
        "template_id": "tpl_test_v1", "version": 1, "page_count": 1,
        "pages": [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
            {"question_id": "q1", "question_no": "1", "order": 1, "bbox": [0.1, 0.1, 0.9, 0.9]},
        ]}],
    }
    template_service.save_template(template)
    template_service.publish_template("tpl_test_v1")
    template_service.create_exam("exam_1", "Template Test")
    template_service.save_exam_questions("exam_1", [{
        "question_id": "q1", "question_no": "1", "question_text": "Test question",
    }], "sub_question_paper")
    template_service.bind_exam_template("exam_1", "tpl_test_v1")
    assert template_service.get_exam_template("exam_1")["template_id"] == "tpl_test_v1"


def test_identity_regions_are_reviewed_and_must_not_overlap_answers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(template_service, "TEMPLATE_ROOT", tmp_path / "templates")
    template = {
        "template_id": "tpl_identity", "version": 1, "page_count": 1,
        "identity_protection": {"required": True, "status": "pending_review"},
        "pages": [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
            {"content_type": "student_name", "bbox": [0.1, 0.05, 0.4, 0.10], "needs_review": False},
            {"content_type": "student_no", "bbox": [0.5, 0.05, 0.9, 0.10], "needs_review": False},
            {"question_id": "q1", "question_no": "1", "order": 1, "bbox": [0.1, 0.2, 0.9, 0.9]},
        ]}],
    }
    template_service.save_template(template)
    published = template_service.publish_template("tpl_identity")

    identity = [region for region in published["pages"][0]["regions"] if region["content_type"].startswith("student_")]
    assert all("question_id" not in region for region in identity)
    assert published["identity_protection"]["status"] == "confirmed"

    overlapping = dict(template)
    overlapping["template_id"] = "tpl_identity_overlap"
    overlapping["pages"] = [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
        {"content_type": "student_name", "bbox": [0.1, 0.2, 0.4, 0.3], "needs_review": False},
        {"content_type": "student_no", "bbox": [0.5, 0.05, 0.9, 0.10], "needs_review": False},
        {"question_id": "q1", "question_no": "1", "order": 1, "bbox": [0.1, 0.2, 0.9, 0.9]},
    ]}]
    try:
        template_service.save_template(overlapping)
    except ValueError as exc:
        assert "must not overlap" in str(exc)
    else:
        raise AssertionError("Expected identity/answer overlap to be rejected")


def test_exam_binding_rejects_template_with_mismatched_question_ids(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(template_service, "TEMPLATE_ROOT", tmp_path / "templates")
    monkeypatch.setattr(template_service, "EXAM_BINDING_FILE", tmp_path / "templates" / "exam_bindings.json")
    monkeypatch.setattr(template_service, "EXAMS_FILE", tmp_path / "templates" / "exams.json")
    template_service.create_exam("exam_1", "Template Test")
    template_service.save_exam_questions("exam_1", [{
        "question_id": "question_1", "question_no": "1", "question_text": "Test question",
    }], "sub_question_paper")
    template_service.save_template({
        "template_id": "tpl_wrong", "version": 1, "page_count": 1,
        "pages": [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
            {"question_id": "question_2", "question_no": "2", "order": 1, "bbox": [0.1, 0.1, 0.9, 0.9]},
        ]}],
    })
    template_service.publish_template("tpl_wrong")

    try:
        template_service.bind_exam_template("exam_1", "tpl_wrong")
    except ValueError as exc:
        assert "question_id mismatch" in str(exc)
    else:
        raise AssertionError("Expected question_id mismatch to prevent binding")


def test_bound_template_rejects_question_catalog_id_changes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(template_service, "TEMPLATE_ROOT", tmp_path / "templates")
    monkeypatch.setattr(template_service, "EXAM_BINDING_FILE", tmp_path / "templates" / "exam_bindings.json")
    monkeypatch.setattr(template_service, "EXAMS_FILE", tmp_path / "templates" / "exams.json")
    template_service.create_exam("exam_1", "Template Test")
    template_service.save_exam_questions("exam_1", [{
        "question_id": "2.1", "question_no": "2.1", "question_text": "Original question",
    }], "sub_original")
    template_service.save_template({
        "template_id": "tpl_1", "version": 1, "page_count": 1,
        "pages": [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
            {"question_id": "2.1", "question_no": "2.1", "order": 1, "bbox": [0.1, 0.1, 0.9, 0.9]},
        ]}],
    })
    template_service.publish_template("tpl_1")
    template_service.bind_exam_template("exam_1", "tpl_1")

    try:
        template_service.save_exam_questions("exam_1", [{
            "question_id": "3.1", "question_no": "3.1", "question_text": "Changed question",
        }], "sub_changed")
    except ValueError as exc:
        assert "question_id mismatch" in str(exc)
    else:
        raise AssertionError("Expected bound template to prevent catalog ID changes")


def test_bound_template_freezes_question_catalog_content(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(template_service, "TEMPLATE_ROOT", tmp_path / "templates")
    monkeypatch.setattr(template_service, "EXAM_BINDING_FILE", tmp_path / "templates" / "exam_bindings.json")
    monkeypatch.setattr(template_service, "EXAMS_FILE", tmp_path / "templates" / "exams.json")
    template_service.create_exam("exam_1", "Template Test")
    template_service.save_exam_questions("exam_1", [{
        "question_id": "2.1", "question_no": "2.1", "question_text": "Original question",
    }], "sub_original")
    template_service.save_template({
        "template_id": "tpl_1", "version": 1, "page_count": 1,
        "pages": [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
            {"question_id": "2.1", "question_no": "2.1", "order": 1, "bbox": [0.1, 0.1, 0.9, 0.9]},
        ]}],
    })
    template_service.publish_template("tpl_1")
    template_service.bind_exam_template("exam_1", "tpl_1")

    try:
        template_service.save_exam_questions("exam_1", [{
            "question_id": "2.1", "question_no": "2.1", "question_text": "Different question text",
        }], "sub_changed")
    except ValueError as exc:
        assert "Question catalog is frozen" in str(exc)
    else:
        raise AssertionError("Expected bound template to freeze question text")


def test_published_template_rejects_review_and_direct_save(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(template_service, "TEMPLATE_ROOT", tmp_path / "templates")
    template = {
        "template_id": "tpl_published", "version": 1, "page_count": 1,
        "pages": [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
            {"question_id": "q1", "question_no": "1", "order": 1, "bbox": [0.1, 0.1, 0.9, 0.9]},
        ]}],
    }
    template_service.save_template(template)
    published = template_service.publish_template("tpl_published")

    try:
        template_service.review_template("tpl_published", published["pages"])
    except ValueError as exc:
        assert "immutable" in str(exc)
    else:
        raise AssertionError("Expected published template review to be rejected")

    changed = dict(published)
    changed["pages"] = [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
        {"question_id": "q1", "question_no": "1", "order": 1, "bbox": [0.2, 0.1, 0.9, 0.9]},
    ]}]
    try:
        template_service.save_template(changed)
    except ValueError as exc:
        assert "immutable" in str(exc)
    else:
        raise AssertionError("Expected direct published template update to be rejected")


def test_binding_requires_draft_exam_and_published_versioned_template(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(template_service, "TEMPLATE_ROOT", tmp_path / "templates")
    monkeypatch.setattr(template_service, "EXAM_BINDING_FILE", tmp_path / "templates" / "exam_bindings.json")
    monkeypatch.setattr(template_service, "EXAMS_FILE", tmp_path / "templates" / "exams.json")
    monkeypatch.setattr(template_service, "SUBMISSIONS_FILE", tmp_path / "templates" / "answer_sheet_submissions.json")
    template_service.create_exam("exam_1", "Template Test")
    template_service.save_exam_questions("exam_1", [{
        "question_id": "q1", "question_no": "1", "question_text": "Question",
    }], "sub_question")
    template_service.save_template({
        "template_id": "tpl_draft", "version": 1, "page_count": 1,
        "pages": [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
            {"question_id": "q1", "question_no": "1", "order": 1, "bbox": [0.1, 0.1, 0.9, 0.9]},
        ]}],
    })
    try:
        template_service.bind_exam_template("exam_1", "tpl_draft")
    except ValueError as exc:
        assert "published" in str(exc)
    else:
        raise AssertionError("Expected draft template to be rejected")
    template_service.publish_template("tpl_draft")
    template_service.bind_exam_template("exam_1", "tpl_draft")
    template_service.set_exam_status("exam_1", "published")
    try:
        template_service.bind_exam_template("exam_1", "tpl_draft")
    except ValueError as exc:
        assert "does not allow" in str(exc)
    else:
        raise AssertionError("Expected published exam to reject binding changes")
    try:
        template_service.validate_template({"template_id": "missing_version", "pages": []})
    except ValueError as exc:
        assert "version" in str(exc)
    else:
        raise AssertionError("Expected template without an explicit version to be rejected")


def test_answer_sheet_submission_locks_template_replacement(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(template_service, "TEMPLATE_ROOT", tmp_path / "templates")
    monkeypatch.setattr(template_service, "EXAM_BINDING_FILE", tmp_path / "templates" / "exam_bindings.json")
    monkeypatch.setattr(template_service, "EXAMS_FILE", tmp_path / "templates" / "exams.json")
    monkeypatch.setattr(template_service, "SUBMISSIONS_FILE", tmp_path / "templates" / "answer_sheet_submissions.json")
    template_service.create_exam("exam_1", "Template Test")
    template_service.save_exam_questions("exam_1", [{
        "question_id": "q1", "question_no": "1", "question_text": "Question",
    }], "sub_question")
    for template_id in ("tpl_v1", "tpl_v2"):
        template_service.save_template({
            "template_id": template_id, "version": 1, "page_count": 1,
            "pages": [{"page_no": 1, "reference_width": 100, "reference_height": 100, "regions": [
                {"question_id": "q1", "question_no": "1", "order": 1, "bbox": [0.1, 0.1, 0.9, 0.9]},
            ]}],
        })
        template_service.publish_template(template_id)
    template_service.bind_exam_template("exam_1", "tpl_v1")
    template_service.record_answer_sheet_submission("exam_1", "student_001", template_service.get_template("tpl_v1"))
    try:
        template_service.bind_exam_template("exam_1", "tpl_v2")
    except ValueError as exc:
        assert "submissions exist" in str(exc)
    else:
        raise AssertionError("Expected submitted exam to reject template replacement")


def test_template_regions_map_to_exam_question_catalog() -> None:
    pages = [{"page_no": 1, "regions": [
        {"question_id": "1", "question_no": "1", "bbox": [0.1, 0.1, 0.9, 0.3], "needs_review": True},
        {"question_id": "2", "question_no": "2", "bbox": [0.1, 0.4, 0.9, 0.7], "needs_review": True},
    ]}]
    questions = [
        {"question_id": "2.1", "question_no": "2.1", "question_text": "First canonical question"},
        {"question_id": "2.2", "question_no": "2.2", "question_text": "Second canonical question"},
    ]

    mapped_pages, status = _map_regions_to_exam_questions(pages, questions)

    regions = mapped_pages[0]["regions"]
    assert status == "mapped"
    assert [region["question_id"] for region in regions] == ["2.1", "2.2"]
    assert [region["template_label"] for region in regions] == ["1", "2"]
    assert all(region["question_id_source"] == "exam_question_catalog" for region in regions)


def test_document_output_schema_version_is_fixed() -> None:
    assert OUTPUT_SCHEMA_VERSION == "exam-document.v1"


def test_fixed_regions_merge_and_blank_detection(tmp_path: Path, monkeypatch) -> None:
    reference = Image.new("RGB", (100, 100), "white")
    student = reference.copy()
    ImageDraw.Draw(student).rectangle((20, 20, 55, 45), fill="black")
    reference_path = tmp_path / "reference.png"
    student_path = tmp_path / "student.png"
    _write_image(reference_path, reference)
    _write_image(student_path, student)

    monkeypatch.setattr(uniform_exam_processor, "run_ocr_on_region", lambda **kwargs: {
        "ocr_text": "answer" if "q1" in kwargs["image_path"] else "",
        "ocr_confidence": 0.9,
        "ocr_blocks": [],
        "ocr_mode": "handwriting",
    })
    template = {
        "template_id": "tpl_test_v1", "version": 1, "_template_dir": str(tmp_path),
        "pages": [{
            "page_no": 1, "reference_width": 100, "reference_height": 100,
            "reference_image_path": "reference.png",
            "regions": [
                {"question_id": "q1", "question_no": "1", "order": 1, "bbox": [0.1, 0.1, 0.5, 0.5]},
                {"question_id": "q1", "question_no": "1", "order": 2, "bbox": [0.5, 0.5, 0.9, 0.9]},
            ],
        }],
    }
    page = {"file_id": "file_test", "page_no": 1, "page_image_path": str(student_path), "preprocessed_image_path": None}
    result = uniform_exam_processor.split_uniform_exam_questions(
        file_id="file_test", template_id="tpl_test_v1", question_regions=[{"question_no": "1", "page_no": 1, "bbox": [0, 0, 1, 1]}],
        normalized_pages=[page], template=template,
    )
    assert len(result["question_level_results"]) == 1
    question = result["question_level_results"][0]
    assert question["question_id"] == "q1"
    assert len(question["region_results"]) == 2
    assert question["ocr_text"] == "answer"
    exported = _build_uniform_export("file_test", result, "answer_sheet")
    assert exported["answers"][0]["question_id"] == "q1"
