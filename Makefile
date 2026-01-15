# ============================================
# MarQed AI Agent Platform - Makefile
# Version: 1.0.0 (Restructure Week 145)
# ============================================
#
# Usage: make <target>
# Run 'make help' for available commands
#
# ============================================

.PHONY: help start stop status dev setup \
        test test-unit test-int test-e2e coverage smoke \
        lint ci build deploy-staging deploy-prod rollback \
        migrate db-reset db-backup db-shell \
        clean deps docs version

# Default target
.DEFAULT_GOAL := help

# Project paths
PROJECT_ROOT := $(shell pwd)
BACKEND_DIR := $(PROJECT_ROOT)/backend
SCRIPTS_DIR := $(PROJECT_ROOT)/scripts
VENV := $(BACKEND_DIR)/.venv/bin

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# ============================================
# HELP
# ============================================

help:
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  MarQed AI Agent Platform - Available Commands$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make start          Start all services (Docker + API)"
	@echo "  make stop           Stop all services"
	@echo "  make status         Check service health status"
	@echo "  make dev            Start in development mode (hot reload)"
	@echo "  make setup          Initial project setup (venv, deps, db)"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-int       Run integration tests only"
	@echo "  make test-e2e       Run end-to-end tests"
	@echo "  make coverage       Run tests with coverage report"
	@echo "  make smoke          Quick smoke test (health check)"
	@echo ""
	@echo "$(GREEN)CI/CD:$(NC)"
	@echo "  make lint           Run linters (ruff, mypy)"
	@echo "  make ci             Full CI validation pipeline"
	@echo "  make build          Build Docker images"
	@echo "  make deploy-staging Deploy to staging environment"
	@echo "  make deploy-prod    Deploy to production (requires confirm)"
	@echo "  make rollback       Rollback last deployment"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make migrate        Run database migrations"
	@echo "  make db-reset       Reset database (drop + recreate)"
	@echo "  make db-backup      Create database backup"
	@echo "  make db-shell       Open database shell (psql)"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make clean          Clean caches and temporary files"
	@echo "  make deps           Update Python dependencies"
	@echo "  make docs           Generate API documentation"
	@echo "  make version        Show current version"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make setup && make start    # First time setup"
	@echo "  make test coverage          # Run tests with coverage"
	@echo "  make ci deploy-staging      # CI + deploy to staging"
	@echo ""

# ============================================
# DEVELOPMENT
# ============================================

start:
	@echo "$(BLUE)Starting MarQed AI Platform...$(NC)"
	@if [ -f "$(SCRIPTS_DIR)/start.sh" ]; then \
		$(SCRIPTS_DIR)/start.sh; \
	else \
		cd $(BACKEND_DIR) && \
		docker-compose up -d db chromadb && \
		sleep 3 && \
		source .venv/bin/activate && \
		uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload; \
	fi

start-bg:
	@echo "$(BLUE)Starting MarQed AI Platform (background)...$(NC)"
	@$(SCRIPTS_DIR)/start.sh --no-browser > /dev/null 2>&1 || true
	@echo "$(GREEN)Services starting in background. Check: curl http://localhost:8000/api/health$(NC)"

stop:
	@echo "$(BLUE)Stopping MarQed AI Platform...$(NC)"
	@if [ -f "$(SCRIPTS_DIR)/stop.sh" ]; then \
		$(SCRIPTS_DIR)/stop.sh; \
	else \
		cd $(BACKEND_DIR) && \
		pkill -f "uvicorn app.main:app" 2>/dev/null || true && \
		docker-compose down; \
	fi

status:
	@echo "$(BLUE)Checking service status...$(NC)"
	@echo ""
	@echo "$(GREEN)Docker Services:$(NC)"
	@cd $(BACKEND_DIR) && docker-compose ps 2>/dev/null || echo "Docker not running"
	@echo ""
	@echo "$(GREEN)API Health:$(NC)"
	@curl -s http://localhost:8000/api/health 2>/dev/null | head -c 200 || echo "API not responding"
	@echo ""

