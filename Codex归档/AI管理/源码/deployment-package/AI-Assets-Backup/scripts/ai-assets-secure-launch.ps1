[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArguments
)

$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot 'ai-assets-run-as.ps1'

if (-not (Test-Path -LiteralPath $runner)) {
    throw "临时账户入口不存在：$runner"
}

function Quote-ProcessArgument {
    param([Parameter(Mandatory)][string]$Value)
    return '"' + $Value.Replace('"', '\"') + '"'
}

$arguments = @(
    '-NoProfile',
    '-ExecutionPolicy',
    'Bypass',
    '-File',
    (Quote-ProcessArgument -Value $runner)
)

foreach ($argument in $CliArguments) {
    $arguments += Quote-ProcessArgument -Value $argument
}

$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
Start-Process `
    -FilePath $powershell `
    -ArgumentList ($arguments -join ' ') `
    -WindowStyle Normal

Write-Output 'SECURE_LOGIN_WINDOW_OPENED'
Write-Output '请在独立 Windows 窗口输入账号和密码；不要在 AI 对话框回复任何凭据。'
