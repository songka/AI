[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$inner = Join-Path $PSScriptRoot 'deploy-with-login.ps1'
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$arguments = "-NoExit -NoProfile -ExecutionPolicy Bypass -File `"$inner`""
Start-Process -FilePath $powershell -ArgumentList $arguments -WindowStyle Normal
Write-Output 'SECURE_DEPLOY_WINDOW_OPENED'
Write-Output '请只在独立 Windows 窗口输入 SMB 账号和密码。'
