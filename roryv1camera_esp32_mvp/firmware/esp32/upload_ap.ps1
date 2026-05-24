# AP mode — upload scripts + ap_config.py to ESP32.
# Usage: .\upload_ap.ps1 -Port COM4
param(
    [Parameter(Mandatory = $true)]
    [string]$Port
)

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ap = Join-Path $root "src\esp32\ap_config.py"
if (-not (Test-Path $ap)) {
    Write-Error "Create src\esp32\ap_config.py first (run .\prepare_ap_config.ps1)."
    exit 1
}

& (Join-Path $PSScriptRoot "upload.ps1") -Port $Port
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Uploading ap_config.py ..."
python -m mpremote connect $Port fs cp $ap ":ap_config.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Reset board ..."
python -m mpremote connect $Port reset
Write-Host "AP mode uploaded. Connect to ESP32 SSID, then open http://192.168.4.1/"
