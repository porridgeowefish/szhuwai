.PHONY: dev-backend dev-frontend test lint build start stop logs

PYTHON ?= python

dev-backend:
	cd backend && $(PYTHON) main.py

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && $(PYTHON) -m pytest test/ -v

lint:
	cd backend && ruff check src main.py test
	cd backend && mypy --strict src/schemas/two_bulu.py src/services/two_bulu_service.py src/services/two_bulu_browser_service.py
	cd frontend && npm run lint

build:
	cd frontend && npm run build

start:
	docker compose up --build -d

stop:
	docker compose down

logs:
	docker compose logs -f
