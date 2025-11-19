# Test Infrastructure Documentation

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

This directory contains the test infrastructure for the Career Copilot backend.

## Quick Links
- [[../../docs/index|Main Documentation Hub]]
- [[../../docs/development/testing-strategies.md|Testing Strategies]]
- [[../README.md#testing|Backend Testing Guide]]
- [[../../tests/e2e/README.md|E2E Testing Framework]]
- [[../../frontend/docs/FUNCTIONAL_TESTING_GUIDE.md|Functional Testing Guide]]

## Test Fixtures

The `conftest.py` file provides comprehensive test fixtures that automatically handle database setup and teardown.

### Key Features

1. **Automatic Test User Creation**: A test user with `id=1` is automatically created for all tests, preventing foreign key violations
2. **Isolated Test Database**: Each test runs in a transaction that is rolled back after the test completes
3. **Both Sync and Async Support**: Fixtures for both synchronous and asynchronous database operations
4. **Test User Factory**: Easy creation of additional test users for complex test scenarios

### Available Fixtures

#### Database Fixtures

- **`db`** - Synchronous database session with automatic rollback
- **`async_db`** - Asynchronous database session with automatic rollback  
- **`engine`** - Synchronous SQLAlchemy engine (session-scoped)
- **`async_engine`** - Asynchronous SQLAlchemy engine (session-scoped)

#### User Fixtures

- **`test_user`** - The primary test user (id=1) - synchronous
- **`async_test_user`** - The primary test user (id=1) - asynchronous
- **`test_user_factory`** - Factory for creating additional test users - synchronous
- **`async_test_user_factory`** - Factory for creating additional test users - asynchronous

### Usage Examples

#### Basic Test with Test User

```python
def test_something(db, test_user):
    """Test that uses the automatic test user."""
    assert test_user.id == 1
    assert test_user.email == "test@example.com"
    
    # Use the db session
    job = Job(
        user_id=test_user.id,
        title="Test Job",
        company="Test Company"
    )
    db.add(job)
    db.commit()
```

#### Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation(async_db, async_test_user):
    """Test async database operations."""
    from sqlalchemy import select
    
    result = await async_db.execute(
        select(User).where(User.id == async_test_user.id)
    )
    user = result.scalars().first()
    assert user is not None
```

#### Creating Additional Users

```python
def test_with_multiple_users(db, test_user, test_user_factory):
    """Test with multiple users."""
    # test_user (id=1) is automatically available
    
    # Create additional users
    user2 = test_user_factory(
        username="user2",
        email="user2@example.com",
        skills=["Python", "Django"]
    )
    
    user3 = test_user_factory(
        username="user3",
        email="user3@example.com",
        experience_level="junior"
    )
    
    # All users are in the same transaction and will be rolled back
    assert db.query(User).count() >= 3
```

## Test Database Seeding

The `seed_test_data.py` script can be used to populate the test database with sample data.

### Usage

```bash
# From the backend directory
python tests/seed_test_data.py
```

This will:
- Create the primary test user (id=1)
- Create additional test users with various profiles
- Set up sample data for testing

## Test User Details

The automatically created test user (id=1) has the following profile:

- **Username**: `test_user`
- **Email**: `test@example.com`  
- **Password**: `testpass123` (hashed)
- **Skills**: Python, FastAPI, JavaScript, React, TypeScript, Docker
- **Locations**: Remote, San Francisco, New York, Austin
- **Experience**: senior
- **Daily Goal**: 10 applications

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_feedback_analysis.py
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Only Unit Tests

```bash
pytest tests/unit/
```

### Run Only Integration Tests

```bash
pytest tests/integration/
```

## Troubleshooting

### Foreign Key Violations

If you see errors like `FOREIGN KEY constraint failed` or `user_id=1 doesn't exist`, make sure:

1. You're using the provided `db` or `async_db` fixture
2. The test function signature includes the fixture: `def test_something(db, test_user):`
3. The `conftest.py` file is in the tests directory

### Import Errors

If you see `ModuleNotFoundError`, make sure:

1. You're running tests from the `backend` directory
2. The `app` package is importable
3. All dependencies are installed: `pip install -r requirements.txt`

### Database Lock Issues

If you see database lock errors:

1. Make sure no other processes are using the test database
2. Delete the test database file: `rm test_career_copilot.db*`
3. Run tests again

## Security Module

The `app/core/security.py` module provides password hashing utilities:

- **`get_password_hash(password: str) -> str`** - Hash a password using bcrypt
- **`verify_password(plain_password: str, hashed_password: str) -> bool`** - Verify a password

This module is automatically used by the test fixtures to create hashed passwords for test users.

## Best Practices

1. **Always use fixtures**: Don't create database connections manually
2. **Keep tests isolated**: Each test should work independently
3. **Use factories for multiple entities**: When you need multiple users, jobs, etc., use factory fixtures
4. **Clean up is automatic**: Don't worry about cleaning up test data - transactions are rolled back
5. **Test both sync and async**: If your code uses async, test with `async_db` fixture

## Adding New Fixtures

To add custom fixtures for your tests, create them in `conftest.py`:

```python
@pytest.fixture
def sample_job(db, test_user):
    """Create a sample job for testing."""
    job = Job(
        user_id=test_user.id,
        title="Sample Job",
        company="Sample Company",
        location="Remote"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
```

Then use it in your tests:

```python
def test_with_sample_job(db, test_user, sample_job):
    assert sample_job.user_id == test_user.id
    assert sample_job.company == "Sample Company"
```
