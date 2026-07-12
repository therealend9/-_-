from __future__ import annotations
"""PDF 转页面图片。

依赖 PyMuPDF：pip install pymupdf
"""

from pathlib import Path
from typing import List, Optional, Union

from d_module import config


def _require_fitz():
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF 渲染需要安装 PyMuPDF：pip install pymupdf") from exc
    return fitz


def render_pdf_pages(
    file_id: str,
    pdf_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    dpi: int = config.DEFAULT_DPI,
) -> List[dict]:
    """把 PDF 每页渲染为 PNG。返回每页图片路径和尺寸。"""
    fitz = _require_fitz()
    output_directory = Path(output_dir) if output_dir else config.PAGE_DIR
    output_directory.mkdir(parents=True, exist_ok=True)

    results = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            output_path = output_directory / f"{file_id}_p{page_index:03d}.png"
            pix.save(output_path)
            results.append({
                "page_no": page_index,
                "image_path": str(output_path),
                "width": pix.width,
                "height": pix.height,
                "dpi": dpi,
            })
    return results