dev:
	@echo "$(BLUE)Starting development server with hot reload...$(NC)"
	@cd $(BACKEND_DIR) && \
		source .venv/bin/activate && \
		uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

setup:
	@echo "$(BLUE)Setting up MarQed AI Platform...$(NC)"
	@echo ""
	@echo "$(YELLOW)[1/5]$(NC) Creating Python virtual environment..."
	@cd $(BACKEND_DIR) && python3 -m venv .venv
	@echo "$(YELLOW)[2/5]$(NC) Installing Python dependencies..."
	@cd $(BACKEND_DIR) && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt
	@echo "$(YELLOW)[3/5]$(NC) Starting database containers..."
	@cd $(BACKEND_DIR) && docker-compose up -d db chromadb
	@echo "$(YELLOW)[4/5]$(NC) Waiting for PostgreSQL..."
	@sleep 5
	@echo "$(YELLOW)[5/5]$(NC) Running database migrations..."
	@cd $(BACKEND_DIR) && .venv/bin/alembic upgrade head
	@echo ""
	@echo "$(GREEN)Setup complete! Run 'make start' to start the platform.$(NC)"

# ============================================
# TESTING
# ============================================

test:
	@echo "$(BLUE)Running all tests...$(NC)"
	@cd $(BACKEND_DIR) && \
		source .venv/bin/activate && \
		python -m pytest tests/ -v --tb=short

test-unit:
	@echo "$(BLUE)Running unit tests...$(NC)"
	@cd $(BACKEND_DIR) && \
		source .venv/bin/activate && \
		python -m pytest tests/ -v --tb=short -m "not integration and not e2e"

test-int:
	@echo "$(BLUE)Running integration tests...$(NC)"
	@cd $(BACKEND_DIR) && \
		source .venv/bin/activate && \
		python -m pytest tests/ -v --tb=short -m "integration"

test-e2e:
	@echo "$(BLUE)Running end-to-end tests...$(NC)"
	@cd $(BACKEND_DIR) && \
		source .venv/bin/activate && \
		python -m pytest tests/ -v --tb=short -m "e2e"

coverage:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@cd $(BACKEND_DIR) && \
		source .venv/bin/activate && \
		python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "$(GREEN)Coverage report: $(BACKEND_DIR)/htmlcov/index.html$(NC)"

smoke:
	@echo "$(BLUE)Running smoke tests...$(NC)"
	@echo ""
	@echo "Checking API health..."
	@curl -sf http://localhost:8000/api/health > /dev/null && echo "$(GREEN)API: OK$(NC)" || echo "$(RED)API: FAIL$(NC)"
	@echo "Checking database..."
	@cd $(BACKEND_DIR) && docker-compose exec -T db pg_isready -U user > /dev/null 2>&1 && echo "$(GREEN)Database: OK$(NC)" || echo "$(RED)Database: FAIL$(NC)"
	@echo "Checking ChromaDB..."
	@curl -sf http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1 && echo "$(GREEN)ChromaDB: OK$(NC)" || echo "$(RED)ChromaDB: FAIL$(NC)"

# ============================================
# CI/CD
# ============================================

lint:
	@echo "$(BLUE)Running linters...$(NC)"
	@cd $(BACKEND_DIR) && \
		source .venv/bin/activate && \
		echo "Running ruff..." && \
		ruff check app/ --fix || true && \
		echo "Running mypy..." && \
		mypy app/ --ignore-missing-imports || true
	@echo "$(GREEN)Linting complete$(NC)"

ci:
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Running Full CI Validation$(NC)"
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@echo ""
	@if [ -f "$(SCRIPTS_DIR)/cicd/ci/validate.sh" ]; then \
		$(SCRIPTS_DIR)/cicd/ci/validate.sh; \
	else \
		$(MAKE) lint && \
		$(MAKE) test && \
		echo "$(GREEN)CI Validation PASSED$(NC)"; \
	fi

build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	@if [ -f "$(SCRIPTS_DIR)/cicd/docker/build.sh" ]; then \
		$(SCRIPTS_DIR)/cicd/docker/build.sh; \
	else \
		cd $(BACKEND_DIR) && \
		docker-compose build; \
	fi

