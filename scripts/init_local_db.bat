@echo off
REM ====================================
REM 户外活动规划助手 - 本地开发环境初始化脚本 (Windows)
REM ====================================
REM 用途：在本地开发环境中初始化数据库
REM ====================================

setlocal enabledelayedexpansion

echo ====================================
echo 户外活动规划助手 - 本地环境初始化
echo ====================================
echo.

REM ====================================
REM 1. MySQL 初始化
REM ====================================
echo [1/3] 检查 MySQL 配置...

REM 检查 MySQL 客户端
where mysql >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] MySQL 客户端已安装

    REM 创建数据库
    echo 创建数据库 outdoor_planner...
    mysql -h localhost -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS outdoor_planner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] 数据库创建成功

        REM 执行初始化脚本
        if exist scripts\init_mysql.sql (
            echo 执行数据库表结构初始化...
            mysql -h localhost -u root -p123456 outdoor_planner < scripts\init_mysql.sql
            echo [OK] 表结构初始化完成
        )
    ) else (
        echo [ERROR] MySQL 连接失败，请检查配置
        echo 提示：请确认 MySQL 服务已启动，密码是否正确（默认：123456）
    )
) else (
    echo [WARNING] 未找到 MySQL 客户端，跳过 MySQL 初始化
    echo 提示：可以安装 MySQL Workbench 或使用 XAMPP/WAMP
)

echo.
echo ====================================

REM ====================================
REM 2. MongoDB 初始化
REM ====================================
echo [2/3] 检查 MongoDB 配置...

where mongosh >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] MongoDB 客户端已安装

    REM 测试连接
    mongosh "mongodb://localhost:27017" --eval "db.adminCommand('ping')" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] MongoDB 连接成功

        REM 执行初始化脚本
        if exist scripts\setup_mongodb.js (
            echo 执行 MongoDB 初始化...
            mongosh "mongodb://localhost:27017/outdoor_planner" scripts\setup_mongodb.js
            echo [OK] MongoDB 初始化完成
        )
    ) else (
        echo [WARNING] MongoDB 未运行
        echo 启动方法：
        echo   - Windows 服务: 在服务管理器中启动 MongoDB
        echo   - Docker: docker-compose up -d mongodb
    )
) else (
    echo [WARNING] 未找到 MongoDB 客户端
    echo 下载地址: https://www.mongodb.com/try/download/community
)

echo.
echo ====================================

REM ====================================
REM 3. Python 依赖检查
REM ====================================
echo [3/3] 检查 Python 依赖...

if exist backend (
    cd backend

    REM 检查虚拟环境
    if exist venv (
        echo [OK] 虚拟环境已存在
    ) else (
        echo 创建虚拟环境...
        python -m venv venv
        echo [OK] 虚拟环境创建成功
    )

    REM 激活虚拟环境并安装依赖
    call venv\Scripts\activate.bat
    echo 安装 Python 依赖...
    pip install -q -r requirements.txt
    echo [OK] Python 依赖安装完成

    cd ..
)

echo.
echo ====================================
echo 初始化完成！
echo ====================================
echo.
echo 启动开发服务器：
echo   cd backend ^&^& python main.py
echo.
echo 或使用 Docker：
echo   docker-compose up -d
echo.
echo 访问地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.

pause
