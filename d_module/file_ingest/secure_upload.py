from __future__ import annotations

"""Security gate for every externally uploaded examination document."""

import hashlib
import json
import os
import shutil
import warnings
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

from d_module import config
from d_module.file_ingest.validators import validate_file_extension, validate_file_name
from d_module.utils.file_utils import safe_filename


MIME_BY_EXTENSION = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "jpg": "image/jpeg",
    "png": "image/png",
}


class UploadSecurityError(ValueError):
    def __init__(self, error_code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code

    def detail(self) -> dict[str, Any]:
        return {"error_code": self.error_code, "message": str(self), "retryable": False, "file_id": None}


@dataclass(frozen=True)
class SecureUpload:
    upload_id: str
    source_path: Path
    origin_name: str
    mime_type: str
    file_size: int
    sha256: str
    purpose: str


async def secure_upload(upload_file: Any, purpose: str) -> SecureUpload:
    """Stream an upload into quarantine, validate it, then atomically accept it."""
    origin_name = str(getattr(upload_file, "filename", "") or "")
    try:
        validate_file_name(origin_name)
        extension = validate_file_extension(origin_name)
    except ValueError as exc:
        raise UploadSecurityError("INVALID_FILE_NAME", str(exc), 400) from exc
    if extension == "jpeg":
        extension = "jpg"

    _validate_client_mime(getattr(upload_file, "content_type", None), extension)
    config.ensure_storage_dirs()
    upload_id = f"upl_{uuid4().hex}"
    quarantine_dir = config.QUARANTINE_DIR / upload_id
    temporary_path = quarantine_dir / "payload.part"
    quarantine_dir.mkdir(parents=True, exist_ok=False)
    digest = hashlib.sha256()
    size = 0
    try:
        with temporary_path.open("xb") as target:
            while True:
                chunk = await upload_file.read(config.UPLOAD_CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                size += len(chunk)
                if size > config.MAX_FILE_SIZE_BYTES:
                    raise UploadSecurityError("FILE_TOO_LARGE", f"文件超过最大允许大小 {config.MAX_FILE_SIZE_BYTES} 字节", 413)
                digest.update(chunk)
                target.write(chunk)

        if size == 0:
            raise UploadSecurityError("FILE_EMPTY", "上传文件不能为空", 400)
        mime_type = inspect_file(temporary_path, extension)
        return _accept_upload(
            upload_id=upload_id,
            temporary_path=temporary_path,
            quarantine_dir=quarantine_dir,
            origin_name=safe_filename(origin_name),
            extension=extension,
            mime_type=mime_type,
            file_size=size,
            sha256=digest.hexdigest(),
            purpose=purpose,
        )
    except UploadSecurityError:
        _remove_tree(quarantine_dir)
        raise
    except Exception as exc:
        _remove_tree(quarantine_dir)
        raise UploadSecurityError("FILE_SECURITY_CHECK_FAILED", "文件安全检查失败", 422) from exc


def inspect_file(path: Path, extension: str) -> str:
    """Verify signature and type-specific resource limits without parsing untrusted content downstream."""
    detected = _detect_file_type(path)
    if detected != extension:
        raise UploadSecurityError("FILE_SIGNATURE_MISMATCH", "文件扩展名与真实内容不一致", 422)
    if detected in {"jpg", "png"}:
        _validate_image(path, detected)
    elif detected == "pdf":
        _validate_pdf(path)
    elif detected == "docx":
        _validate_docx_archive(path)
    else:
        raise UploadSecurityError("FILE_TYPE_NOT_ALLOWED", "文件类型不支持", 415)
    return MIME_BY_EXTENSION[detected]


def _detect_file_type(path: Path) -> str | None:
    with path.open("rb") as source:
        header = source.read(8)
    if header.startswith(b"%PDF-"):
        return "pdf"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header.startswith(b"PK\x03\x04") or header.startswith(b"PK\x05\x06"):
        return "docx" if _looks_like_docx(path) else None
    return None


def _looks_like_docx(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            return "[Content_Types].xml" in names and "word/document.xml" in names
    except zipfile.BadZipFile:
        return False


def _validate_image(path: Path, expected_type: str) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise UploadSecurityError("IMAGE_VALIDATOR_UNAVAILABLE", "图片安全校验组件不可用", 503) from exc
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                width, height = image.size
                image_format = str(image.format or "").lower()
                if image_format not in {"jpeg", "png"} or (expected_type == "jpg" and image_format != "jpeg") or (expected_type == "png" and image_format != "png"):
                    raise UploadSecurityError("FILE_SIGNATURE_MISMATCH", "图片格式与文件内容不一致", 422)
                if width <= 0 or height <= 0 or width > config.MAX_IMAGE_DIMENSION or height > config.MAX_IMAGE_DIMENSION:
                    raise UploadSecurityError("IMAGE_DIMENSIONS_EXCEEDED", "图片尺寸超过安全限制", 422)
                if width * height > config.MAX_IMAGE_PIXELS:
                    raise UploadSecurityError("IMAGE_PIXELS_EXCEEDED", "图片总像素超过安全限制", 422)
                image.verify()
    except UploadSecurityError:
        raise
    except Exception as exc:
        raise UploadSecurityError("FILE_CORRUPTED", "图片文件损坏或无法安全解码", 422) from exc


def _validate_pdf(path: Path) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise UploadSecurityError("PDF_VALIDATOR_UNAVAILABLE", "PDF 安全校验组件不可用", 503) from exc
    try:
        with fitz.open(path) as document:
            if not document.is_pdf:
                raise UploadSecurityError("FILE_SIGNATURE_MISMATCH", "文件不是有效 PDF", 422)
            if len(document) < 1 or len(document) > config.MAX_PDF_PAGES:
                raise UploadSecurityError("PDF_PAGE_LIMIT_EXCEEDED", "PDF 页数超过安全限制", 422)
            for page in document:
                rect = page.rect
                if rect.width <= 0 or rect.height <= 0 or rect.width > 20000 or rect.height > 20000:
                    raise UploadSecurityError("PDF_PAGE_DIMENSIONS_EXCEEDED", "PDF 页面尺寸超过安全限制", 422)
                render_scale = config.DEFAULT_DPI / 72
                render_pixels = rect.width * render_scale * rect.height * render_scale
                if render_pixels > config.MAX_PDF_RENDER_PIXELS:
                    raise UploadSecurityError("PDF_RENDER_PIXELS_EXCEEDED", "PDF 页面渲染像素超过安全限制", 422)
    except UploadSecurityError:
        raise
    except Exception as exc:
        raise UploadSecurityError("FILE_CORRUPTED", "PDF 文件损坏或无法安全打开", 422) from exc


def _validate_docx_archive(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > config.MAX_ARCHIVE_ENTRIES:
                raise UploadSecurityError("ARCHIVE_ENTRY_LIMIT_EXCEEDED", "DOCX 内部文件数量超过安全限制", 422)
            total_size = 0
            for entry in entries:
                _validate_archive_entry(entry)
                total_size += entry.file_size
                if total_size > config.MAX_ARCHIVE_UNPACKED_BYTES:
                    raise UploadSecurityError("ARCHIVE_SIZE_LIMIT_EXCEEDED", "DOCX 解压后大小超过安全限制", 422)
                if entry.compress_size and entry.file_size / entry.compress_size > config.MAX_ARCHIVE_COMPRESSION_RATIO:
                    raise UploadSecurityError("ARCHIVE_COMPRESSION_RATIO_EXCEEDED", "DOCX 压缩比异常", 422)
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise UploadSecurityError("FILE_CORRUPTED", "DOCX 结构不完整", 422)
            if any(name.lower().endswith("vbaproject.bin") for name in names):
                raise UploadSecurityError("DOCX_MACRO_NOT_ALLOWED", "DOCX 不允许包含宏", 422)
            _reject_external_relationships(archive, names)
    except UploadSecurityError:
        raise
    except (zipfile.BadZipFile, OSError) as exc:
        raise UploadSecurityError("FILE_CORRUPTED", "DOCX 文件损坏或无法安全打开", 422) from exc


def _validate_archive_entry(entry: zipfile.ZipInfo) -> None:
    entry_path = PurePosixPath(entry.filename)
    if entry.filename.startswith(("/", "\\")) or ".." in entry_path.parts or ":" in entry.filename:
        raise UploadSecurityError("ARCHIVE_PATH_TRAVERSAL", "DOCX 包含非法内部路径", 422)


def _reject_external_relationships(archive: zipfile.ZipFile, names: set[str]) -> None:
    for name in names:
        if not name.endswith(".rels"):
            continue
        relation = archive.read(name)
        if b'TargetMode="External"' in relation or b"TargetMode='External'" in relation:
            raise UploadSecurityError("DOCX_EXTERNAL_RELATIONSHIP_NOT_ALLOWED", "DOCX 不允许包含外部关系", 422)


def _validate_client_mime(supplied_mime: str | None, extension: str) -> None:
    if not supplied_mime or supplied_mime == "application/octet-stream":
        return
    expected = MIME_BY_EXTENSION[extension]
    if supplied_mime != expected:
        raise UploadSecurityError("FILE_MIME_MISMATCH", "客户端 MIME 类型与文件扩展名不一致", 415)


def _accept_upload(
    upload_id: str,
    temporary_path: Path,
    quarantine_dir: Path,
    origin_name: str,
    extension: str,
    mime_type: str,
    file_size: int,
    sha256: str,
    purpose: str,
) -> SecureUpload:
    accepted_dir = config.ACCEPTED_DIR / upload_id
    accepted_dir.mkdir(parents=True, exist_ok=False)
    try:
        accepted_path = accepted_dir / f"original.{extension}"
        os.replace(temporary_path, accepted_path)
        manifest = {
            "upload_id": upload_id,
            "origin_name": origin_name,
            "mime_type": mime_type,
            "file_size": file_size,
            "sha256": sha256,
            "purpose": purpose,
            "security_status": "accepted",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        manifest_path = accepted_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        _remove_tree(accepted_dir)
        raise
    _remove_tree(quarantine_dir)
    return SecureUpload(upload_id, accepted_path, origin_name, mime_type, file_size, sha256, purpose)


def _remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
