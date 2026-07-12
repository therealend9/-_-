from __future__ import annotations
"""PDF 解析工具。

依赖 PyMuPDF：pip install pymupdf
未安装时会在调用 PDF 解析函数时抛出明确错误。
"""

import math
import re
from pathlib import Path
from typing import Dict, List


_SPACE_RE = re.compile(r"\s+")
_DIGIT_RE = re.compile(r"\d+")
_MARGIN_AD_RE = re.compile(
    r"(?:QQ|微信|公众号|搜集整理|资料自用|版权所有|禁止转载|仅供学习)",
    re.IGNORECASE,
)


def _require_fitz():
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError("PDF 解析需要安装 PyMuPDF：pip install pymupdf") from exc
    return fitz


def get_pdf_page_count(pdf_path: str | Path) -> int:
    fitz = _require_fitz()
    with fitz.open(pdf_path) as doc:
        return len(doc)


def extract_pdf_text_pages(
    pdf_path: str | Path,
    min_chars_per_page: int = 20,
) -> List[Dict]:
    """Extract horizontal PDF text lines with geometry and noise filtering.

    Rotated decorative text is removed. Repeated top/bottom margin lines are
    removed across pages, and obvious margin advertisements are removed even on
    a one-page PDF. The returned bbox stays in PDF point coordinates; the OCR
    wrapper scales it to the rendered page image.
    """
    fitz = _require_fitz()
    raw_pages: List[Dict] = []

    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc, start=1):
            page_width = float(page.rect.width)
            page_height = float(page.rect.height)
            lines: List[Dict] = []
            filtered_rotated = 0

            for block in (page.get_text("dict") or {}).get("blocks", []):
                if int(block.get("type", -1)) != 0:
                    continue
                for line in block.get("lines", []):
                    text = _normalize_text("".join(str(span.get("text", "")) for span in line.get("spans", [])))
                    if not text:
                        continue
                    direction = line.get("dir", (1.0, 0.0)) or (1.0, 0.0)
                    angle = math.degrees(math.atan2(float(direction[1]), float(direction[0])))
                    if abs(angle) > 5.0:
                        filtered_rotated += 1
                        continue
                    bbox = [float(value) for value in line.get("bbox", [0.0, 0.0, 0.0, 0.0])]
                    if len(bbox) != 4:
                        continue
                    lines.append({"text": text, "bbox": bbox, "angle": round(angle, 2)})

            raw_pages.append(
                {
                    "page_no": index,
                    "page_width": page_width,
                    "page_height": page_height,
                    "blocks": lines,
                    "filtered_rotated_blocks": filtered_rotated,
                }
            )

    repeated_margin_signatures = _find_repeated_margin_signatures(raw_pages)
    results: List[Dict] = []
    for page in raw_pages:
        kept_blocks: List[Dict] = []
        filtered_margin = 0
        for block in page["blocks"]:
            if _should_filter_margin_block(page, block, repeated_margin_signatures):
                filtered_margin += 1
                continue
            kept_blocks.append(block)

        text = "\n".join(block["text"] for block in kept_blocks).strip()
        compact_length = len(re.sub(r"\s+", "", text))
        results.append(
            {
                **page,
                "blocks": kept_blocks,
                "text": text,
                "usable": compact_length >= min_chars_per_page,
                "filtered_margin_blocks": filtered_margin,
            }
        )
    return results


def extract_pdf_text(pdf_path: str | Path) -> List[Dict]:
    """Backward-compatible page text API."""
    return [
        {"page_no": page["page_no"], "text": page["text"]}
        for page in extract_pdf_text_pages(pdf_path)
    ]


def is_text_pdf(pdf_path: str | Path, min_chars_per_page: int = 20) -> bool:
    pages = extract_pdf_text_pages(pdf_path, min_chars_per_page=min_chars_per_page)
    if not pages:
        return False
    text_page_count = sum(1 for page in pages if page.get("usable"))
    return text_page_count >= max(1, len(pages) // 2)


def count_text_pdf_pages(extracted_text_pages: List[Dict], min_chars_per_page: int = 20) -> int:
    return sum(
        1
        for page in extracted_text_pages
        if page.get("usable") or len(re.sub(r"\s+", "", page.get("text", ""))) >= min_chars_per_page
    )


def _find_repeated_margin_signatures(pages: List[Dict]) -> set[str]:
    signature_pages: dict[str, set[int]] = {}
    for page in pages:
        page_height = max(float(page.get("page_height", 0.0) or 0.0), 1.0)
        for block in page.get("blocks", []):
            bbox = block.get("bbox") or [0.0, 0.0, 0.0, 0.0]
            top_ratio = float(bbox[1]) / page_height
            bottom_ratio = float(bbox[3]) / page_height
            if top_ratio > 0.12 and bottom_ratio < 0.88:
                continue
            signature = _canonical_margin_text(block.get("text", ""))
            if len(signature) < 4:
                continue
            signature_pages.setdefault(signature, set()).add(int(page["page_no"]))
    return {signature for signature, page_nos in signature_pages.items() if len(page_nos) >= 2}


def _should_filter_margin_block(page: Dict, block: Dict, repeated_signatures: set[str]) -> bool:
    page_height = max(float(page.get("page_height", 0.0) or 0.0), 1.0)
    bbox = block.get("bbox") or [0.0, 0.0, 0.0, 0.0]
    top_ratio = float(bbox[1]) / page_height
    bottom_ratio = float(bbox[3]) / page_height
    in_margin = top_ratio <= 0.12 or bottom_ratio >= 0.88
    signature = _canonical_margin_text(block.get("text", ""))
    if in_margin and signature in repeated_signatures:
        return True
    if bottom_ratio >= 0.9 and _MARGIN_AD_RE.search(str(block.get("text", ""))):
        return True
    return False


def _canonical_margin_text(text: object) -> str:
    normalized = _normalize_text(text).lower()
    normalized = _DIGIT_RE.sub("#", normalized)
    return re.sub(r"[^\w\u4e00-\u9fff#]+", "", normalized)


def _normalize_text(text: object) -> str:
    return _SPACE_RE.sub(" ", str(text or "")).strip()
