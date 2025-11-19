# Testing Notes and Known Issues

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

## Async Fixture Configuration

### ✅ Working Configuration

The async database fixtures are correctly configured in `conftest.py`:

```python
# Use NullPool to avoid connection pooling issues with asyncpg
engine = create_async_engine(TEST_ASYNC_DATABASE_URL, poolclass=NullPool, echo=False)

# Function-scoped fixtures work reliably
@pytest_asyncio.fixture
async def async_db():
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session_factory()
    yield session
    await session.close()
```

**Key Fixes Applied:**
- ✅ Commented out session-scoped `async_engine` fixture (caused DROP SCHEMA CASCADE hangs)
- ✅ Removed custom `event_loop` fixture (conflicts with pytest-asyncio 1.2.0)
- ✅ Use `NullPool` for async engines to prevent connection pooling issues
- ✅ Skip `Base.metadata.create_all()` on every test (use `setup_test_schema.py` once)
- ✅ Function-scoped fixtures for better isolation

### ✅ Verified Working Tests

These tests demonstrate the async fixtures work correctly:

1. **test_simple_async.py** - Passes in 0.72s
   - Simple async database operations
   - Self-contained fixture with NullPool
   - Proves async infrastructure is functional

2. **test_service_init.py** - Passes in 0.86s
   - UnifiedNotificationService initialization
   - Proves service creation doesn't hang
   - Shows issue is in specific service methods

## ⚠️ Known Issue: WebSocket Manager + pytest-asyncio Hang

### Problem Description

Tests involving `UnifiedNotificationService.create_notification()` hang indefinitely when run with pytest-asyncio, even during test collection phase.

### Root Cause

The hang occurs due to interaction between:
1. WebSocket manager (`app.core.websocket_manager.websocket_manager`)
2. pytest-asyncio event loop management
3. Async SQLAlchemy sessions

**Evidence:**
- ✅ Service works perfectly outside pytest (tested with `asyncio.run()`)
- ❌ Tests hang even with WebSocket manager mocked at module level
- ❌ Hang occurs during pytest collection, before test execution
- ❌ Happens even with `channels=[]` parameter to skip delivery

### Attempted Solutions

All of these were attempted and failed to resolve the hang:

1. **Mocking at test level** - `@patch('app.services.notification_service.websocket_manager')`
2. **Mocking at module level** - Patch before imports
3. **Mocking at fixture level** - `autouse=True` fixtures
4. **Skipping delivery** - `channels=[]` parameter
5. **Self-contained fixtures** - Independent async_db per test file
6. **Different session scopes** - Function vs session scoped

### Affected Test Files

- `test_unified_notification_service.py` - 15 comprehensive test cases (SKIPPED)
- `test_notification_mocked.py` - 3 test cases with mocking (SKIPPED)

### Workaround Status

**Currently SKIPPED pending WebSocket testing pattern establishment.**

The comprehensive test files are ready and contain:
- ✅ 15 test cases covering full service functionality
- ✅ Proper async fixture setup
- ✅ Correct mocking patterns
- ✅ Edge case coverage

These will be re-enabled once we establish a reliable WebSocket manager testing pattern.

### Alternative Coverage

**Phase 6 tests provide good coverage:**
- ✅ 11/11 notification service Phase 6 tests passing
- ✅ Tests run via different test infrastructure (sync fixtures)
- ✅ Core CRUD functionality verified
- ✅ Scheduled notifications tested

## Test Execution Best Practices

### One-Time Setup

Before running async tests for the first time:

```bash
cd backend
python tests/setup_test_schema.py
```

This creates all database tables in `career_copilot_test` database.

### Running Tests

```bash
# All backend tests
pytest -v

# Specific test file
pytest tests/unit/test_simple_async.py -xvs

# With coverage
pytest --cov=backend --cov-report=html

# Skip known hanging tests
pytest -m "not skip_websocket"
```

### Debugging Async Tests

If you encounter hangs:

1. **Add timeout**: `timeout 10 pytest ...`
2. **Check event loop**: Ensure no custom event_loop fixture
3. **Verify NullPool**: Use `poolclass=NullPool` for async engines
4. **Test outside pytest**: Verify service works with `asyncio.run()`
5. **Check imports**: WebSocket manager imported at module level can cause issues

## Coverage Status

Current backend test coverage (as of 2025-11-14):

| Service              | Coverage       | Status                |
| -------------------- | -------------- | --------------------- |
| LLM Service          | 78%            | ✅ Good                |
| Job Deduplication    | 88%            | ✅ Good                |
| Job Service          | 55%            | ⚠️ Needs improvement   |
| Notification Service | ~50% (Phase 6) | ⚠️ Async tests skipped |
| Overall Services     | 4%             | ❌ Low (many untested) |

**Next Steps:**
1. ✅ Document WebSocket testing issue (this file)
2. 🔄 Focus on simpler services (job_service, application_service) for quick wins
3. 🔄 Establish WebSocket manager mocking pattern
4. 📋 Re-enable comprehensive notification tests

## Future Improvements

### WebSocket Testing Pattern

Consider these approaches for future work:

1. **Environment-based skipping**:
   ```python
   if os.getenv('TESTING') == 'true':
       self.websocket_manager = None
   ```

2. **Dependency injection**:
   ```python
   def __init__(self, db=None, ws_manager=None):
       self.websocket_manager = ws_manager or websocket_manager
   ```

3. **Separate WebSocket tests**:
   - Integration tests with real WebSocket server
   - Unit tests with mocked manager
   - Skip WebSocket in async SQLAlchemy tests

### Test Organization

- `tests/unit/` - Pure unit tests, fast, no external dependencies
- `tests/integration/` - Integration tests with database
- `tests/e2e/` - End-to-end tests with WebSocket, Redis, etc.
- `tests/fixtures/` - Shared fixtures by category

## References

- pytest-asyncio docs: https://pytest-asyncio.readthedocs.io/
- SQLAlchemy async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- asyncpg pooling: https://magicstack.github.io/asyncpg/current/