deploy-staging:
	@echo "$(BLUE)Deploying to staging...$(NC)"
	@if [ -f "$(SCRIPTS_DIR)/cicd/cd/deploy-staging.sh" ]; then \
		$(SCRIPTS_DIR)/cicd/cd/deploy-staging.sh; \
	else \
		echo "$(RED)Deploy script not found. Create scripts/cicd/cd/deploy-staging.sh$(NC)"; \
		exit 1; \
	fi

deploy-prod:
	@echo "$(YELLOW)════════════════════════════════════════$(NC)"
	@echo "$(YELLOW)  PRODUCTION DEPLOYMENT$(NC)"
	@echo "$(YELLOW)════════════════════════════════════════$(NC)"
	@echo ""
	@if [ -f "$(SCRIPTS_DIR)/cicd/cd/deploy-prod.sh" ]; then \
		$(SCRIPTS_DIR)/cicd/cd/deploy-prod.sh; \
	else \
		echo "$(RED)Deploy script not found. Create scripts/cicd/cd/deploy-prod.sh$(NC)"; \
		exit 1; \
	fi

rollback:
	@echo "$(YELLOW)Rolling back last deployment...$(NC)"
	@if [ -f "$(SCRIPTS_DIR)/cicd/cd/rollback.sh" ]; then \
		$(SCRIPTS_DIR)/cicd/cd/rollback.sh; \
	else \
		echo "$(RED)Rollback script not found. Create scripts/cicd/cd/rollback.sh$(NC)"; \
		exit 1; \
	fi

# ============================================
# DATABASE
# ============================================

migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	@cd $(BACKEND_DIR) && \
		source .venv/bin/activate && \
		alembic upgrade head
	@echo "$(GREEN)Migrations complete$(NC)"

db-reset:
	@echo "$(YELLOW)Resetting database...$(NC)"
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Type 'reset' to confirm: " confirm && \
	if [ "$$confirm" = "reset" ]; then \
		cd $(BACKEND_DIR) && \
		docker-compose down -v && \
		docker-compose up -d db && \
		sleep 5 && \
		source .venv/bin/activate && \
		alembic upgrade head && \
		echo "$(GREEN)Database reset complete$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

db-backup:
	@echo "$(BLUE)Creating database backup...$(NC)"
	@if [ -f "$(SCRIPTS_DIR)/db/backup.sh" ]; then \
		$(SCRIPTS_DIR)/db/backup.sh; \
	else \
		BACKUP_FILE="backup_$$(date +%Y%m%d_%H%M%S).sql" && \
		cd $(BACKEND_DIR) && \
		docker-compose exec -T db pg_dump -U user project_manager > $$BACKUP_FILE && \
		echo "$(GREEN)Backup created: $$BACKUP_FILE$(NC)"; \
	fi

db-shell:
	@echo "$(BLUE)Opening database shell...$(NC)"
	@cd $(BACKEND_DIR) && \
		docker-compose exec db psql -U user -d project_manager

# ============================================
# UTILITIES
# ============================================

clean:
	@echo "$(BLUE)Cleaning caches and temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete$(NC)"

deps:
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@cd $(BACKEND_DIR) && \
		source .venv/bin/activate && \
		pip install --upgrade pip && \
		pip install -r requirements.txt
	@echo "$(GREEN)Dependencies updated$(NC)"

docs:
	@echo "$(BLUE)Generating API documentation...$(NC)"
	@echo "API docs available at: http://localhost:8000/docs"
	@echo "ReDoc available at: http://localhost:8000/redoc"

version:
	@if [ -f "VERSION" ]; then \
		echo "$(BLUE)MarQed AI Platform v$$(cat VERSION)$(NC)"; \
	else \
		echo "$(BLUE)MarQed AI Platform (version not set)$(NC)"; \
	fi
	@echo ""
	@echo "Components:"
	@echo "  - API Endpoints: 700+"
	@echo "  - Database Tables: 198+"
	@echo "  - Core Agents: 11"
	@echo "  - Dashboards: 32"
