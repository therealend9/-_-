from __future__ import annotations

"""Post-OCR text cleanup helpers.

Current strategy stays intentionally conservative:
- normalize whitespace for OCR text blocks
- drop isolated low-confidence single-character latin noise like ``o`` / ``O``

The goal is to reduce obvious OCR artifacts without rewriting valid student text.
"""

import re


_MULTISPACE_RE = re.compile(r"\s+")
_ISOLATED_LATIN_NOISE_RE = re.compile(r"^[A-Za-z]$")


def normalize_ocr_text(text: str) -> str:
    """Normalize OCR text with low-risk whitespace cleanup."""
    if not text:
        return ""
    cleaned = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    cleaned = _MULTISPACE_RE.sub(" ", cleaned)
    return cleaned.strip()


def is_low_value_noise_text(text: str, confidence: float, threshold: float = 0.75) -> bool:
    """Detect obvious OCR noise blocks that are safe to discard.

    Current rule only removes isolated single latin letters under low confidence.
    This specifically targets artifacts like ``o`` / ``O`` observed in sample runs.
    """
    normalized = normalize_ocr_text(text)
    if not normalized:
        return True
    if confidence >= threshold:
        return False
    return bool(_ISOLATED_LATIN_NOISE_RE.fullmatch(normalized))
