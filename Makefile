# Makefile for Outdoor Agent Planner
# Docker Compose 部署方式

.PHONY: help start stop restart logs status clean build \
        test lint typecheck install \
        dev-frontend dev-backend \
        backup health shell

# Default target
help:
	@echo "户外活动智能规划系统 - Docker 部署"
	@echo ""
	@echo "快速启动:"
	@echo "  make start          - 启动所有服务 (含前端)"
	@echo "  make stop           - 停止所有服务"
	@echo "  make restart        - 重启服务"
	@echo "  make logs           - 查看所有日志"
	@echo "  make status         - 查看服务状态"
	@echo ""
	@echo "开发模式:"
	@echo "  make dev-frontend   - 启动前端开发服务器"
	@echo "  make dev-backend    - 启动后端开发服务器"
	@echo "  make dev            - 启动完整开发环境"
	@echo ""
	@echo "开发测试:"
	@echo "  make test           - 运行测试"
	@echo "  make lint           - 代码检查"
	@echo "  make typecheck      - 类型检查"
	@echo ""
	@echo "构建清理:"
	@echo "  make build          - 重新构建镜像"
	@echo "  make clean          - 清理容器和数据卷"
	@echo ""
	@echo "运维工具:"
	@echo "  make backup         - 备份数据库"
	@echo "  make health         - 健康检查"
	@echo "  make shell          - 进入后端容器"
	@echo ""
	@echo "访问地址:"
	@echo "  前端: http://localhost"
	@echo "  后端: http://localhost:8000"
	@echo "  API文档: http://localhost:8000/docs"

# ============================================
# Docker Commands
# ============================================

start:
	@echo "🚀 启动所有服务..."
	docker-compose up -d
	@echo ""
	@echo "✅ 服务已启动!"
	@echo "🌐 前端: http://localhost"
	@echo "📡 后端: http://localhost:8000"
	@echo "📚 文档: http://localhost:8000/docs"

stop:
	@echo "⏹️  停止所有服务..."
	docker-compose down

restart:
	@echo "🔄 重启服务..."
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

status:
	@docker-compose ps

# 仅启动数据库
db:
	@echo "🗄️  启动数据库服务..."
	docker-compose up -d mysql mongodb

# 仅启动后端
backend-only:
	@echo "🔧 启动后端服务..."
	docker-compose up -d backend mysql mongodb

# ============================================
# Development Commands
# ============================================

dev:
	@echo "🛠️  启动完整开发环境..."
	@make db
	@echo "⏳ 等待数据库启动..."
	@sleep 10
	@make dev-backend
	@make dev-frontend

dev-frontend:
	@echo "🎨 启动前端开发服务器..."
	@cd frontend && npm run dev

dev-backend:
	@echo "🐍 启动后端开发服务器..."
	@cd backend && python main.py

# ============================================
# Build Commands
# ============================================

build:
	@echo "🔨 重新构建镜像..."
	docker-compose build --no-cache

rebuild: build

# ============================================
# Testing Commands
# ============================================

# 在 Docker 容器中运行测试
test:
	@echo "🧪 运行测试..."
	docker-compose exec backend pytest test/ -v

# 代码检查
lint:
	@echo "🔍 代码检查..."
	@cd frontend && npm run lint
	@docker-compose exec backend ruff check .

# 类型检查
typecheck:
	@echo "📝 TypeScript 类型检查..."
	@cd frontend && npm run lint
	@docker-compose exec backend mypy src/ --strict

# ============================================
# Clean Commands
# ============================================

clean:
	@echo "🧹 清理容器..."
	docker-compose down

# 完全清理（包括数据）
clean-all:
	@echo "🧹 清理容器和数据卷..."
	docker-compose down -v
	docker volume rm outdoor_mongodb_data outdoor_mongodb_config outdoor_mysql_data 2>/dev/null || true

# ============================================
# Backup Commands
# ============================================

backup:
	@echo "💾 备份数据库..."
	@mkdir -p backups
	docker exec outdoor-mysql sh -c 'exec mysqldump --all-databases -uroot -p"$${MYSQL_ROOT_PASSWORD:-123456}"' > backups/mysql_backup_$$(date +%Y%m%d_%H%M%S).sql
	docker exec outdoor-mongodb mongodump --archive=/data/backup --db=outdoor_planner
	docker cp outdoor-mongodb:/data/backup.archive backups/mongodb_backup_$$(date +%Y%m%d_%H%M%S).archive
	@echo "✅ 备份完成: backups/"

# ============================================
# Health Check
# ============================================

health:
	@echo "🔍 检查服务健康状态..."
	@curl -f http://localhost:8000/health && echo "✅ 后端健康" || echo "❌ 后端异常"
	@curl -f http://localhost/ && echo "✅ 前端健康" || echo "❌ 前端异常"

# ============================================
# Shell Access
# ============================================

shell:
	@echo "🐚 进入后端容器..."
	docker-compose exec backend bash

shell-mysql:
	@echo "🗄️  进入 MySQL 容器..."
	docker-compose exec mysql bash

shell-mongodb:
	@echo "🍃 进入 MongoDB 容器..."
	docker-compose exec mongodb mongosh

# ============================================
# Install Commands
# ============================================

install:
	@echo "📦 安装依赖..."
	@cd backend && pip install -r requirements.txt
	@cd frontend && npm install
	@echo "✅ 依赖安装完成"

install-backend:
	@echo "📦 安装后端依赖..."
	@cd backend && pip install -r requirements.txt

install-frontend:
	@echo "📦 安装前端依赖..."
	@cd frontend && npm install
