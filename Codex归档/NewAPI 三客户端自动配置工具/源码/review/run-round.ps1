param(
    [Parameter(Mandatory = $true)][int]$Round,
    [string]$ProjectRoot = "D:\codex\NewAPI 三客户端自动配置工具"
)

$ErrorActionPreference = "Stop"
$codexCli = "C:\Users\lfaf-120-2\AppData\Local\OpenAI\Codex\bin\8e8bf206e63ac436\codex.exe"
$promptsDir = Join-Path $ProjectRoot "review\prompts"
$roundDir = Join-Path $ProjectRoot ("review\round-{0:D2}" -f $Round)

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
        "-C", $ProjectRoot,
        "-s", "read-only",
        "--skip-git-repo-check",
        "--ephemeral",
        "-o", $outFile,
        $prompt
    )
    & $codexCli @args 2>&1 | Out-Host
    $exit = $LASTEXITCODE
    $summary += "[Round $Round] $agentName => exit $exit -> $outFile"
    Write-Host "[Round $Round] $agentName finished (exit $exit)"
}

$summary | Set-Content -Encoding UTF8 (Join-Path $roundDir "_summary.txt")
Write-Host "Round $Round complete. Outputs in $roundDir"
