# Memory Explorer Pro Launcher (PowerShell)
# Launches with proper error handling and dependency checks

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  MEMORY EXPLORER PRO - LAUNCHER" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Check StealthEngine
Write-Host "Checking StealthEngine..." -ForegroundColor Yellow
if (Test-Path "StealthEngine\StealthEngine.dll") {
    Write-Host "[OK] StealthEngine.dll found" -ForegroundColor Green
} else {
    Write-Host "[WARNING] StealthEngine.dll not found!" -ForegroundColor Yellow
    Write-Host "Expected location: StealthEngine\StealthEngine.dll" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Memory operations may fail without kernel driver." -ForegroundColor Yellow
    Read-Host "Press Enter to continue anyway"
}
Write-Host ""

# Check dependencies
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
try {
    & python -c "import psutil" 2>&1 | Out-Null
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Missing dependencies" -ForegroundColor Yellow
    Write-Host "Installing from requirements.txt..." -ForegroundColor Yellow
    & pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
}
Write-Host ""

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "[WARNING] NOT RUNNING AS ADMINISTRATOR" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "For best results, run PowerShell as Administrator:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor Yellow
    Write-Host "  2. Select 'Run as administrator'" -ForegroundColor Yellow
    Write-Host "  3. Navigate to this folder and run: .\LAUNCH.ps1" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 0
    }
} else {
    Write-Host "[OK] Running with admin privileges" -ForegroundColor Green
}

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  LAUNCHING MEMORY EXPLORER PRO" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Launch application
try {
    & python MemoryExplorer.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[ERROR] Application exited with error code $LASTEXITCODE" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host ""
    Write-Host "Application closed successfully" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to launch application:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"
