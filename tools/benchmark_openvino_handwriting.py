from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
import openvino as ov


SAMPLE_DIR = ROOT / "test_artifacts" / "paddleocr_handwriting_20260716"
MODEL_PATH = ROOT / "third_party" / "openvino_models" / "intel" / "handwritten-simplified-chinese-recognition-0001" / "FP32" / "handwritten-simplified-chinese-recognition-0001.xml"
OUTPUT = SAMPLE_DIR / "openvino_handwriting_benchmark.json"


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


class OpenVINOHandwritingRecognizer:
    def __init__(self) -> None:
        self.charset = SAMPLE_DIR.joinpath("scut_ept_charset.txt").read_text(encoding="utf-8").splitlines()
        core = ov.Core()
        self.model = core.compile_model(str(MODEL_PATH), "CPU")
        self.input_layer = self.model.input(0)
        self.output_layer = self.model.output(0)

    def recognize(self, image_path: Path) -> str:
        data = np.fromfile(str(image_path), dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Cannot read {image_path}")
        target_height, target_width = 96, 2000
        width = min(target_width, max(1, round(image.shape[1] * target_height / image.shape[0])))
        resized = cv2.resize(image, (width, target_height), interpolation=cv2.INTER_CUBIC)
        canvas = np.full((target_height, target_width), 255, dtype=np.uint8)
        canvas[:, :width] = resized
        logits = self.model([canvas[np.newaxis, np.newaxis, :, :]])[self.output_layer]
        indices = np.argmax(logits[:, 0, :], axis=1).tolist()
        decoded = []
        previous = -1
        for index in indices:
            if index != 0 and index != previous and index - 1 < len(self.charset):
                decoded.append(self.charset[index - 1])
            previous = index
        return "".join(decoded)


def load_labels() -> dict[str, str]:
    labels = {}
    for line in SAMPLE_DIR.joinpath("scut_test_img_id_gt.txt").read_text(encoding="utf-8").splitlines():
        image_id, text = line.split(",", 1)
        labels[f"{image_id}.jpg"] = text
    return labels


def main() -> None:
    recognizer = OpenVINOHandwritingRecognizer()
    labeled = []
    for image_name, expected in load_labels().items():
        predicted = recognizer.recognize(SAMPLE_DIR / image_name)
        expected_text, predicted_text = compact(expected), compact(predicted)
        labeled.append(
            {
                "image": image_name,
                "expected_text": expected,
                "predicted_text": predicted,
                "character_error_rate": round(edit_distance(expected_text, predicted_text) / max(1, len(expected_text)), 4),
            }
        )
    scut_records = []
    for image_path in sorted((SAMPLE_DIR / "scut_ept_unlabeled").glob("*.jpg")):
        scut_records.append({"image": image_path.name, "predicted_text": recognizer.recognize(image_path)})
    output = {
        "engine": "OpenVINO handwritten-simplified-chinese-recognition-0001 FP32",
        "model_path": str(MODEL_PATH.relative_to(ROOT)),
        "labeled_sample_count": len(labeled),
        "average_character_error_rate": round(sum(item["character_error_rate"] for item in labeled) / len(labeled), 4),
        "labeled_records": labeled,
        "scut_ept_unlabeled_sample_count": len(scut_records),
        "scut_ept_unlabeled_records": scut_records,
        "limitation": "Only the five Intel repository samples have public per-image transcriptions. The 30 SCUT-EPT examples are qualitative outputs and are excluded from the error-rate calculation.",
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
