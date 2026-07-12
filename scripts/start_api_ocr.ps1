param(
    [int]$Port = 8000
)

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv-ocr\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw "OCR virtual environment is missing: $python"
}

Set-Location $root
& $python -m uvicorn api_service.app:app --host 127.0.0.1 --port $Port
