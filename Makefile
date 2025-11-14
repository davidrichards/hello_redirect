.PHONY: help clean lint build docker-build docker-up docker-down docker-logs test-e2e

# Default target
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ''
	@echo 'Environment:'

# Code quality
lint: ## Run linting
	@echo "Running ruff (Python linter)..."
	ruff check src/ tests/

# Build and deployment
build: ## Build the package
	python -m build

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker commands
docker-build: ## Build Docker images
	@echo "Building Docker images..."
	docker-compose build

docker-up: ## Start the services with docker-compose
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started. Gateway: http://localhost:8000, Runtime: http://localhost:8001"

docker-down: ## Stop the services
	@echo "Stopping services..."
	docker-compose down

docker-logs: ## View logs from all services
	docker-compose logs -f

docker-restart: docker-down docker-up ## Restart all services

# Testing
test-e2e: ## Run end-to-end test
	@echo "Running end-to-end test..."
	@echo "Testing gateway health..."
	curl -f http://localhost:8000/health || (echo "Gateway health check failed" && exit 1)
	@echo "Testing runtime health..."
	curl -f http://localhost:8001/health || (echo "Runtime health check failed" && exit 1)
	@echo "Testing full redirect flow..."
	python test_e2e.py

demo: ## Run interactive demo of the complete flow
	@echo "Running interactive demo..."
	python demo.py

# Development workflow
dev-setup: docker-build docker-up test-e2e ## Set up development environment and run tests
	@echo "Development environment ready and tested!"
	@echo "Gateway: http://localhost:8000"
	@echo "Runtime: http://localhost:8001"
	@echo "Try visiting: http://localhost:8000/"

dev-reset: docker-down clean docker-build docker-up ## Complete reset for development

