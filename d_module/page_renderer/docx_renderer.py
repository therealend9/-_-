from __future__ import annotations
"""DOCX 混合模式的占位页面。

DOCX 当前不再强制整页转图片：
- 可编辑文本直接提取。
- 内嵌图片导出后单独 OCR。
- 这里仅生成一张占位页面图，保证 NormalizedPage 和 OCRPageResult 仍有 image_path。
"""

from pathlib import Path
from typing import List, Optional, Union

from d_module import config


def create_docx_placeholder_page(
    file_id: str,
    docx_elements: Optional[List[dict]] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> dict:
    """为 DOCX 混合模式创建占位页面。"""
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("创建 DOCX 占位页面需要安装 Pillow：pip install pillow") from exc

    output_directory = Path(output_dir) if output_dir else config.PAGE_DIR
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / f"{file_id}_docx_mixed_p001.png"

    width = config.DOCX_PLACEHOLDER_WIDTH
    # 根据元素数稍微拉长占位页，避免 B 调试看顺序时太拥挤。
    element_count = len(docx_elements or [])
    height = max(config.DOCX_PLACEHOLDER_HEIGHT, 120 + element_count * 42)

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 30), "DOCX mixed mode placeholder", fill="black")
    draw.text((40, 55), "Text is extracted directly; inline images are marked and OCRed separately.", fill="black")

    y = 100
    for index, element in enumerate(docx_elements or [], start=1):
        if element.get("type") == "image":
            line = f"{index:03d}. [IMAGE_MARKER] {element.get('image_id', '')}"
        else:
            text = str(element.get("text", "")).replace("\n", " ")
            line = f"{index:03d}. [TEXT] {text[:80]}"
        # 使用 ASCII 前缀，避免默认字体不支持中文时报错；中文内容只做截断预览。
        try:
            draw.text((40, y), line, fill="black")
        except UnicodeEncodeError:
            safe_line = f"{index:03d}. [{element.get('type', 'text').upper()}]"
            draw.text((40, y), safe_line, fill="black")
        y += 40

    image.save(output_path)
    return {
        "page_no": 1,
        "image_path": str(output_path),
        "width": width,
        "height": height,
        "dpi": None,
    }
