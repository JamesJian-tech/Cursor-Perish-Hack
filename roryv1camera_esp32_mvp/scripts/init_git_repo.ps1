# Initialize git repo and create first commit (run from repo root).
# Requires Git for Windows: https://git-scm.com/download/win

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$git = @(
    "git",
    "C:\Program Files\Git\cmd\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
) | ForEach-Object {
    if ($_ -eq "git") { $_ } else { $_ }
} | Where-Object {
    if ($_ -eq "git") {
        $null -ne (Get-Command git -ErrorAction SilentlyContinue)
    } else {
        Test-Path $_
    }
} | Select-Object -First 1

if (-not $git) {
    Write-Host "Git is not installed or not on PATH."
    Write-Host "Install: https://git-scm.com/download/win"
    Write-Host "Then re-run: .\scripts\init_git_repo.ps1"
    exit 1
}

function Invoke-Git {
    param([string[]]$Args)
    if ($git -eq "git") {
        & git @Args
    } else {
        & $git @Args
    }
}

if (-not (Test-Path ".git")) {
    Invoke-Git @("init")
}

Invoke-Git @("add", "-A")
Invoke-Git @("status")

$msg = @"
feat: ESP32 camera edge + WiFi JPEG backend (MVP)

- Freenove WROVER/OV3660 MicroPython camera (Phase 1)
- WiFi POST to FastAPI on model laptop (Phase 2)
- Ollama detector stub for merge with model repo
"@

Invoke-Git @("commit", "-m", $msg)
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing to commit or commit failed."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Commit created. To push:"
Write-Host "  git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git"
Write-Host "  git branch -M main"
Write-Host "  git push -u origin main"
