# Makefile for Outdoor Agent Planner
# Provides convenient commands for development, testing, and building

.PHONY: help test test-all test-schemas test-api test-integration test-fast \
        lint format type-check clean install check-all \
        frontend-dev frontend-build frontend-lint \
        docker-up docker-down docker-build

# Default target
help:
	@echo "Outdoor Agent Planner - Available Commands:"
	@echo ""
	@echo "Backend (Python/FastAPI):"
	@echo "  make test          - Run all backend tests"
	@echo "  make test-schemas  - Run schema tests only"
	@echo "  make test-api      - Run API tests only"
	@echo "  make lint          - Run linter (ruff check)"
	@echo "  make format        - Format code (ruff format)"
	@echo "  make type-check    - Run type checker (mypy)"
	@echo "  make check-all     - Run all quality checks"
	@echo ""
	@echo "Frontend (React/TypeScript):"
	@echo "  make frontend-dev     - Start frontend dev server"
	@echo "  make frontend-build   - Build frontend for production"
	@echo "  make frontend-lint    - Run frontend linter"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up     - Start all services with docker-compose"
	@echo "  make docker-down   - Stop all services"
	@echo "  make docker-build  - Rebuild all Docker images"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install backend dependencies"
	@echo "  make clean         - Clean cache and build artifacts"
	@echo ""

# ============================================
# Backend Commands
# ============================================

# Testing commands
test test-all:
	cd backend && pytest test/ -v

test-schemas:
	cd backend && pytest test/schemas/ -v

test-api:
	cd backend && pytest test/api/ -v

test-integration:
	cd backend && pytest test/integration/ -v -m integration

test-fast:
	cd backend && pytest test/ -v -m "not slow"

# Code quality commands
lint:
	cd backend && ruff check .

format:
	cd backend && ruff format .

type-check:
	cd backend && mypy src/ --strict

check-all: lint format type-check
	@echo ""
	@echo "All backend checks passed!"

# Coverage commands
run-coverage:
	cd backend && pytest test/ --cov=src --cov-report=term --cov-report=html

coverage-html: run-coverage
	@echo ""
	@echo "Coverage report generated in backend/htmlcov/index.html"

# Development commands
install:
	cd backend && pip install -r requirements.txt

# ============================================
# Frontend Commands
# ============================================

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

frontend-install:
	cd frontend && npm install

# ============================================
# Docker Commands
# ============================================

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build --no-cache

docker-logs:
	docker-compose logs -f

# ============================================
# Clean Commands
# ============================================

clean:
	@echo "Cleaning cache and build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean completed!"
