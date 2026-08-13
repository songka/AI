[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArguments
)

$ErrorActionPreference = 'Stop'
$shareRoot = '\\10.97.0.210\lfaf_Engineer'
$publicRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets'
$backupRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets-Backup'
$client = Join-Path $PSScriptRoot '..\client\asset_hub.py'
$temporaryDrive = $null

function Get-AiAssetsSmbUser {
    $connection = Get-SmbConnection -ErrorAction SilentlyContinue |
        Where-Object {
            $_.ServerName -ieq '10.97.0.210' -and
            $_.ShareName -ieq 'lfaf_Engineer'
        } |
        Select-Object -First 1

    if ($connection) {
        return $connection.UserName
    }
    return $null
}

function Normalize-GetacadAccount {
    param([Parameter(Mandatory)][string]$Account)

    $trimmed = $Account.Trim()
    if (-not $trimmed) {
        throw '账号不能为空。'
    }
    if ($trimmed.IndexOf([char]92) -ge 0 -or $trimmed.Contains('@')) {
        return $trimmed
    }
    return "GETACAD\$trimmed"
}

try {
    $accessible = Test-Path -LiteralPath $publicRepository
    $actor = Get-AiAssetsSmbUser

    if (-not $accessible) {
        Write-Host '当前 Windows 会话无法访问 AI Assets SMB，需要登录。'
        $inputAccount = Read-Host '请输入账号（未填写域时自动使用 GETACAD）'
        $normalizedAccount = Normalize-GetacadAccount -Account $inputAccount
        $credential = Get-Credential `
            -UserName $normalizedAccount `
            -Message "请输入 $normalizedAccount 的 SMB 密码"

        if (-not $credential) {
            throw '用户取消了 SMB 登录。'
        }

        $driveName = "AIA$PID"
        $temporaryDrive = New-PSDrive `
            -Name $driveName `
            -PSProvider FileSystem `
            -Root $shareRoot `
            -Credential $credential `
            -Scope Script

        if (-not (Test-Path -LiteralPath $publicRepository)) {
            throw "凭据已提交，但仍无法访问：$publicRepository"
        }
        $actor = Get-AiAssetsSmbUser
        if (-not $actor) {
            $actor = $normalizedAccount
        }
    }

    if (-not $actor) {
        $actor = (& whoami).Trim()
    }

    $env:AI_ASSET_ACTOR = $actor
    $env:AI_ASSET_REPO = $publicRepository
    $env:AI_ASSET_BACKUP_REPO = $backupRepository

    Write-Host 'SMB 身份验证成功，已按实际连接账户匹配角色。'
    & python $client @CliArguments
    exit $LASTEXITCODE
}
catch {
    Write-Error $_
    Write-Host '如果 Windows 提示同一服务器存在其他账号连接，请先关闭相关资源管理器窗口，再执行：'
    Write-Host 'net use \\10.97.0.210\lfaf_Engineer /delete'
    exit 2
}
finally {
    if ($temporaryDrive) {
        Remove-PSDrive -Name $temporaryDrive.Name -Force -ErrorAction SilentlyContinue
    }
    if ($credential -and $credential.Password) {
        $credential.Password.Dispose()
    }
    Remove-Variable credential -Force -ErrorAction SilentlyContinue
}
