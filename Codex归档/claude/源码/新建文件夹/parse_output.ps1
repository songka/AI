# Parse a Claude Code stream-json raw output file and print RESULT / CONTEXT / ERROR
param([string]$Path)

$lastResult = $null
$lastWindow = $null
$errorMsg = $null
$sawJson = $false

foreach ($line in [System.IO.File]::ReadLines($Path)) {
    $line = $line.Trim()
    if (-not $line) { continue }
    if ($line.Substring(0,1) -ne "{") { continue }
    try { $obj = $line | ConvertFrom-Json } catch { continue }
    $sawJson = $true
    if ($obj.type -eq "result") {
        $lastResult = $obj.result
        if ($obj.modelUsage -and $obj.modelUsage.contextWindow) { $lastWindow = $obj.modelUsage.contextWindow }
        if ($obj.api_error_status) { $errorMsg = "api_error: $($obj.api_error_status)" }
        if ($obj.terminal_reason -and $obj.terminal_reason -ne "completed") { $errorMsg = "terminal: $($obj.terminal_reason)" }
    }
    if ($obj.type -eq "error") { $errorMsg = $obj.error }
}

if (-not $sawJson) {
    $tail = (Get-Content $Path -Tail 3) -join " || "
    Write-Output ("NOTJSON_TAIL: " + $tail)
} else {
    if ($lastResult) { Write-Output ("RESULT: " + $lastResult) }
    if ($lastWindow) { Write-Output ("CONTEXT: " + $lastWindow) }
    if (-not $lastResult -and -not $errorMsg) { Write-Output "NO_RESULT" }
}
if ($errorMsg) { Write-Output ("ERROR: " + $errorMsg) }
