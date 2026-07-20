from __future__ import annotations

import asyncio
import io
import zipfile
from pathlib import Path

from PIL import Image
import pytest

from d_module import config
from d_module.file_ingest.secure_upload import UploadSecurityError, secure_upload


class MemoryUpload:
    def __init__(self, filename: str, content_type: str, data: bytes) -> None:
        self.filename = filename
        self.content_type = content_type
        self._stream = io.BytesIO(data)

    async def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)


@pytest.fixture(autouse=True)
def isolated_storage(monkeypatch, tmp_path: Path):
    base = tmp_path / "storage"
    monkeypatch.setattr(config, "BASE_STORAGE_DIR", base)
    monkeypatch.setattr(config, "RAW_DIR", base / "raw")
    monkeypatch.setattr(config, "QUARANTINE_DIR", base / "quarantine")
    monkeypatch.setattr(config, "ACCEPTED_DIR", base / "accepted")
    monkeypatch.setattr(config, "CONVERTED_DIR", base / "converted")
    monkeypatch.setattr(config, "PAGE_DIR", base / "pages")
    monkeypatch.setattr(config, "PREPROCESSED_DIR", base / "preprocessed")
    monkeypatch.setattr(config, "EXTRACTED_IMAGE_DIR", base / "docx_images")


def png_bytes() -> bytes:
    image = Image.new("RGB", (8, 8), "white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_secure_upload_accepts_valid_png() -> None:
    result = asyncio.run(secure_upload(MemoryUpload("answer.png", "image/png", png_bytes()), "answer_sheet"))

    assert result.mime_type == "image/png"
    assert result.file_size > 0
    assert result.source_path.is_file()
    assert (result.source_path.parent / "manifest.json").is_file()
    assert not (config.QUARANTINE_DIR / result.upload_id).exists()


def test_secure_upload_rejects_signature_mismatch() -> None:
    with pytest.raises(UploadSecurityError) as error:
        asyncio.run(secure_upload(MemoryUpload("answer.pdf", "application/pdf", png_bytes()), "answer_sheet"))

    assert error.value.error_code == "FILE_SIGNATURE_MISMATCH"


def test_secure_upload_rejects_docx_path_traversal() -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "<w:document />")
        archive.writestr("../escape.txt", "blocked")

    with pytest.raises(UploadSecurityError) as error:
        asyncio.run(
            secure_upload(
                MemoryUpload(
                    "answer.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    output.getvalue(),
                ),
                "answer_sheet_template",
            )
        )

    assert error.value.error_code == "ARCHIVE_PATH_TRAVERSAL"


def test_secure_upload_rejects_pdf_that_would_render_too_large() -> None:
    import fitz

    document = fitz.open()
    document.new_page(width=5000, height=5000)
    pdf = document.tobytes()
    document.close()

    with pytest.raises(UploadSecurityError) as error:
        asyncio.run(
            secure_upload(
                MemoryUpload("large-page.pdf", "application/pdf", pdf),
                "question_paper",
            )
        )

    assert error.value.error_code == "PDF_RENDER_PIXELS_EXCEEDED"
