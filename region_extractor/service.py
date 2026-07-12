from __future__ import annotations

from pathlib import Path
from typing import Any

from d_module import config


def crop_region(
    aligned_image_path: str,
    bbox: list[float],
    output_stem: str,
    inward_margin_ratio: float = 0.01,
) -> dict[str, Any]:
    """Crop one normalized answer region after page alignment."""
    cv2 = _optional_cv2()
    if cv2 is None:
        return _crop_with_pillow(aligned_image_path, bbox, output_stem, inward_margin_ratio)
    image = cv2.imread(str(aligned_image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read aligned image: {aligned_image_path}")
    height, width = image.shape[:2]
    if len(bbox) != 4 or not (0 <= bbox[0] < bbox[2] <= 1 and 0 <= bbox[1] < bbox[3] <= 1):
        raise ValueError("region bbox must be normalized and inside [0, 1]")
    x1, y1, x2, y2 = int(bbox[0] * width), int(bbox[1] * height), int(bbox[2] * width), int(bbox[3] * height)
    margin_x = int((x2 - x1) * max(0.0, inward_margin_ratio))
    margin_y = int((y2 - y1) * max(0.0, inward_margin_ratio))
    x1, y1, x2, y2 = x1 + margin_x, y1 + margin_y, x2 - margin_x, y2 - margin_y
    if x2 <= x1 or y2 <= y1:
        raise ValueError("region crop is empty after inward margin")
    crop = image[y1:y2, x1:x2]
    output_path = config.PREPROCESSED_DIR / "regions" / f"{output_stem}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), crop)
    return {"image_path": str(output_path), "bbox": [x1, y1, x2, y2], "width": x2 - x1, "height": y2 - y1}


def _crop_with_pillow(
    aligned_image_path: str, bbox: list[float], output_stem: str, inward_margin_ratio: float,
) -> dict[str, Any]:
    from PIL import Image
    if len(bbox) != 4 or not (0 <= bbox[0] < bbox[2] <= 1 and 0 <= bbox[1] < bbox[3] <= 1):
        raise ValueError("region bbox must be normalized and inside [0, 1]")
    with Image.open(aligned_image_path) as image:
        width, height = image.size
        x1, y1, x2, y2 = int(bbox[0] * width), int(bbox[1] * height), int(bbox[2] * width), int(bbox[3] * height)
        margin_x, margin_y = int((x2 - x1) * max(0.0, inward_margin_ratio)), int((y2 - y1) * max(0.0, inward_margin_ratio))
        x1, y1, x2, y2 = x1 + margin_x, y1 + margin_y, x2 - margin_x, y2 - margin_y
        if x2 <= x1 or y2 <= y1:
            raise ValueError("region crop is empty after inward margin")
        output_path = config.PREPROCESSED_DIR / "regions" / f"{output_stem}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.crop((x1, y1, x2, y2)).save(output_path)
    return {"image_path": str(output_path), "bbox": [x1, y1, x2, y2], "width": x2 - x1, "height": y2 - y1}


def _optional_cv2() -> Any | None:
    try:
        import cv2
    except ImportError:
        return None
    return cv2
