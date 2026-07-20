from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
from PIL import Image, ImageOps

from d_module.ocr_engine.service import run_ocr_on_page
from d_module.schemas.normalized_page import NormalizedPage


SAMPLE_DIR = ROOT / "test_artifacts" / "paddleocr_handwriting_20260716"
VARIANT_DIR = SAMPLE_DIR / "preprocessing_variants"
OUTPUT = SAMPLE_DIR / "paddleocr_preprocessing_benchmark.json"
VARIANTS = ("original", "gray_upscale_2x", "clahe_upscale_2x", "otsu_upscale_2x")


def edit_distance(first: str, second: str) -> int:
    previous = list(range(len(second) + 1))
    for index, left in enumerate(first, start=1):
        current = [index]
        for column, right in enumerate(second, start=1):
            current.append(min(current[-1] + 1, previous[column] + 1, previous[column - 1] + (left != right)))
        previous = current
    return previous[-1]


def compact(value: str) -> str:
    return "".join(value.split())


def make_variant(source: Path, variant: str) -> Path:
    if variant == "original":
        return source
    target = VARIANT_DIR / variant / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if variant == "gray_upscale_2x":
        with Image.open(source) as image:
            result = ImageOps.autocontrast(image.convert("L")).resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
            result.save(target)
        return target
    image = cv2.imdecode(np.fromfile(str(source), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Cannot open {source}")
    if variant == "clahe_upscale_2x":
        image = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(image)
    elif variant == "otsu_upscale_2x":
        _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        raise ValueError(variant)
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    ok, encoded = cv2.imencode(".jpg", image)
    if not ok:
        raise ValueError(f"Cannot encode {target}")
    encoded.tofile(str(target))
    return target


def page_for(file_id: str, image_path: Path) -> NormalizedPage:
    with Image.open(image_path) as image:
        width, height = image.size
    return NormalizedPage(
        file_id=file_id,
        page_no=1,
        page_image_path=str(image_path),
        preprocessed_image_path=None,
        original_width=width,
        original_height=height,
        processed_width=width,
        processed_height=height,
        dpi=None,
    )


def main() -> None:
    labels = {}
    for line in (SAMPLE_DIR / "scut_test_img_id_gt.txt").read_text(encoding="utf-8").splitlines():
        image_id, text = line.split(",", 1)
        labels[f"{image_id}.jpg"] = text
    benchmark = {"engine": "current default PaddleOCR", "variants": []}
    for variant in VARIANTS:
        records = []
        for image_name, expected in labels.items():
            image_path = make_variant(SAMPLE_DIR / image_name, variant)
            page = page_for(f"{variant}_{image_path.stem}", image_path)
            result = run_ocr_on_page(page.file_id, page)
            predicted = "\n".join(block.text for block in result.blocks if block.text).strip()
            expected_text = compact(expected)
            predicted_text = compact(predicted)
            records.append(
                {
                    "image": image_name,
                    "predicted_text": predicted,
                    "character_error_rate": round(edit_distance(expected_text, predicted_text) / max(1, len(expected_text)), 4),
                    "confidence": result.overall_confidence or 0.0,
                }
            )
        benchmark["variants"].append(
            {
                "id": variant,
                "average_character_error_rate": round(sum(item["character_error_rate"] for item in records) / len(records), 4),
                "records": records,
            }
        )
    benchmark["winner"] = min(benchmark["variants"], key=lambda item: item["average_character_error_rate"])["id"]
    OUTPUT.write_text(json.dumps(benchmark, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(benchmark, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
