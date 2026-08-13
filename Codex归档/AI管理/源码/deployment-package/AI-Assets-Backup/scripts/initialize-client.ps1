[CmdletBinding()]
param(
    [string]$Destination = "$env:LOCALAPPDATA\Programs\AIAssetHub"
)

$publicRepository = '\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\data\AI-Assets'
$source = Join-Path $publicRepository 'client'

if (-not (Test-Path -LiteralPath $source)) {
    throw "公共槽客户端目录不存在：$source"
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
Copy-Item -LiteralPath (Join-Path $source 'asset_hub.py') -Destination $Destination -Force
Copy-Item -LiteralPath (Join-Path $source 'ai_assets.py') -Destination $Destination -Force

Write-Host "客户端已安装到：$Destination"
Write-Warning '正式生产前必须补充客户端签名验证，并通过受控软件分发替代此初始化脚本。'
