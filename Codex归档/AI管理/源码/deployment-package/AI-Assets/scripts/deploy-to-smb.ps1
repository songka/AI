[CmdletBinding()]
param(
    [string]$PackageRoot
)

$ErrorActionPreference = 'Stop'
if (-not $PackageRoot) {
    $scriptDirectory = Split-Path $MyInvocation.MyCommand.Path -Parent
    $PackageRoot = Join-Path (Split-Path $scriptDirectory -Parent) 'deployment-package'
}
$publicRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets'
$backupRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets-Backup'
$hubWebsite = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\AI-Assets-Hub'
$identityScript = Join-Path $PackageRoot 'AI-Assets\skills\ai-assets-manager\scripts\smb-identity.ps1'

if (-not (Test-Path -LiteralPath $identityScript)) {
    throw "部署包缺少 SMB 身份脚本：$identityScript"
}
. $identityScript
$initialAdministrator = Get-AiAssetsSmbPrincipal
if (-not $initialAdministrator) {
    throw '无法从 Windows SMB 会话确认实际登录账户，拒绝部署无管理员的 Hub。'
}

function Assert-EmptyTarget {
    param([Parameter(Mandatory)][string]$Destination)
    if (Test-Path -LiteralPath $Destination) {
        $existing = @(Get-ChildItem -LiteralPath $Destination -Force)
        if ($existing.Count -gt 0) {
            throw "目标目录已存在且非空，拒绝覆盖：$Destination"
        }
    }
}

function Initialize-Repository {
    param(
        [Parameter(Mandatory)]
        [string]$Source,
        [Parameter(Mandatory)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "本地部署包不存在：$Source"
    }

    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -ItemType Directory -Path $Destination | Out-Null
    }

    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $Destination -Recurse
    }
}

function Initialize-Administrator {
    param(
        [Parameter(Mandatory)][string[]]$Repositories,
        [Parameter(Mandatory)][string]$Principal
    )

    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    $states = @()
    foreach ($repository in $Repositories) {
        $rolesPath = Join-Path $repository 'config\roles.json'
        if (-not (Test-Path -LiteralPath $rolesPath)) {
            throw "部署后的角色配置不存在：$rolesPath"
        }
        $states += [PSCustomObject]@{
            RolesPath = $rolesPath
            MarkerPath = Join-Path $repository 'config\bootstrap-admin.completed.json'
            OriginalBytes = [IO.File]::ReadAllBytes($rolesPath)
        }
    }

    $updated = @()
    try {
        foreach ($state in $states) {
            $roles = Get-Content -LiteralPath $state.RolesPath -Raw -Encoding UTF8 |
                ConvertFrom-Json
            $roles.roles.administrator.accounts = @($Principal)
            $rolesJson = $roles | ConvertTo-Json -Depth 20
            [IO.File]::WriteAllText($state.RolesPath, $rolesJson, $utf8WithoutBom)
            $updated += $state

            $marker = [ordered]@{
                schemaVersion = 1
                event = 'initial-administrator-bootstrap'
                completedAt = (Get-Date).ToUniversalTime().ToString('o')
                actualSmbPrincipal = $Principal
            } | ConvertTo-Json -Depth 5
            [IO.File]::WriteAllText($state.MarkerPath, $marker, $utf8WithoutBom)
        }
    }
    catch {
        foreach ($state in $updated) {
            [IO.File]::WriteAllBytes($state.RolesPath, $state.OriginalBytes)
            if (Test-Path -LiteralPath $state.MarkerPath) {
                Remove-Item -LiteralPath $state.MarkerPath -Force
            }
        }
        throw
    }
}

Assert-EmptyTarget -Destination $publicRepository
Assert-EmptyTarget -Destination $backupRepository
Assert-EmptyTarget -Destination $hubWebsite

Initialize-Repository `
    -Source (Join-Path $PackageRoot 'AI-Assets') `
    -Destination $publicRepository

Initialize-Repository `
    -Source (Join-Path $PackageRoot 'AI-Assets-Backup') `
    -Destination $backupRepository

Initialize-Repository `
    -Source (Join-Path $PackageRoot 'AI-Assets-Hub') `
    -Destination $hubWebsite

Initialize-Administrator `
    -Repositories @($backupRepository, $publicRepository) `
    -Principal $initialAdministrator

Write-Host '双 SMB 仓库和静态 Hub 看板初始化完成。'
Write-Host "首位管理员已按实际 SMB 身份设置为：$initialAdministrator"

