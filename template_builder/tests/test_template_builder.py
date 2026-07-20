from pathlib import Path

from PIL import Image, ImageDraw

from template_builder.service import (
    propose_identity_regions_from_ocr_pages,
    propose_regions_from_ocr_pages,
    propose_regions_from_page_layout,
)


def test_proposals_are_pending_manual_review() -> None:
    pages = [{"page_no": 1, "processed_width": 1000, "processed_height": 2000}]
    ocr_results = [{
        "page_no": 1,
        "blocks": [
            {"text": "1.", "bbox": [50, 180, 90, 220]},
            {"text": "2、", "bbox": [50, 900, 90, 940]},
        ],
    }]
    proposals = propose_regions_from_ocr_pages(pages, ocr_results)
    assert [item["question_id"] for item in proposals] == ["1", "2"]
    assert all(item["content_type"] == "answer" for item in proposals)
    assert all(item["needs_review"] is True for item in proposals)
    assert proposals[0]["bbox"][1] < proposals[0]["bbox"][3]


def test_rectangle_layout_proposals_prefer_answer_boxes(tmp_path: Path) -> None:
    image = Image.new("RGB", (1000, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((60, 100, 460, 700), outline="black", width=4)
    draw.rectangle((540, 100, 940, 700), outline="black", width=4)
    image_path = tmp_path / "answer_sheet.png"
    image.save(image_path)

    proposals = propose_regions_from_page_layout(
        [{"page_no": 1, "processed_width": 1000, "processed_height": 800, "page_image_path": str(image_path)}],
        [{"page_no": 1, "blocks": []}],
    )

    assert len(proposals) == 2
    assert [proposal["region_source"] for proposal in proposals] == ["auto_rectangle_layout"] * 2
    assert proposals[0]["bbox"][0] < 0.1
    assert proposals[1]["bbox"][0] > 0.5


def test_identity_labels_produce_reviewable_name_and_student_number_blocks() -> None:
    pages = [{"page_no": 1, "processed_width": 1000, "processed_height": 2000}]
    ocr_results = [{
        "page_no": 1,
        "blocks": [
            {"text": "姓名：", "bbox": [80, 100, 180, 145]},
            {"text": "学号：", "bbox": [500, 100, 610, 145]},
        ],
    }]

    proposals = propose_identity_regions_from_ocr_pages(pages, ocr_results)

    assert [item["content_type"] for item in proposals] == ["student_name", "student_no"]
    assert all(item["needs_review"] is True for item in proposals)
    assert all("question_id" not in item for item in proposals)
