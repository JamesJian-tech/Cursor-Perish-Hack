# Push this project to branch Roryv1camera on GitHub.
# Usage:
#   .\scripts\push_roryv1camera.ps1
#   .\scripts\push_roryv1camera.ps1 -RemoteUrl https://github.com/YOUR_USER/Roryv1camera.git
#   .\scripts\push_roryv1camera.ps1 -RemoteUrl https://github.com/YOUR_USER/Cursor-Perish-Hack.git

param(
    [string]$RemoteUrl = "https://github.com/RoryTuke/Roryv1camera.git",
    [string]$Branch = "Roryv1camera"
)

$ErrorActionPreference = "Stop"
$env:Path = "C:\Program Files\Git\cmd;" + $env:Path
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if (-not (Test-Path ".git")) {
    Write-Error "No git repo. Run: .\scripts\init_git_repo.ps1"
}

$status = git status --porcelain
if ($status) {
    git add -A
    git commit -m "chore: update NomSpot ESP32 camera edge + backend"
}

git branch -M $Branch

$remotes = git remote
if ($remotes -notcontains "origin") {
    git remote add origin $RemoteUrl
} else {
    git remote set-url origin $RemoteUrl
}

Write-Host "Pushing branch $Branch to $RemoteUrl ..."
git push -u origin $Branch

Write-Host "Done. Open: $($RemoteUrl -replace '\.git$','')/tree/$Branch"
