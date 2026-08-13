[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$shareRoot = '\\10.97.0.210\lfaf_Engineer'
$deployScript = Join-Path $PSScriptRoot 'deploy-to-smb.ps1'
$logRoot = Join-Path $env:LOCALAPPDATA 'AIAssetHub\logs'
$logFile = Join-Path $logRoot ("deploy-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')

function Normalize-GetacadAccount {
    param([Parameter(Mandatory)][string]$Account)
    $value = $Account.Trim()
    if (-not $value) { throw '账号不能为空。' }
    if ($value.Contains('\') -or $value.Contains('@')) { return $value }
    return "GETACAD\$value"
}

try {
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
    if (-not (Test-Path -LiteralPath $shareRoot)) {
        Write-Host '请只在此独立窗口输入 SMB 凭据，不要把账号密码发送到 AI 对话。'
        $account = Normalize-GetacadAccount (Read-Host '账号（未写域时自动加 GETACAD）')
        Write-Host "接下来由 Windows net use 安全读取 $account 的密码；输入时不会显示字符。"
        & "$env:SystemRoot\System32\net.exe" use $shareRoot '*' "/user:$account" '/persistent:no'
        if ($LASTEXITCODE -ne 0) {
            throw "SMB 登录失败，net use 退出码为 $LASTEXITCODE。"
        }
    }
    & $deployScript
    Write-Host '部署完成。可用 Chrome 打开 014-AI\AI-Assets-Hub\index.html。'
    Write-Host '管理员查看账户请运行：'
    Write-Host 'powershell -NoProfile -ExecutionPolicy Bypass -File "<管理Skill>\scripts\hub.ps1" accounts list'
}
catch {
    $message = $_.Exception.Message
    $record = @(
        "Time: $(Get-Date -Format o)"
        "Stage: secure SMB deployment"
        "Error: $message"
        'No credentials are recorded in this log.'
    )
    $record | Set-Content -LiteralPath $logFile -Encoding UTF8
    Write-Host ''
    Write-Host '部署未执行或被安全预检拒绝。' -ForegroundColor Red
    Write-Host "原因：$message" -ForegroundColor Red
    Write-Host "诊断日志：$logFile"
    Write-Host '如果提示目标目录已存在且非空，表示首次部署已经完成，不要重复覆盖。'
}
finally {
    Remove-Variable account -Force -ErrorAction SilentlyContinue
    Write-Host ''
    Write-Host '此窗口会保持打开；确认信息后可手动关闭。'
}
