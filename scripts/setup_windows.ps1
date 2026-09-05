$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}

Set-ExecutionPolicy -Scope Process Bypass -Force
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
Write-Host ""
Write-Host "DoomForge instalado. Ejecuta: python main.py" -ForegroundColor Magenta
