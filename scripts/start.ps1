$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    throw 'Virtual environment missing. Run scripts\setup.ps1 first.'
}

Write-Host 'Dashboard: http://127.0.0.1:8000/' -ForegroundColor Cyan
Write-Host 'Press Ctrl+C to stop.'
Push-Location $ProjectRoot
try {
    & $Python (Join-Path $ProjectRoot 'backend\manage.py') runserver 127.0.0.1:8000 --noreload
} finally {
    Pop-Location
}
