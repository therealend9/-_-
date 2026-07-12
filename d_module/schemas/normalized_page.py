from __future__ import annotations
"""NormalizedPage：统一后的页面图像对象。"""

from dataclasses import asdict, dataclass, field
from typing import List, Optional

from d_module.constants import COORDINATE_BASE_PAGE_IMAGE, COORDINATE_BASE_PREPROCESSED_IMAGE


@dataclass
class NormalizedPage:
    file_id: str
    page_no: int
    page_image_path: str
    preprocessed_image_path: Optional[str]
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    dpi: Optional[int] = None
    coordinate_base: str = COORDINATE_BASE_PAGE_IMAGE
    rotation_degree: float = 0.0
    has_perspective_fix: bool = False
    transform_matrix: Optional[List[List[float]]] = None
    preprocess_steps: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.file_id:
            raise ValueError("file_id 不能为空")
        if self.page_no < 1:
            raise ValueError("page_no 必须从 1 开始")
        if not self.page_image_path:
            raise ValueError("page_image_path 不能为空")
        if self.original_width <= 0 or self.original_height <= 0:
            raise ValueError("original_width/original_height 必须大于 0")
        if self.processed_width <= 0 or self.processed_height <= 0:
            raise ValueError("processed_width/processed_height 必须大于 0")
        if self.coordinate_base not in {COORDINATE_BASE_PAGE_IMAGE, COORDINATE_BASE_PREPROCESSED_IMAGE}:
            raise ValueError(f"非法 coordinate_base: {self.coordinate_base}")

    @property
    def effective_image_path(self) -> str:
        """返回当前坐标所依附的图片路径。"""
        return self.preprocessed_image_path or self.page_image_path

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "NormalizedPage":
        return cls(**data)
