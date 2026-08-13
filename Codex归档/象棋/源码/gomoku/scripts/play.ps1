[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PreviousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = Join-Path $ProjectRoot "src"
try {
    Push-Location $ProjectRoot
    python -m gomoku
    exit $LASTEXITCODE
}
finally {
    Pop-Location
    $env:PYTHONPATH = $PreviousPythonPath
}

