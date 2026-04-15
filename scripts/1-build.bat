@echo off
chcp 65001 >nul 2>&1
REM ====================================
REM BUILD - start deps via Docker, install Python deps
REM ====================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."

echo.
echo ============================================
echo   Outdoor Agent Planner - Build
echo ============================================
echo.

REM ---------- 0. Check Docker ----------
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] docker not found. Install Docker Desktop first.
    pause & exit /b 1
)

docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker daemon not running. Start Docker Desktop.
    pause & exit /b 1
)
echo [OK] Docker is running

REM ---------- 1. Start MySQL + MongoDB + Redis ----------
echo.
echo [1/2] Starting MySQL, MongoDB, Redis via Docker ...

pushd "%ROOT%"
docker-compose up -d mysql mongodb redis 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] docker-compose up failed
    popd & pause & exit /b 1
)
popd

echo       [OK] Containers started
echo       Waiting for services to be healthy ...

REM Wait up to 60s for services
set "WAIT=0"
:wait_loop
if !WAIT! GEQ 30 (
    echo       [WARN] Timeout waiting for services, continuing anyway
    goto wait_done
)

docker-compose -f "%ROOT%\docker-compose.yml" ps --format "{{.Name}} {{.Health}}" 2>nul | findstr /i "starting unhealthy" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    timeout /t 2 /nobreak >nul
    set /a "WAIT+=2"
    goto wait_loop
)
echo       [OK] All services healthy

:wait_done

REM ---------- 2. Python deps ----------
echo.
echo [2/2] Python deps ...

pushd "%ROOT%\backend"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] backend dir not found
    pause & exit /b 1
)

if defined CONDA_PREFIX (
    echo       Conda env: %CONDA_PREFIX%
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo       Using system Python
)

pip install -q -r requirements.txt
if %ERRORLEVEL% EQU 0 (
    echo       [OK] deps installed
) else (
    echo       [WARN] pip install had errors
)

popd

echo.
echo ============================================
echo   Build complete
echo ============================================
echo.
echo   Services running (Docker):
echo     MySQL:    localhost:3307
echo     MongoDB:  localhost:27017
echo     Redis:    localhost:6379
echo.
echo   Start: scripts\2-run.bat
echo   Test:  scripts\3-test.bat
echo   Stop:  scripts\4-stop.bat
echo.
pause
