from __future__ import annotations

from identity_extractor import service


def test_extracts_all_configured_identity_fields_without_answer_regions(monkeypatch) -> None:
    template = {
        "pages": [{
            "page_no": 1,
            "regions": [
                {"content_type": "student_name", "bbox": [0.1, 0.1, 0.2, 0.2]},
                {"content_type": "student_no", "bbox": [0.2, 0.1, 0.3, 0.2]},
                {"content_type": "major", "bbox": [0.3, 0.1, 0.4, 0.2]},
                {"content_type": "college", "bbox": [0.4, 0.1, 0.5, 0.2]},
                {"content_type": "grade", "bbox": [0.5, 0.1, 0.6, 0.2]},
                {"content_type": "answer", "question_id": "q1", "question_no": "1", "bbox": [0.1, 0.3, 0.9, 0.9]},
            ],
        }],
        "_template_dir": "storage/templates/tpl_1",
    }
    page = {"page_no": 1, "page_image_path": "student.png"}

    monkeypatch.setattr(service, "align_page_to_template", lambda **kwargs: {"image_path": "aligned.png"})
    monkeypatch.setattr(service, "crop_region", lambda **kwargs: {"image_path": kwargs["output_stem"]})
    values = {
        "student_name": "张三",
        "student_no": "202615001",
        "major": "马克思主义理论",
        "college": "马克思主义学院",
        "grade": "2024级",
    }
    # Use the field name encoded by the crop output to keep the fake OCR deterministic.
    def fake_ocr(**kwargs):
        return {"ocr_text": next(field_value for field, field_value in values.items() if field in kwargs["image_path"]), "ocr_confidence": 0.95}

    monkeypatch.setattr(service, "run_ocr_on_region", fake_ocr)
    result = service.extract_identity_fields("file_1", template, [page])

    assert result["status"] == "recognized"
    assert {key: value["value"] for key, value in result["fields"].items()} == values
    assert "answer" not in result["fields"]
