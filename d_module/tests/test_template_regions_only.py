from __future__ import annotations

from d_module import pipeline
from d_module.constants import PARSE_MODE_IMAGE, SOURCE_TYPE_IMAGE, TASK_STATUS_UPLOADED
from d_module.schemas.file_task import FileTask
from d_module.schemas.normalized_page import NormalizedPage


def test_template_regions_only_skips_whole_page_ocr(monkeypatch) -> None:
    task = FileTask(
        file_id="file_1", submission_id="sub_1", origin_name="answer.png", ext="png",
        mime_type="image/png", storage_path="storage/raw/file_1.png", file_size=1,
        page_count=None, source_type=SOURCE_TYPE_IMAGE, parse_mode=None,
        task_status=TASK_STATUS_UPLOADED, created_at="2026-07-19T00:00:00+00:00",
    )
    page = NormalizedPage(
        file_id="file_1", page_no=1, page_image_path="storage/pages/file_1.png",
        preprocessed_image_path=None, original_width=100, original_height=100,
        processed_width=100, processed_height=100,
    )
    calls = {"preprocess": 0}

    monkeypatch.setattr(pipeline, "create_file_task", lambda **kwargs: task)
    monkeypatch.setattr(pipeline, "classify_and_parse_document", lambda file_task: {"parse_mode": PARSE_MODE_IMAGE})
    monkeypatch.setattr(pipeline, "render_pages_to_images", lambda file_task, parse_result: [page])

    def fake_preprocess(pages):
        calls["preprocess"] += 1
        return list(pages)

    monkeypatch.setattr(pipeline, "preprocess_pages", fake_preprocess)
    monkeypatch.setattr(pipeline, "run_ocr_on_pages", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("whole-page OCR must not run")))

    result = pipeline.process_file_to_ocr_results(
        submission_id="sub_1", origin_name="answer.png", mime_type="image/png",
        file_bytes=b"x", parse_strategy="template_regions_only",
    )

    assert calls["preprocess"] == 1
    assert result["ocr_page_results"] == []
