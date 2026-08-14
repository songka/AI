$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = 'C:\Users\lfaf-120-2\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$archiveRepo = Join-Path $scriptRoot 'codex-archive-repo\codex-archive-stable'
$syncScript = Join-Path $scriptRoot 'codex_archive_sync.py'

if (-not (Test-Path -LiteralPath $pythonExe)) { throw "Python not found: $pythonExe" }
if (-not (Test-Path -LiteralPath (Join-Path $archiveRepo '.git'))) { throw "Archive repo not found: $archiveRepo" }
if (-not (Test-Path -LiteralPath $syncScript)) { throw "Sync script not found: $syncScript" }

# ---------------------------------------------------------------------------
# Proxy detection: direct HTTPS to github.com:443 is frequently blocked on this
# network, while a local HTTP proxy (system proxy / common proxy ports) can
# reach GitHub.  If a working proxy is found, export it so git (spawned by the
# Python archiver and by this script) uses it.
# ---------------------------------------------------------------------------
function Test-HttpsProxy([string]$proxy) {
    if (-not $proxy) { return $false }
    try {
        $code = & curl.exe -s -o NUL -w '%{http_code}' -m 8 -x $proxy https://github.com 2>$null
        return ($code -eq '200')
    } catch {
        return $false
    }
}

$candidates = New-Object System.Collections.Generic.List[string]
try {
    $inet = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction SilentlyContinue
    if ($inet.ProxyEnable -and $inet.ProxyServer) { $candidates.Add($inet.ProxyServer) }
} catch { }
foreach ($port in 10808, 10809, 7890, 7897, 1080, 8080, 8888) {
    $candidates.Add("127.0.0.1:$port")
}

$proxy = $null
foreach ($candidate in ($candidates | Select-Object -Unique)) {
    if ($candidate -notmatch '^https?://') { $candidate = "http://$candidate" }
    if (Test-HttpsProxy $candidate) { $proxy = $candidate; break }
}

if ($proxy) {
    Write-Host "[sync] using proxy: $proxy"
    $env:http_proxy  = $proxy
    $env:https_proxy = $proxy
    $env:all_proxy   = $proxy
} else {
    Write-Host '[sync] no working proxy found; trying direct connection'
}

# Force UTF-8 inside Python so git output (UTF-8) never trips GBK decoding.
$env:PYTHONUTF8 = '1'

# ---------------------------------------------------------------------------
# 1) Archive and commit locally (no push yet).  Archiving is incremental and
#    only commits when something changed.
# ---------------------------------------------------------------------------
& $pythonExe $syncScript --repo $archiveRepo --no-push
if ($LASTEXITCODE -ne 0) { throw "Archive step failed with exit code $LASTEXITCODE" }

# ---------------------------------------------------------------------------
# 2) Push with retries.  The network to GitHub is flaky, so retry transient
#    failures with backoff instead of dropping the freshly created commit.
# ---------------------------------------------------------------------------
$maxAttempts = 4
$delaySeconds = 5
$pushOk = $false

for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    Write-Host "[sync] push attempt $attempt/$maxAttempts"
    # git writes progress ("To https://...") to stderr; under PS 5.1 the 2>&1
    # merge would turn that into a terminating error when EAP=Stop, so relax
    # EAP for the native call and rely on $LASTEXITCODE instead.
    $output = $null
    $ErrorActionPreference = 'Continue'
    $output = & git -C $archiveRepo push origin HEAD:main 2>&1
    $pushExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($pushExit -eq 0) { $pushOk = $true; break }
    Write-Host "[sync] push attempt $attempt failed (exit $pushExit): $($output | Out-String)"
    if ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds $delaySeconds
        $delaySeconds *= 2
    }
}

if (-not $pushOk) { throw "git push failed after $maxAttempts attempts" }

Write-Host '[sync] OK: archive committed and pushed.'
exit 0