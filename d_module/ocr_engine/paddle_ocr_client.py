from __future__ import annotations
"""PaddleOCR 客户端封装。

兼容 PaddleOCR 2.x 与 3.x：
- 2.x 常用 client.ocr(image_path, cls=True)
- 3.x 常用 client.predict(image_path)，不再接受 cls 参数
"""

from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def get_paddle_ocr_client() -> Any:
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError("运行 PaddleOCR 需要安装 paddleocr：pip install paddleocr") from exc

    # 不同 PaddleOCR 版本构造参数略有差异，所以逐级回退。
    init_candidates = [
        {"use_angle_cls": True, "lang": "ch", "enable_mkldnn": False},
        {"use_angle_cls": True, "lang": "ch"},
        {"lang": "ch", "enable_mkldnn": False},
        {"lang": "ch"},
    ]

    last_error = None
    for kwargs in init_candidates:
        try:
            return PaddleOCR(**kwargs)
        except TypeError as exc:
            last_error = exc
            continue

    raise RuntimeError(f"初始化 PaddleOCR 失败：{last_error}")


def _as_list(result: Any) -> Any:
    """把 predict 返回的生成器/迭代器转成 list；普通结果原样返回。"""
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, tuple):
        return list(result)
    try:
        return list(result)
    except TypeError:
        return result


def run_paddle_ocr(image_path: str | Path) -> Any:
    """执行 OCR。

    这里不能固定调用 ``ocr(..., cls=True)``，因为 PaddleOCR 3.x 的 predict
    接口不再支持 cls 参数，继续传入会报：
    ``predict() got an unexpected keyword argument 'cls'``。
    """
    client = get_paddle_ocr_client()
    image_path = str(image_path)

    # PaddleOCR 3.x 优先使用 predict，不传 cls。
    if hasattr(client, "predict"):
        try:
            return _as_list(client.predict(input=image_path))
        except TypeError:
            try:
                return _as_list(client.predict(image_path))
            except TypeError:
                # 极少数版本虽然有 predict，但不可用，继续尝试旧接口。
                pass

    # PaddleOCR 2.x 旧接口。
    if hasattr(client, "ocr"):
        try:
            return client.ocr(image_path, cls=True)
        except TypeError as exc:
            if "cls" in str(exc):
                return client.ocr(image_path)
            raise

    raise RuntimeError("当前 PaddleOCR 对象既没有 predict，也没有 ocr 方法。")
