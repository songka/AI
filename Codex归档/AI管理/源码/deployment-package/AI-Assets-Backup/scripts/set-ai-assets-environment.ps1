[CmdletBinding()]
param(
    [ValidateSet('User', 'Machine')]
    [string]$Scope = 'User'
)

$publicRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets'
$backupRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets-Backup'

[Environment]::SetEnvironmentVariable('AI_ASSET_REPO', $publicRepository, $Scope)

# 备份地址默认只配置给管理员、审核者和发布者电脑。
if ($env:AI_ASSET_CONFIGURE_BACKUP -eq '1') {
    [Environment]::SetEnvironmentVariable('AI_ASSET_BACKUP_REPO', $backupRepository, $Scope)
}

Write-Host "AI_ASSET_REPO=$publicRepository"
if ($env:AI_ASSET_CONFIGURE_BACKUP -eq '1') {
    Write-Host "AI_ASSET_BACKUP_REPO=$backupRepository"
} else {
    Write-Host '未配置备份地址；如为管理电脑，先设置 AI_ASSET_CONFIGURE_BACKUP=1。'
}
