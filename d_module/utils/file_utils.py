from __future__ import annotations
"""文件相关工具。"""

from pathlib import Path
import re
import shutil
from typing import Optional


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_file_ext(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def get_file_size(path: str | Path) -> int:
    return Path(path).stat().st_size


def safe_filename(filename: str) -> str:
    """返回仅用于展示或日志的安全文件名，不用于真实存储主键。"""
    name = Path(filename).name
    name = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fa5]", "_", name)
    return name or "unnamed"


def guess_ext_from_mime(mime_type: str) -> Optional[str]:
    mapping = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "image/jpeg": "jpg",
        "image/png": "png",
    }
    return mapping.get(mime_type)


def copy_file(source_path: str | Path, target_path: str | Path) -> Path:
    source = Path(source_path)
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def write_bytes(target_path: str | Path, data: bytes) -> Path:
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target
