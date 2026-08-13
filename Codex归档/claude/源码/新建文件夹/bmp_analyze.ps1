param([string]$Path = ".\22.bmp")

Add-Type -AssemblyName System.Drawing

$img = [System.Drawing.Image]::FromFile($Path)

# --- Global color stats (sample every 4px) ---
$rSum = 0.0; $gSum = 0.0; $bSum = 0.0; $n = 0
$minLum = 255.0; $maxLum = 0.0
$distinct = @{}
$step = 4
for ($y = 0; $y -lt $img.Height; $y += $step) {
    for ($x = 0; $x -lt $img.Width; $x += $step) {
        $px = $img.GetPixel($x, $y)
        $rSum += $px.R; $gSum += $px.G; $bSum += $px.B; $n++
        $lum = 0.299*$px.R + 0.587*$px.G + 0.114*$px.B
        if ($lum -lt $minLum) { $minLum = $lum }
        if ($lum -gt $maxLum) { $maxLum = $lum }
        $key = "$([int]($px.R/16))$([int]($px.G/16))$([int]($px.B/16))"
        $distinct[$key] = $true
    }
}

Write-Output ("Size: {0}x{1}" -f $img.Width, $img.Height)
Write-Output ("Avg color: R={0} G={1} B={2}" -f [int]($rSum/$n), [int]($gSum/$n), [int]($bSum/$n))
Write-Output ("Luminance range: {0} ~ {1}" -f [int]$minLum, [int]$maxLum)
Write-Output ("Distinct quantized colors: {0}" -f $distinct.Count)

# --- ASCII outline (96x54 downscale) ---
$cols = 96; $rows = 54
$thumb = New-Object System.Drawing.Bitmap $cols, $rows
$g = [System.Drawing.Graphics]::FromImage($thumb)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.DrawImage($img, 0, 0, $cols, $rows)
$g.Dispose()

$ramp = " .:-=+*#%@"
$sb = New-Object System.Text.StringBuilder
for ($y = 0; $y -lt $rows; $y++) {
    $line = ""
    for ($x = 0; $x -lt $cols; $x++) {
        $px = $thumb.GetPixel($x, $y)
        $lum = 0.299*$px.R + 0.587*$px.G + 0.114*$px.B
        $idx = [int]($lum / 255.0 * ($ramp.Length-1))
        $line += $ramp[$idx]
    }
    [void]$sb.AppendLine($line)
}

$thumb.Dispose()
$img.Dispose()
Write-Output "--- ASCII outline (bright = space, dark = @) ---"
Write-Output $sb.ToString()
