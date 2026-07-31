# Generates resources/icon.ico (16/32/48/256 px) - a flow curve (shear
# stress vs shear rate axes with a shear-thinning curve) icon for
# rheology-fit.
# Re-run after changing colors below, then rebuild: packaging\build_exe.ps1

Add-Type -AssemblyName System.Drawing

$outDir = "C:\Users\Karen\Cloude-python\rheology-fit\resources"
$sizes = 16, 32, 48, 256

$axisColor = [System.Drawing.ColorTranslator]::FromHtml("#5a2d0c")
$curveColor = [System.Drawing.ColorTranslator]::FromHtml("#e64a19")
$dotColor = [System.Drawing.ColorTranslator]::FromHtml("#ffb300")

function New-IconBitmap([int]$size) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.Clear([System.Drawing.Color]::Transparent)

    $originX = $size * 0.16
    $originY = $size * 0.84
    $topY = $size * 0.10
    $rightX = $size * 0.90

    $axisWidth = [Math]::Max(1.0, $size * 0.045)
    $axisPen = New-Object System.Drawing.Pen $axisColor, $axisWidth
    $axisPen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    $axisPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $axisPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $g.DrawLine($axisPen, $originX, $originY, $originX, $topY)
    $g.DrawLine($axisPen, $originX, $originY, $rightX, $originY)

    # Shear-thinning flow curve: steep rise then leveling off (Herschel-Bulkley shape).
    $curveWidth = [Math]::Max(1.2, $size * 0.06)
    $curvePen = New-Object System.Drawing.Pen $curveColor, $curveWidth
    $curvePen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    $curvePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $curvePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round

    $usableW = $rightX - $originX
    $usableH = $originY - $topY
    $n = 24
    $points = New-Object 'System.Collections.Generic.List[System.Drawing.PointF]'
    for ($i = 0; $i -le $n; $i++) {
        $t = $i / $n
        # normalized power-law-ish shape: y = t^0.35, plus a small yield offset
        $yieldFrac = 0.12
        $yNorm = $yieldFrac + (1 - $yieldFrac) * [Math]::Pow($t, 0.4)
        $px = $originX + $usableW * (0.06 + 0.90 * $t)
        $py = $originY - $usableH * $yNorm
        $points.Add((New-Object System.Drawing.PointF $px, $py))
    }
    $g.DrawCurve($curvePen, $points.ToArray())

    if ($size -ge 32) {
        $dotR = $size * 0.055
        $dotBrush = New-Object System.Drawing.SolidBrush $dotColor
        $lastPt = $points[$points.Count - 1]
        $g.FillEllipse($dotBrush, ($lastPt.X - $dotR / 2), ($lastPt.Y - $dotR / 2), $dotR, $dotR)
        $midPt = $points[[int]($points.Count * 0.45)]
        $g.FillEllipse($dotBrush, ($midPt.X - $dotR / 2), ($midPt.Y - $dotR / 2), $dotR, $dotR)
    }

    $g.Dispose()
    return $bmp
}

$pngBlobs = @()
foreach ($s in $sizes) {
    $bmp = New-IconBitmap $s
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    $pngBlobs += ,@{ Size = $s; Bytes = $ms.ToArray() }
    $bmp.Dispose()
}

$icoPath = Join-Path $outDir "icon.ico"
$ms = New-Object System.IO.MemoryStream
$bw = New-Object System.IO.BinaryWriter($ms)

$bw.Write([UInt16]0)
$bw.Write([UInt16]1)
$bw.Write([UInt16]$pngBlobs.Count)

$headerSize = 6 + 16 * $pngBlobs.Count
$offset = $headerSize
foreach ($blob in $pngBlobs) {
    $wByte = if ($blob.Size -ge 256) { 0 } else { $blob.Size }
    $hByte = if ($blob.Size -ge 256) { 0 } else { $blob.Size }
    $bw.Write([byte]$wByte)
    $bw.Write([byte]$hByte)
    $bw.Write([byte]0)
    $bw.Write([byte]0)
    $bw.Write([UInt16]1)
    $bw.Write([UInt16]32)
    $bw.Write([UInt32]$blob.Bytes.Length)
    $bw.Write([UInt32]$offset)
    $offset += $blob.Bytes.Length
}
foreach ($blob in $pngBlobs) {
    $bw.Write($blob.Bytes)
}
$bw.Flush()

[System.IO.File]::WriteAllBytes($icoPath, $ms.ToArray())
$bw.Close()
$ms.Close()

"Saved: $icoPath ($([System.IO.File]::ReadAllBytes($icoPath).Length) bytes)"
