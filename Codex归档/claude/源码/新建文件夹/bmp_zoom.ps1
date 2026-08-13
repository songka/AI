param([string]$Path = ".\22.bmp")

Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($Path)

$minX = 99999; $minY = 99999; $maxX = -1; $maxY = -1
for ($y = 0; $y -lt $img.Height; $y++) {
    for ($x = 0; $x -lt $img.Width; $x++) {
        $px = $img.GetPixel($x, $y)
        if ($px.R -lt 245 -or $px.G -lt 245 -or $px.B -lt 245) {
            if ($x -lt $minX) { $minX = $x }
            if ($y -lt $minY) { $minY = $y }
            if ($x -gt $maxX) { $maxX = $x }
            if ($y -gt $maxY) { $maxY = $y }
        }
    }
}
$w = $maxX - $minX + 1; $h = $maxY - $minY + 1

# Per-pixel render of content box: dark => '#', light => space
$darkChar = "#"
for ($y = $minY; $y -le $maxY; $y++) {
    $line = ""
    for ($x = $minX; $x -le $maxX; $x++) {
        $px = $img.GetPixel($x, $y)
        $lum = 0.299*$px.R + 0.587*$px.G + 0.114*$px.B
        if ($lum -lt 200) { $line += $darkChar } else { $line += " " }
    }
    Write-Output ("{0,3}: {1}" -f $y, $line)
}
$img.Dispose()
Write-Output ""
Write-Output ("Box: x={0}..{1} y={2}..{3} w={4} h={5}" -f $minX, $maxX, $minY, $maxY, $w, $h)
