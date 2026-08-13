function Get-AiAssetsSmbPrincipal {
    [CmdletBinding()]
    param(
        [string]$Server = '10.97.0.210',
        [string]$Share = 'lfaf_Engineer'
    )

    $connection = Get-SmbConnection -ErrorAction SilentlyContinue |
        Where-Object {
            $_.ServerName -ieq $Server -and
            $_.ShareName -ieq $Share -and
            $_.UserName
        } |
        Select-Object -First 1
    if ($connection) {
        return [string]$connection.UserName
    }

    # Get-SmbConnection can omit a valid connection on non-domain PCs. WNetGetUser
    # asks the Windows network provider for the account actually bound to this UNC
    # resource; it does not use chat input, environment variables, or saved passwords.
    if (-not ('AiAssets.NativeMethods' -as [type])) {
        Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
using System.Text;

namespace AiAssets {
    public static class NativeMethods {
        [DllImport("mpr.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern int WNetGetUser(
            string name,
            StringBuilder userName,
            ref int length
        );
    }
}
'@
    }

    $remote = "\\$Server\$Share"
    $length = 256
    $buffer = New-Object System.Text.StringBuilder $length
    $result = [AiAssets.NativeMethods]::WNetGetUser($remote, $buffer, [ref]$length)
    if ($result -eq 234 -and $length -gt 256) {
        $buffer = New-Object System.Text.StringBuilder $length
        $result = [AiAssets.NativeMethods]::WNetGetUser($remote, $buffer, [ref]$length)
    }
    if ($result -eq 0 -and $buffer.Length -gt 0) {
        return $buffer.ToString()
    }
    return $null
}
