$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$source = Join-Path $scriptDir "BomCheckNetworkLauncher.cs"
$outDir = Join-Path $projectRoot "dist\network_launcher"
$singleExeDir = Join-Path $projectRoot "dist\single_exe"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$webLauncher = Join-Path $outDir "bomcheck_web_launcher.exe"
$appLauncher = Join-Path $outDir "bomcheck_app_launcher.exe"

if (Test-Path $webLauncher) {
    Remove-Item -LiteralPath $webLauncher -Force
}
if (Test-Path $appLauncher) {
    Remove-Item -LiteralPath $appLauncher -Force
}

Add-Type `
    -Path $source `
    -OutputAssembly $webLauncher `
    -OutputType WindowsApplication `
    -ReferencedAssemblies "System.Windows.Forms.dll","System.dll","System.Core.dll"

Copy-Item -LiteralPath $webLauncher -Destination $appLauncher -Force

if (Test-Path $singleExeDir) {
    Copy-Item -LiteralPath $webLauncher -Destination (Join-Path $singleExeDir "bomcheck_web_launcher.exe") -Force
    Copy-Item -LiteralPath $appLauncher -Destination (Join-Path $singleExeDir "bomcheck_app_launcher.exe") -Force
}

Get-ChildItem -LiteralPath $outDir -Filter "*_launcher.exe" |
    Select-Object Name,Length,LastWriteTime,FullName
