#!/bin/bash
# ====================================
# 户外活动规划助手 - 本地开发环境初始化脚本
# ====================================
# 用途：在本地开发环境中初始化数据库
# ====================================

set -e

echo "===================================="
echo "户外活动规划助手 - 本地环境初始化"
echo "===================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ====================================
# 1. MySQL 初始化
# ====================================
echo -e "\n${YELLOW}[1/3] 检查 MySQL 配置...${NC}"

# 读取 MySQL 配置
if [ -f .env ]; then
    source .env
else
    echo -e "${RED}错误: 未找到 .env 文件${NC}"
    exit 1
fi

# 检查 MySQL 连接
if command -v mysql &> /dev/null; then
    echo -e "${GREEN}✓ MySQL 客户端已安装${NC}"

    # 测试连接
    if mysql -h"${MYSQL_HOST:-localhost}" -P"${MYSQL_PORT:-3306}" -u"${MYSQL_USER:-root}" -e "SELECT 1" &> /dev/null; then
        echo -e "${GREEN}✓ MySQL 连接成功${NC}"

        # 创建数据库
        echo "创建数据库 ${MYSQL_DATABASE:-outdoor_planner}..."
        mysql -h"${MYSQL_HOST:-localhost}" -P"${MYSQL_PORT:-3306}" -u"${MYSQL_USER:-root}" << EOF
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE:-outdoor_planner} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF
        echo -e "${GREEN}✓ 数据库创建成功${NC}"

        # 执行初始化脚本
        if [ -f scripts/init_mysql.sql ]; then
            echo "执行数据库表结构初始化..."
            mysql -h"${MYSQL_HOST:-localhost}" -P"${MYSQL_PORT:-3306}" -u"${MYSQL_USER:-root}" "${MYSQL_DATABASE:-outdoor_planner}" < scripts/init_mysql.sql
            echo -e "${GREEN}✓ 表结构初始化完成${NC}"
        fi
    else
        echo -e "${RED}✗ MySQL 连接失败，请检查配置${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 未找到 MySQL 客户端，跳过 MySQL 初始化${NC}"
fi

# ====================================
# 2. MongoDB 初始化
# ====================================
echo -e "\n${YELLOW}[2/3] 检查 MongoDB 配置...${NC}"

if command -v mongosh &> /dev/null; then
    echo -e "${GREEN}✓ MongoDB 客户端已安装${NC}"

    # 测试连接
    if mongosh "mongodb://${MONGO_HOST:-localhost}:${MONGO_PORT:-27017}" --eval "db.adminCommand('ping')" &> /dev/null; then
        echo -e "${GREEN}✓ MongoDB 连接成功${NC}"

        # 执行初始化脚本
        if [ -f scripts/setup_mongodb.js ]; then
            echo "执行 MongoDB 初始化..."
            mongosh "mongodb://${MONGO_HOST:-localhost}:${MONGO_PORT:-27017}/${MONGO_DATABASE:-outdoor_planner}" scripts/setup_mongodb.js
            echo -e "${GREEN}✓ MongoDB 初始化完成${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ MongoDB 未运行，请先启动 MongoDB 服务${NC}"
        echo "   Windows: 在服务中启动 MongoDB"
        echo "   或使用 Docker: docker-compose up -d mongodb"
    fi
else
    echo -e "${YELLOW}⚠ 未找到 MongoDB 客户端${NC}"
    echo "   安装方法: https://www.mongodb.com/try/download/community"
fi

# ====================================
# 3. Python 依赖检查
# ====================================
echo -e "\n${YELLOW}[3/3] 检查 Python 依赖...${NC}"

if [ -d "backend" ]; then
    cd backend

    # 检查虚拟环境
    if [ -d "venv" ]; then
        echo -e "${GREEN}✓ 虚拟环境已存在${NC}"
    else
        echo "创建虚拟环境..."
        python -m venv venv
        echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
    fi

    # 激活虚拟环境
    source venv/bin/activate || source venv/Scripts/activate

    # 安装依赖
    echo "安装 Python 依赖..."
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Python 依赖安装完成${NC}"

    cd ..
fi

# ====================================
# 完成
# ====================================
echo -e "\n${GREEN}====================================${NC}"
echo -e "${GREEN}初始化完成！${NC}"
echo -e "${GREEN}====================================${NC}"
echo -e "\n启动开发服务器："
echo -e "  ${YELLOW}cd backend && python main.py${NC}"
echo -e "\n或使用 Docker："
echo -e "  ${YELLOW}docker-compose up -d${NC}"
echo -e "\n访问地址: http://localhost:8000"
echo -e "API 文档: http://localhost:8000/docs"
