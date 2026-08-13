[CmdletBinding()]
param(
    [switch]$IncludeSkill,
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RepositoryRoot = Split-Path -Parent $ProjectRoot
$SkillRoot = Join-Path $RepositoryRoot ".agents\skills\manage-gomoku"

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "validate-project.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "Release blocked: project validation failed."
}

$Contract = Get-Content -LiteralPath (Join-Path $ProjectRoot "project-contract.json") -Raw |
    ConvertFrom-Json
if (-not $OutputPath) {
    $PackageDirectory = Join-Path $ProjectRoot "packages"
    New-Item -ItemType Directory -Path $PackageDirectory -Force | Out-Null
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $PackageDirectory "gomoku-$($Contract.version)-$Timestamp.zip"
}
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $OutputPath) {
    throw "Release blocked: output already exists and will not be overwritten: $OutputPath"
}
$OutputDirectory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}

$ForbiddenDirectoryNames = @(
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", "packages", "logs", "cache"
)
$ForbiddenSuffixes = @(".key", ".pem", ".pfx", ".p12", ".log", ".pyc")
$ForbiddenNameParts = @(".env", "credentials", "password", "passwd", "secret", "token")

function Get-CompatibleRelativePath {
    param(
        [string]$Root,
        [string]$Path
    )
    $RootPath = [System.IO.Path]::GetFullPath($Root).TrimEnd("\") + "\"
    $RootUri = New-Object System.Uri($RootPath)
    $PathUri = New-Object System.Uri([System.IO.Path]::GetFullPath($Path))
    return [System.Uri]::UnescapeDataString(
        $RootUri.MakeRelativeUri($PathUri).ToString()
    ).Replace("/", "\")
}

function Get-SafeFiles {
    param([string]$Root)
    Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object {
        $File = $_
        $Relative = Get-CompatibleRelativePath $Root $File.FullName
        $Parts = $Relative -split "[\\/]"
        $LowerName = $File.Name.ToLowerInvariant()
        -not ($Parts | Where-Object { $ForbiddenDirectoryNames -contains $_ }) -and
        -not ($ForbiddenSuffixes -contains $File.Extension.ToLowerInvariant()) -and
        -not ($ForbiddenNameParts | Where-Object { $LowerName.Contains($_) })
    }
}

$Entries = @()
foreach ($File in Get-SafeFiles $ProjectRoot) {
    $Relative = Get-CompatibleRelativePath $ProjectRoot $File.FullName
    $Entries += [PSCustomObject]@{ File = $File; Entry = "gomoku/$($Relative.Replace('\', '/'))" }
}
if ($IncludeSkill) {
    foreach ($File in Get-SafeFiles $SkillRoot) {
        $Relative = Get-CompatibleRelativePath $SkillRoot $File.FullName
        $Entries += [PSCustomObject]@{
            File = $File
            Entry = ".agents/skills/manage-gomoku/$($Relative.Replace('\', '/'))"
        }
    }
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$PartialPath = "$OutputPath.partial-$([Guid]::NewGuid().ToString('N'))"
$Archive = [System.IO.Compression.ZipFile]::Open(
    $PartialPath,
    [System.IO.Compression.ZipArchiveMode]::Create
)
try {
    foreach ($Item in $Entries) {
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $Archive,
            $Item.File.FullName,
            $Item.Entry,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
}
finally {
    $Archive.Dispose()
}
Move-Item -LiteralPath $PartialPath -Destination $OutputPath
Write-Host "Release created: $OutputPath"
Write-Host "Skill included: $($IncludeSkill.IsPresent)"
