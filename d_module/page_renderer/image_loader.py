from __future__ import annotations
"""图片文件标准化为单页 NormalizedPage 所需信息。"""

from pathlib import Path
from typing import Optional, Union

from d_module import config
from d_module.utils.file_utils import copy_file
from d_module.utils.image_utils import get_image_size


def load_image_as_page(file_id: str, image_path: Union[str, Path], output_dir: Optional[Union[str, Path]] = None) -> dict:
    output_directory = Path(output_dir) if output_dir else config.PAGE_DIR
    output_directory.mkdir(parents=True, exist_ok=True)

    ext = Path(image_path).suffix.lower() or ".png"
    output_path = output_directory / f"{file_id}_p001{ext}"
    copy_file(image_path, output_path)
    width, height = get_image_size(output_path)

    return {
        "page_no": 1,
        "image_path": str(output_path),
        "width": width,
        "height": height,
        "dpi": None,
    }
