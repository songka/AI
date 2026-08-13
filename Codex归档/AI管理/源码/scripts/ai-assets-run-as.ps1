[CmdletBinding()]
param(
    [string]$Account,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArguments
)

$ErrorActionPreference = 'Stop'

function Normalize-GetacadAccount {
    param([Parameter(Mandatory)][string]$InputAccount)

    $trimmed = $InputAccount.Trim()
    if (-not $trimmed) {
        throw '账号不能为空。'
    }
    if ($trimmed.IndexOf([char]92) -ge 0 -or $trimmed.Contains('@')) {
        return $trimmed
    }
    return "GETACAD\$trimmed"
}

if (-not $Account) {
    Write-Host '请只在此本地 Windows 窗口输入账号和密码，不要输入到 AI 对话框。'
    $Account = Read-Host '请输入临时 SMB 账号（未填写域时自动使用 GETACAD）'
}

$normalizedAccount = Normalize-GetacadAccount -InputAccount $Account
$loginScript = Join-Path $PSScriptRoot 'ai-assets-login.ps1'

if (-not (Test-Path -LiteralPath $loginScript)) {
    throw "登录入口不存在：$loginScript"
}

$escapedArguments = foreach ($argument in $CliArguments) {
    "'" + $argument.Replace("'", "''") + "'"
}

$program = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$loginScript`""
if ($escapedArguments) {
    $program += ' ' + ($escapedArguments -join ' ')
}

Write-Host '即将打开 Windows runas 密码提示。密码不会显示、保存或返回给 AI。'
& runas.exe /netonly "/user:$normalizedAccount" $program

if ($LASTEXITCODE -ne 0) {
    throw "runas 启动失败，退出码：$LASTEXITCODE"
}
