from __future__ import annotations

"""Line-level Chinese handwriting recognition backed by OpenVINO."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from d_module.utils.path_utils import project_root


DEFAULT_MODEL_PATH = (
    project_root()
    / "third_party"
    / "openvino_models"
    / "intel"
    / "handwritten-simplified-chinese-recognition-0001"
    / "FP32"
    / "handwritten-simplified-chinese-recognition-0001.xml"
)
DEFAULT_CHARSET_PATH = project_root() / "third_party" / "openvino_models" / "intel" / "handwritten-simplified-chinese-recognition-0001" / "scut_ept_charset.txt"


def _model_path() -> Path:
    return Path(os.getenv("HANDWRITING_OCR_MODEL_PATH", str(DEFAULT_MODEL_PATH)))


def _charset_path() -> Path:
    return Path(os.getenv("HANDWRITING_OCR_CHARSET_PATH", str(DEFAULT_CHARSET_PATH)))


@lru_cache(maxsize=1)
def _recognizer() -> tuple[Any, Any, Any, list[str]]:
    try:
        import openvino as ov
    except ImportError as exc:
        raise RuntimeError("OpenVINO is required for handwriting OCR") from exc

    model_path = _model_path()
    charset_path = _charset_path()
    if not model_path.is_file():
        raise RuntimeError(f"Handwriting OCR model is missing: {model_path}")
    if not charset_path.is_file():
        raise RuntimeError(f"Handwriting OCR charset is missing: {charset_path}")

    core = ov.Core()
    compiled = core.compile_model(str(model_path), "CPU")
    charset = charset_path.read_text(encoding="utf-8").splitlines()
    return compiled, compiled.input(0), compiled.output(0), charset


def _read_grayscale(path: str | Path) -> Any:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("OpenCV and NumPy are required for handwriting OCR") from exc

    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Cannot read handwriting crop: {path}")
    return image


def _split_lines(image: Any) -> list[tuple[int, int, Any]]:
    import cv2
    import numpy as np

    height, width = image.shape[:2]
    binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(24, width // 4), 1)),
    )
    ink = cv2.subtract(binary, horizontal)
    projection = (ink > 0).sum(axis=1)
    active = projection >= max(2, width // 500)

    groups: list[tuple[int, int]] = []
    start: int | None = None
    last_active = -10
    for row, value in enumerate(active):
        if value:
            if start is None:
                start = row
            last_active = row
        elif start is not None and row - last_active > 4:
            if last_active - start >= 7:
                groups.append((max(0, start - 4), min(height, last_active + 5)))
            start = None
    if start is not None and last_active - start >= 7:
        groups.append((max(0, start - 4), min(height, last_active + 5)))

    if not groups or len(groups) > 20:
        return [(0, height, image)]
    return [(top, bottom, image[top:bottom, :]) for top, bottom in groups]


def _decode(line: Any) -> tuple[str, float]:
    import cv2
    import numpy as np

    compiled, input_layer, output_layer, charset = _recognizer()
    target_height, target_width = 96, 2000
    width = min(target_width, max(1, round(line.shape[1] * target_height / line.shape[0])))
    resized = cv2.resize(line, (width, target_height), interpolation=cv2.INTER_CUBIC)
    canvas = np.full((target_height, target_width), 255, dtype=np.uint8)
    canvas[:, :width] = resized
    logits = compiled([canvas[np.newaxis, np.newaxis, :, :]])[output_layer][:, 0, :]
    indices = np.argmax(logits, axis=1).tolist()

    chars: list[str] = []
    confidences: list[float] = []
    previous = -1
    for row, index in enumerate(indices):
        if index != 0 and index != previous and index - 1 < len(charset):
            values = logits[row]
            peak = float(values[index])
            probability = float(np.exp(peak - values.max()) / np.exp(values - values.max()).sum())
            chars.append(charset[index - 1])
            confidences.append(probability)
        previous = index
    return "".join(chars), round(sum(confidences) / len(confidences), 4) if confidences else 0.0


def run_openvino_handwriting_ocr(file_id: str, page_no: int, image_path: str | Path) -> dict[str, Any]:
    """Recognize one answer region by splitting it into handwriting lines."""
    image = _read_grayscale(image_path)
    height, width = image.shape[:2]
    blocks = []
    for index, (top, bottom, line) in enumerate(_split_lines(image), start=1):
        text, confidence = _decode(line)
        if not text:
            continue
        blocks.append(
            {
                "block_id": f"{file_id}_{page_no}_handwriting_{index}",
                "bbox": [0, top, width, bottom],
                "text": text,
                "confidence": confidence,
                "line_index": index,
                "reading_order": index,
            }
        )
    text = "\n".join(item["text"] for item in blocks)
    confidence = round(sum(item["confidence"] for item in blocks) / len(blocks), 4) if blocks else 0.0
    return {
        "ocr_text": text,
        "ocr_confidence": confidence,
        "ocr_blocks": blocks,
        "ocr_mode": "handwriting",
        "ocr_engine": "openvino_handwritten_simplified_chinese",
    }
