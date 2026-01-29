# macOS Cleaner Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev test test-cov lint format type-check security clean build upload docs run-gui run-web run-cli

# Default target
help: ## Show this help message
	@echo "🍎 macOS Cleaner - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install the package in development mode
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install || echo "pre-commit not available"

install-all: ## Install all dependencies
	pip install -e ".[dev,web,test]"

# Testing
test: ## Run all tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=src/mac_cleaner --cov-report=html --cov-report=term-missing -v

test-fast: ## Run tests without coverage (faster)
	pytest tests/ -x -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v -m integration

test-unit: ## Run unit tests only
	pytest tests/ -v -m "not integration"

# Code Quality
lint: ## Run linting checks
	flake8 src/ tests/
	mypy src/

format: ## Format code with black
	black src/ tests/
	isort src/ tests/

format-check: ## Check code formatting
	black --check src/ tests/
	isort --check-only src/ tests/

type-check: ## Run type checking
	mypy src/

# Security
security: ## Run security scans
	bandit -r src/
	safety check

security-report: ## Generate security reports
	bandit -r src/ -f json -o bandit-report.json
	safety check --json --output safety-report.json || true

# Building and Distribution
clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean ## Build the package
	python -m build

build-check: build ## Check the built package
	twine check dist/*

upload-test: build ## Upload to test PyPI
	twine upload --repository testpypi dist/*

upload: build ## Upload to PyPI
	twine upload dist/

# Development
dev-setup: install-dev ## Set up development environment
	@echo "🚀 Development environment ready!"
	@echo "Run 'make test' to verify everything works."

dev-check: lint test-cov security ## Run all development checks
	@echo "✅ All checks passed!"

# Documentation
docs: ## Generate documentation
	@echo "📚 Documentation generation not yet implemented"

docs-serve: ## Serve documentation locally
	@echo "📚 Documentation serving not yet implemented"

# Running the Application
run-gui: ## Run the GUI application
	python -m mac_cleaner.gui

run-web: ## Run the web interface
	python -m mac_cleaner.web_gui

run-cli: ## Run CLI with help
	python -m mac_cleaner.cli --help

run-cli-dry: ## Run CLI dry-run cleaning
	python -m mac_cleaner.cli clean --dry-run --category all

# Development Server
dev-web: ## Run web interface in development mode
	FLASK_ENV=development python -m mac_cleaner.web_gui

# Database and Cache
clean-cache: ## Clean application cache
	rm -rf ~/.mac_cleaner_cache/
	rm -rf .mac_cleaner_backup/
	rm -rf .mac_cleaner_logs/

reset-config: ## Reset configuration to defaults
	rm -f mac_cleaner.yaml
	@echo "🔄 Configuration reset. Run the application to create a new config."

# Git and Release
pre-commit: format lint test-cov ## Run pre-commit checks
	@echo "✅ Ready to commit!"

release-check: clean dev-check build-check ## Full release preparation
	@echo "🚀 Ready for release!"

# Docker (if needed)
docker-build: ## Build Docker image
	docker build -t macos-cleaner .

docker-run: ## Run Docker container
	docker run -it --rm macos-cleaner

# Performance
benchmark: ## Run performance benchmarks
	@echo "⏱️  Benchmarking not yet implemented"

profile: ## Run profiling
	@echo "📊 Profiling not yet implemented"

# Utilities
check-deps: ## Check for outdated dependencies
	pip list --outdated

update-deps: ## Update dependencies
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt

freeze: ## Freeze current dependencies
	pip freeze > requirements-freeze.txt

# CI/CD Helpers
ci-test: ## Run CI-like tests locally
	pytest tests/ --cov=src/mac_cleaner --cov-report=xml --cov-fail-under=70 -v

ci-lint: ## Run CI-like linting
	flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
	black --check src/ tests/
	mypy src/ --ignore-missing-imports --strict-optional

ci-security: ## Run CI-like security checks
	bandit -r src/ -f json -o bandit-report.json
	bandit -r src/ -f txt
	safety check --json --output safety-report.json || true
	safety check || true

ci-all: ci-test ci-lint ci-security ## Run all CI checks locally
	@echo "✅ CI checks completed!"

# Quick start for new developers
quickstart: ## Quick setup for new developers
	@echo "🍎 Setting up macOS Cleaner for development..."
	@echo ""
	@echo "1. Installing dependencies..."
	make install-all
	@echo ""
	@echo "2. Running tests..."
	make test-fast
	@echo ""
	@echo "3. Checking code quality..."
	make format-check
	@echo ""
	@echo "✅ Setup complete! You're ready to develop."
	@echo ""
	@echo "Common commands:"
	@echo "  make test        # Run tests"
	@echo "  make format      # Format code"
	@echo "  make lint        # Check code quality"
	@echo "  make run-gui     # Run GUI application"
	@echo "  make run-web     # Run web interface"
