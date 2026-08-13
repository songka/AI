[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RepositoryRoot = Split-Path -Parent $ProjectRoot
$SkillRoot = Join-Path $RepositoryRoot ".agents\skills\manage-gomoku"
$PreviousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = Join-Path $ProjectRoot "src"

function Invoke-Gate {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )
    Write-Host "`n== $Name =="
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Validation gate failed: $Name (exit $LASTEXITCODE)"
    }
}

try {
    Push-Location $ProjectRoot
    Invoke-Gate "Compile/static check" { python -m compileall -q src tests scripts }
    Invoke-Gate "Unit tests" {
        python -m unittest discover -s tests -p "test_unit_*.py" -v
    }
    Invoke-Gate "Regression tests" {
        python -m unittest discover -s tests -p "test_regression_*.py" -v
    }
    Invoke-Gate "Business and safety smoke test" { python scripts/smoke-test.py }
    Invoke-Gate "Skill smoke test" { python scripts/skill-smoke-test.py }
    Invoke-Gate "quick_validate.py" { python scripts/quick_validate.py $SkillRoot }
    Invoke-Gate "Code-Skill contract test" { python scripts/contract-test.py }
    Invoke-Gate "Sensitive file check" {
        python scripts/check-sensitive-files.py $ProjectRoot $SkillRoot
    }
    Write-Host "`nALL VALIDATION GATES PASSED"
}
finally {
    Pop-Location
    $env:PYTHONPATH = $PreviousPythonPath
}
