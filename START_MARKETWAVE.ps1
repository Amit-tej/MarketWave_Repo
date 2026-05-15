#!/usr/bin/env powershell

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "    MarketWave Application Startup" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $projectRoot "frontend"
$pythonExe = "C:\Users\HP\AppData\Local\Programs\Python\Python39\python.exe"

# Start API Server
Write-Host "[1/2] Starting API Server..." -ForegroundColor Yellow
Start-Process -FilePath $pythonExe -ArgumentList "api_server.py" -NoNewWindow -WorkingDirectory $projectRoot
Start-Sleep -Seconds 2
Write-Host "[OK] API running on http://localhost:8000`n" -ForegroundColor Green

# Start Frontend
Write-Host "[2/2] Starting Frontend Dev Server..." -ForegroundColor Yellow
Push-Location $frontendDir
Start-Process -FilePath "cmd" -ArgumentList "/c npm run dev" -NoNewWindow
Pop-Location

Write-Host "[OK] Frontend running on http://localhost:5173`n" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "      MarketWave is Ready!" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "  Open: http://localhost:5173 in browser" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan
