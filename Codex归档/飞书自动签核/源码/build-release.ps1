param(
    [string]$Output = (Join-Path $PSScriptRoot 'qh-deploy-fixed.zip'),
    [switch]$IncludeSkill,
    [Parameter(Mandatory = $true)][string]$ChangeRecord
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$deployRoot = (Resolve-Path -LiteralPath (Join-Path $repoRoot 'deploy')).Path
$agentsRoot = (Resolve-Path -LiteralPath (Join-Path $repoRoot '.agents')).Path
$scriptsRoot = (Resolve-Path -LiteralPath (Join-Path $repoRoot 'scripts')).Path
$outputPath = [System.IO.Path]::GetFullPath($Output)
$validationScript = Join-Path $repoRoot 'scripts\validate-project.ps1'
$changeValidator = Join-Path $repoRoot 'scripts\validate-change.py'
$python = (Get-Command python -ErrorAction Stop).Source
$callbackSource = Get-Content -LiteralPath (Join-Path $deployRoot 'auto-sign\callback_server.py') -Raw -Encoding UTF8
$versionMatch = [regex]::Match($callbackSource, 'APP_VERSION\s*=\s*"([^"]+)"')
if (-not $versionMatch.Success) {
    throw 'Unable to read APP_VERSION.'
}
$changeRecordPath = (Resolve-Path -LiteralPath $ChangeRecord).Path

if (-not $outputPath.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The release archive must stay inside the repository.'
}

& $validationScript
& $python $changeValidator $changeRecordPath --version $versionMatch.Groups[1].Value
if ($LASTEXITCODE -ne 0) {
    throw 'Production change approval validation failed.'
}

$excludedDeployFiles = @(
    'config.json',
    'feishu.json',
    'secrets.enc',
    'auth.enc',
    'rules.json',
    'groups.json',
    'whitelist.txt',
    'name_blacklist.txt',
    'content_whitelist.txt',
    'content_whitelist.zip',
    'auto-sign/whitelist.txt',
    'auto-sign/name_blacklist.txt',
    'auto-sign/content_whitelist.txt',
    'auto-sign/description_new_list.txt',
    'auto-sign/groups.json'
)
$forbiddenRuntimePatterns = @(
    '(^|/)users/',
    '(^|/)data/',
    '(^|/)auth\.json$',
    '(^|/)auth\.enc$',
    '(^|/)secrets\.enc$',
    '(^|/)qh\.env$',
    '(^|/).*\.qhb$',
    '(^|/)qh-master\.key$',
    '(^|/)sign_events\.json$',
    '(^|/)sign_records\.xlsx$',
    '(^|/).*\.log$'
)

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$stream = [System.IO.File]::Open($outputPath, [System.IO.FileMode]::Create)
$archive = [System.IO.Compression.ZipArchive]::new(
    $stream,
    [System.IO.Compression.ZipArchiveMode]::Create,
    $false
)

try {
    $files = Get-ChildItem -LiteralPath $deployRoot -Recurse -File | Where-Object {
        $relative = $_.FullName.Substring($deployRoot.Length + 1).Replace('\', '/')
        ($excludedDeployFiles -notcontains $relative) -and
        ($relative -notmatch '(^|/)__pycache__/') -and
        ($relative -notmatch '\.py[co]$') -and
        -not ($forbiddenRuntimePatterns | Where-Object { $relative -match $_ })
    }
    foreach ($file in $files) {
        $entryName = $file.FullName.Substring($deployRoot.Length + 1).Replace('\', '/')
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive, $file.FullName, $entryName,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $archive, $changeRecordPath, 'release-change-record.json',
        [System.IO.Compression.CompressionLevel]::Optimal
    ) | Out-Null

    if ($IncludeSkill) {
        Get-ChildItem -LiteralPath $agentsRoot -Recurse -File | ForEach-Object {
            $entryName = $_.FullName.Substring($repoRoot.Length + 1).Replace('\', '/')
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive, $_.FullName, $entryName,
                [System.IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
        }

        Get-ChildItem -LiteralPath $scriptsRoot -Recurse -File | ForEach-Object {
            $entryName = $_.FullName.Substring($repoRoot.Length + 1).Replace('\', '/')
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive, $_.FullName, $entryName,
                [System.IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
        }

        foreach ($projectFile in @('AGENTS.md', 'build-release.ps1')) {
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive, (Join-Path $repoRoot $projectFile), $projectFile,
                [System.IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
        }
    }
}
finally {
    $archive.Dispose()
    $stream.Dispose()
}

if ($IncludeSkill) {
    & $validationScript -ArchivePath $outputPath -ExpectSkill -SkipCodeChecks
}
else {
    & $validationScript -ArchivePath $outputPath -SkipCodeChecks
}

Write-Output "Release archive created: $outputPath"
