from __future__ import annotations

"""High-fidelity DOCX rendering via LibreOffice -> PDF -> page images."""

import subprocess
import base64
import os
from pathlib import Path
from typing import List, Union

from d_module import config
from d_module.page_renderer.pdf_renderer import render_pdf_pages


def can_render_docx_via_pdf() -> bool:
    return config.resolve_libreoffice_bin() is not None or os.name == "nt"


def convert_docx_to_pdf(docx_path: Union[str, Path], output_dir: Union[str, Path]) -> Path:
    """Convert a DOCX through LibreOffice or Microsoft Word on Windows."""
    source_path = Path(docx_path).resolve()
    target_dir = Path(output_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    libreoffice_bin = config.resolve_libreoffice_bin()
    if libreoffice_bin:
        command = [
            libreoffice_bin,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(target_dir),
            str(source_path),
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        pdf_path = target_dir / f"{source_path.stem}.pdf"
        if pdf_path.is_file():
            return pdf_path
        raise RuntimeError(f"DOCX converted PDF not found: {pdf_path}")
    if os.name == "nt":
        # Word COM can fail to export when the target basename contains
        # non-ASCII characters. The source path remains Unicode-safe through
        # the encoded PowerShell command; the generated filename stays ASCII.
        return _convert_with_word_com(source_path, target_dir / "source.pdf")
    raise RuntimeError("LibreOffice/soffice executable not found for DOCX high-fidelity rendering")


def render_docx_pages_via_pdf(
    file_id: str,
    docx_path: Union[str, Path],
    dpi: int = config.DEFAULT_DPI,
) -> List[dict]:
    source_path = Path(docx_path).resolve()
    config.CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

    output_dir = config.CONVERTED_DIR / f"{file_id}_docx_pdf"
    pdf_path = convert_docx_to_pdf(source_path, output_dir)

    return render_pdf_pages(file_id=file_id, pdf_path=pdf_path, dpi=dpi)


def _convert_with_word_com(source_path: Path, pdf_path: Path) -> Path:
    """Use installed Microsoft Word when LibreOffice is unavailable on Windows."""
    script = f"""
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {{
  $document = $word.Documents.Open('{_ps_quote(source_path)}', $false, $true)
  $document.ExportAsFixedFormat('{_ps_quote(pdf_path)}', 17)
  $document.Close($false)
}} finally {{
  if ($word) {{ $word.Quit() }}
}}
"""
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    process = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True,
        text=True,
    )
    # Word can finish writing the PDF and then report an RPC error while the
    # COM server tears down. A real output file is the reliable success signal.
    if pdf_path.is_file():
        return pdf_path
    if process.returncode != 0:
        detail = (process.stderr or process.stdout or "Microsoft Word conversion failed").strip()
        raise RuntimeError(f"Microsoft Word DOCX conversion failed: {detail}")
    raise RuntimeError(f"Microsoft Word did not create converted PDF: {pdf_path}")


def _ps_quote(value: Path) -> str:
    return str(value).replace("'", "''")
