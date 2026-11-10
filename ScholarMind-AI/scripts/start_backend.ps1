<# Starts the FastAPI backend on http://127.0.0.1:8000  (Swagger UI: http://127.0.0.1:8000/docs) #>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { throw "Virtual environment missing. Run scripts\setup.ps1 first." }
& $venvPy -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
