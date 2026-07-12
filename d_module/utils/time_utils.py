from __future__ import annotations
"""时间工具。"""

from datetime import datetime, timezone


def now_iso() -> str:
    """返回带时区的 ISO 8601 时间字符串。"""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
