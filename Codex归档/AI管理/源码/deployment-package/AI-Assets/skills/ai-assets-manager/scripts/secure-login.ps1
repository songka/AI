[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$shareRoot = '\\10.97.0.210\lfaf_Engineer'
$identityScript = Join-Path $PSScriptRoot 'smb-identity.ps1'
. $identityScript

function Normalize-GetacadAccount {
    param([Parameter(Mandatory)][string]$Account)
    $value = $Account.Trim()
    if (-not $value) { throw '账号不能为空。' }
    if ($value.Contains('\') -or $value.Contains('@')) { return $value }
    return "GETACAD\$value"
}

function Connect-AiAssetsSmb {
    param([Parameter(Mandatory)][string]$Account)
    $connectProcess = Start-Process `
        -FilePath "$env:SystemRoot\System32\net.exe" `
        -ArgumentList @('use', $shareRoot, '*', "/user:$Account", '/persistent:no') `
        -Wait `
        -NoNewWindow `
        -PassThru
    return [int]$connectProcess.ExitCode
}

function Disconnect-AiAssetsServerConnections {
    $netOutput = (& "$env:SystemRoot\System32\net.exe" use 2>&1 | Out-String)
    $pattern = '\\\\10\.97\.0\.210\\[^\s]+'
    $remotePaths = [regex]::Matches($netOutput, $pattern) |
        ForEach-Object { $_.Value.TrimEnd('.') } |
        Sort-Object -Unique

    $remotePaths += @(
        '\\10.97.0.210\lfaf_Engineer',
        '\\10.97.0.210\IPC$'
    )

    foreach ($remotePath in ($remotePaths | Sort-Object -Unique)) {
        # A missing candidate connection is normal. Start-Process lets us inspect
        # the exit code without PowerShell converting net.exe stderr into a
        # terminating NativeCommandError under ErrorActionPreference=Stop.
        $deleteProcess = Start-Process `
            -FilePath "$env:SystemRoot\System32\net.exe" `
            -ArgumentList @('use', $remotePath, '/delete', '/y') `
            -Wait `
            -WindowStyle Hidden `
            -PassThru
        if ($deleteProcess.ExitCode -eq 0) {
            Write-Host "已断开旧连接：$remotePath"
        }
    }
}

try {
    $principal = Get-AiAssetsSmbPrincipal
    if ($principal -and (Test-Path -LiteralPath $shareRoot -ErrorAction SilentlyContinue)) {
        Write-Host "当前 Windows 用户会话已连接 SMB：$principal"
        exit 0
    }
    Write-Host '请只在此独立 Windows 窗口输入 SMB 凭据，不要在 AI 对话中输入。'
    $account = Normalize-GetacadAccount (Read-Host '账号（未写域时自动加 GETACAD）')
    Write-Host "接下来由 Windows net use 安全读取 $account 的密码；输入时不会显示字符。"
    $connectResult = Connect-AiAssetsSmb -Account $account
    if ($connectResult -ne 0) {
        Write-Host ''
        Write-Host '检测到登录失败，常见原因是已用其他账户连接 10.97.0.210。' -ForegroundColor Yellow
        $confirmation = Read-Host '是否只断开指向 10.97.0.210 的现有连接并重试？输入 Y 确认'
        if ($confirmation -notmatch '^(?i)y(es)?$') {
            throw "用户未同意断开冲突连接；SMB 登录停止，退出码为 $connectResult。"
        }
        Disconnect-AiAssetsServerConnections
        Write-Host '目标服务器的旧连接已断开。请重新输入同一账户的密码。'
        $connectResult = Connect-AiAssetsSmb -Account $account
        if ($connectResult -ne 0) {
            throw "清理目标服务器连接后仍无法登录，net use 退出码为 $connectResult。"
        }
    }
    if (-not (Test-Path -LiteralPath $shareRoot -ErrorAction SilentlyContinue)) {
        throw "凭据已接受，但仍无法访问 SMB 共享：$shareRoot"
    }
    $principal = Get-AiAssetsSmbPrincipal
    if (-not $principal) {
        throw '共享可以访问，但 Windows 网络提供程序仍无法确认实际登录账户；拒绝继续特权操作。'
    }
    Write-Host 'SMB 登录成功，连接将保留在当前 Windows 用户会话中。'
    Write-Host "已确认实际 SMB 账户：$principal"
    Write-Host '请回到 AI 对话继续；不要发送账号或密码。'
    Read-Host '按 Enter 关闭窗口'
}
finally {
    Remove-Variable account -Force -ErrorAction SilentlyContinue
    Remove-Variable principal -Force -ErrorAction SilentlyContinue
    Remove-Variable confirmation -Force -ErrorAction SilentlyContinue
    Remove-Variable connectResult -Force -ErrorAction SilentlyContinue
    Remove-Variable connectProcess -Force -ErrorAction SilentlyContinue
    Remove-Variable deleteProcess -Force -ErrorAction SilentlyContinue
}
