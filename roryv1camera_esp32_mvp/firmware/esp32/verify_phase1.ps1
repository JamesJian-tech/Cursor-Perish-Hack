# Verify Phase 1 without reflashing: smoke test + pull sample JPEG to PC.
# Usage: .\verify_phase1.ps1 -Port COM4
param(
    [Parameter(Mandatory = $true)]
    [string]$Port
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$src = Join-Path $root "src\esp32"
$captures = Join-Path $root "captures"
New-Item -ItemType Directory -Force -Path $captures | Out-Null
$outJpg = Join-Path $captures "phase1_sample.jpg"

Write-Host "Uploading Phase 1 scripts ..."
& (Join-Path $PSScriptRoot "upload_phase1.ps1") -Port $Port

Write-Host "Checking camera module ..."
python -m mpremote connect $Port exec "import camera; print('camera OK')"

Write-Host "Running smoke test ..."
python -m mpremote connect $Port run (Join-Path $src "main.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Capturing sample frame to device ..."
python -m mpremote connect $Port run (Join-Path $src "capture_one.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Copying $outJpg ..."
python -m mpremote connect $Port fs cp ":capture.jpg" $outJpg
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$size = (Get-Item $outJpg).Length
Write-Host "Phase 1 verify OK - sample saved ($size bytes): $outJpg"
