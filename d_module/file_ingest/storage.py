from __future__ import annotations
"""原始文件存储。"""

from pathlib import Path
from typing import Optional, Union

from d_module import config
from d_module.utils.file_utils import copy_file, write_bytes


def build_storage_path(file_id: str, ext: str, raw_dir: Optional[Union[str, Path]] = None) -> Path:
    directory = Path(raw_dir) if raw_dir else config.RAW_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{file_id}.{ext}"


def save_raw_file(
    file_id: str,
    ext: str,
    source_path: Optional[Union[str, Path]] = None,
    file_bytes: Optional[bytes] = None,
    raw_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """保存原始文件。source_path 和 file_bytes 二选一。"""
    target_path = build_storage_path(file_id=file_id, ext=ext, raw_dir=raw_dir)

    if file_bytes is not None:
        return write_bytes(target_path, file_bytes)

    if source_path is not None:
        return copy_file(source_path, target_path)

    raise ValueError("source_path 和 file_bytes 至少需要提供一个")
