$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    & (Join-Path $PSScriptRoot 'setup.ps1')
}

& (Join-Path $PSScriptRoot 'start.ps1')
