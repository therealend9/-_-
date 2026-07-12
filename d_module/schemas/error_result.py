from __future__ import annotations
"""ErrorResult：统一错误返回结构。"""

from dataclasses import asdict, dataclass
from typing import Optional

from d_module.constants import STAGES


@dataclass
class ErrorResult:
    success: bool
    file_id: Optional[str]
    page_no: Optional[int]
    stage: str
    error_code: str
    error_message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        if self.success:
            raise ValueError("ErrorResult.success 应固定为 False")
        if self.stage not in STAGES:
            raise ValueError(f"非法 stage: {self.stage}")
        if self.page_no is not None and self.page_no < 1:
            raise ValueError("page_no 必须从 1 开始")
        if not self.error_code:
            raise ValueError("error_code 不能为空")
        if not self.error_message:
            raise ValueError("error_message 不能为空")

    def to_dict(self) -> dict:
        return asdict(self)
