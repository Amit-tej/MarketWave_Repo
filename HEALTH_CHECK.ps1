#!/usr/bin/env powershell

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "    MarketWave Health Check Script" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

$issues = @()
$warnings = @()

# 1. Check Python
Write-Host "[1/8] Checking Python..." -ForegroundColor Yellow
$pythonExe = "C:\Users\HP\AppData\Local\Programs\Python\Python39\python.exe"
if (Test-Path $pythonExe) {
    $pythonVersion = & $pythonExe --version 2>&1
    Write-Host "[OK] Python installed: $pythonVersion" -ForegroundColor Green
} else {
    $issues += "Python 3.9 not found at $pythonExe"
    Write-Host "[FAIL] Python not found" -ForegroundColor Red
}

# 2. Check Node.js
Write-Host "[2/8] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = & node --version 2>&1
    Write-Host "[OK] Node.js installed: $nodeVersion" -ForegroundColor Green
} catch {
    $issues += "Node.js not installed"
    Write-Host "[FAIL] Node.js not found" -ForegroundColor Red
}

# 3. Check npm
Write-Host "[3/8] Checking npm..." -ForegroundColor Yellow
try {
    $npmVersion = & npm --version 2>&1
    Write-Host "[OK] npm installed: $npmVersion" -ForegroundColor Green
} catch {
    $issues += "npm not installed"
    Write-Host "[FAIL] npm not found" -ForegroundColor Red
}

# 4. Check frontend dependencies
Write-Host "[4/8] Checking frontend dependencies..." -ForegroundColor Yellow
$frontendNodeModules = "C:\Users\HP\OneDrive\Desktop\marketwave 2.0\frontend\node_modules"
if (Test-Path $frontendNodeModules) {
    Write-Host "[OK] Frontend dependencies installed" -ForegroundColor Green
} else {
    $warnings += "Frontend dependencies not installed. Run: cd frontend; npm install"
    Write-Host "[WARN] Frontend dependencies missing (optional)" -ForegroundColor Yellow
}

# 5. Check dataset files
Write-Host "[5/8] Checking dataset files..." -ForegroundColor Yellow
$datasetDir = "C:\Users\HP\OneDrive\Desktop\marketwave 2.0\dataset"
$csvCount = @(Get-ChildItem -Path $datasetDir -Filter "*.csv" -ErrorAction SilentlyContinue).Count
if ($csvCount -ge 5) {
    Write-Host "[OK] Dataset files present ($csvCount CSV files)" -ForegroundColor Green
} else {
    $issues += "Missing dataset CSV files (found: $csvCount)"
    Write-Host "[FAIL] Dataset incomplete" -ForegroundColor Red
}

# 6. Check model files
Write-Host "[6/8] Checking model files..." -ForegroundColor Yellow
$modelsDir = "C:\Users\HP\OneDrive\Desktop\marketwave 2.0\models"
$joblibs = @(Get-ChildItem -Path $modelsDir -Recurse -Filter "*.joblib" -ErrorAction SilentlyContinue).Count
if ($joblibs -ge 5) {
    Write-Host "[OK] Model files present ($joblibs ensemble models)" -ForegroundColor Green
} else {
    $warnings += "Few ensemble models found ($joblibs). Some market combinations may not work."
    Write-Host "[WARN] Limited model coverage ($joblibs models)" -ForegroundColor Yellow
}

# 7. Check API server
Write-Host "[7/8] Checking API server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] API server is running" -ForegroundColor Green
    } else {
        Write-Host "[WARN] API server not responding (not running yet - start with START_MARKETWAVE.ps1)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] API server not running (expected if not started yet)" -ForegroundColor Yellow
}

# 8. Check frontend
Write-Host "[8/8] Checking frontend server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Frontend server is running" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Frontend server not responding (not running yet - start with START_MARKETWAVE.ps1)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] Frontend server not running (expected if not started yet)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "              Health Summary" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

if ($issues.Count -gt 0) {
    Write-Host "[ERROR] ISSUES FOUND:" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
    Write-Host ""
}

if ($warnings.Count -gt 0) {
    Write-Host "[WARN] WARNINGS:" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "  - $warning" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($issues.Count -eq 0) {
    Write-Host "[SUCCESS] All systems ready! Run: .\START_MARKETWAVE.ps1`n" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Please fix the issues above before starting.`n" -ForegroundColor Red
}
