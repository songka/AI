param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$sw = $null
$model = $null
try {
    $sw = New-Object -ComObject SldWorks.Application
    $sw.Visible = $false
    $extension = [IO.Path]::GetExtension($SourcePath).ToLowerInvariant()
    $docType = if ($extension -eq '.sldprt') { 1 } elseif ($extension -eq '.slddrw') { 3 } else { throw '不支持的 SOLIDWORKS 文件类型' }
    $errors = 0
    $warnings = 0
    $model = $sw.OpenDoc6($SourcePath, $docType, 1, '', [ref]$errors, [ref]$warnings)
    if ($null -eq $model) { throw "SOLIDWORKS 打开文件失败，错误代码：$errors" }
    $ok = $model.SaveAs3($OutputPath, 0, 1)
    if (-not $ok -or -not (Test-Path -LiteralPath $OutputPath)) { throw 'SOLIDWORKS 无法将该文件导出为 DXF' }
    exit 0
} finally {
    if ($null -ne $model) { $sw.CloseDoc($model.GetTitle()) }
    if ($null -ne $sw) { $sw.ExitApp() }
}
