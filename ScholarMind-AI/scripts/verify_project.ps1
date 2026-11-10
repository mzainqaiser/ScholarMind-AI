<#
 Runs every automated check and prints a PASS/FAIL summary:
   backend tests (pytest), frontend tests (vitest), TypeScript + production build, retrieval evaluation.
 No LLM or internet is needed (tests use a labelled mock LLM). Run:  powershell -ExecutionPolicy Bypass -File scripts\verify_project.ps1
#>
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { throw "Run scripts\setup.ps1 first." }
$results = [ordered]@{}
function Run($name, [scriptblock]$cmd) {
    Write-Host "`n=== $name ===" -ForegroundColor Cyan
    & $cmd
    $script:results[$name] = ($LASTEXITCODE -eq 0)
}
Run "Backend tests (pytest)"      { & $venvPy -m pytest backend/tests -q }
Run "Retrieval evaluation"        { & $venvPy evaluation/evaluate_retrieval.py }
Push-Location frontend
Run "Frontend tests (vitest)"     { npm test }
Run "TypeScript + production build" { npm run build }
Pop-Location
Write-Host "`n================ SUMMARY ================"
foreach ($k in $results.Keys) {
    $c = if ($results[$k]) { "Green" } else { "Red" }
    Write-Host ("{0,-34} {1}" -f $k, $(if ($results[$k]) { "PASS" } else { "FAIL" })) -ForegroundColor $c
}
if ($results.Values -contains $false) { exit 1 }
