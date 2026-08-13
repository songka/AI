param([string]$Path = ".\22.bmp")

Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($Path)

# Find bounding box of non-white pixels
$minX = 99999; $minY = 99999; $maxX = -1; $maxY = -1
$nonWhite = 0; $total = 0
for ($y = 0; $y -lt $img.Height; $y++) {
    for ($x = 0; $x -lt $img.Width; $x++) {
        $px = $img.GetPixel($x, $y)
        $total++
        if ($px.R -lt 245 -or $px.G -lt 245 -or $px.B -lt 245) {
            $nonWhite++
            if ($x -lt $minX) { $minX = $x }
            if ($y -lt $minY) { $minY = $y }
            if ($x -gt $maxX) { $maxX = $x }
            if ($y -gt $maxY) { $maxY = $y }
        }
    }
}
Write-Output ("Non-white pixels: {0} / {1} ({2:P2})" -f $nonWhite, $total, ($nonWhite/$total))
if ($nonWhite -eq 0) { Write-Output "All white image"; exit }

$w = $maxX - $minX + 1; $h = $maxY - $minY + 1
Write-Output ("Content bounding box: x={0}..{1} y={2}..{3}  (w={4} h={5})" -f $minX, $maxX, $minY, $maxY, $w, $h)

# Render the content region in detail via downscale
$cols = 120
$ratio = $h / $w
$rows = [int][Math]::Max(1, $cols * $ratio * 1.6)
if ($rows -gt 80) { $rows = 80 }

$thumb = New-Object System.Drawing.Bitmap $cols, $rows
$g = [System.Drawing.Graphics]::FromImage($thumb)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $cols, $rows),
             (New-Object System.Drawing.Rectangle $minX, $minY, $w, $h),
             [System.Drawing.GraphicsUnit]::Pixel)
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

Write-Output "--- Detail (white=@ black=space) ---"
Write-Output $sb.ToString()
