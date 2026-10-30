$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    $PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        $PreviousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'SilentlyContinue'
        $InstalledPythons = py -0p 2>$null
        $ErrorActionPreference = $PreviousPreference
        if ($InstalledPythons -match '-V:3\.12') {
            py -3.12 -m venv (Join-Path $ProjectRoot '.venv')
        } else {
            py -3 -m venv (Join-Path $ProjectRoot '.venv')
        }
    } else {
        $SystemPython = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $SystemPython) {
            throw 'Python 3.10+ was not found. Install Python, then rerun setup.ps1.'
        }
        & $SystemPython.Source -m venv (Join-Path $ProjectRoot '.venv')
    }
}

$Wheelhouse = Join-Path $ProjectRoot 'wheels'
if (Test-Path $Wheelhouse) {
    & $Python -m pip install --no-index --find-links $Wheelhouse -r (Join-Path $ProjectRoot 'requirements.txt')
} else {
    & $Python -m pip install -r (Join-Path $ProjectRoot 'requirements.txt')
}
if ($LASTEXITCODE -ne 0) {
    throw 'Python dependency installation failed.'
}

$FrontendIndex = Join-Path $ProjectRoot 'frontend\dist\client\index.html'
$Npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($Npm) {
    Push-Location (Join-Path $ProjectRoot 'frontend')
    try {
        npm install
        npm run build
    } finally {
        Pop-Location
    }
} elseif (-not (Test-Path $FrontendIndex)) {
    throw 'Frontend build is missing and npm was not found. Install Node.js 20+, then rerun setup.ps1.'
} else {
    Write-Host 'npm not found; using the packaged frontend build.' -ForegroundColor Yellow
}

Push-Location $ProjectRoot
try {
    & $Python -m pipeline.run_pipeline
    if ($LASTEXITCODE -ne 0) {
        throw 'Pipeline execution failed.'
    }
} finally {
    Pop-Location
}

Write-Host 'Setup complete. Run scripts\start.ps1 next.' -ForegroundColor Green
