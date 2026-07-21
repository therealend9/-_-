from __future__ import annotations

from pathlib import Path
import os
from typing import Any

from d_module import config
from d_module.ocr_engine.service import run_ocr_on_page
from d_module.schemas.normalized_page import NormalizedPage
from d_module.utils.image_utils import get_image_size


def detect_blank_region(
    student_crop_path: str,
    template_crop_path: str | None = None,
    ink_threshold: float = 0.002,
) -> dict[str, Any]:
    """Detect added handwriting, preferring blank-template subtraction."""
    cv2 = _optional_cv2()
    if cv2 is None:
        return _detect_blank_with_pillow(student_crop_path, template_crop_path, ink_threshold)
    student = _read_image(cv2, Path(student_crop_path), cv2.IMREAD_GRAYSCALE)
    if student is None:
        raise ValueError(f"Cannot read region crop: {student_crop_path}")
    if template_crop_path:
        template = _read_image(cv2, Path(template_crop_path), cv2.IMREAD_GRAYSCALE)
        if template is not None and template.shape == student.shape:
            delta = cv2.absdiff(student, template)
            ink_ratio = float((delta > 30).sum()) / delta.size
            return {"is_blank": ink_ratio < ink_threshold, "ink_ratio": round(ink_ratio, 6), "method": "template_difference"}
    ink_ratio = float((student < 180).sum()) / student.size
    return {"is_blank": ink_ratio < ink_threshold, "ink_ratio": round(ink_ratio, 6), "method": "dark_pixel_fallback"}


def run_ocr_on_region(
    file_id: str,
    page_no: int,
    image_path: str,
    ocr_mode: str = "handwriting",
) -> dict[str, Any]:
    """Run OCR on a cropped answer region."""
    # PaddleOCR is the default handwriting route because it detects text lines
    # inside complex answer regions; OpenVINO remains available when explicitly
    # selected through HANDWRITING_OCR_ENGINE=openvino.
    if ocr_mode == "handwriting" and os.getenv("HANDWRITING_OCR_ENGINE", "paddleocr").strip().lower() == "openvino":
        try:
            from region_ocr.openvino_handwriting import run_openvino_handwriting_ocr

            return run_openvino_handwriting_ocr(file_id=file_id, page_no=page_no, image_path=image_path)
        except (ImportError, RuntimeError, FileNotFoundError):
            # Keep answer-sheet processing available when a deployment has not
            # installed the optional model assets yet.
            pass

    width, height = get_image_size(image_path)
    page = NormalizedPage(
        file_id=file_id,
        page_no=page_no,
        page_image_path=image_path,
        preprocessed_image_path=None,
        original_width=width,
        original_height=height,
        processed_width=width,
        processed_height=height,
        dpi=None,
    )
    result = run_ocr_on_page(file_id=file_id, page=page)
    text = "\n".join(block.text for block in result.blocks if block.text).strip()
    return {
        "ocr_text": text,
        "ocr_confidence": result.overall_confidence or 0.0,
        "ocr_blocks": [block.to_dict() for block in result.blocks],
        "ocr_mode": ocr_mode,
        "ocr_engine": "paddleocr",
    }


def _detect_blank_with_pillow(
    student_crop_path: str, template_crop_path: str | None, ink_threshold: float,
) -> dict[str, Any]:
    import numpy as np
    from PIL import Image, ImageChops
    with Image.open(student_crop_path) as image:
        student = image.convert("L")
    if template_crop_path:
        with Image.open(template_crop_path) as image:
            template = image.convert("L")
        if student.size == template.size:
            delta = np.asarray(ImageChops.difference(student, template))
            ink_ratio = float((delta > 30).sum()) / delta.size
            return {"is_blank": ink_ratio < ink_threshold, "ink_ratio": round(ink_ratio, 6), "method": "template_difference"}
    pixels = np.asarray(student)
    ink_ratio = float((pixels < 180).sum()) / pixels.size
    return {"is_blank": ink_ratio < ink_threshold, "ink_ratio": round(ink_ratio, 6), "method": "dark_pixel_fallback"}


def _optional_cv2() -> Any | None:
    try:
        import cv2
    except ImportError:
        return None
    return cv2


def _read_image(cv2: Any, path: Path, flags: int) -> Any | None:
    import numpy as np

    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, flags)
