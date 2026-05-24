# Install PC-side tools only (run once)
Set-Location $PSScriptRoot
python -m pip install -r requirements.txt
Write-Host "Installed. Use: .\setup.ps1 -Port COMx (board plugged in)"
