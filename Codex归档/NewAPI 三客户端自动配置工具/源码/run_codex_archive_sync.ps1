$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = 'C:\Users\lfaf-120-2\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$archiveRepo = Join-Path $scriptRoot 'codex-archive-repo\codex-archive-stable'

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "未找到 Python：$pythonExe"
}
if (-not (Test-Path -LiteralPath (Join-Path $archiveRepo '.git'))) {
    throw "未找到归档仓库：$archiveRepo"
}

& $pythonExe (Join-Path $scriptRoot 'codex_archive_sync.py') --repo $archiveRepo
