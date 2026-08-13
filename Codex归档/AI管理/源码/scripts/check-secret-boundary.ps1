[CmdletBinding()]
param(
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
if (-not $ProjectRoot) {
    $scriptDirectory = Split-Path $MyInvocation.MyCommand.Path -Parent
    $ProjectRoot = Split-Path $scriptDirectory -Parent
}
$self = $MyInvocation.MyCommand.Path
$sourceFiles = @()
foreach ($relativeRoot in @('scripts', 'tools', 'skills')) {
    $scanRoot = Join-Path $ProjectRoot $relativeRoot
    if (Test-Path -LiteralPath $scanRoot) {
        $sourceFiles += Get-ChildItem -LiteralPath $scanRoot -Recurse -File |
            Where-Object { $_.Extension -in '.ps1', '.py' -and $_.FullName -ne $self }
    }
}

$forbidden = @(
    @{ Name = '保存 runas 密码'; Pattern = '(?i)/savecred' },
    @{ Name = 'cmdkey 明文密码'; Pattern = '(?i)cmdkey.+/pass' },
    @{ Name = 'SecureString 转明文'; Pattern = '(?i)GetNetworkCredential\s*\(\s*\)\s*\.Password' },
    @{ Name = '明文 SecureString'; Pattern = '(?i)ConvertTo-SecureString.+-AsPlainText' },
    @{ Name = '密码环境变量'; Pattern = '(?i)\$env:[A-Z0-9_]*(PASSWORD|PASSWD|PWD)' },
    @{ Name = '凭据序列化'; Pattern = '(?i)ConvertFrom-SecureString' }
)

$violations = @()
foreach ($file in $sourceFiles) {
    $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
    foreach ($rule in $forbidden) {
        if ($content -match $rule.Pattern) {
            $violations += [PSCustomObject]@{
                File = $file.FullName
                Rule = $rule.Name
            }
        }
    }
}

$loginScript = Join-Path $ProjectRoot 'scripts\ai-assets-login.ps1'
$loginContent = Get-Content -LiteralPath $loginScript -Raw -Encoding UTF8
if ($loginContent -notmatch 'Get-Credential') {
    $violations += [PSCustomObject]@{
        File = $loginScript
        Rule = '缺少 Windows 安全凭据提示'
    }
}
if ($loginContent -match '(?i)New-PSDrive[\s\S]{0,400}-Persist') {
    $violations += [PSCustomObject]@{
        File = $loginScript
        Rule = 'SMB 凭据映射不应持久化'
    }
}

$secureLauncher = Join-Path $ProjectRoot 'scripts\ai-assets-secure-launch.ps1'
if (-not (Test-Path -LiteralPath $secureLauncher)) {
    $violations += [PSCustomObject]@{
        File = $secureLauncher
        Rule = '缺少 AI 对话专用的独立安全窗口入口'
    }
}

if ($violations.Count -gt 0) {
    $violations | Format-Table -AutoSize
    throw '凭据边界检查失败。'
}

Write-Host '凭据边界检查通过：未发现明文密码、密码持久化或密码环境变量。'
