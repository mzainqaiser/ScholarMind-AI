<# Starts the React dev server on http://localhost:5173 (it proxies /api to the backend on port 8000) #>
$ErrorActionPreference = "Stop"
Set-Location (Join-Path (Split-Path -Parent $PSScriptRoot) "frontend")
if (-not (Test-Path "node_modules")) { throw "Dependencies missing. Run scripts\setup.ps1 first." }
npm run dev
