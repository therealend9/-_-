from __future__ import annotations
"""上传文件校验。"""

from d_module import config
from d_module.utils.file_utils import get_file_ext


def validate_file_extension(origin_name: str) -> str:
    ext = get_file_ext(origin_name)
    if ext == "jpeg":
        ext = "jpg"
    if ext not in config.ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件扩展名: {ext}")
    return ext


def validate_mime_type(mime_type: str) -> None:
    if mime_type not in config.ALLOWED_MIME_TYPES:
        raise ValueError(f"不支持的 MIME 类型: {mime_type}")


def validate_file_size(file_size: int) -> None:
    if file_size <= 0:
        raise ValueError("文件大小必须大于 0")
    if file_size > config.MAX_FILE_SIZE_BYTES:
        raise ValueError(f"文件过大，最大允许 {config.MAX_FILE_SIZE_BYTES} 字节")


def validate_file_name(origin_name: str) -> None:
    if not origin_name or origin_name.strip() in {".", ".."}:
        raise ValueError("文件名不合法")
    if "/" in origin_name or "\\" in origin_name:
        raise ValueError("文件名不能包含路径分隔符")
    if len(origin_name) > 256:
        raise ValueError("文件名长度不能超过 256 个字符")
    if any(ord(char) < 32 for char in origin_name):
        raise ValueError("文件名不能包含控制字符")
