param(
    [Parameter(Mandatory = $true)][int]$Round
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$codexCli = "C:\Users\lfaf-120-2\AppData\Local\OpenAI\Codex\bin\8e8bf206e63ac436\codex.exe"
$promptsDir = Join-Path $scriptDir "prompts"
$roundDir = Join-Path $scriptDir ("round-{0:D2}" -f $Round)

if (-not (Test-Path $promptsDir)) {
    throw "prompts dir not found: $promptsDir"
}

New-Item -ItemType Directory -Force -Path $roundDir | Out-Null

$summary = @()
foreach ($promptFile in (Get-ChildItem -Path $promptsDir -Filter *.md | Sort-Object Name)) {
    $agentName = [System.IO.Path]::GetFileNameWithoutExtension($promptFile.Name)
    $outFile = Join-Path $roundDir ($agentName + ".md")
    Write-Host "[Round $Round] Running agent: $agentName"
    $prompt = Get-Content -Raw -LiteralPath $promptFile.FullName
    $args = @(
        "exec",
        "-C", $projectRoot,
        "-s", "read-only",
        "--skip-git-repo-check",
        "--ephemeral",
        "-o", $outFile,
        "-"
    )
    $prompt | & $codexCli @args 2>&1 | Out-Host
    $exit = $LASTEXITCODE
    $summary += "[Round $Round] $agentName => exit $exit -> $outFile"
    Write-Host "[Round $Round] $agentName finished (exit $exit)"
}

$summary | Set-Content -Encoding UTF8 (Join-Path $roundDir "_summary.txt")
Write-Host "Round $Round complete. Outputs in $roundDir"
