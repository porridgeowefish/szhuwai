# Makefile for Outdoor Agent Planner
# Provides convenient commands for development, testing, and building

.PHONY: help test test-all test-schemas test-api test-integration test-fast \
        lint format type-check clean install \
        run-coverage coverage-html install-deps check-all

# Default target
help:
	@echo "Outdoor Agent Planner - Available Commands:"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make test-all      - Alias for test"
	@echo "  make test-schemas  - Run schema tests only"
	@echo "  make test-api      - Run API tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-fast     - Run fast tests (skip slow)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run linter (ruff check)"
	@echo "  make format        - Format code (ruff format)"
	@echo "  make type-check    - Run type checker (mypy)"
	@echo "  make check-all     - Run all quality checks"
	@echo ""
	@echo "Coverage:"
	@echo "  make run-coverage  - Run tests with coverage"
	@echo "  make coverage-html - Generate HTML coverage report"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install dependencies"
	@echo "  make clean        - Clean cache and build artifacts"
	@echo ""

# Testing commands
test test-all:
	pytest test/ -v

test-schemas:
	pytest test/schemas/ -v

test-api:
	pytest test/api/ -v

test-integration:
	pytest test/integration/ -v -m integration

test-fast:
	pytest test/ -v -m "not slow"

# Code quality commands
lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy schemas/ api/ --strict

check-all: lint format type-check
	@echo ""
	@echo "All checks passed!"

# Coverage commands
run-coverage:
	pytest test/ --cov=schemas --cov=api --cov-report=term --cov-report=html

coverage-html: run-coverage
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Development commands
install:
	pip install -r requirements.txt

clean:
	@echo "Cleaning cache and build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean completed!"
