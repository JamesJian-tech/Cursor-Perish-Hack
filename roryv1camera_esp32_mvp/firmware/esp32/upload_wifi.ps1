# Phase 2 — upload scripts + wifi_config.py to ESP32
# Usage: .\upload_wifi.ps1 -Port COM4
# Create src\esp32\wifi_config.py from wifi_config.example.py first.
param(
    [Parameter(Mandatory = $true)]
    [string]$Port
)

$wifi = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")) "src\esp32\wifi_config.py"
if (-not (Test-Path $wifi)) {
    Write-Error "Create src\esp32\wifi_config.py from wifi_config.example.py (SSID, password, BACKEND_URL)."
    exit 1
}

& (Join-Path $PSScriptRoot "upload.ps1") -Port $Port
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Uploading wifi_config.py ..."
python -m mpremote connect $Port fs cp $wifi ":wifi_config.py"
python -m mpremote connect $Port reset
Write-Host "Phase 2: watch serial for WiFi OK and POST status: 200"
