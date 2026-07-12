from __future__ import annotations
"""OCRPageResult：A 输出给 B 的页面级 OCR 结果。"""

from dataclasses import asdict, dataclass, field
from typing import List, Optional

from d_module.constants import COORDINATE_BASE_PAGE_IMAGE, COORDINATE_BASE_PREPROCESSED_IMAGE
from d_module.schemas.ocr_block import OCRBlock


@dataclass
class OCRPageResult:
    file_id: str
    page_no: int
    image_path: str
    width: int
    height: int
    dpi: Optional[int]
    coordinate_base: str
    ocr_engine: str
    overall_confidence: Optional[float]
    blocks: List[OCRBlock] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.file_id:
            raise ValueError("file_id 不能为空")
        if self.page_no < 1:
            raise ValueError("page_no 必须从 1 开始")
        if not self.image_path:
            raise ValueError("image_path 不能为空")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width/height 必须大于 0")
        if self.coordinate_base not in {COORDINATE_BASE_PAGE_IMAGE, COORDINATE_BASE_PREPROCESSED_IMAGE}:
            raise ValueError(f"非法 coordinate_base: {self.coordinate_base}")
        if self.overall_confidence is not None and not 0 <= self.overall_confidence <= 1:
            raise ValueError("overall_confidence 必须在 0 到 1 之间")

        # 允许从 dict 反序列化。
        normalized_blocks = []
        for block in self.blocks:
            if isinstance(block, OCRBlock):
                normalized_blocks.append(block)
            else:
                normalized_blocks.append(OCRBlock.from_dict(block))
        self.blocks = sorted(normalized_blocks, key=lambda item: item.reading_order)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["blocks"] = [block.to_dict() for block in self.blocks]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "OCRPageResult":
        return cls(**data)
