from __future__ import annotations
"""图像预处理服务。"""

from pathlib import Path
from typing import Iterable, List, Optional

from d_module import config
from d_module.constants import COORDINATE_BASE_PREPROCESSED_IMAGE, TASK_STATUS_PREPROCESSED
from d_module.image_preprocess.basic_ops import binarize, denoise, to_grayscale
from d_module.schemas.normalized_page import NormalizedPage
from d_module.utils.file_utils import copy_file
from d_module.utils.image_utils import get_image_size


def preprocess_page_image(
    page: NormalizedPage,
    enable_grayscale: bool = True,
    enable_denoise: bool = True,
    enable_binarize: bool = True,
) -> NormalizedPage:
    """预处理单页图片，并返回更新后的 NormalizedPage。"""
    config.ensure_storage_dirs()

    current_path = Path(page.page_image_path)
    steps: List[str] = []

    # 每个中间文件带步骤名，方便排查问题。
    if enable_grayscale:
        out = config.PREPROCESSED_DIR / f"{page.file_id}_p{page.page_no:03d}_gray.png"
        current_path = to_grayscale(current_path, out)
        steps.append("grayscale")

    if enable_denoise:
        out = config.PREPROCESSED_DIR / f"{page.file_id}_p{page.page_no:03d}_denoise.png"
        current_path = denoise(current_path, out)
        steps.append("denoise")

    if enable_binarize:
        out = config.PREPROCESSED_DIR / f"{page.file_id}_p{page.page_no:03d}_binarize.png"
        current_path = binarize(current_path, out)
        steps.append("binarize")

    if not steps:
        out = config.PREPROCESSED_DIR / f"{page.file_id}_p{page.page_no:03d}_copy.png"
        current_path = copy_file(page.page_image_path, out)
        steps.append("copy")

    width, height = get_image_size(current_path)

    if config.KEEP_IMAGE_SIZE_AFTER_PREPROCESS and (width != page.original_width or height != page.original_height):
        raise ValueError(
            "第一版要求预处理后尺寸不变，"
            f"原始尺寸=({page.original_width},{page.original_height})，"
            f"处理后尺寸=({width},{height})"
        )

    page.preprocessed_image_path = str(current_path)
    page.processed_width = width
    page.processed_height = height
    page.coordinate_base = COORDINATE_BASE_PREPROCESSED_IMAGE
    page.preprocess_steps = steps
    return page


def preprocess_pages(pages: Iterable[NormalizedPage]) -> List[NormalizedPage]:
    return [preprocess_page_image(page) for page in pages]
