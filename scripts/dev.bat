@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
set "ROOT=%~dp0.."
set "COMPOSE=%ROOT%\docker-compose.yml"

if "%~1"=="" goto usage
if "%~1"=="up"     goto cmd_up
if "%~1"=="run"    goto cmd_run
if "%~1"=="dev"    goto cmd_dev
if "%~1"=="status" goto cmd_status
if "%~1"=="stop"   goto cmd_stop
if "%~1"=="test"   goto cmd_test
if "%~1"=="clean"  goto cmd_clean
goto usage

:cmd_up
echo.
echo [UP] Starting middleware containers...
docker-compose -f "%COMPOSE%" up -d mysql mongodb redis postgres 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] docker-compose up failed
    pause & exit /b 1
)
echo       Waiting for health checks...
set "WAIT=0"
:up_wait
if !WAIT! GEQ 30 (
    echo       [WARN] Timeout, continuing...
    goto up_done
)
docker-compose -f "%COMPOSE%" ps --format "{{.Name}} {{.Health}}" 2>nul | findstr /i "starting unhealthy" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    timeout /t 2 /nobreak >nul
    set /a "WAIT+=2"
    goto up_wait
)
:up_done
echo.
echo [UP] Middleware started:
echo       MySQL:      localhost:3307
echo       MongoDB:    localhost:27017
echo       Redis:      localhost:6379
echo       PostgreSQL: localhost:5432
echo.
call :show_status
pause & exit /b 0

:cmd_run
echo.
echo [RUN] Starting backend...
echo.
set MYSQL_HOST=localhost
set MYSQL_PORT=3307
set MONGO_HOST=localhost
set REDIS_HOST=localhost

docker-compose -f "%COMPOSE%" ps --format "{{.Name}} {{.Health}}" 2>nul | findstr /i "mysql mongodb redis" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Middleware not running. Run: dev.bat up
    echo.
)

pushd "%ROOT%\backend"
echo   URL:  http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo   Ctrl+C to stop
echo.
python main.py
popd
exit /b 0

:cmd_dev
echo.
echo [DEV] Starting frontend dev server...
pushd "%ROOT%\frontend"
echo   URL: http://localhost:5173
echo   Ctrl+C to stop
echo.
call npm run dev
popd
exit /b 0

:cmd_status
echo.
echo ============================================
echo   Outdoor Agent Planner - Status
echo ============================================
echo.
echo [Docker Containers]
docker ps -a --filter "name=outdoor" --format "  {{.Names}}	{{.Status}}	{{.Ports}}" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   Docker not available
)
echo.
echo [Backend Process]
set "BE_FOUND=0"
for /f "tokens=2 delims= " %%a in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr /i "PID"') do (
    wmic process where "ProcessId=%%a and CommandLine like '%%main.py%%'" get ProcessId 2>nul | findstr "%%a" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo   Backend running PID=%%a
        set "BE_FOUND=1"
    )
)
if "!BE_FOUND!"=="0" echo   Backend not running
echo.
echo [Port Check]
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   Backend :8000  - OK
) else (
    echo   Backend :8000  - not responding
)
curl -s http://localhost:5173 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   Frontend :5173 - OK
) else (
    echo   Frontend :5173 - not responding
)
echo.
pause & exit /b 0

:show_status
echo [Container Status]
docker ps --filter "name=outdoor" --format "  {{.Names}}	{{.Status}}	{{.Ports}}" 2>nul
echo.
exit /b 0

:cmd_stop
echo.
echo [STOP] Stopping all services...
set "FOUND=0"
for /f "tokens=2 delims= " %%a in ('tasklist /fi "imagename eq python.exe" /fo list 2^>nul ^| findstr /i "PID"') do (
    wmic process where "ProcessId=%%a and CommandLine like '%%main.py%%'" get ProcessId 2>nul | findstr "%%a" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        taskkill /pid %%a /f >nul 2>&1
        echo   Backend PID=%%a stopped
        set "FOUND=1"
    )
)
if "!FOUND!"=="0" echo   Backend: not running

docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    docker-compose -f "%COMPOSE%" down 2>&1
    echo   Docker containers stopped
) else (
    echo   Docker: not running
)
echo.
echo [STOP] All stopped.
pause & exit /b 0

:cmd_test
echo.
echo [TEST] Running backend tests...
pushd "%ROOT%\backend"
if "%~2"=="" (
    python -m pytest test/ --ignore=test/integration -v --tb=short
) else (
    python -m pytest %2 %3 %4 %5 -v --tb=short
)
popd
pause & exit /b 0

:cmd_clean
echo.
echo [CLEAN] Removing containers and volumes...
docker-compose -f "%COMPOSE%" down -v 2>&1
docker volume rm outdoor_mongodb_data outdoor_mongodb_config outdoor_mysql_data outdoor_redis_data outdoor_postgres_data 2>nul
echo [CLEAN] Done.
pause & exit /b 0

:usage
echo.
echo   Usage: dev.bat [command]
echo.
echo   up      Start middleware (MySQL + MongoDB + Redis + PostgreSQL)
echo   run     Start backend (local Python)
echo   dev     Start frontend (Vite dev server)
echo   status  Check services and containers
echo   stop    Stop backend process + Docker containers
echo   test    Run backend tests
echo   clean   Remove all containers and volumes
echo.
pause & exit /b 0
