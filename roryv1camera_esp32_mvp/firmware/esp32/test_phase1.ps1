# Phase 1 test — checks COM port is free, then runs verify_phase1.ps1
# Usage: .\test_phase1.ps1
#        .\test_phase1.ps1 -Port COM4
param(
    [string]$Port = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $Port) {
    $Port = & (Join-Path $PSScriptRoot "detect_port.ps1")
}
if (-not $Port) {
    Write-Host "No COM port found. Plug in ESP32 (CH340) and install driver if needed."
    exit 1
}

Write-Host "Testing port $Port ..."
$check = python -c @"
import serial
try:
    s = serial.Serial('$Port', 115200, timeout=1)
    s.close()
    print('OK')
except Exception as e:
    print('BUSY:', e)
    raise SystemExit(1)
"@ 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "COM port $Port is in use. Before retrying:"
    Write-Host "  1. Close Thonny, Arduino IDE, PuTTY, or any serial monitor"
    Write-Host "  2. Unplug USB, wait 3s, plug back in, press RST on the board"
    Write-Host "  3. Run this script again"
    Write-Host ""
    exit 1
}

& (Join-Path $PSScriptRoot "verify_phase1.ps1") -Port $Port
