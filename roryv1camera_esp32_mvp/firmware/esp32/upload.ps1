# Upload all scripts (Phase 1 + Phase 2 helpers).
# For Phase 1 only, use upload_phase1.ps1 instead.
# Usage: .\upload.ps1 -Port COM4
param(
    [Parameter(Mandatory = $true)]
    [string]$Port
)

& (Join-Path $PSScriptRoot "upload_phase1.ps1") -Port $Port

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$src = Join-Path $root "src\esp32"

foreach ($file in @("upload_client.py", "main_upload.py")) {
    $path = Join-Path $src $file
    Write-Host "Uploading $file ..."
    python -m mpremote connect $Port fs cp $path ":$file"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "All scripts uploaded."
