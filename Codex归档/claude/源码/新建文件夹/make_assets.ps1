# Generate: (1) cropped+upscaled 22.bmp corner, (2) vision test image
Add-Type -AssemblyName System.Drawing

$src = [System.Drawing.Image]::FromFile(".\22.bmp")
$sx = 5; $sy = 0; $sw = 126; $sh = 37
$scale = 6
$outW = $sw * $scale; $outH = $sh * $scale
$bmp = New-Object System.Drawing.Bitmap $outW, $outH
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
$g.Clear([System.Drawing.Color]::White)
$g.DrawImage($src, (New-Object System.Drawing.Rectangle 0, 0, $outW, $outH),
             (New-Object System.Drawing.Rectangle $sx, $sy, $sw, $sh),
             [System.Drawing.GraphicsUnit]::Pixel)
$g.Dispose()
$bmp.Save(".\22_corner_zoomed.png", [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "Saved 22_corner_zoomed.png"

# --- Vision test image: clear known content ---
$w = 640; $h = 400
$img = New-Object System.Drawing.Bitmap $w, $h
$g2 = [System.Drawing.Graphics]::FromImage($img)
$g2.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g2.Clear([System.Drawing.Color]::White)

# Red filled circle, top-left
$brushRed = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(220, 30, 30))
$g2.FillEllipse($brushRed, 50, 50, 100, 100)

# Blue filled square, top-right
$brushBlue = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(30, 80, 220))
$g2.FillRectangle($brushBlue, 460, 40, 90, 90)

# Green triangle, bottom-left
$brushGreen = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(40, 160, 60))
$tri = [System.Drawing.Point[]]@(
    (New-Object System.Drawing.Point 40, 350),
    (New-Object System.Drawing.Point 130, 260),
    (New-Object System.Drawing.Point 220, 350))
$g2.FillPolygon($brushGreen, $tri)

# Black bold text "VISION-42" centered
$font = New-Object System.Drawing.Font "Arial", 52, ([System.Drawing.FontStyle]::Bold)
$brushBlack = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::Black)
$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = [System.Drawing.StringAlignment]::Center
$sf.LineAlignment = [System.Drawing.StringAlignment]::Center
$g2.DrawString("VISION-42", $font, $brushBlack, (New-Object System.Drawing.RectangleF 140, 150, 360, 100), $sf)

# Orange text "HELLO" near bottom-right
$brushOrange = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(240, 140, 20))
$font2 = New-Object System.Drawing.Font "Arial", 28, ([System.Drawing.FontStyle]::Bold)
$g2.DrawString("HELLO", $font2, $brushOrange, (New-Object System.Drawing.RectangleF 380, 320, 180, 50), $sf)

$g2.Dispose()
$img.Save(".\vision_test.png", [System.Drawing.Imaging.ImageFormat]::Png)
$img.Dispose()
Write-Output "Saved vision_test.png"
