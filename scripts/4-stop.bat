@echo off
chcp 65001 >nul 2>&1
REM ====================================
REM STOP - stop backend and Docker services
REM ====================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."

echo.
echo ============================================
echo   Outdoor Agent Planner - Stop
echo ============================================
echo.

REM ---------- 1. stop backend (python main.py) ----------
echo [1/2] Stopping backend ...

set "FOUND=0"
for /f "tokens=2 delims= " %%a in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr /i "PID"') do (
    wmic process where "ProcessId=%%a and CommandLine like '%%main.py%%'" get ProcessId 2>nul | findstr "%%a" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        taskkill /pid %%a /f >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo       [OK] killed backend PID=%%a
            set "FOUND=1"
        )
    )
)
if "!FOUND!"=="0" (
    echo       [INFO] no running backend process found
)

REM ---------- 2. stop Docker services ----------
echo [2/2] Docker services ...

where docker >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    docker info >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        docker-compose -f "%ROOT%\docker-compose.yml" down 2>&1
        echo       [OK] Docker services stopped
    ) else (
        echo       [INFO] Docker not running
    )
) else (
    echo       [INFO] docker not found, skip
)

echo.
echo ============================================
echo   Stopped
echo ============================================
echo.
pause
