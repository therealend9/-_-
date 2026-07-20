from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from d_module.ocr_engine.service import run_ocr_on_page
from d_module.schemas.normalized_page import NormalizedPage
from PIL import Image


SAMPLE_DIR = ROOT / "test_artifacts" / "paddleocr_handwriting_20260716"
OUTPUT = SAMPLE_DIR / "paddleocr_results.json"


def edit_distance(first: str, second: str) -> int:
    previous = list(range(len(second) + 1))
    for i, left in enumerate(first, start=1):
        current = [i]
        for j, right in enumerate(second, start=1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left != right)))
        previous = current
    return previous[-1]


def normalize(value: str) -> str:
    return "".join(value.split())


def main() -> None:
    labels = {}
    for line in (SAMPLE_DIR / "scut_test_img_id_gt.txt").read_text(encoding="utf-8").splitlines():
        image_id, text = line.split(",", 1)
        labels[f"{image_id}.jpg"] = text

    records = []
    for image_name, expected in labels.items():
        image_path = SAMPLE_DIR / image_name
        with Image.open(image_path) as image:
            width, height = image.size
        page = NormalizedPage(
            file_id=f"handwriting_{image_path.stem}",
            page_no=1,
            page_image_path=str(image_path),
            preprocessed_image_path=None,
            original_width=width,
            original_height=height,
            processed_width=width,
            processed_height=height,
            dpi=None,
        )
        result = run_ocr_on_page(
            file_id=page.file_id,
            page=page,
        )
        predicted = "\n".join(block.text for block in result.blocks if block.text).strip()
        expected_normalized = normalize(expected)
        predicted_normalized = normalize(predicted)
        distance = edit_distance(expected_normalized, predicted_normalized)
        records.append(
            {
                "image": image_name,
                "expected_text": expected,
                "predicted_text": predicted,
                "expected_char_count": len(expected_normalized),
                "predicted_char_count": len(predicted_normalized),
                "edit_distance": distance,
                "character_error_rate": round(distance / max(1, len(expected_normalized)), 4),
                "confidence": result.overall_confidence or 0.0,
                "block_count": len(result.blocks),
            }
        )

    summary = {
        "engine": "PaddleOCR via d_module.ocr_engine.service.run_ocr_on_page",
        "sample_source": "https://github.com/lql-dev/handwritten-chinese-ocr-samples",
        "ground_truth_source": "https://raw.githubusercontent.com/lql-dev/handwritten-chinese-ocr-samples/main/images/scut_test_img_id_gt.txt",
        "sample_count": len(records),
        "average_character_error_rate": round(sum(item["character_error_rate"] for item in records) / len(records), 4),
        "records": records,
        "interpretation": "This isolates OCR from page alignment and answer-region cropping. It is a single-line handwriting benchmark, not an exam-answer benchmark.",
    }
    OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
