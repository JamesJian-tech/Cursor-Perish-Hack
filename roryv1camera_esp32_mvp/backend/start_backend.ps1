# Run NomSpot backend on the model laptop (listens on all interfaces).
Set-Location $PSScriptRoot
python -m pip install -r requirements.txt -q

$ip = (
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notmatch '^169\.' } |
    Select-Object -First 1 -ExpandProperty IPAddress
)

Write-Host ""
Write-Host "NomSpot backend starting on http://0.0.0.0:8000"
if ($ip) {
    Write-Host "ESP32 BACKEND_URL should use: http://${ip}:8000/api/frame"
}
Write-Host "Health: http://127.0.0.1:8000/health"
Write-Host "Allow Python through Windows Firewall (private network) if the ESP32 cannot connect."
Write-Host ""

python -m uvicorn app:app --host 0.0.0.0 --port 8000
