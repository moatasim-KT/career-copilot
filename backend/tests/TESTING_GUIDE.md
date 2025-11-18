# Testing Guide - Career Copilot Backend

**Last Updated**: November 17, 2025

## Overview

The Career Copilot backend test suite is designed to run with **PostgreSQL** to match the production environment. This ensures accurate testing of PostgreSQL-specific features like ARRAY types, JSONB, and GIN indexes.

## Prerequisites

### Option 1: Docker PostgreSQL (Recommended)
```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Verify it's running
docker ps | grep postgres
```

### Option 2: Local PostgreSQL Installation
```bash
# macOS (Homebrew)
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian
sudo apt-get install postgresql-14
sudo systemctl start postgresql

# Verify installation
psql --version
```

## Database Setup

### Automated Setup (Recommended)
```bash
# Run the setup script
cd backend
./scripts/setup_test_db.sh
```

This script will:
- Check if PostgreSQL is running
- Drop existing test database (if any)
- Create fresh `career_copilot_test` database
- Grant necessary privileges

### Manual Setup
```bash
# Connect to PostgreSQL
psql -U postgres

# Create test database
CREATE DATABASE career_copilot_test;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE career_copilot_test TO postgres;

# Exit
\q
```

## Running Tests

### Quick Start
```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_application_service.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Test Categories

#### Unit Tests
```bash
# Core services
pytest tests/unit/test_job_service.py -v
pytest tests/unit/test_application_service.py -v
pytest tests/unit/test_job_deduplication_service.py -v

# API endpoints
pytest tests/unit/test_jobs_api.py -v
pytest tests/unit/test_applications_api.py -v
```

#### Integration Tests
```bash
# Job management workflow
pytest tests/integration/test_job_management_services.py -v

# LLM service integration
pytest tests/integration/test_llm_service_integration.py -v

# API integration
pytest tests/integration/test_api_integration.py -v
```

#### Authentication Tests
```bash
# Auth endpoints
pytest tests/test_auth.py -v
pytest tests/integration/test_auth_endpoint.py -v
```

### Performance Tests
```bash
# Run with timing
pytest tests/ -v --durations=10

# Parallel execution (requires pytest-xdist)
pytest tests/ -n auto
```

## Environment Configuration

### Test Database URL

The test configuration uses PostgreSQL by default:

```bash
# Default (in tests/conftest.py)
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/career_copilot_test

# Override via environment variable
export TEST_DATABASE_URL=postgresql://myuser:mypass@localhost:5432/my_test_db
pytest tests/
```

### Fallback to SQLite (Not Recommended)

If PostgreSQL is unavailable, you can temporarily use SQLite, but be aware this will **fail tests** that rely on PostgreSQL features:

```bash
# Temporarily use SQLite (will cause failures)
export TEST_DATABASE_URL=sqlite:///./test_career_copilot.db
pytest tests/
```

**Known Issues with SQLite**:
- ❌ ARRAY type not supported (job tech_stack, skills, etc.)
- ❌ JSONB type not supported
- ❌ GIN indexes not supported
- ❌ Some advanced SQL features unavailable

## Test Coverage Goals

### Current Status (Phase 1 Complete)
- ✅ WebSocket Manager: Tests unblocked (18 tests)
- ✅ Template Service: 100% (3/3 tests passing)
- ✅ Notification Service: ~50% coverage
- ⚠️ Job Service: 55% coverage (target: 80%)
- ⚠️ Application Service: 40% coverage (target: 80%)

### Phase 2 Goals
- [ ] Job Service: 55% → 80%
- [ ] Application Service: 40% → 80%
- [ ] Calendar Service: Add unit tests
- [ ] Dashboard Service: Add unit tests
- [ ] Auth Service: Add comprehensive tests

### Measuring Coverage
```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# View in browser
open htmlcov/index.html

# Show coverage for specific service
pytest tests/unit/test_job_service.py --cov=app.services.job_service --cov-report=term-missing
```

## Troubleshooting

### PostgreSQL Not Running
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Start via Docker
docker-compose up -d postgres

# Check logs
docker-compose logs postgres
```

### Connection Refused
```bash
# Verify PostgreSQL is listening
netstat -an | grep 5432

# Check Docker port mapping
docker-compose ps postgres

# Test connection
psql -h localhost -p 5432 -U postgres -d career_copilot_test
```

### Permission Denied
```bash
# Grant database privileges
psql -U postgres -d career_copilot_test -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;"
psql -U postgres -d career_copilot_test -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;"
```

### Test Database Not Clean
```bash
# Reset test database
./scripts/setup_test_db.sh

# Or manually
psql -U postgres -c "DROP DATABASE IF EXISTS career_copilot_test;"
psql -U postgres -c "CREATE DATABASE career_copilot_test;"
```

### Import Errors
```bash
# Ensure backend is in Python path
cd backend
export PYTHONPATH=$PWD:$PYTHONPATH

# Or run from backend directory
cd backend
pytest tests/
```

## Continuous Integration

### GitHub Actions
The test suite runs automatically on push/PR via GitHub Actions:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    cd backend
    pytest tests/ --cov=app --cov-report=xml
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## Writing Tests

### Test Structure
```python
# tests/unit/test_my_service.py
import pytest
from sqlalchemy.orm import Session

from app.services.my_service import MyService

def test_my_function(db: Session):
    """Test description."""
    # Arrange
    service = MyService(db)
    
    # Act
    result = service.my_function()
    
    # Assert
    assert result is not None
```

### Async Tests
```python
# tests/unit/test_my_async_service.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.my_async_service import MyAsyncService

@pytest.mark.asyncio
async def test_my_async_function(async_db: AsyncSession):
    """Test async function."""
    service = MyAsyncService(async_db)
    result = await service.my_async_function()
    assert result is not None
```

### Fixtures
Common fixtures are available in `tests/conftest.py`:
- `db`: Synchronous database session
- `async_db`: Async database session
- `client`: FastAPI TestClient
- `mock_websocket_manager`: Mock WebSocket manager

## Best Practices

1. **Use PostgreSQL for tests** - Matches production environment
2. **Clean database per test** - Each test gets fresh database state
3. **Test isolation** - Tests should not depend on each other
4. **Mock external services** - Don't call real APIs in tests
5. **Use fixtures** - Reuse common test setup
6. **Test edge cases** - Include error handling tests
7. **Measure coverage** - Aim for 80%+ on critical services

## Quick Reference

```bash
# Setup
./scripts/setup_test_db.sh

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_job_service.py::test_create_job -v

# Run tests matching pattern
pytest tests/ -k "job" -v

# Show slowest tests
pytest tests/ --durations=10

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Parallel execution
pytest tests/ -n auto
```

## Related Documentation

- [[backend/tests/TESTING_NOTES.md|Testing Notes]] - Detailed testing patterns
- [[CONTRIBUTING.md|Contributing Guide]] - How to contribute
- [[PROJECT_STATUS.md|Project Status]] - Current project state
- [[TODO.md|TODO List]] - Testing tasks

---

**Need Help?**
- Check PostgreSQL logs: `docker-compose logs postgres`
- Verify database exists: `psql -U postgres -l`
- Review test output: `pytest tests/ -v --tb=short`
