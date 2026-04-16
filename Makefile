# Makefile for Outdoor Agent Planner
#
# 两种运行模式:
#   本地开发:  make dev-up / make dev-run / make dev-stop
#   全 Docker: make start / make stop / make build
#
# 中间件: MySQL + MongoDB + Redis + PostgreSQL(PostGIS)

.PHONY: help \
        dev-up dev-run dev-frontend dev-stop dev-status dev-test dev \
        start stop restart logs status build clean clean-all \
        test lint health shell backup

PYTHON ?= python
DOCKER_COMPOSE := docker-compose

# ============================================
# 本地开发模式 (推荐)
# ============================================

help:
	@echo "Outdoor Agent Planner"
	@echo ""
	@echo "本地开发:"
	@echo "  make dev-up       启动中间件容器"
	@echo "  make dev-run      启动后端 (本地 Python)"
	@echo "  make dev-frontend 启动前端 (Vite)"
	@echo "  make dev          启动完整开发环境"
	@echo "  make dev-stop     停止所有服务"
	@echo "  make dev-status   检查状态"
	@echo "  make dev-test     运行测试"
	@echo ""
	@echo "全 Docker 部署:"
	@echo "  make start        构建并启动全部容器"
	@echo "  make stop         停止全部容器"
	@echo "  make build        重新构建镜像"
	@echo "  make clean        清理容器和数据卷"
	@echo ""
	@echo "访问地址:"
	@echo "  后端:  http://localhost:8000"
	@echo "  前端:  http://localhost:5173 (dev) / http://localhost (docker)"
	@echo "  文档:  http://localhost:8000/docs"

# 仅启动中间件
dev-up:
	@echo "启动中间件..."
	$(DOCKER_COMPOSE) up -d mysql mongodb redis postgres
	@echo "等待健康检查..."
	@sleep 5
	@$(DOCKER_COMPOSE) ps

# 启动后端 (本地)
dev-run:
	@cd backend && MYSQL_HOST=localhost MYSQL_PORT=3307 MONGO_HOST=localhost REDIS_HOST=localhost $(PYTHON) main.py

# 启动前端
dev-frontend:
	@cd frontend && npm run dev

# 启动完整开发环境
dev: dev-up
	@echo "等待中间件就绪..."
	@sleep 8
	@echo "启动后端和前端..."
	@make dev-run & make dev-frontend

# 停止
dev-stop:
	@echo "停止中间件容器..."
	$(DOCKER_COMPOSE) down

# 状态
dev-status:
	@echo "=== Docker 容器 ==="
	@docker ps -a --filter "name=outdoor" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker 未运行"
	@echo ""
	@echo "=== 后端 ==="
	@curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "后端 :8000 - OK" || echo "后端 :8000 - 未响应"
	@echo ""
	@echo "=== 前端 ==="
	@curl -s http://localhost:5173 > /dev/null 2>&1 && echo "前端 :5173 - OK" || echo "前端 :5173 - 未响应"

# 测试
dev-test:
	@cd backend && $(PYTHON) -m pytest test/ --ignore=test/integration -v --tb=short

# ============================================
# 全 Docker 部署模式
# ============================================

start:
	@echo "构建并启动全部服务..."
	$(DOCKER_COMPOSE) up -d --build
	@echo ""
	@echo "前端: http://localhost"
	@echo "后端: http://localhost:8000"

stop:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) restart

logs:
	$(DOCKER_COMPOSE) logs -f

status:
	@$(DOCKER_COMPOSE) ps

build:
	$(DOCKER_COMPOSE) build --no-cache

clean:
	$(DOCKER_COMPOSE) down

clean-all:
	$(DOCKER_COMPOSE) down -v
	docker volume rm outdoor_mongodb_data outdoor_mongodb_config outdoor_mysql_data outdoor_redis_data outdoor_postgres_data 2>/dev/null || true

# ============================================
# 测试 / 检查
# ============================================

test:
	@cd backend && $(PYTHON) -m pytest test/ -v

lint:
	@cd frontend && npm run lint
	@cd backend && ruff check src/

health:
	@curl -sf http://localhost:8000/health && echo " OK" || echo "后端异常"
	@curl -sf http://localhost/ > /dev/null && echo "前端 OK" || echo "前端异常"

shell:
	$(DOCKER_COMPOSE) exec backend bash

backup:
	@mkdir -p backups
	docker exec outdoor-mysql sh -c 'exec mysqldump --all-databases -uroot -p"$${MYSQL_ROOT_PASSWORD:-123456}"' > backups/mysql_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "备份完成: backups/"
