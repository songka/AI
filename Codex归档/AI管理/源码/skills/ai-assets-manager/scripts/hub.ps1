[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$HubArguments
)

$ErrorActionPreference = 'Stop'
$publicRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets'
$backupRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets-Backup'
$client = Join-Path $PSScriptRoot 'asset_hub.py'
$loginScript = Join-Path $PSScriptRoot 'secure-login.ps1'
$identityScript = Join-Path $PSScriptRoot 'smb-identity.ps1'
. $identityScript

$principal = Get-AiAssetsSmbPrincipal

if (-not $principal) {
    Write-Host '当前 PowerShell 尚无可验证的 SMB 身份，先在本地完成安全登录。'
    & $loginScript
    $principal = Get-AiAssetsSmbPrincipal
}

if (-not $principal) {
    throw '无法确认实际 SMB 登录账户，拒绝执行 Hub 命令。'
}

if (-not (Test-Path -LiteralPath $client -ErrorAction SilentlyContinue)) {
    throw "Skill 内置 Hub 客户端不存在：$client。请重新安装 ai-assets-manager。"
}

if (-not $HubArguments -or $HubArguments.Count -eq 0) {
    $HubArguments = @('--help')
}

& python $client --repo $publicRepository --backup-repo $backupRepository @HubArguments
exit $LASTEXITCODE
