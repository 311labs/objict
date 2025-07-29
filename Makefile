.PHONY: help install test build publish clean bump-patch bump-minor bump-major version lint format check

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

test: ## Run tests
	poetry run pytest -v

test-cov: ## Run tests with coverage
	poetry run pytest --cov=objict --cov-report=html --cov-report=term

build: ## Build the package
	poetry build

publish: build ## Build and publish to PyPI
	poetry publish

publish-test: build ## Build and publish to TestPyPI
	poetry publish --repository testpypi

clean: ## Clean build artifacts
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

version: ## Show current version
	python bump_version.py --show

bump-patch: ## Bump patch version (1.0.0 -> 1.0.1)
	python bump_version.py patch

bump-minor: ## Bump minor version (1.0.0 -> 1.1.0)
	python bump_version.py minor

bump-major: ## Bump major version (1.0.0 -> 2.0.0)
	python bump_version.py major

lint: ## Run code linting
	poetry run python -m py_compile objict/__init__.py

format: ## Format code (if black is available)
	@if poetry run black --version >/dev/null 2>&1; then \
		poetry run black objict/; \
	else \
		echo "Black not installed. Run: poetry add --group dev black"; \
	fi

check: lint test ## Run linting and tests

dev-setup: install ## Set up development environment
	@echo "Development environment setup complete!"
	@echo "Run 'make help' to see available commands"

release-patch: bump-patch build publish ## Bump patch version, build, and publish
	@echo "Released new patch version!"

release-minor: bump-minor build publish ## Bump minor version, build, and publish
	@echo "Released new minor version!"

release-major: bump-major build publish ## Bump major version, build, and publish
	@echo "Released new major version!"
