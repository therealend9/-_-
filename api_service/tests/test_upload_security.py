from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from api_service.app import app
from d_module import config


def _png_bytes() -> bytes:
    image = Image.new("RGB", (8, 8), "white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _configure_storage(monkeypatch, tmp_path: Path) -> None:
    base = tmp_path / "storage"
    monkeypatch.setattr(config, "BASE_STORAGE_DIR", base)
    monkeypatch.setattr(config, "RAW_DIR", base / "raw")
    monkeypatch.setattr(config, "QUARANTINE_DIR", base / "quarantine")
    monkeypatch.setattr(config, "ACCEPTED_DIR", base / "accepted")
    monkeypatch.setattr(config, "CONVERTED_DIR", base / "converted")
    monkeypatch.setattr(config, "PAGE_DIR", base / "pages")
    monkeypatch.setattr(config, "PREPROCESSED_DIR", base / "preprocessed")
    monkeypatch.setattr(config, "EXTRACTED_IMAGE_DIR", base / "docx_images")


def test_process_rejects_file_signature_mismatch(monkeypatch, tmp_path: Path) -> None:
    _configure_storage(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/process",
        data={"document_role": "question_paper"},
        files={"file": ("forged.pdf", _png_bytes(), "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "FILE_SIGNATURE_MISMATCH"
