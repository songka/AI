param(
    [switch]$PrepareOnly,
    [string]$LocalRoot = ""
)

$ErrorActionPreference = "Stop"

function Show-LauncherError([string]$Message) {
    try {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show(
            $Message,
            "Mechanical Quotation Fast Launcher",
            [System.Windows.MessageBoxButton]::OK,
            [System.Windows.MessageBoxImage]::Error
        ) | Out-Null
    }
    catch {
        Write-Host $Message
    }
}

try {
    $sourceRoot = Split-Path -Parent $PSCommandPath
    $manifest = Join-Path $sourceRoot "package_manifest.json"
    $executableName = "MechanicalQuotation.exe"
    if (-not (Test-Path -LiteralPath $manifest)) {
        throw "The shared package is incomplete: package_manifest.json is missing."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot $executableName))) {
        throw "The shared package is incomplete: $executableName is missing."
    }

    $versionHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifest).Hash.Substring(0, 16)
    if ([string]::IsNullOrWhiteSpace($LocalRoot)) {
        $versionsRoot = Join-Path $env:LOCALAPPDATA "MechanicalQuotation\versions"
    }
    else {
        $versionsRoot = Join-Path $LocalRoot "versions"
    }
    $targetRoot = Join-Path $versionsRoot $versionHash
    $readyMarker = Join-Path $targetRoot ".ready"

    if (-not (Test-Path -LiteralPath $readyMarker)) {
        Write-Host "Preparing a local copy. Please wait..."
        New-Item -ItemType Directory -Force -Path $versionsRoot | Out-Null
        $stagingRoot = Join-Path $versionsRoot (".staging-" + $versionHash + "-" + $PID)
        if (Test-Path -LiteralPath $stagingRoot) {
            Remove-Item -LiteralPath $stagingRoot -Recurse -Force
        }
        New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null

        $excludedDirectories = @(
            (Join-Path $sourceRoot "runtime\cache"),
            (Join-Path $sourceRoot "runtime\reports"),
            (Join-Path $sourceRoot "runtime\tmp"),
            (Join-Path $sourceRoot "exports")
        )
        & robocopy.exe $sourceRoot $stagingRoot /E /COPY:DAT /DCOPY:DAT /R:2 /W:1 /NP /NFL /NDL /NJH /NJS /XD $excludedDirectories
        if ($LASTEXITCODE -gt 7) {
            throw "Copying from the shared folder failed. Robocopy exit code: $LASTEXITCODE"
        }
        foreach ($relative in @("runtime\cache", "runtime\reports", "runtime\tmp", "exports")) {
            New-Item -ItemType Directory -Force -Path (Join-Path $stagingRoot $relative) | Out-Null
        }
        Set-Content -LiteralPath (Join-Path $stagingRoot ".ready") -Value $versionHash -Encoding ASCII

        if (Test-Path -LiteralPath $targetRoot) {
            Remove-Item -LiteralPath $targetRoot -Recurse -Force
        }
        Move-Item -LiteralPath $stagingRoot -Destination $targetRoot
    }

    $localExecutable = Join-Path $targetRoot $executableName
    if (-not (Test-Path -LiteralPath $localExecutable)) {
        throw "The local application cache is incomplete. Remove this folder and retry:`n$targetRoot"
    }
    if ($PrepareOnly) {
        Write-Output $targetRoot
    }
    else {
        Start-Process -FilePath $localExecutable -WorkingDirectory $targetRoot
    }
}
catch {
    Show-LauncherError $_.Exception.Message
    exit 1
}
