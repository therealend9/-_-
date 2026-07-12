from __future__ import annotations
"""路径序列化工具。

目标：项目输出 JSON 中尽量保存相对路径，避免把本机绝对路径写进 A/B 对接结果。
"""

from pathlib import Path
from typing import Any, Iterable, Optional


PATH_KEY_HINTS = (
    "path",
    "dir",
    "directory",
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _candidate_bases(base_dir: Optional[Path] = None) -> Iterable[Path]:
    seen = set()
    for base in (base_dir, Path.cwd(), project_root()):
        if base is None:
            continue
        try:
            resolved = base.resolve()
        except Exception:
            resolved = base
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        yield resolved


def to_relative_path_str(value: Any, base_dir: Optional[Path] = None) -> Any:
    """把路径字符串尽量转成相对路径。

    如果 value 不是字符串/Path，原样返回。
    如果路径已经是相对路径，规范化分隔符后返回。
    如果路径是绝对路径，并且能相对当前项目根目录或当前工作目录表示，则返回相对路径。
    """
    if value is None:
        return None
    if isinstance(value, Path):
        raw = str(value)
    elif isinstance(value, str):
        raw = value
    else:
        return value

    text = raw.strip()
    if not text:
        return raw

    # 普通文本字段不要误当路径处理。调用方只会对路径字段使用本函数。
    path = Path(text)
    if not path.is_absolute():
        return text.replace('\\', '/')

    for base in _candidate_bases(base_dir):
        try:
            rel = path.resolve().relative_to(base)
            return str(rel).replace('\\', '/')
        except Exception:
            continue

    return text.replace('\\', '/')


def relativize_paths_in_data(data: Any, base_dir: Optional[Path] = None) -> Any:
    """递归把 dict/list 中常见路径字段改成相对路径。"""
    if isinstance(data, list):
        return [relativize_paths_in_data(item, base_dir=base_dir) for item in data]

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            lower_key = str(key).lower()
            if any(hint in lower_key for hint in PATH_KEY_HINTS):
                if isinstance(value, list):
                    result[key] = [to_relative_path_str(item, base_dir=base_dir) for item in value]
                else:
                    result[key] = to_relative_path_str(value, base_dir=base_dir)
            else:
                result[key] = relativize_paths_in_data(value, base_dir=base_dir)
        return result

    return data
