param(
    [string]$TaskName = "CodexProxyRecovery",
    [int]$IntervalMinutes = 30
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "Monitor-CodexWithProxy.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Monitor script not found: $scriptPath"
}

$powershellPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

$action = New-ScheduledTaskAction -Execute $powershellPath -Argument $arguments
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Every $IntervalMinutes minutes: if Codex is not ready, enable v2rayN system proxy, start Codex, then clear proxy after the UI opens." `
    -Force | Out-Null

Write-Host "Installed scheduled task '$TaskName'."
Write-Host "Monitor script: $scriptPath"
Write-Host "Log file: $env:LOCALAPPDATA\CodexProxyRecovery\monitor.log"
