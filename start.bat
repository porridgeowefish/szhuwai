@echo off
REM ====================================
REM 户外活动规划助手 - Docker Compose 启动脚本
REM ====================================

setlocal enabledelayedexpansion

echo ====================================
echo 户外活动规划助手 - Docker 部署
echo ====================================
echo.

REM 检查 Docker
echo [1/4] 检查 Docker 环境...
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker 未安装或未启动
    echo 请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker 已就绪

REM 检查 Docker Compose
echo.
echo [2/4] 检查 Docker Compose...
docker-compose version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker Compose 未可用
    pause
    exit /b 1
)
echo [OK] Docker Compose 已就绪

REM 构建并启动服务
echo.
echo [3/4] 启动数据库服务 (MySQL + MongoDB)...
docker-compose up -d mysql mongodb
timeout /t 3 >nul

echo.
echo [4/4] 启动后端服务...
docker-compose up -d backend

REM 显示状态
echo.
echo ====================================
echo 服务状态
echo ====================================
docker-compose ps

echo.
echo ====================================
echo 启动完成！
echo ====================================
echo.
echo 服务地址:
echo   - API 服务:     http://localhost:8000
echo   - API 文档:     http://localhost:8000/docs
echo   - MySQL 端口:   3307 (主机) -> 3306 (容器)
echo   - MongoDB 端口: 27017
echo.
echo 常用命令:
echo   - 查看日志:     docker-compose logs -f
echo   - 停止服务:     docker-compose down
echo   - 重启服务:     docker-compose restart
echo   - 仅启动数据库: docker-compose up -d mysql mongodb
echo.
pause
