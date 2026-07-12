from __future__ import annotations
"""ID 生成工具。"""

from uuid import uuid4


def generate_file_id(prefix: str = "file") -> str:
    """生成文件 ID。

    示例：file_7f3a9c2b1d4e
    """
    return f"{prefix}_{uuid4().hex[:12]}"


def generate_block_id(file_id: str, page_no: int, index: int) -> str:
    """生成全局唯一 OCRBlock ID。

    示例：blk_file_001_p001_0001
    """
    safe_file_id = file_id.replace("/", "_").replace("\\", "_")
    return f"blk_{safe_file_id}_p{page_no:03d}_{index:04d}"
