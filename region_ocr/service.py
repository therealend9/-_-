from __future__ import annotations

from pathlib import Path
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
    student = cv2.imread(str(student_crop_path), cv2.IMREAD_GRAYSCALE)
    if student is None:
        raise ValueError(f"Cannot read region crop: {student_crop_path}")
    if template_crop_path:
        template = cv2.imread(str(template_crop_path), cv2.IMREAD_GRAYSCALE)
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
    """Run the configured OCR engine on a cropped answer region.

    ``ocr_mode`` is retained in the result for model routing. PaddleOCR remains
    the installed default; deployments can replace this function with a
    handwriting-specific engine without changing the template contract.
    """
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
