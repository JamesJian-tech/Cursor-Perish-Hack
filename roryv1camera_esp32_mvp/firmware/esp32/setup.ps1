# Phase 1 full setup: flash camera firmware + upload Phase 1 scripts + verify.
# Usage: .\setup.ps1
#        .\setup.ps1 -Port COM4
#        .\setup.ps1 -Port COM4 -SkipFlash
param(
    [string]$Port = "",
    [switch]$SkipFlash
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $Port) {
    $Port = & (Join-Path $PSScriptRoot "detect_port.ps1")
}
if (-not $Port) {
    Write-Error @"
No serial port found. Plug in the ESP32-WROVER via USB, install the CH340 driver if needed,
then run: .\setup.ps1 -Port COMx
"@
}

Write-Host "Using port $Port"

if (-not $SkipFlash) {
    & (Join-Path $PSScriptRoot "flash.ps1") -Port $Port
} else {
    Write-Host "Skipping flash (-SkipFlash)"
}

& (Join-Path $PSScriptRoot "verify_phase1.ps1") -Port $Port

Write-Host "Phase 1 setup complete."
