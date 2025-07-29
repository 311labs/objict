.PHONY: help install test test-cov build publish publish-test clean bump-patch bump-minor bump-major version lint format check dev-setup release-patch release-minor release-major pre-release-check

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "🚀 PyObjict Development Commands"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "📦 Quick Release Workflow:"
	@echo "  make release-patch  # Test → Bump → Build → Publish"
	@echo ""

install: ## Install dependencies
	@echo "📥 Installing dependencies..."
	poetry install

test: ## Run tests
	@echo "🧪 Running tests..."
	poetry run pytest -v

test-cov: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	poetry run pytest --cov=objict --cov-report=html --cov-report=term-missing

test-quiet: ## Run tests quietly (for CI/scripts)
	@poetry run pytest -q

lint: ## Run code linting
	@echo "🔍 Running linting..."
	@poetry run python -m py_compile objict/__init__.py
	@echo "✅ Linting passed"

format: ## Format code (requires black)
	@echo "🎨 Formatting code..."
	@if poetry run black --version >/dev/null 2>&1; then \
		poetry run black objict/ --diff; \
		poetry run black objict/; \
		echo "✅ Code formatted"; \
	else \
		echo "❌ Black not installed. Run: poetry add --group dev black"; \
		exit 1; \
	fi

check: lint test ## Run linting and tests
	@echo "✅ All checks passed!"

pre-release-check: ## Run comprehensive pre-release checks
	@echo "🔍 Running pre-release checks..."
	@echo "  → Checking git status..."
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "❌ Git working directory is not clean. Commit or stash changes first."; \
		git status --short; \
		exit 1; \
	fi
	@echo "  → Running tests..."
	@$(MAKE) test-quiet
	@echo "  → Running linting..."
	@$(MAKE) lint
	@echo "  → Checking if on main/master branch..."
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" != "main" ] && [ "$$BRANCH" != "master" ]; then \
		echo "⚠️  Warning: Not on main/master branch (currently on $$BRANCH)"; \
		read -p "Continue anyway? (y/N): " confirm; \
		if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
			echo "❌ Release cancelled"; \
			exit 1; \
		fi; \
	fi
	@echo "✅ Pre-release checks passed!"

build: ## Build the package
	@echo "🔨 Building package..."
	poetry build
	@echo "✅ Package built successfully!"

clean: ## Clean build artifacts
	@echo "🧹 Cleaning build artifacts..."
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned successfully!"

version: ## Show current version
	@python bump_version.py --show

bump-patch: pre-release-check ## Bump patch version (1.0.0 -> 1.0.1)
	@echo "⬆️  Bumping patch version..."
	python bump_version.py patch

bump-minor: pre-release-check ## Bump minor version (1.0.0 -> 1.1.0)
	@echo "⬆️  Bumping minor version..."
	python bump_version.py minor

bump-major: pre-release-check ## Bump major version (1.0.0 -> 2.0.0)
	@echo "⬆️  Bumping major version..."
	python bump_version.py major

publish: build ## Publish to PyPI (requires build)
	@echo "🚀 Publishing to PyPI..."
	@echo "⚠️  This will publish to the LIVE PyPI!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		poetry publish; \
		echo "✅ Published successfully!"; \
	else \
		echo "❌ Publish cancelled"; \
		exit 1; \
	fi

publish-test: build ## Publish to TestPyPI (requires build)
	@echo "🧪 Publishing to TestPyPI..."
	poetry publish --repository testpypi

dev-setup: install ## Set up development environment
	@echo "🛠️  Setting up development environment..."
	@$(MAKE) install
	@echo ""
	@echo "✅ Development environment ready!"
	@echo "📖 Run 'make help' to see available commands"

# Release workflows that run tests first
release-patch: ## 🚀 Full patch release (test → bump → build → publish)
	@echo "🚀 Starting patch release workflow..."
	@$(MAKE) bump-patch
	@$(MAKE) build
	@$(MAKE) publish
	@echo "🎉 Patch release complete!"

release-minor: ## 🚀 Full minor release (test → bump → build → publish)
	@echo "🚀 Starting minor release workflow..."
	@$(MAKE) bump-minor
	@$(MAKE) build
	@$(MAKE) publish
	@echo "🎉 Minor release complete!"

release-major: ## 🚀 Full major release (test → bump → build → publish)
	@echo "🚀 Starting major release workflow..."
	@$(MAKE) bump-major
	@$(MAKE) build
	@$(MAKE) publish
	@echo "🎉 Major release complete!"

# Test release workflows (publish to TestPyPI)
release-patch-test: ## 🧪 Test patch release (to TestPyPI)
	@echo "🧪 Starting test patch release..."
	@$(MAKE) bump-patch
	@$(MAKE) build
	@$(MAKE) publish-test
	@echo "✅ Test patch release complete!"

release-minor-test: ## 🧪 Test minor release (to TestPyPI)
	@echo "🧪 Starting test minor release..."
	@$(MAKE) bump-minor
	@$(MAKE) build
	@$(MAKE) publish-test
	@echo "✅ Test minor release complete!"

release-major-test: ## 🧪 Test major release (to TestPyPI)
	@echo "🧪 Starting test major release..."
	@$(MAKE) bump-major
	@$(MAKE) build
	@$(MAKE) publish-test
	@echo "✅ Test major release complete!"

# Convenience shortcuts
patch: release-patch ## Alias for release-patch
minor: release-minor ## Alias for release-minor
major: release-major ## Alias for release-major

# Development helpers
watch-test: ## Run tests in watch mode (requires pytest-watch)
	@if poetry run ptw --version >/dev/null 2>&1; then \
		poetry run ptw -- -v; \
	else \
		echo "❌ pytest-watch not installed. Run: poetry add --group dev pytest-watch"; \
		exit 1; \
	fi

ci: check build ## Run all CI checks (lint, test, build)
	@echo "✅ All CI checks passed!"
