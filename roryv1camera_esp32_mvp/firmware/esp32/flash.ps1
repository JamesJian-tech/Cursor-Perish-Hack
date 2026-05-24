# Flash camera-enabled MicroPython to Freenove ESP32-WROVER
# Usage: .\flash.ps1 -Port COM4
param(
    [Parameter(Mandatory = $true)]
    [string]$Port,
    [string]$Bin = (Join-Path $PSScriptRoot "micropython_camera.bin")
)

if (-not (Test-Path $Bin)) {
    Write-Error "Firmware not found: $Bin`nDownload from lemariva/micropython-camera-driver (see README.md)."
    exit 1
}

Write-Host "Erasing flash on $Port ..."
python -m esptool --chip esp32 --port $Port erase-flash
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Writing firmware ..."
python -m esptool --chip esp32 --port $Port --baud 460800 write-flash -z 0x1000 $Bin
exit $LASTEXITCODE
