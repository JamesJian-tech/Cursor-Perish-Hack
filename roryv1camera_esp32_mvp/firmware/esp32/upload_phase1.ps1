# Upload Phase 1 scripts only (camera — no WiFi upload loop on device).
# Usage: .\upload_phase1.ps1 -Port COM4
param(
    [Parameter(Mandatory = $true)]
    [string]$Port
)

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$src = Join-Path $root "src\esp32"

foreach ($file in @("boot.py", "camera_freenove.py", "main.py", "capture_one.py")) {
    $path = Join-Path $src $file
    if (-not (Test-Path $path)) {
        Write-Error "Missing $path"
        exit 1
    }
    Write-Host "Uploading $file ..."
    python -m mpremote connect $Port fs cp $path ":$file"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Phase 1 scripts uploaded. Resetting ..."
python -m mpremote connect $Port reset
