# Makefile for Outdoor Agent Planner
# Docker Compose 部署方式

.PHONY: help start stop restart logs status clean build \
        test lint typecheck install

# Default target
help:
	@echo "Outdoor Agent Planner - Docker 部署:"
	@echo ""
	@echo "快速启动:"
	@echo "  make start      - 启动所有服务 (数据库 + 后端)"
	@echo "  make stop       - 停止所有服务"
	@echo "  make restart    - 重启服务"
	@echo "  make logs       - 查看日志"
	@echo "  make status     - 查看服务状态"
	@echo ""
	@echo "开发测试:"
	@echo "  make test       - 运行测试"
	@echo "  make lint       - 代码检查"
	@echo "  make typecheck  - 类型检查"
	@echo ""
	@echo "构建清理:"
	@echo "  make build      - 重新构建镜像"
	@echo "  make clean      - 清理容器和数据卷"
	@echo ""
	@echo "访问地址:"
	@echo "  http://localhost:8000"
	@echo "  http://localhost:8000/docs"

# ============================================
# Docker Commands
# ============================================

start:
	@echo "启动所有服务..."
	docker-compose up -d
	@echo ""
	@echo "服务已启动!"
	@echo "API: http://localhost:8000"
	@echo "文档: http://localhost:8000/docs"

stop:
	@echo "停止所有服务..."
	docker-compose down

restart:
	@echo "重启服务..."
	docker-compose restart

logs:
	docker-compose logs -f

status:
	@docker-compose ps

# 仅启动数据库
db:
	docker-compose up -d mysql mongodb

# 仅启动后端
backend-only:
	docker-compose up -d backend

# ============================================
# Build Commands
# ============================================

build:
	@echo "重新构建镜像..."
	docker-compose build --no-cache

rebuild: build

# ============================================
# Development Commands
# ============================================

# 在 Docker 容器中运行测试
test:
	docker-compose exec backend pytest test/ -v

# 代码检查
lint:
	docker-compose exec backend ruff check .

# 类型检查
typecheck:
	docker-compose exec backend mypy src/ --strict

# ============================================
# Clean Commands
# ============================================

clean:
	@echo "清理容器..."
	docker-compose down -v

# 完全清理（包括数据）
clean-all: clean
	@echo "清理数据卷..."
	docker volume rm outdoor_mongodb_data outdoor_mongodb_config outdoor_mysql_data 2>/dev/null || true

# ============================================
# Install Commands
# ============================================

install:
	@echo "安装 Python 依赖 (本地)..."
	cd backend && pip install -r requirements.txt
