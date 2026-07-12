from __future__ import annotations

"""High-fidelity DOCX rendering via LibreOffice -> PDF -> page images."""

import subprocess
from pathlib import Path
from typing import List, Union

from d_module import config
from d_module.page_renderer.pdf_renderer import render_pdf_pages


def can_render_docx_via_pdf() -> bool:
    return config.resolve_libreoffice_bin() is not None


def render_docx_pages_via_pdf(
    file_id: str,
    docx_path: Union[str, Path],
    dpi: int = config.DEFAULT_DPI,
) -> List[dict]:
    libreoffice_bin = config.resolve_libreoffice_bin()
    if not libreoffice_bin:
        raise RuntimeError("LibreOffice/soffice executable not found for DOCX high-fidelity rendering")

    source_path = Path(docx_path).resolve()
    config.CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

    output_dir = config.CONVERTED_DIR / f"{file_id}_docx_pdf"
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        libreoffice_bin,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(source_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)

    pdf_path = output_dir / f"{source_path.stem}.pdf"
    if not pdf_path.exists():
        raise RuntimeError(f"DOCX converted PDF not found: {pdf_path}")

    return render_pdf_pages(file_id=file_id, pdf_path=pdf_path, dpi=dpi)
