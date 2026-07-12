from __future__ import annotations
"""把 OCR 引擎原始输出转换为 OCRPageResult。

兼容 PaddleOCR 2.x 与 PaddleOCR 3.x / PaddleX 输出。

本版本额外修复：
- PaddleOCR 3.x 返回的 numpy.ndarray 不能直接参与 ``or`` / ``if not xxx`` 判断；
  否则会报：
  ``The truth value of an array with more than one element is ambiguous``。
"""

from typing import Any, Iterable, List, Sequence, Tuple

from d_module.constants import BBOX_SOURCE_OCR, SOURCE_MODE_OCR
from d_module.ocr_engine.text_cleaner import is_low_value_noise_text, normalize_ocr_text
from d_module.schemas.normalized_page import NormalizedPage
from d_module.schemas.ocr_block import OCRBlock
from d_module.schemas.ocr_page_result import OCRPageResult
from d_module.utils.id_generator import generate_block_id


def _to_builtin(value: Any) -> Any:
    """把 numpy array / paddle tensor 等转成 Python 内置类型。"""
    if value is None:
        return None
    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except Exception:
            pass
    return value


def _is_empty(value: Any) -> bool:
    """安全判断空值，避免 numpy.ndarray 的布尔歧义。"""
    if value is None:
        return True
    if isinstance(value, (str, bytes)):
        return len(value) == 0
    try:
        return len(value) == 0  # type: ignore[arg-type]
    except Exception:
        return False


def _first_not_none(*values: Any) -> Any:
    """返回第一个不是 None 的值。

    注意：不能写成 ``a or b``，因为 PaddleOCR 3.x 常返回 numpy.ndarray，
    numpy.ndarray 参与布尔判断会触发：
    ``The truth value of an array with more than one element is ambiguous``。
    """
    for value in values:
        if value is not None:
            return value
    return None


def _get_first(data: dict, *keys: str) -> Any:
    """从 dict 中按顺序取第一个存在且值不是 None 的字段。"""
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def _bbox_from_points(points: Sequence[Sequence[float]]) -> List[float]:
    points = _to_builtin(points)
    if _is_empty(points):
        return [0.0, 0.0, 1.0, 1.0]

    xs: List[float] = []
    ys: List[float] = []

    for point in points:
        point = _to_builtin(point)
        if point is None or len(point) < 2:
            continue
        xs.append(float(point[0]))
        ys.append(float(point[1]))

    if not xs or not ys:
        return [0.0, 0.0, 1.0, 1.0]

    return [min(xs), min(ys), max(xs), max(ys)]


def _points_from_box(box: Sequence[float]) -> List[List[float]]:
    box = _to_builtin(box)
    if not _is_empty(box) and len(box) >= 4:
        x_min, y_min, x_max, y_max = [float(x) for x in box[:4]]
        return [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]
    return [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]


def _result_to_dict(item: Any) -> dict:
    """尽量把 PaddleOCR 3.x 的 OCRResult 转成 dict。"""
    item = _to_builtin(item)

    if isinstance(item, dict):
        # 有些版本 json() 返回 {"res": {...}}
        res = item.get("res")
        if isinstance(res, dict):
            return res
        return item

    # PaddleOCR 3.x 的结果对象常见有 json / to_json / to_dict / dict 等属性或方法。
    for attr in ("json", "to_json", "to_dict", "dict"):
        if hasattr(item, attr):
            try:
                value = getattr(item, attr)
                value = value() if callable(value) else value
                value = _to_builtin(value)
                if isinstance(value, dict):
                    res = value.get("res")
                    if isinstance(res, dict):
                        return res
                    return value
            except Exception:
                continue

    # 部分结果对象支持 get / keys，但不是 dict 子类。
    try:
        keys = list(item.keys())
        return {key: _to_builtin(item[key]) for key in keys}
    except Exception:
        pass

    return {}


