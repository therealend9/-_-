from __future__ import annotations
"""FileTask：上传文件进入 A 负责人链路后的任务对象。"""

from dataclasses import asdict, dataclass
from typing import Optional

from d_module.constants import PARSE_MODES, SOURCE_TYPES, TASK_STATUSES


@dataclass
class FileTask:
    file_id: str
    submission_id: str
    origin_name: str
    ext: str
    mime_type: str
    storage_path: str
    file_size: int
    page_count: Optional[int]
    source_type: str
    parse_mode: Optional[str]
    task_status: str
    created_at: str

    def __post_init__(self) -> None:
        self.ext = self.ext.lower().lstrip(".")
        if not self.file_id:
            raise ValueError("file_id 不能为空")
        if not self.submission_id:
            raise ValueError("submission_id 不能为空")
        if not self.origin_name:
            raise ValueError("origin_name 不能为空")
        if self.file_size < 0:
            raise ValueError("file_size 不能为负数")
        if self.page_count is not None and self.page_count < 1:
            raise ValueError("page_count 必须大于等于 1")
        if self.source_type not in SOURCE_TYPES:
            raise ValueError(f"非法 source_type: {self.source_type}")
        if self.parse_mode is not None and self.parse_mode not in PARSE_MODES:
            raise ValueError(f"非法 parse_mode: {self.parse_mode}")
        if self.task_status not in TASK_STATUSES:
            raise ValueError(f"非法 task_status: {self.task_status}")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FileTask":
        return cls(**data)
