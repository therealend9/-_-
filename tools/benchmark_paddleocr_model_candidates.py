from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image
from paddleocr import PaddleOCR

from d_module.ocr_engine.result_normalizer import normalize_paddle_result
from d_module.schemas.normalized_page import NormalizedPage


SAMPLE_DIR = ROOT / "test_artifacts" / "paddleocr_handwriting_20260716"
OUTPUT = SAMPLE_DIR / "paddleocr_candidate_benchmark.json"
CANDIDATES = [
    {"id": "default", "model_name": None},
    {"id": "pp_ocrv5_server_rec", "model_name": "PP-OCRv5_server_rec"},
    {"id": "pp_ocrv5_mobile_rec", "model_name": "PP-OCRv5_mobile_rec"},
]


def edit_distance(first: str, second: str) -> int:
    previous = list(range(len(second) + 1))
    for index, left in enumerate(first, start=1):
        current = [index]
        for column, right in enumerate(second, start=1):
            current.append(min(current[-1] + 1, previous[column] + 1, previous[column - 1] + (left != right)))
        previous = current
    return previous[-1]


def normalize_text(value: str) -> str:
    return "".join(value.split())


def run_predict(client: PaddleOCR, image_path: Path):
    if hasattr(client, "predict"):
        try:
            return list(client.predict(input=str(image_path)))
        except TypeError:
            return list(client.predict(str(image_path)))
    return client.ocr(str(image_path), cls=True)


def make_page(file_id: str, image_path: Path) -> NormalizedPage:
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

    benchmark = {
        "source": str(SAMPLE_DIR),
        "metric": "character_error_rate = Levenshtein distance / reference character count",
        "candidates": [],
    }
    for candidate in CANDIDATES:
        started = perf_counter()
        candidate_result = {"id": candidate["id"], "model_name": candidate["model_name"], "records": []}
        try:
            # Keep the benchmark aligned with the production client. Enabling
            # the v3 document-orientation stack triggers an unsupported
            # oneDNN path in this Windows Paddle runtime.
            kwargs = {"lang": "ch", "use_angle_cls": True, "enable_mkldnn": False}
            if candidate["model_name"]:
                kwargs["text_recognition_model_name"] = candidate["model_name"]
            client = PaddleOCR(**kwargs)
            for image_name, expected in labels.items():
                image_path = SAMPLE_DIR / image_name
                page = make_page(f"{candidate['id']}_{image_path.stem}", image_path)
                raw = run_predict(client, image_path)
                ocr_result = normalize_paddle_result(
                    file_id=page.file_id,
                    page=page,
                    raw_result=raw,
                    ocr_engine=f"paddleocr:{candidate['id']}",
                    low_confidence_threshold=0.0,
                )
                predicted = "\n".join(block.text for block in ocr_result.blocks if block.text).strip()
                expected_normalized = normalize_text(expected)
                predicted_normalized = normalize_text(predicted)
                distance = edit_distance(expected_normalized, predicted_normalized)
                candidate_result["records"].append(
                    {
                        "image": image_name,
                        "expected_text": expected,
                        "predicted_text": predicted,
                        "character_error_rate": round(distance / max(1, len(expected_normalized)), 4),
                        "confidence": ocr_result.overall_confidence or 0.0,
                    }
                )
            candidate_result["average_character_error_rate"] = round(
                sum(record["character_error_rate"] for record in candidate_result["records"]) / len(candidate_result["records"]), 4
            )
            candidate_result["status"] = "ok"
        except Exception as exc:
            candidate_result["status"] = "failed"
            candidate_result["error"] = str(exc)
        candidate_result["elapsed_seconds"] = round(perf_counter() - started, 2)
        benchmark["candidates"].append(candidate_result)
        OUTPUT.write_text(json.dumps(benchmark, ensure_ascii=False, indent=2), encoding="utf-8")

    successful = [item for item in benchmark["candidates"] if item["status"] == "ok"]
    if successful:
        benchmark["winner"] = min(successful, key=lambda item: item["average_character_error_rate"])["id"]
    OUTPUT.write_text(json.dumps(benchmark, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(benchmark, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
