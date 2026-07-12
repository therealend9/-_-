from __future__ import annotations
"""OCRBlock：标准 OCR 文本块。"""

from dataclasses import asdict, dataclass
from typing import List, Optional

from d_module.constants import BLOCK_TYPE_TEXT, BLOCK_TYPES, BBOX_SOURCES, SOURCE_MODES


@dataclass
class OCRBlock:
    block_id: str
    bbox: List[float]
    bbox_source: str
    source_mode: str
    text: str
    confidence: float
    reading_order: int
    is_low_confidence: bool
    line_index: Optional[int] = None

    # 扩展字段：兼容 DOCX 文本+图片混合策略。
    block_type: str = BLOCK_TYPE_TEXT
    image_id: Optional[str] = None
    image_path: Optional[str] = None
    parent_block_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.block_id:
            raise ValueError("block_id 不能为空")
        if len(self.bbox) != 4:
            raise ValueError("bbox 必须为 [x_min, y_min, x_max, y_max]")
        x_min, y_min, x_max, y_max = self.bbox
        if x_min > x_max or y_min > y_max:
            raise ValueError("bbox 坐标不合法，必须满足 x_min <= x_max 且 y_min <= y_max")
        if self.bbox_source not in BBOX_SOURCES:
            raise ValueError(f"非法 bbox_source: {self.bbox_source}")
        if self.source_mode not in SOURCE_MODES:
            raise ValueError(f"非法 source_mode: {self.source_mode}")
        if self.block_type not in BLOCK_TYPES:
            raise ValueError(f"非法 block_type: {self.block_type}")
        if self.text is None:
            raise ValueError("text 不允许为 None，空文本请传空字符串")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence 必须在 0 到 1 之间")
        if self.reading_order < 1:
            raise ValueError("reading_order 必须从 1 开始")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "OCRBlock":
        return cls(**data)
