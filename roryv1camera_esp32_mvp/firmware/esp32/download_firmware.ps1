# Download lemariva camera MicroPython firmware (Freenove Path A)
$out = Join-Path $PSScriptRoot "micropython_camera.bin"
$url = "https://raw.githubusercontent.com/lemariva/micropython-camera-driver/master/firmware/micropython_camera_feeeb5ea3_esp32_idf4_4.bin"

Write-Host "Downloading to $out ..."
Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
$size = (Get-Item $out).Length
Write-Host "Done. Size: $size bytes"
if ($size -lt 1000000) {
    Write-Error "Download looks too small; check network or URL."
    exit 1
}
