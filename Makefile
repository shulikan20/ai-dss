# Requires: docker, docker-compose, python 3.11+, ollama, node 18+
#
# Quick start:
#   make install
#   make db-up
#   make migrate
#   make dev
#   make start

.DEFAULT_GOAL := help
COMPOSE_FILE := docker-compose.dev.yml
TEST_DB_URL := postgresql://aidss:aidss@localhost:5433/aidss_test

.PHONY: help
help:
	@echo ""
	@echo "  AI-DSS development targets"
	@echo ""
	@echo "  Setup"
	@echo "    make install        Install Python + Node dependencies"
	@echo ""
	@echo "  Database"
	@echo "    make db-up          Start PostgreSQL (dev + test containers)"
	@echo "    make db-down        Stop and remove containers (keeps dev volume)"
	@echo "    make db-reset       Wipe dev volume and restart fresh"
	@echo "    make migrate        Apply Alembic migrations (idempotent)"
	@echo ""
	@echo "  Run"
	@echo "    make dev            Start FastAPI in reload mode (port 8000)"
	@echo "    make frontend       Start React/Vite dev server (port 5173)"
	@echo "    make start          db-up + migrate + dev  [foreground]"
	@echo ""
	@echo "  Test"
	@echo "    make test           Run Phase 2 pytest suite against test DB"
	@echo "    make test-all       Run all Python tests"
	@echo "    make test-frontend  Run Vitest suite"
	@echo "    make verify         End-to-end smoke test (verify_phase2.py)"
	@echo ""
	@echo "  Catalog"
	@echo "    make catalog        Run extend_catalog.py → 30 capabilities"
	@echo ""

.PHONY: install
install:
	pip install -r requirements.txt -r requirements-dev.txt
	cd frontend && npm install

.PHONY: db-up
db-up:
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "Waiting for postgres to be healthy..."
	@docker-compose -f $(COMPOSE_FILE) ps

.PHONY: db-down
db-down:
	docker-compose -f $(COMPOSE_FILE) down

.PHONY: db-reset
db-reset:
	docker-compose -f $(COMPOSE_FILE) down -v
	docker-compose -f $(COMPOSE_FILE) up -d

.PHONY: migrate
migrate:
	alembic upgrade head

.PHONY: dev
dev:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: frontend
frontend:
	cd frontend && npm run dev

.PHONY: start
start: db-up migrate dev

.PHONY: test
test:
	TEST_DATABASE_URL=$(TEST_DB_URL) pytest tests/phase2/ -v

.PHONY: test-all
test-all:
	TEST_DATABASE_URL=$(TEST_DB_URL) pytest tests/ -v

.PHONY: test-frontend
test-frontend:
	cd frontend && npm run test:run

.PHONY: verify
verify:
	python scripts/verify_phase2.py

.PHONY: catalog
catalog:
	python scripts/extend_catalog.py
