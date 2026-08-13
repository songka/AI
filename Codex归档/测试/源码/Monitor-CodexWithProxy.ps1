param(
    [string]$TaskName = "CodexProxyRecovery",
    [string]$CodexAppId = "OpenAI.Codex_2p2nqsd0c76g0!App",
    [string]$V2rayNPath = "C:\Program Files\v2rayN-windows-64\v2rayN.exe",
    [string]$V2rayNConfigPath = "$env:LOCALAPPDATA\v2rayN\guiConfigs\guiNConfig.json",
    [int]$CodexReadyTimeoutSeconds = 300,
    [int]$CodexStableSeconds = 20,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$script:LogDir = Join-Path $env:LOCALAPPDATA "CodexProxyRecovery"
$script:LogPath = Join-Path $script:LogDir "monitor.log"
$script:InternetSettingsPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"

function Write-Log {
    param([string]$Message)

    if (-not (Test-Path $script:LogDir)) {
        New-Item -Path $script:LogDir -ItemType Directory -Force | Out-Null
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $script:LogPath -Value "[$timestamp] $Message" -Encoding UTF8
}

Add-Type -Namespace WinInet -Name NativeMethods -MemberDefinition @"
[System.Runtime.InteropServices.DllImport("wininet.dll", SetLastError=true)]
public static extern bool InternetSetOption(System.IntPtr hInternet, int dwOption, System.IntPtr lpBuffer, int dwBufferLength);
"@

function Notify-ProxyChanged {
    [void][WinInet.NativeMethods]::InternetSetOption([IntPtr]::Zero, 39, [IntPtr]::Zero, 0)
    [void][WinInet.NativeMethods]::InternetSetOption([IntPtr]::Zero, 37, [IntPtr]::Zero, 0)
}

function Get-V2rayNProxyServer {
    $fallbackPort = 10808

    if (Test-Path $V2rayNConfigPath) {
        try {
            $config = Get-Content -Path $V2rayNConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $inbound = @($config.Inbound | Where-Object { $_.Protocol -in @("socks", "http") } | Select-Object -First 1)
            if ($inbound -and $inbound.LocalPort) {
                return "127.0.0.1:$($inbound.LocalPort)"
            }
        }
        catch {
            Write-Log "Could not read v2rayN config, falling back to port $fallbackPort. Error: $($_.Exception.Message)"
        }
    }

    return "127.0.0.1:$fallbackPort"
}

function Get-V2rayNProxyOverride {
    if (Test-Path $V2rayNConfigPath) {
        try {
            $config = Get-Content -Path $V2rayNConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $exceptions = $config.SystemProxyItem.SystemProxyExceptions
            if ($exceptions) {
                if ($config.SystemProxyItem.NotProxyLocalAddress) {
                    return "<local>;$exceptions"
                }
                return $exceptions
            }
        }
        catch {
            Write-Log "Could not read v2rayN proxy exceptions. Error: $($_.Exception.Message)"
        }
    }

    return "<local>;localhost;127.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;172.20.*;172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*;192.168.*"
}

function Set-V2rayNAutoProxy {
    $proxyServer = Get-V2rayNProxyServer
    $proxyOverride = Get-V2rayNProxyOverride

    Set-ItemProperty -Path $script:InternetSettingsPath -Name ProxyServer -Value $proxyServer
    Set-ItemProperty -Path $script:InternetSettingsPath -Name ProxyOverride -Value $proxyOverride
    Set-ItemProperty -Path $script:InternetSettingsPath -Name ProxyEnable -Value 1 -Type DWord

    try {
        Remove-ItemProperty -Path $script:InternetSettingsPath -Name AutoConfigURL -ErrorAction SilentlyContinue
    }
    catch {
        Write-Log "Could not remove AutoConfigURL. Error: $($_.Exception.Message)"
    }

    Notify-ProxyChanged
    Write-Log "System proxy enabled through v2rayN local proxy $proxyServer."
}

function Clear-V2rayNProxy {
    Set-ItemProperty -Path $script:InternetSettingsPath -Name ProxyEnable -Value 0 -Type DWord
    try {
        Remove-ItemProperty -Path $script:InternetSettingsPath -Name AutoConfigURL -ErrorAction SilentlyContinue
    }
    catch {
        Write-Log "Could not remove AutoConfigURL. Error: $($_.Exception.Message)"
    }

    Notify-ProxyChanged
    Write-Log "System proxy cleared."
}

function Ensure-V2rayNRunning {
    $running = Get-Process -Name "v2rayN" -ErrorAction SilentlyContinue
    if ($running) {
        return
    }

    if (-not (Test-Path $V2rayNPath)) {
        throw "v2rayN was not running and $V2rayNPath does not exist."
    }

    Start-Process -FilePath $V2rayNPath -WindowStyle Hidden
    Write-Log "Started v2rayN."
    Start-Sleep -Seconds 5
}

function Get-CodexReadyProcess {
    Get-Process -Name "Codex" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.MainWindowHandle -ne 0 -and
            $_.MainWindowTitle -and
            $_.Responding
        } |
        Select-Object -First 1
}

function Test-CodexReady {
    [bool](Get-CodexReadyProcess)
}

function Start-CodexApp {
    Start-Process -FilePath "explorer.exe" -ArgumentList "shell:AppsFolder\$CodexAppId"
    Write-Log "Requested Codex start through $CodexAppId."
}

function Wait-CodexReady {
    $deadline = (Get-Date).AddSeconds($CodexReadyTimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        if (Test-CodexReady) {
            Write-Log "Codex window is visible and responding; waiting $CodexStableSeconds seconds for UI stabilization."
            Start-Sleep -Seconds $CodexStableSeconds
            if (Test-CodexReady) {
                return $true
            }
        }

        Start-Sleep -Seconds 5
    }

    return $false
}

$mutexName = "Global\$TaskName"
$mutex = [System.Threading.Mutex]::new($false, $mutexName)
$hasMutex = $false

try {
    $hasMutex = $mutex.WaitOne(0)
    if (-not $hasMutex) {
        Write-Log "Another monitor instance is already running; exiting."
        exit 0
    }

    if (-not $Force -and (Test-CodexReady)) {
        Write-Log "Codex is already ready; no action needed."
        exit 0
    }

    Write-Log "Codex is not ready; enabling proxy, starting Codex, then waiting for recovery."
    Ensure-V2rayNRunning
    Set-V2rayNAutoProxy
    Start-CodexApp

    if (Wait-CodexReady) {
        Clear-V2rayNProxy
        Write-Log "Recovery completed."
        exit 0
    }

    Write-Log "Timed out waiting for Codex; leaving proxy enabled for the next scheduled run."
    exit 2
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}
finally {
    if ($hasMutex) {
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}
