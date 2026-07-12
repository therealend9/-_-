from template_builder.service import propose_regions_from_ocr_pages


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
