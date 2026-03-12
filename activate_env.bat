@echo off
REM ===============================================
REM 户外规划智能系统
REM ===============================================
REM 脚本激活 real_base Conda 环境

set CONDA_ROOT=C:\Users\xmz14_ugn3mh4\anaconda3
set ENV_NAME=real_base

echo 激活 Conda 環境: %ENV_NAME%...
call "%CONDA_ROOT%\Scripts\activate.bat" %ENV_NAME%

if %ERRORLEVEL% NEQ 0 (
    echo [錯誤] 無法激活環境 %ENV_NAME%
    pause
    exit /b 1
)

echo.
echo [成功] 環境 %ENV_NAME% 已激活
echo.
echo 可用命令:
echo   make test          - 運行所有測試
echo   make lint          - 代碼檢查
echo   make format        - 代碼格式化
echo   python            - 啟動 Python
echo.
cd /d "%~dp0"
