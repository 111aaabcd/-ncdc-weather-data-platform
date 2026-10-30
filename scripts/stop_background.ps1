$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $ProjectRoot 'logs\backend.pid'

if (-not (Test-Path -LiteralPath $PidFile)) {
    Write-Host 'No saved dashboard PID was found.' -ForegroundColor Yellow
    exit 0
}

$ProcessId = [int](Get-Content -LiteralPath $PidFile)
$process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $ProcessId
    Write-Host "Dashboard process $ProcessId stopped." -ForegroundColor Green
} else {
    Write-Host 'The saved dashboard process is no longer running.' -ForegroundColor Yellow
}
