param(
    [string]$ArchivePath = '',
    [switch]$ExpectSkill,
    [switch]$SkipCodeChecks
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$skillRoot = Join-Path $repoRoot '.agents\skills\manage-feishu-signing'
$python = (Get-Command python -ErrorAction Stop).Source

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (exit $LASTEXITCODE): $FilePath $($Arguments -join ' ')"
    }
}

function Test-ReleaseArchive {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [bool]$ShouldContainSkill
    )

    $resolved = (Resolve-Path -LiteralPath $Path).Path
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($resolved)
    try {
        $names = @($archive.Entries | ForEach-Object { $_.FullName.Replace('\', '/') })
        if ($names.Count -eq 0) {
            throw 'Release archive is empty.'
        }
        if ($names -notcontains 'auto-sign/callback_server.py') {
            throw 'Release archive is missing auto-sign/callback_server.py.'
        }
        if ($names -notcontains 'release-change-record.json') {
            throw 'Release archive is missing release-change-record.json.'
        }
        foreach ($runtimeScript in @('run-server.sh', 'run-scheduler.sh')) {
            if ($names -notcontains $runtimeScript) {
                throw "Release archive is missing $runtimeScript."
            }
        }

        $skillEntry = '.agents/skills/manage-feishu-signing/SKILL.md'
        if ($ShouldContainSkill -and $names -notcontains $skillEntry) {
            throw 'Maintenance archive is missing the project Skill.'
        }
        if (-not $ShouldContainSkill -and $names -contains $skillEntry) {
            throw 'Runtime archive must not contain the project Skill; use -IncludeSkill explicitly.'
        }
        if ($ShouldContainSkill) {
            foreach ($requiredMaintenanceEntry in @(
                'AGENTS.md',
                'build-release.ps1',
                'scripts/validate-project.ps1',
                'scripts/validate-skill.py'
            )) {
                if ($names -notcontains $requiredMaintenanceEntry) {
                    throw "Maintenance archive is missing $requiredMaintenanceEntry."
                }
            }
        }
        else {
            foreach ($localOnlyEntry in @('AGENTS.md', 'build-release.ps1', 'scripts/validate-project.ps1')) {
                if ($names -contains $localOnlyEntry) {
                    throw "Runtime archive contains local maintenance file: $localOnlyEntry"
                }
            }
        }

        $forbidden = @(
            '(^|/)users/',
            '(^|/)data/',
            '(^|/)auth\.json$',
            '(^|/)auth\.enc$',
            '(^|/)secrets\.enc$',
            '(^|/)qh\.env$',
            '(^|/).*\.qhb$',
            '(^|/)qh-master\.key$',
            '(^|/)feishu\.json$',
            '(^|/)config\.json$',
            '(^|/)rules\.json$',
            '(^|/)groups\.json$',
            '(^|/)sign_events\.json$',
            '(^|/)sign_records\.xlsx$',
            '(^|/)__pycache__/',
            '\.py[co]$',
            '\.log$'
        )
        foreach ($name in $names) {
            foreach ($pattern in $forbidden) {
                if ($name -match $pattern) {
                    throw "Release archive contains a forbidden file: $name"
                }
            }
        }

        $callbackPath = Join-Path $repoRoot 'deploy\auto-sign\callback_server.py'
        $localCallback = Get-Content -LiteralPath $callbackPath -Raw -Encoding UTF8
        $versionMatch = [regex]::Match($localCallback, 'APP_VERSION\s*=\s*"([^"]+)"')
        if (-not $versionMatch.Success) {
            throw 'Unable to read local APP_VERSION.'
        }
        $callbackEntry = $archive.GetEntry('auto-sign/callback_server.py')
        $reader = [System.IO.StreamReader]::new($callbackEntry.Open(), [System.Text.Encoding]::UTF8)
        try {
            $archivedCallback = $reader.ReadToEnd()
        }
        finally {
            $reader.Dispose()
        }
        if ($archivedCallback -notmatch [regex]::Escape($versionMatch.Groups[1].Value)) {
            throw "Archived callback version does not match $($versionMatch.Groups[1].Value)."
        }
    }
    finally {
        $archive.Dispose()
    }
    Write-Output "PASS: release archive verified: $resolved"
}

Push-Location $repoRoot
try {
    if (-not $SkipCodeChecks) {
        Invoke-Checked $python '-m' 'compileall' '-q' 'deploy\auto-sign'
        Invoke-Checked $python 'deploy\auto-sign\tests\test_regressions.py'
        Invoke-Checked $python 'deploy\auto-sign\tests\test_skill_contract.py'
        Invoke-Checked $python '.agents\skills\manage-feishu-signing\scripts\smoke-test.py'
        Invoke-Checked $python 'scripts\validate-skill.py' $skillRoot

        $officialValidator = Join-Path $env:USERPROFILE '.codex\skills\.system\skill-creator\scripts\quick_validate.py'
        if (Test-Path -LiteralPath $officialValidator) {
            $yamlAvailable = & $python -c "import importlib.util; print('yes' if importlib.util.find_spec('yaml') else 'no')"
            if ($LASTEXITCODE -ne 0) {
                throw 'Unable to inspect the PyYAML dependency.'
            }
            if ($yamlAvailable.Trim() -eq 'yes') {
                Invoke-Checked $python $officialValidator $skillRoot
            }
            else {
                Write-Warning 'Official quick_validate.py requires PyYAML; the dependency-free project validator passed.'
            }
        }
        Write-Output 'PASS: code, regression, Skill contract and smoke validation'
    }

    if ($ArchivePath) {
        Test-ReleaseArchive -Path $ArchivePath -ShouldContainSkill ([bool]$ExpectSkill)
    }
}
finally {
    Pop-Location
}
