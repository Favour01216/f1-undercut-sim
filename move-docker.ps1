# Docker Migration Script
# Run this as Administrator

param(
    [Parameter(Mandatory=$true)]
    [string]$NewDrive = "D:"  # Change to your SSD drive letter
)

Write-Host "🐳 Docker Migration to $NewDrive" -ForegroundColor Cyan

# Stop Docker Desktop
Write-Host "1. Stopping Docker Desktop..." -ForegroundColor Yellow
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue

# Create new Docker directory
$NewDockerPath = "$NewDrive\Docker"
Write-Host "2. Creating new Docker directory at $NewDockerPath" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $NewDockerPath -Force

# Move Docker data
$OldDockerPath = "$env:LOCALAPPDATA\Docker"
Write-Host "3. Moving Docker data from $OldDockerPath to $NewDockerPath" -ForegroundColor Yellow

if (Test-Path $OldDockerPath) {
    robocopy $OldDockerPath $NewDockerPath /E /MOVE /MT:8
    Write-Host "✅ Docker data moved successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Docker path not found!" -ForegroundColor Red
}

Write-Host "4. Next steps:" -ForegroundColor Cyan
Write-Host "   - Open Docker Desktop" -ForegroundColor White
Write-Host "   - Go to Settings > Resources > Advanced" -ForegroundColor White
Write-Host "   - Set Disk image location to: $NewDockerPath" -ForegroundColor White
Write-Host "   - Apply & Restart Docker" -ForegroundColor White

Write-Host "🏁 Migration script complete!" -ForegroundColor Green