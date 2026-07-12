from __future__ import annotations

"""Text joining helpers shared by paragraph, question and merge stages."""

import re
from typing import Iterable


_SPACE_RE = re.compile(r"\s+")
_ASCII_WORD_CHAR_RE = re.compile(r"[A-Za-z0-9]")
_CJK_LEFT_SPACE_RE = re.compile(r"(?<=[\u3400-\u9fff，。！？；：、（《【〔〈「『‘“])\s+(?=[\u3400-\u9fffA-Za-z0-9])")
_CJK_RIGHT_SPACE_RE = re.compile(r"(?<=[A-Za-z0-9])\s+(?=[\u3400-\u9fff，。！？；：、）》】〕〉」』’”])")
_NO_SPACE_BEFORE = set("，。！？；：、）》】〕〉」』’”％%.,!?;:)]}")
_NO_SPACE_AFTER = set("（《【〔〈「『‘“([{￥¥$")
_CONTEXT_BOUNDARY_RE = re.compile(
    r"^(?:材料\s*\d+\s*$|结合(?:上述|以上|以下)?材料.*(?:问题|作答)[:：]?$|[【\[].*(?:根据|来源|改编).*[】\]])"
)


def normalize_inline_text(text: object) -> str:
    """Collapse source newlines/whitespace without changing visible characters."""
    normalized = _SPACE_RE.sub(" ", str(text or "").replace("\r", " ").replace("\n", " ")).strip()
    normalized = _CJK_LEFT_SPACE_RE.sub("", normalized)
    return _CJK_RIGHT_SPACE_RE.sub("", normalized)


def join_text_parts(parts: Iterable[object]) -> str:
    """Join OCR/PDF line fragments without inserting spaces inside Chinese text.

    A space is kept only for a likely ASCII word boundary.  Chinese characters,
    numbers next to Chinese units, and punctuation are joined directly.
    """
    result = ""
    for raw_part in parts:
        part = normalize_inline_text(raw_part)
        if not part:
            continue
        if not result:
            result = part
            continue
        separator = " " if _needs_ascii_space(result[-1], part[0]) else ""
        result += separator + part
    return result


def join_context_parts(parts: Iterable[object]) -> str:
    """Join shared material text while preserving semantic paragraph breaks."""
    normalized_parts = [normalize_inline_text(part) for part in parts]
    normalized_parts = [part for part in normalized_parts if part]
    result = ""
    previous = ""
    for part in normalized_parts:
        if not result:
            result = part
        elif _CONTEXT_BOUNDARY_RE.match(part) or _CONTEXT_BOUNDARY_RE.match(previous):
            result += "\n" + part
        else:
            separator = " " if _needs_ascii_space(result[-1], part[0]) else ""
            result += separator + part
        previous = part
    return result


def _needs_ascii_space(left: str, right: str) -> bool:
    if left in _NO_SPACE_AFTER or right in _NO_SPACE_BEFORE:
        return False
    return bool(_ASCII_WORD_CHAR_RE.fullmatch(left) and _ASCII_WORD_CHAR_RE.fullmatch(right))
