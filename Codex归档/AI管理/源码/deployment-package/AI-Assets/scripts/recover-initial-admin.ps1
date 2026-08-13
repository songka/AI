[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ExpectedPrincipal,

    [Parameter(Mandatory)]
    [string]$Confirmation
)

$ErrorActionPreference = 'Stop'
$publicRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets'
$backupRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets-Backup'
$identityScript = Join-Path (Split-Path $PSScriptRoot -Parent) 'skills\ai-assets-manager\scripts\smb-identity.ps1'
$legacyAdministrators = @('GETACAD\lfaf-test', 'lfaf-test\lfaf-test')

function Test-SameAccountSet {
    param([string[]]$Left, [string[]]$Right)
    $leftNormalized = @($Left | ForEach-Object { $_.Trim().ToLowerInvariant() } | Sort-Object -Unique)
    $rightNormalized = @($Right | ForEach-Object { $_.Trim().ToLowerInvariant() } | Sort-Object -Unique)
    return (
        $leftNormalized.Count -eq $rightNormalized.Count -and
        (Compare-Object -ReferenceObject $leftNormalized -DifferenceObject $rightNormalized).Count -eq 0
    )
}

function Write-JsonAtomically {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )
    $temporary = "$Path.recovery-$PID.tmp"
    $json = $Value | ConvertTo-Json -Depth 20
    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    try {
        [IO.File]::WriteAllText($temporary, $json, $utf8WithoutBom)
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

if (-not (Test-Path -LiteralPath $identityScript)) {
    throw "SMB 身份脚本不存在：$identityScript"
}
. $identityScript

$actualPrincipal = Get-AiAssetsSmbPrincipal
if (-not $actualPrincipal) {
    throw '无法从 Windows SMB 会话确认实际登录账户，拒绝恢复。'
}
if ($actualPrincipal -ine $ExpectedPrincipal) {
    throw "当前实际 SMB 账户是 $actualPrincipal，不是待恢复账户 $ExpectedPrincipal。"
}
$requiredConfirmation = "RECOVER $ExpectedPrincipal"
if ($Confirmation -cne $requiredConfirmation) {
    throw "恢复确认文字不匹配；必须精确为：$requiredConfirmation"
}

$repositories = @($backupRepository, $publicRepository)
$states = @()
foreach ($repository in $repositories) {
    $rolesPath = Join-Path $repository 'config\roles.json'
    $markerPath = Join-Path $repository 'config\bootstrap-admin.completed.json'
    if (-not (Test-Path -LiteralPath $rolesPath)) {
        throw "角色配置不存在：$rolesPath"
    }
    if (Test-Path -LiteralPath $markerPath) {
        throw "首次管理员恢复已执行过，拒绝重复运行：$markerPath"
    }
    $roles = Get-Content -LiteralPath $rolesPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $accounts = @($roles.roles.administrator.accounts)
    if (-not (Test-SameAccountSet -Left $accounts -Right $legacyAdministrators)) {
        throw "管理员列表已不是已知的首次部署占位状态，拒绝自动恢复：$rolesPath"
    }
    $states += [PSCustomObject]@{
        Repository = $repository
        RolesPath = $rolesPath
        MarkerPath = $markerPath
        Roles = $roles
        OriginalBytes = [IO.File]::ReadAllBytes($rolesPath)
        OriginalSha256 = (Get-FileHash -LiteralPath $rolesPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$recoveryId = "bootstrap-admin-$stamp"
$completed = @()
try {
    foreach ($state in $states) {
        $recoveryFolder = Join-Path $state.Repository "recovery\$recoveryId"
        New-Item -ItemType Directory -Path $recoveryFolder -Force | Out-Null
        $backupPath = Join-Path $recoveryFolder 'roles.before.json'
        [IO.File]::WriteAllBytes($backupPath, $state.OriginalBytes)
        $completed += $state

        $state.Roles.roles.administrator.accounts = @($ExpectedPrincipal)
        Write-JsonAtomically -Path $state.RolesPath -Value $state.Roles

        $marker = [ordered]@{
            schemaVersion = 1
            recoveryId = $recoveryId
            completedAt = (Get-Date).ToUniversalTime().ToString('o')
            actualSmbPrincipal = $actualPrincipal
            restoredAdministrator = $ExpectedPrincipal
            replacedAccounts = $legacyAdministrators
            originalRolesSha256 = $state.OriginalSha256
            backupPath = $backupPath
        }
        Write-JsonAtomically -Path $state.MarkerPath -Value $marker
    }

    $auditFolder = Join-Path $backupRepository 'audit'
    New-Item -ItemType Directory -Path $auditFolder -Force | Out-Null
    $auditPath = Join-Path $auditFolder "$recoveryId.json"
    $audit = [ordered]@{
        schemaVersion = 1
        event = 'initial-administrator-recovery'
        recoveryId = $recoveryId
        completedAt = (Get-Date).ToUniversalTime().ToString('o')
        actor = $actualPrincipal
        restoredAdministrator = $ExpectedPrincipal
        repositories = @($states | ForEach-Object {
            [ordered]@{
                path = $_.Repository
                originalRolesSha256 = $_.OriginalSha256
            }
        })
    }
    Write-JsonAtomically -Path $auditPath -Value $audit
}
catch {
    foreach ($state in $completed) {
        [IO.File]::WriteAllBytes($state.RolesPath, $state.OriginalBytes)
        if (Test-Path -LiteralPath $state.MarkerPath) {
            Remove-Item -LiteralPath $state.MarkerPath -Force
        }
    }
    throw
}

foreach ($state in $states) {
    $verified = Get-Content -LiteralPath $state.RolesPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not (Test-SameAccountSet -Left @($verified.roles.administrator.accounts) -Right @($ExpectedPrincipal))) {
        throw "恢复后验证失败：$($state.RolesPath)"
    }
}

[PSCustomObject]@{
    State = 'recovered'
    RecoveryId = $recoveryId
    Principal = $actualPrincipal
    Role = 'administrator'
    Audit = (Join-Path $backupRepository "audit\$recoveryId.json")
    Repositories = $repositories
} | ConvertTo-Json -Depth 4


