$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$Manage = Join-Path $ProjectRoot 'backend\manage.py'
$Logs = Join-Path $ProjectRoot 'logs'

if (-not (Test-Path -LiteralPath $Python)) {
    throw 'Virtual environment missing. Run scripts\setup.ps1 first.'
}

New-Item -ItemType Directory -Force -Path $Logs | Out-Null
$server = Start-Process -FilePath $Python `
    -ArgumentList @($Manage, 'runserver', '127.0.0.1:8000', '--noreload') `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput (Join-Path $Logs 'backend.out.log') `
    -RedirectStandardError (Join-Path $Logs 'backend.err.log')

Set-Content -LiteralPath (Join-Path $Logs 'backend.pid') -Value $server.Id
$server.WaitForExit()
exit $server.ExitCode
