from __future__ import annotations
"""图片相关工具。"""

from pathlib import Path
from typing import Tuple


def get_image_size(image_path: str | Path) -> Tuple[int, int]:
    """返回图片宽高。优先使用 Pillow。"""
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("读取图片尺寸需要安装 Pillow：pip install pillow") from exc

    with Image.open(image_path) as image:
        return image.size


def create_placeholder_page(
    output_path: str | Path,
    text: str = "",
    width: int = 2480,
    height: int = 3508,
) -> Path:
    """创建一张占位页面图。

    用于 DOCX / 文本型 PDF 在第一版不做真实渲染时，仍然给 B 提供 image_path。
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("创建占位页面需要安装 Pillow：pip install pillow") from exc

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    preview = (text or "text_extract_placeholder")[:500]
    draw.multiline_text((80, 80), preview, fill="black", spacing=8)
    image.save(output)
    return output
