from __future__ import annotations
"""基础图像预处理操作。

第一版只做尺寸稳定的处理：灰度化、轻度去噪、二值化。
"""

from pathlib import Path


def _require_pillow():
    try:
        from PIL import Image, ImageFilter
    except ImportError as exc:
        raise RuntimeError("图像预处理需要安装 Pillow：pip install pillow") from exc
    return Image, ImageFilter


def to_grayscale(input_path: str | Path, output_path: str | Path) -> Path:
    Image, _ = _require_pillow()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        image.convert("L").save(output)
    return output


def denoise(input_path: str | Path, output_path: str | Path) -> Path:
    Image, ImageFilter = _require_pillow()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        image.filter(ImageFilter.MedianFilter(size=3)).save(output)
    return output


def binarize(input_path: str | Path, output_path: str | Path, threshold: int = 180) -> Path:
    Image, _ = _require_pillow()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        gray = image.convert("L")
        binary = gray.point(lambda pixel: 255 if pixel > threshold else 0, mode="1")
        binary.save(output)
    return output
