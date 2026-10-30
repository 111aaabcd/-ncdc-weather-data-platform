$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$HostScript = Join-Path $PSScriptRoot 'service_host.ps1'

try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/api/health/' -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        Write-Host 'Dashboard is already running: http://127.0.0.1:8000/' -ForegroundColor Green
        exit 0
    }
} catch {}

$listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    throw "Port 8000 is already used by PID $($listener.OwningProcess)."
}

Start-Process -FilePath 'powershell.exe' `
    -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $HostScript) `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden | Out-Null

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Milliseconds 500
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/api/health/' -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {}
}

if (-not $ready) {
    $errorLog = Join-Path $ProjectRoot 'logs\backend.err.log'
    $details = if (Test-Path -LiteralPath $errorLog) { Get-Content -Raw -LiteralPath $errorLog } else { '' }
    throw "Dashboard failed to start. $details"
}

Write-Host 'Dashboard started: http://127.0.0.1:8000/' -ForegroundColor Green
