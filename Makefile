.PHONY: install dev dev-web dev-api dev-env build test lint clean docker-build docker-run

# Installation
install:
	npm install
	cd apps/api && pip install -r requirements.txt
	cd openenv/compute_market_env && pip install -e .

install-dev:
	npm install
	cd apps/api && pip install -r requirements.txt -r requirements-dev.txt
	cd openenv/compute_market_env && pip install -e ".[dev]"

# Development servers (Node 20+ required for Next.js 16)
NODE20 := /opt/homebrew/opt/node@20/bin

dev:
	@echo "Starting all services..."
	make -j3 dev-web dev-api dev-env

dev-web:
	@[ -d "$(NODE20)" ] && PATH="$(NODE20):$$PATH" npm run dev:web || npm run dev:web

dev-api:
	cd apps/api && python3 -m uvicorn main:app --reload --port 8000

dev-env:
	cd openenv/compute_market_env && python3 -m uvicorn server.app:app --reload --port 8001

# Build
build:
	npm run build

build-env:
	cd openenv/compute_market_env && docker build -t compute-market-env:latest .

# Testing
test:
	cd apps/api && pytest tests/ -v
	cd openenv/compute_market_env && pytest tests/ -v

test-env:
	cd openenv/compute_market_env && pytest tests/ -v --cov=server

validate-trajectory:
	python scripts/validate_trajectory_export.py --no-http

# Linting
lint:
	npm run lint
	cd apps/api && ruff check .
	cd openenv/compute_market_env && ruff check .

lint-fix:
	npm run lint -- --fix
	cd apps/api && ruff check . --fix
	cd openenv/compute_market_env && ruff check . --fix

# Docker
docker-build:
	docker build -t compute-market-env:latest ./openenv/compute_market_env

docker-run:
	docker run -p 8001:8001 compute-market-env:latest

# Clean
clean:
	rm -rf node_modules
	rm -rf apps/web/.next
	rm -rf apps/web/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Demo
demo:
	@echo "🚀 ComputeExchange Demo Mode"
	@echo "1. Starting OpenEnv environment server..."
	@make dev-env &
	@sleep 3
	@echo "2. Starting API server..."
	@make dev-api &
	@sleep 2
	@echo "3. Starting frontend..."
	@make dev-web

# Help
help:
	@echo "ComputeExchange - OpenEnv Multi-Agent Compute Marketplace"
	@echo ""
	@echo "Usage:"
	@echo "  make install     - Install all dependencies"
	@echo "  make dev         - Start all development servers"
	@echo "  make dev-web     - Start Next.js frontend only"
	@echo "  make dev-api     - Start FastAPI backend only"
	@echo "  make dev-env     - Start OpenEnv environment server only"
	@echo "  make build       - Build for production"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run linters"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make docker-build - Build Docker image for OpenEnv"
	@echo "  make demo        - Start demo mode"
	@echo "  make validate-trajectory - Validate RL trajectory export schema"
