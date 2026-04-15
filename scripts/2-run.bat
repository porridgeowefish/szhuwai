@echo off
chcp 65001 >nul 2>&1
REM ====================================
REM RUN - start backend dev server
REM ====================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."

echo.
echo ============================================
echo   Outdoor Agent Planner - Run
echo ============================================
echo.

REM ---------- env vars for local dev ----------
set MYSQL_HOST=localhost
set MYSQL_PORT=3307
set MONGO_HOST=localhost
set REDIS_HOST=localhost

REM ---------- check Docker services ----------
docker-compose -f "%ROOT%\docker-compose.yml" ps --format "{{.Name}} {{.Health}}" 2>nul | findstr /i "mysql mongodb redis" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Docker services not running. Run scripts\1-build.bat first.
    echo.
)

echo.

REM ---------- start backend ----------
pushd "%ROOT%\backend"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] backend dir not found
    pause & exit /b 1
)

echo [Starting] python main.py
echo.
echo   URL:  http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo   SMS:  search [DEV] in terminal or run scripts\get_sms_code.py
echo.
echo   Ctrl+C to stop
echo.

python main.py
popd
