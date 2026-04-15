@echo off
chcp 65001 >nul 2>&1
REM ====================================
REM TEST - run backend tests
REM ====================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."

echo.
echo ============================================
echo   Outdoor Agent Planner - Test
echo ============================================
echo.

pushd "%ROOT%\backend"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] backend dir not found
    pause & exit /b 1
)

if "%~1"=="" (
    echo [Run] unit tests (skip integration)
    echo.
    python -m pytest test/ --ignore=test/integration -v --tb=short
) else if "%~1"=="all" (
    echo [Run] all tests (with integration)
    echo.
    python -m pytest test/ -v --tb=short
) else if "%~1"=="fast" (
    echo [Run] fast tests (-x stop on first fail)
    echo.
    python -m pytest test/ --ignore=test/integration -x -q --tb=line
) else if "%~1"=="sms" (
    echo [Run] SMS module tests
    echo.
    python -m pytest test/services/test_sms_service.py test/infrastructure/test_aliyun_sms_client.py test/repositories/test_sms_code_repo.py -v --tb=short
) else (
    echo [Run] pytest %*
    echo.
    python -m pytest %* -v --tb=short
)

popd

echo.
pause