def _iter_paddle_v3_items(raw_result: Any) -> Iterable[Tuple[Any, str, float]]:
    """解析 PaddleOCR 3.x / PaddleX 输出。"""
    if _is_empty(raw_result):
        return []

    result_items = raw_result if isinstance(raw_result, list) else [raw_result]
    parsed_items: List[Tuple[Any, str, float]] = []

    for result_item in result_items:
        data = _result_to_dict(result_item)
        if not data:
            continue

        texts = _to_builtin(_get_first(data, "rec_texts", "texts", "text"))
        scores = _to_builtin(_get_first(data, "rec_scores", "scores", "confidence"))
        polys = _to_builtin(
            _get_first(data, "rec_polys", "dt_polys", "text_det_polys", "polys")
        )
        boxes = _to_builtin(_get_first(data, "rec_boxes", "boxes", "det_boxes"))

        if isinstance(texts, str):
            texts = [texts]
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        if _is_empty(texts):
            continue

        for index, text in enumerate(texts):
            confidence = 1.0
            if not _is_empty(scores) and index < len(scores):
                try:
                    confidence = float(scores[index])
                except Exception:
                    confidence = 1.0

            if not _is_empty(polys) and index < len(polys):
                points = polys[index]
            elif not _is_empty(boxes) and index < len(boxes):
                points = _points_from_box(boxes[index])
            else:
                # 没有坐标时给一个最小占位框，避免结构缺字段。
                points = _points_from_box([0, 0, 1, 1])

            parsed_items.append((points, str(text or ""), confidence))

    return parsed_items


def _looks_like_v2_line(item: Any) -> bool:
    """粗略判断是否是 PaddleOCR 2.x 的单行结果。"""
    try:
        return len(item) >= 2 and len(item[0]) >= 4
    except Exception:
        return False


def _iter_paddle_v2_items(raw_result: Any) -> Iterable[Tuple[Any, str, float]]:
    """解析 PaddleOCR 2.x 旧输出。"""
    if _is_empty(raw_result):
        return []

    page_result = raw_result[0] if isinstance(raw_result, list) and raw_result else raw_result
    if _is_empty(page_result):
        return []

    items: List[Tuple[Any, str, float]] = []
    for item in page_result:
        try:
            # 旧格式 item = [points, [text, confidence]]
            points = item[0]
            text = item[1][0] or ""
            confidence = float(item[1][1])
            items.append((points, text, confidence))
        except Exception:
            continue
    return items


def _iter_paddle_items(raw_result: Any) -> Iterable[Tuple[Any, str, float]]:
    """兼容常见 PaddleOCR 输出格式。"""
    v3_items = list(_iter_paddle_v3_items(raw_result))
    if v3_items:
        return v3_items
    return list(_iter_paddle_v2_items(raw_result))


def sort_blocks_by_reading_order(blocks: List[OCRBlock]) -> List[OCRBlock]:
    """按从上到下、从左到右排序，并重写 reading_order。"""
    sorted_blocks = sorted(blocks, key=lambda block: (block.bbox[1], block.bbox[0]))
    for index, block in enumerate(sorted_blocks, start=1):
        block.reading_order = index
        block.line_index = index
    return sorted_blocks


def calculate_overall_confidence(blocks: List[OCRBlock]) -> Any:
    if not blocks:
        return None
    return round(sum(block.confidence for block in blocks) / len(blocks), 4)


def normalize_paddle_result(
    file_id: str,
    page: NormalizedPage,
    raw_result: Any,
    ocr_engine: str,
    low_confidence_threshold: float,
) -> OCRPageResult:
    blocks: List[OCRBlock] = []

    for index, (points, text, confidence) in enumerate(_iter_paddle_items(raw_result), start=1):
        confidence = max(0.0, min(1.0, float(confidence)))
        cleaned_text = normalize_ocr_text(text or "")
        if is_low_value_noise_text(cleaned_text, confidence, threshold=low_confidence_threshold):
            continue
        block = OCRBlock(
            block_id=generate_block_id(file_id, page.page_no, index),
            bbox=_bbox_from_points(points),
            bbox_source=BBOX_SOURCE_OCR,
            source_mode=SOURCE_MODE_OCR,
            text=cleaned_text,
            confidence=confidence,
            line_index=index,
            reading_order=index,
            is_low_confidence=confidence < low_confidence_threshold,
        )
        blocks.append(block)

    blocks = sort_blocks_by_reading_order(blocks)

    return OCRPageResult(
        file_id=file_id,
        page_no=page.page_no,
        image_path=page.effective_image_path,
        width=page.processed_width,
        height=page.processed_height,
        dpi=page.dpi,
        coordinate_base=page.coordinate_base,
        ocr_engine=ocr_engine,
        overall_confidence=calculate_overall_confidence(blocks),
        blocks=blocks,
    )
