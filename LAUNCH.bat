@echo off
REM Memory Explorer Pro Launcher
REM Launches the memory analysis tool with proper error handling

echo ===================================
echo   MEMORY EXPLORER PRO - LAUNCHER
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if StealthEngine exists
if not exist "StealthEngine\StealthEngine.dll" (
    echo [WARNING] StealthEngine.dll not found!
    echo Expected location: StealthEngine\StealthEngine.dll
    echo.
    echo Memory operations may fail without kernel driver.
    echo Press any key to continue anyway...
    pause >nul
)

echo [OK] StealthEngine present
echo.

REM Check dependencies
echo Checking dependencies...
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] psutil not installed
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [OK] Dependencies installed
echo.

REM Check admin privileges
net session >nul 2>&1
if errorlevel 1 (
    echo ========================================
    echo [WARNING] NOT RUNNING AS ADMINISTRATOR
    echo ========================================
    echo.
    echo For best results, run as Administrator:
    echo   1. Right-click this file
    echo   2. Select "Run as administrator"
    echo.
    echo Press any key to continue anyway...
    pause >nul
) else (
    echo [OK] Running with admin privileges
)

echo.
echo ===================================
echo   LAUNCHING MEMORY EXPLORER PRO
echo ===================================
echo.

REM Launch the application
python MemoryExplorer.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed or closed with error
    echo Check the console output above for details
    pause
    exit /b 1
)

echo.
echo Application closed successfully
pause
