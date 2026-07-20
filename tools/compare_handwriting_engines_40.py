from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from d_module.ocr_engine.service import run_ocr_on_page
from d_module.schemas.normalized_page import NormalizedPage
from benchmark_openvino_handwriting import OpenVINOHandwritingRecognizer, compact, edit_distance
from benchmark_handwriting_preprocessing import page_for


SAMPLE_DIR = ROOT / "test_artifacts" / "paddleocr_handwriting_20260716"
SCUT_DIR = SAMPLE_DIR / "scut_ept_unlabeled"
CROSS_DIR = SAMPLE_DIR / "cross_domain_unlabeled"
OUTPUT = SAMPLE_DIR / "handwriting_engines_40_comparison.json"


def labeled_images() -> dict[Path, str]:
    labels: dict[Path, str] = {}
    for line in SAMPLE_DIR.joinpath("scut_test_img_id_gt.txt").read_text(encoding="utf-8").splitlines():
        image_id, text = line.split(",", 1)
        labels[SAMPLE_DIR / f"{image_id}.jpg"] = text
    manual = json.loads(CROSS_DIR.joinpath("manual_labels.json").read_text(encoding="utf-8"))["labels"]
    for name, text in manual.items():
        labels[CROSS_DIR / name] = text
    return labels


def all_images() -> list[Path]:
    images = sorted(SAMPLE_DIR.glob("000*.jpg"))
    images += sorted(SCUT_DIR.glob("*.jpg"))
    images += sorted(CROSS_DIR.glob("*.jpg"))
    if len(images) != 40:
        raise ValueError(f"Expected 40 images, found {len(images)}")
    return images


def paddle_text(image_path: Path) -> str:
    page: NormalizedPage = page_for(f"paddle_{image_path.stem}", image_path)
    result = run_ocr_on_page(page.file_id, page)
    return "\n".join(block.text for block in result.blocks if block.text).strip()


def run_engine(engine_id: str, images: list[Path], labels: dict[Path, str], recognizer: OpenVINOHandwritingRecognizer | None) -> dict:
    records = []
    for image_path in images:
        predicted = recognizer.recognize(image_path) if recognizer else paddle_text(image_path)
        record = {
            "image": str(image_path.relative_to(SAMPLE_DIR)).replace("\\", "/"),
            "predicted_text": predicted,
            "has_reference": image_path in labels,
        }
        if image_path in labels:
            expected = labels[image_path]
            record["expected_text"] = expected
            record["character_error_rate"] = round(
                edit_distance(compact(expected), compact(predicted)) / max(1, len(compact(expected))), 4
            )
        records.append(record)
    scored = [item for item in records if item["has_reference"]]
    return {
        "id": engine_id,
        "total_image_count": len(records),
        "labeled_image_count": len(scored),
        "average_character_error_rate": round(sum(item["character_error_rate"] for item in scored) / len(scored), 4),
        "nonempty_output_count": sum(bool(item["predicted_text"]) for item in records),
        "records": records,
    }


def main() -> None:
    labels = labeled_images()
    images = all_images()
    openvino = OpenVINOHandwritingRecognizer()
    engines = [
        run_engine("current_paddleocr", images, labels, None),
        run_engine("openvino_handwritten_simplified_chinese", images, labels, openvino),
    ]
    output = {
        "total_images": len(images),
        "labeled_images": len(labels),
        "unlabeled_images": len(images) - len(labels),
        "metric": "Average character error rate over the 10 images with public or manually verified references.",
        "engines": engines,
        "winner": min(engines, key=lambda item: item["average_character_error_rate"])["id"],
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
