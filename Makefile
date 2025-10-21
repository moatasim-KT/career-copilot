# Career Copilot Makefile
# Streamlined commands for development and deployment

.PHONY: help install dev-install test lint format clean build docker-build docker-run deploy

# Default target
help:
	@echo "Career Copilot - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev-install  - Install development dependencies"
	@echo "  make setup        - Complete development environment setup"
	@echo "  make run          - Start the application (streamlined)"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-quick   - Run quick smoke tests"
	@echo "  make lint         - Run code linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean temporary files"
	@echo ""
	@echo "Production:"
	@echo "  make build        - Build production artifacts"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo ""
	@echo "Utilities:"
	@echo "  make status       - Show system status"
	@echo "  make cleanup      - Run comprehensive cleanup"

install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements-prod.txt

dev-install:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements-dev.txt

setup:
	@echo "🔧 Setting up development environment..."
	@if [ -f "scripts/dev_manager.py" ]; then \
		python scripts/dev_manager.py setup; \
	else \
		echo "Setting up basic environment..."; \
		mkdir -p data/logs data/uploads data/backups logs; \
		if [ ! -f ".env" ]; then cp .env.example .env 2>/dev/null || echo "Please create .env file"; fi; \
	fi

run:
	@echo "🚀 Starting Career Copilot (streamlined)..."
	@if [ -f "start_streamlined.sh" ]; then \
		./start_streamlined.sh; \
	else \
		./start.sh; \
	fi

test:
	@echo "🧪 Running all tests..."
	@if [ -f "tests/test_runner.py" ]; then \
		python tests/test_runner.py all; \
	else \
		python -m pytest tests/ -v --tb=short --disable-warnings; \
	fi

test-unit:
	@echo "🧪 Running unit tests..."
	@if [ -f "tests/test_runner.py" ]; then \
		python tests/test_runner.py unit; \
	else \
		python -m pytest tests/unit/ -v --tb=short --disable-warnings; \
	fi

test-integration:
	@echo "🧪 Running integration tests..."
	@if [ -f "tests/test_runner.py" ]; then \
		python tests/test_runner.py integration; \
	else \
		python -m pytest tests/integration/ -v --tb=short --disable-warnings; \
	fi

test-e2e:
	@echo "🧪 Running end-to-end tests..."
	@if [ -f "tests/test_runner.py" ]; then \
		python tests/test_runner.py e2e; \
	else \
		python -m pytest tests/e2e/ -v --tb=short --disable-warnings; \
	fi

test-quick:
	@echo "💨 Running quick smoke tests..."
	@if [ -f "tests/test_runner.py" ]; then \
		python tests/test_runner.py quick; \
	else \
		python -m pytest tests/unit/ -k "not slow" -v --tb=short --disable-warnings --maxfail=3; \
	fi

lint:
	@echo "🔍 Running code linting..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 backend/app/ --max-line-length=100 --ignore=E203,W503; \
	else \
		echo "flake8 not installed, skipping linting"; \
	fi
	@if command -v mypy >/dev/null 2>&1; then \
		mypy backend/app/ --ignore-missing-imports; \
	else \
		echo "mypy not installed, skipping type checking"; \
	fi

format:
	@echo "✨ Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black backend/app/ frontend/ scripts/ --line-length=100; \
	else \
		echo "black not installed, skipping formatting"; \
	fi
	@if command -v isort >/dev/null 2>&1; then \
		isort backend/app/ frontend/ scripts/ --profile black; \
	else \
		echo "isort not installed, skipping import sorting"; \
	fi

format-check:
	@echo "🔍 Checking code formatting..."
	@if command -v black >/dev/null 2>&1; then \
		black --check backend/app/ frontend/ scripts/ --line-length=100; \
	fi
	@if command -v isort >/dev/null 2>&1; then \
		isort --check-only backend/app/ frontend/ scripts/ --profile black; \
	fi

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✅ Cleanup completed"

build:
	@echo "🏗️ Building production artifacts..."
	@if [ -f "scripts/system_manager.py" ]; then \
		python scripts/system_manager.py build; \
	else \
		echo "Building basic artifacts..."; \
		mkdir -p dist/; \
		echo "Build completed"; \
	fi

docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t career-copilot .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 8002:8002 -p 8501:8501 career-copilot

status:
	@echo "📊 Checking system status..."
	@if [ -f "scripts/system_manager.py" ]; then \
		python scripts/system_manager.py status; \
	else \
		echo "System Status:"; \
		echo "- Python: $$(python3 --version)"; \
		echo "- Pip: $$(pip --version | cut -d' ' -f1-2)"; \
		echo "- Project: Career Copilot"; \
		echo "- Tests: $$(find tests/ -name '*.py' | wc -l) test files"; \
	fi

cleanup:
	@echo "🧹 Running comprehensive cleanup..."
	@if [ -f "scripts/comprehensive_cleanup.py" ]; then \
		python scripts/comprehensive_cleanup.py; \
	else \
		make clean; \
	fi