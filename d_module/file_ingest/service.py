from __future__ import annotations
"""文件接入服务。"""

from pathlib import Path
from typing import Optional, Union

from d_module import config
from d_module.constants import (
    SOURCE_TYPE_DOCX,
    SOURCE_TYPE_IMAGE,
    SOURCE_TYPE_PDF,
    TASK_STATUS_UPLOADED,
)
from d_module.file_ingest.storage import save_raw_file
from d_module.file_ingest.validators import (
    validate_file_extension,
    validate_file_name,
    validate_file_size,
    validate_mime_type,
)
from d_module.schemas.file_task import FileTask
from d_module.utils.file_utils import get_file_size
from d_module.utils.id_generator import generate_file_id
from d_module.utils.time_utils import now_iso


def _source_type_from_ext(ext: str) -> str:
    if ext == "docx":
        return SOURCE_TYPE_DOCX
    if ext == "pdf":
        return SOURCE_TYPE_PDF
    if ext in {"jpg", "jpeg", "png"}:
        return SOURCE_TYPE_IMAGE
    raise ValueError(f"无法识别 source_type: {ext}")


def create_file_task(
    submission_id: str,
    origin_name: str,
    mime_type: str,
    file_size: Optional[int] = None,
    source_path: Optional[Union[str, Path]] = None,
    file_bytes: Optional[bytes] = None,
) -> FileTask:
    """创建 FileTask，并把原始文件保存到 raw 目录。

    参数说明：
    - source_path：本地已有文件路径。
    - file_bytes：Web 上传场景中的文件内容。
    两者二选一。
    """
    config.ensure_storage_dirs()

    validate_file_name(origin_name)
    ext = validate_file_extension(origin_name)
    validate_mime_type(mime_type)

    actual_size = file_size
    if actual_size is None:
        if file_bytes is not None:
            actual_size = len(file_bytes)
        elif source_path is not None:
            actual_size = get_file_size(source_path)
        else:
            raise ValueError("无法确定文件大小")

    validate_file_size(actual_size)

    file_id = generate_file_id()
    storage_path = save_raw_file(
        file_id=file_id,
        ext=ext,
        source_path=source_path,
        file_bytes=file_bytes,
    )

    return FileTask(
        file_id=file_id,
        submission_id=submission_id,
        origin_name=origin_name,
        ext=ext,
        mime_type=mime_type,
        storage_path=str(storage_path),
        file_size=actual_size,
        page_count=None,
        source_type=_source_type_from_ext(ext),
        parse_mode=None,
        task_status=TASK_STATUS_UPLOADED,
        created_at=now_iso(),
    )
