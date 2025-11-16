.PHONY: help install lint format type-check security test quality-check quality-fix clean verify-pyproject
.DEFAULT_GOAL := help

# Python environment
PYTHON := python
PIP := pip
CONDA_ENV := /Users/moatasimfarooque/Downloads/Data_Science/GITHUB/career-copilot/.conda

# Directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend
PYTHON_DIRS := $(BACKEND_DIR) scripts

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "Installing Python dependencies..."
	$(PIP) install -e .[dev,ai,all]
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install

# Python linting and formatting
lint-python: ## Run Python linting (flake8, ruff)
	@echo "Running flake8..."
	flake8 $(PYTHON_DIRS)
	@echo "Running ruff..."
	ruff check $(PYTHON_DIRS)

format-python: ## Format Python code (black, isort, ruff)
	@echo "Running black..."
	black $(PYTHON_DIRS)
	@echo "Running isort..."
	isort $(PYTHON_DIRS)
	@echo "Running ruff format..."
	ruff format $(PYTHON_DIRS)
	@echo "Running ruff fix..."
	ruff check --fix $(PYTHON_DIRS)

type-check-python: ## Run Python type checking (mypy)
	@echo "Running mypy..."
	mypy $(PYTHON_DIRS)

security-python: ## Run Python security checks (bandit, safety)
	@echo "Running bandit..."
	bandit -r $(PYTHON_DIRS) -f json -o bandit-report.json || true
	@echo "Running safety..."
	@mkdir -p reports
	safety check --output json > reports/safety-report.json || true
	@echo "Running pip-audit (dependency scan)..."
	@if command -v pip-audit >/dev/null 2>&1; then \
		pip-audit -f json -o reports/pip_audit_report.json || true; \
	else \
		echo "pip-audit not installed. Run 'pip install pip-audit' to enable Python dependency scanning."; \
	fi

# Frontend linting and formatting
lint-frontend: ## Run frontend linting (ESLint)
	@echo "Running ESLint..."
	cd $(FRONTEND_DIR) && npm run lint:check

format-frontend: ## Format frontend code (Prettier, ESLint)
	@echo "Running Prettier..."
	cd $(FRONTEND_DIR) && npm run format
	@echo "Running ESLint fix..."
	cd $(FRONTEND_DIR) && npm run lint

type-check-frontend: ## Run frontend type checking (TypeScript)
	@echo "Running TypeScript type check..."
	cd $(FRONTEND_DIR) && npm run type-check

# Combined commands
lint: lint-python lint-frontend ## Run all linting

format: format-python format-frontend ## Format all code

type-check: type-check-python type-check-frontend ## Run all type checking

security: security-python ## Run all security checks
	@echo "Running Semgrep (SAST)..."
	@mkdir -p reports
	@if command -v semgrep >/dev/null 2>&1; then \
		semgrep --config=p/ci --error --json > reports/semgrep-report.json || true; \
	elif [ -x "$(HOME)/.local/bin/semgrep" ]; then \
		$(HOME)/.local/bin/semgrep --config=p/ci --error --json > reports/semgrep-report.json || true; \
	else \
		echo "semgrep not installed. Install via 'pip install semgrep' (virtualenv) or 'pipx install semgrep'"; \
	fi
	@echo "Running npm audit (frontend dependency scan)..."
	@cd $(FRONTEND_DIR) && npm audit --audit-level=high --omit=dev --json > ../reports/npm_audit_report.json || true

test-python: ## Run Python tests
	@echo "Running Python tests..."
	PYTHONPATH=. pytest -v --cov=$(BACKEND_DIR) --cov-report=html --cov-report=term

test-frontend: ## Run frontend tests
	@echo "Running frontend tests..."
	cd $(FRONTEND_DIR) && npm run test:coverage
	cd $(FRONTEND_DIR) && npm run test:a11y

test: test-python test-frontend ## Run all tests

# Quality checks
quality-check: ## Run all quality checks (lint, type-check, security)
	@echo "Running comprehensive quality checks..."
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) security
	@echo "✅ All quality checks completed!"

quality-fix: ## Fix all auto-fixable quality issues
	@echo "Fixing all auto-fixable issues..."
	@$(MAKE) format
	@echo "✅ All auto-fixes applied!"

# Pre-commit
pre-commit-run: ## Run pre-commit on all files
	@echo "Running pre-commit on all files..."
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	@echo "Updating pre-commit hooks..."
	pre-commit autoupdate

# Development workflow
dev-setup: install ## Complete development setup
	@echo "Setting up development environment..."
	@$(MAKE) quality-fix
	@echo "✅ Development environment ready!"

ci-check: ## Run all CI checks (used in CI/CD)
	@echo "Running CI checks..."
	@$(MAKE) quality-check
	@$(MAKE) test
	@echo "✅ All CI checks passed!"

# Pyproject validation
verify-pyproject: ## Validate pyproject.toml for duplicates and invalid extras
	@echo "Validating pyproject.toml..."
	python scripts/verify/validate_pyproject.py

# Cleanup
clean: ## Clean up generated files
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -f bandit-report.json
	rm -f reports/safety-report.json reports/pip_audit_report.json reports/semgrep-report.json reports/npm_audit_report.json
	cd $(FRONTEND_DIR) && rm -rf .next build dist coverage
	@echo "✅ Cleanup completed!"

# Environment activation helper
activate: ## Show command to activate conda environment
	@echo "To activate the conda environment, run:"
	@echo "conda activate $(CONDA_ENV)"

# Tool versions
versions: ## Show versions of all tools
	@echo "Tool versions:"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Black: $$(black --version)"
	@echo "Ruff: $$(ruff --version)"
	@echo "Flake8: $$(flake8 --version)"
	@echo "MyPy: $$(mypy --version)"
	@echo "Bandit: $$(bandit --version)"
	@echo "Safety: $$(safety --version)"
	@echo "isort: $$(isort --version)"
	@echo "Pre-commit: $$(pre-commit --version)"
	@cd $(FRONTEND_DIR) && echo "Node: $$(node --version)"
	@cd $(FRONTEND_DIR) && echo "NPM: $$(npm --version)"
	@cd $(FRONTEND_DIR) && echo "ESLint: $$(npx eslint --version)"
	@cd $(FRONTEND_DIR) && echo "Prettier: $$(npx prettier --version)"
	@cd $(FRONTEND_DIR) && echo "TypeScript: $$(npx tsc --version)"