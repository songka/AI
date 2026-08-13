param([string]$Dir = ".\cap_test_results")
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$files = Get-ChildItem "$Dir\*.vision.raw" | Sort-Object Name
foreach ($f in $files) {
    $model = $f.BaseName -replace "\.vision$",""
    $lastResult = ""
    foreach ($line in [System.IO.File]::ReadLines($f.FullName)) {
        if (-not $line.Trim()) { continue }
        if ($line.Trim().Substring(0,1) -ne "{") { continue }
        try { $obj = $line | ConvertFrom-Json } catch { continue }
        if ($obj.type -eq "result" -and $obj.result) { $lastResult = $obj.result }
    }
    Write-Output "### $model"
    Write-Output $lastResult
    Write-Output ""
}
