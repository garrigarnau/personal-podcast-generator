# ==============================================================================
# Personal Podcast Generator - Makefile
# ==============================================================================
# Convenient commands for Docker management
#
# Usage:
#   make help           Show this help message
#   make deploy         Deploy production services
#   make dev            Start development environment
#   make stop           Stop all services
#   make restart        Restart all services
#   make logs           Show logs from all services
#   make clean          Stop and remove all containers and volumes

.PHONY: help deploy dev stop restart logs clean status test migrate backup

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[1;33m
RED    := \033[0;31m
NC     := \033[0m

help: ## Show this help message
	@echo "$(GREEN)Personal Podcast Generator - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

deploy: ## Deploy production services
	@echo "$(GREEN)Deploying production services...$(NC)"
	@./scripts/docker-deploy.sh

dev: ## Start development environment with hot-reload
	@echo "$(GREEN)Starting development environment...$(NC)"
	@./scripts/docker-dev.sh

stop: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)Services stopped$(NC)"

restart: ## Restart all services
	@echo "$(YELLOW)Restarting services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)Services restarted$(NC)"

logs: ## Show logs from all services (Ctrl+C to exit)
	@docker-compose logs -f

logs-backend: ## Show backend logs only
	@docker-compose logs -f backend

logs-frontend: ## Show frontend logs only
	@docker-compose logs -f frontend

logs-db: ## Show database logs only
	@docker-compose logs -f db

status: ## Show status of all services
	@echo "$(GREEN)Service Status:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(GREEN)Health Checks:$(NC)"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "$(RED)Backend not responding$(NC)"
	@curl -s http://localhost:3000/health || echo "$(RED)Frontend not responding$(NC)"

clean: ## Stop and remove all containers, volumes, and images
	@echo "$(RED)WARNING: This will remove all containers, volumes, and data!$(NC)"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@docker-compose down -v
	@echo "$(GREEN)Cleanup complete$(NC)"

build: ## Rebuild all images
	@echo "$(GREEN)Building images...$(NC)"
	@docker-compose build --no-cache
	@echo "$(GREEN)Build complete$(NC)"

build-backend: ## Rebuild backend image only
	@echo "$(GREEN)Building backend image...$(NC)"
	@docker-compose build --no-cache backend
	@echo "$(GREEN)Backend build complete$(NC)"

build-frontend: ## Rebuild frontend image only
	@echo "$(GREEN)Building frontend image...$(NC)"
	@docker-compose build --no-cache frontend
	@echo "$(GREEN)Frontend build complete$(NC)"

shell-backend: ## Open shell in backend container
	@docker-compose exec backend bash

shell-frontend: ## Open shell in frontend container
	@docker-compose exec frontend sh

shell-db: ## Open PostgreSQL shell
	@docker-compose exec db psql -U podcast_user -d podcast_db

migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	@docker-compose exec backend alembic upgrade head
	@echo "$(GREEN)Migrations complete$(NC)"

migrate-create: ## Create a new migration (usage: make migrate-create name="your_migration_name")
	@echo "$(GREEN)Creating new migration: $(name)$(NC)"
	@docker-compose exec backend alembic revision --autogenerate -m "$(name)"

migrate-history: ## Show migration history
	@docker-compose exec backend alembic history

migrate-current: ## Show current migration
	@docker-compose exec backend alembic current

backup: ## Backup database and audio files
	@echo "$(GREEN)Creating backup...$(NC)"
	@mkdir -p backups
	@docker-compose exec -T db pg_dump -U podcast_user podcast_db > backups/db_$$(date +%Y%m%d_%H%M%S).sql
	@docker run --rm -v personal-podcast-generator_audio_files:/data \
		-v $(PWD)/backups:/backup alpine tar czf /backup/audio_$$(date +%Y%m%d_%H%M%S).tar.gz /data
	@echo "$(GREEN)Backup complete in ./backups/$(NC)"

restore-db: ## Restore database from backup (usage: make restore-db file=backups/db_20240504.sql)
	@echo "$(YELLOW)Restoring database from $(file)...$(NC)"
	@cat $(file) | docker-compose exec -T db psql -U podcast_user -d podcast_db
	@echo "$(GREEN)Database restored$(NC)"

test: ## Run tests in backend container
	@echo "$(GREEN)Running tests...$(NC)"
	@docker-compose exec backend pytest -v

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	@docker-compose exec backend pytest --cov=app --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

lint-backend: ## Run linter on backend code
	@echo "$(GREEN)Linting backend...$(NC)"
	@docker-compose exec backend flake8 app/
	@docker-compose exec backend black --check app/

format-backend: ## Format backend code
	@echo "$(GREEN)Formatting backend code...$(NC)"
	@docker-compose exec backend black app/

lint-frontend: ## Run linter on frontend code
	@echo "$(GREEN)Linting frontend...$(NC)"
	@docker-compose exec frontend npm run lint

volumes: ## List all volumes
	@docker volume ls | grep personal-podcast-generator

volume-inspect: ## Inspect volumes usage
	@echo "$(GREEN)Volume Usage:$(NC)"
	@docker system df -v | grep personal-podcast-generator

prune: ## Remove unused Docker resources
	@echo "$(YELLOW)Removing unused Docker resources...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)Prune complete$(NC)"

update: ## Pull latest images and restart
	@echo "$(GREEN)Updating services...$(NC)"
	@docker-compose pull
	@docker-compose up -d
	@echo "$(GREEN)Update complete$(NC)"

.DEFAULT_GOAL := help
