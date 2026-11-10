<#
 ScholarMind AI - one-time setup (Windows PowerShell). Run from anywhere:
     powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
 Options:  -SkipEmbeddings   skip the ~2 GB PyTorch/sentence-transformers install (app falls back to a
                             NON-semantic keyword embedder; fine for a quick look, not for real use)
 NOTE: written for Windows but could not be executed in the Linux build sandbox - see README "Verification status".
#>
param([switch]$SkipEmbeddings)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== 1/5 Checking Python ==" -ForegroundColor Cyan
$py = if (Get-Command py -ErrorAction SilentlyContinue) { "py -3" } elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { $null }
if (-not $py) { throw "Python 3.10+ not found. Install it from https://www.python.org/downloads/ (tick 'Add to PATH')." }
$ver = Invoke-Expression "$py -c `"import sys; print('%d.%d' % sys.version_info[:2])`""
Write-Host "Found Python $ver"
if ([version]$ver -lt [version]"3.10") { throw "Python 3.10 or newer is required (found $ver)." }

Write-Host "== 2/5 Creating virtual environment (.venv) ==" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) { Invoke-Expression "$py -m venv .venv" }
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
& $venvPy -m pip install --upgrade pip

Write-Host "== 3/5 Installing backend dependencies ==" -ForegroundColor Cyan
if ($SkipEmbeddings) {
    $tmp = Join-Path $env:TEMP "scholarmind_requirements.txt"
    Get-Content requirements.txt | Where-Object { $_ -notmatch "sentence-transformers" } | Set-Content $tmp
    & $venvPy -m pip install -r $tmp
} else {
    & $venvPy -m pip install -r requirements.txt
}

Write-Host "== 4/5 Installing frontend dependencies ==" -ForegroundColor Cyan
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "Node.js 18+ not found. Install it from https://nodejs.org/" }
Push-Location frontend; npm install --no-audit --no-fund; Pop-Location

Write-Host "== 5/5 Configuration and LLM check ==" -ForegroundColor Cyan
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "Created .env from .env.example" }
$model = "qwen2.5:3b-instruct"
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "Ollama found. Download the model once with:   ollama pull $model"
} else {
    Write-Host "Ollama NOT found. Install it from https://ollama.com, then run:   ollama pull $model" -ForegroundColor Yellow
}
Write-Host "`nSetup finished. Next: scripts\start_backend.ps1 (terminal 1) and scripts\start_frontend.ps1 (terminal 2)." -ForegroundColor Green
