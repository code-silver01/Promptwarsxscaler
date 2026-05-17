# LexGuard One - Development Makefile
# Provides common development tasks and quality checks

.PHONY: help install install-dev test test-fast test-integration test-security test-performance lint format type-check security-scan clean build run dev setup-hooks pre-commit docker-build docker-run

# Default target
help:
	@echo "LexGuard One Development Commands"
	@echo "================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo "  setup-hooks      Setup pre-commit hooks"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev              Start development server"
	@echo "  run              Start production server"
	@echo "  build            Build frontend assets"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test             Run all tests"
	@echo "  test-fast        Run fast tests only"
	@echo "  test-integration Run integration tests"
	@echo "  test-security    Run security tests"
	@echo "  test-performance Run performance tests"
	@echo "  test-coverage    Run tests with coverage report"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  lint             Run all linters"
	@echo "  format           Format code with black and isort"
	@echo "  type-check       Run mypy type checking"
	@echo "  security-scan    Run security scans"
	@echo "  pre-commit       Run pre-commit checks"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean            Clean build artifacts"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"

# Installation
install:
	@echo "Installing production dependencies..."
	pip install -r backend/requirements.txt

install-dev: install
	@echo "Installing development dependencies..."
	pip install -r backend/requirements-dev.txt
	cd frontend && npm install

setup-hooks: install-dev
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg

# Development
dev:
	@echo "Starting development servers..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:5173"
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill %1; kill %2' INT; \
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000 & \
	cd frontend && npm run dev & \
	wait

run:
	@echo "Starting production server..."
	cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

build:
	@echo "Building frontend assets..."
	cd frontend && npm run build

# Testing
test: test-fast test-integration test-security

test-fast:
	@echo "Running fast tests..."
	cd backend && python -m pytest -v -m "not slow and not integration and not security and not performance" --tb=short

test-integration:
	@echo "Running integration tests..."
	cd backend && python -m pytest -v -m "integration" --tb=short

test-security:
	@echo "Running security tests..."
	cd backend && python -m pytest -v -m "security" --tb=short

test-performance:
	@echo "Running performance tests..."
	cd backend && python -m pytest -v -m "performance" --tb=short --benchmark-only

test-coverage:
	@echo "Running tests with coverage..."
	cd backend && python -m pytest --cov=backend --cov-report=html --cov-report=term-missing --cov-report=xml

# Code Quality
lint: lint-python lint-frontend

lint-python:
	@echo "Running Python linters..."
	cd backend && flake8 --config=../pyproject.toml .
	cd backend && mypy --config-file=../pyproject.toml .
	cd backend && bandit -r . -f json -o ../reports/bandit-report.json || true

lint-frontend:
	@echo "Running frontend linters..."
	cd frontend && npm run lint || true

format:
	@echo "Formatting code..."
	cd backend && black .
	cd backend && isort .
	cd frontend && npm run format || true

type-check:
	@echo "Running type checks..."
	cd backend && mypy --config-file=../pyproject.toml .

security-scan:
	@echo "Running security scans..."
	@mkdir -p reports
	cd backend && bandit -r . -f json -o ../reports/bandit-report.json
	cd backend && safety check --json --output ../reports/safety-report.json || true
	@echo "Security reports generated in reports/ directory"

pre-commit:
	@echo "Running pre-commit checks..."
	pre-commit run --all-files

# Quality Gates
quality-gate: lint test-fast security-scan
	@echo "All quality gates passed!"

ci-test: install-dev quality-gate test-integration
	@echo "CI pipeline completed successfully!"

# Utility
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf reports
	@echo "Clean completed!"

# Docker
docker-build:
	@echo "Building Docker image..."
	docker build -t lexguard-one:latest .

docker-run: docker-build
	@echo "Running Docker container..."
	docker run -p 8000:8000 -e PORT=8000 lexguard-one:latest

# Database and Infrastructure
db-setup:
	@echo "Setting up database..."
	# Add database setup commands here

db-migrate:
	@echo "Running database migrations..."
	# Add migration commands here

# Monitoring and Profiling
profile:
	@echo "Running performance profiling..."
	cd backend && python -m cProfile -o ../reports/profile.stats -m pytest -m performance

memory-profile:
	@echo "Running memory profiling..."
	cd backend && python -m memory_profiler main.py

# Documentation
docs:
	@echo "Building documentation..."
	cd backend && sphinx-build -b html docs/ ../docs/_build/

docs-serve:
	@echo "Serving documentation..."
	cd docs/_build && python -m http.server 8080

# Release Management
version-bump-patch:
	@echo "Bumping patch version..."
	# Add version bumping logic here

version-bump-minor:
	@echo "Bumping minor version..."
	# Add version bumping logic here

version-bump-major:
	@echo "Bumping major version..."
	# Add version bumping logic here

# Environment Management
env-create:
	@echo "Creating virtual environment..."
	python -m venv venv
	@echo "Activate with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"

env-update:
	@echo "Updating environment..."
	pip install --upgrade pip
	pip install -r backend/requirements-dev.txt

# Load Testing
load-test:
	@echo "Running load tests..."
	cd backend && locust -f tests/load_test.py --host=http://localhost:8000

# Backup and Restore
backup:
	@echo "Creating backup..."
	# Add backup commands here

restore:
	@echo "Restoring from backup..."
	# Add restore commands here

# Deployment
deploy-staging:
	@echo "Deploying to staging..."
	# Add staging deployment commands here

deploy-production:
	@echo "Deploying to production..."
	# Add production deployment commands here

# Health Checks
health-check:
	@echo "Running health checks..."
	curl -f http://localhost:8000/health || echo "Health check failed"

# Benchmarking
benchmark:
	@echo "Running benchmarks..."
	cd backend && python -m pytest --benchmark-only --benchmark-sort=mean

# Git Hooks and Workflow
git-setup:
	@echo "Setting up git workflow..."
	git config core.hooksPath .githooks
	chmod +x .githooks/*

# All-in-one commands
setup: install-dev setup-hooks
	@echo "Development environment setup complete!"

check: lint test-fast
	@echo "Quick quality check complete!"

full-check: lint test security-scan
	@echo "Full quality check complete!"

# Platform-specific commands
ifeq ($(OS),Windows_NT)
    SHELL := cmd
    RM := del /Q
    MKDIR := mkdir
else
    SHELL := /bin/bash
    RM := rm -f
    MKDIR := mkdir -p
endif

# Help for specific categories
help-test:
	@echo "Testing Commands Help"
	@echo "===================="
	@echo "test-fast:        Quick tests for development feedback"
	@echo "test-integration: End-to-end workflow tests"
	@echo "test-security:    Security vulnerability tests"
	@echo "test-performance: Performance and load tests"
	@echo "test-coverage:    Generate coverage reports"

help-quality:
	@echo "Code Quality Commands Help"
	@echo "========================="
	@echo "lint:         Run all linters (flake8, mypy, bandit)"
	@echo "format:       Auto-format code (black, isort)"
	@echo "type-check:   Static type checking with mypy"
	@echo "security-scan: Security vulnerability scanning"
	@echo "pre-commit:   Run all pre-commit hooks"

help-dev:
	@echo "Development Commands Help"
	@echo "========================"
	@echo "dev:    Start both backend and frontend in development mode"
	@echo "run:    Start production server"
	@echo "build:  Build frontend for production"
	@echo "clean:  Remove build artifacts and cache files"