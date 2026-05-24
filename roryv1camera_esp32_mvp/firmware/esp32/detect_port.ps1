# Find first usable COM port for ESP32 (CH340 / CP210x)
$fromNet = [System.IO.Ports.SerialPort]::getportnames()
if ($fromNet.Count -gt 0) {
    Write-Host "Serial port: $($fromNet[0])"
    return $fromNet[0]
}

$wmi = Get-CimInstance Win32_SerialPort -ErrorAction SilentlyContinue
foreach ($p in $wmi) {
    if ($p.DeviceID) {
        Write-Host "WMI serial: $($p.DeviceID) ($($p.Name))"
        return $p.DeviceID
    }
}

$mp = python -m mpremote connect list 2>&1 | Out-String
if ($mp -match '(COM\d+)') {
    Write-Host "mpremote: $($Matches[1])"
    return $Matches[1]
}

return $null
