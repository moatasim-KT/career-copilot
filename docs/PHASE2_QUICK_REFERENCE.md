# Phase 2 Test Infrastructure Quick Reference

## Overview
Phase 2 introduced a unified test infrastructure with consolidated test orchestration, improved fixture hierarchy, and streamlined CI integration.

## Quick Commands

### Run Tests Locally

```bash
# Run all tests
python scripts/test_orchestrator.py run --suite all

# Run specific suite
python scripts/test_orchestrator.py run --suite unit
python scripts/test_orchestrator.py run --suite integration
python scripts/test_orchestrator.py run --suite e2e

# Run with parallel execution (4 workers)
python scripts/test_orchestrator.py run --suite all --parallel --workers 4

# Run with coverage
python scripts/test_orchestrator.py run --suite unit --coverage

# Run with specific markers
python scripts/test_orchestrator.py run --suite all --markers cache database

# Run with custom timeout (in seconds)
python scripts/test_orchestrator.py run --suite e2e --timeout 600
```

### Run Tests via CI Script

```bash
# Default: run all tests with parallel execution
./scripts/ci_test_runner.sh

# Run specific suite
./scripts/ci_test_runner.sh --suite unit

# Customize workers
./scripts/ci_test_runner.sh --workers 8

# Disable parallel execution
./scripts/ci_test_runner.sh --no-parallel

# Set custom timeout
./scripts/ci_test_runner.sh --timeout 600

# Set custom report directory
./scripts/ci_test_runner.sh --report-dir custom-reports/
```

### Run Tests Directly with Pytest

```bash
# Run all cache tests
pytest tests/unit/test_cache.py -v

# Run specific test class
pytest tests/unit/test_cache.py::TestSimpleCache -v

# Run specific test method
pytest tests/unit/test_cache.py::TestSimpleCache::test_basic_set_and_get -v

# Run with markers
pytest -m cache -v
pytest -m "cache and not slow" -v

# Run with coverage
pytest tests/unit/ --cov=backend/app --cov-report=html
```

## Available Test Markers

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests  
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.slow          # Slow running tests
@pytest.mark.cache         # Cache-related tests
@pytest.mark.database      # Tests requiring database
@pytest.mark.api           # API endpoint tests
@pytest.mark.auth          # Authentication tests
@pytest.mark.celery        # Celery task tests
```

## Test Fixtures Available

### From Root Conftest (`tests/conftest_new.py`)

```python
# Event loop
event_loop                 # Session-scoped async event loop

# HTTP clients
mock_http_client          # Mock HTTP client with default responses

# User fixtures
test_user                 # Single test user with profile
test_users                # List of 5 test users

# Job fixtures
test_job                  # Single test job posting
test_jobs                 # List of 5 test jobs

# Recommendation fixtures
test_recommendation       # Single recommendation with scoring
test_recommendations      # List of 3 recommendations

# File fixtures
temp_test_dir            # Temporary directory for file operations
temp_config_file         # Temporary YAML config file
```

### From Unit Conftest (`tests/unit/conftest.py`)

```python
# Analytics
test_config              # Analytics test configuration
mock_analytics_data      # Mock analytics data
mock_reporting_service   # Mock reporting service
mock_db_session         # Mock database session
async_reporting_service  # Async mock reporting service
```

### From Integration Conftest (`tests/integration/conftest.py`)

```python
mock_services           # Dictionary of all major service mocks
event_loop             # Event loop for integration tests
```

### From E2E Conftest (`tests/e2e/conftest.py`)

```python
test_environment        # E2E test environment config
test_orchestrator       # E2E test orchestrator instance
http_client            # HTTP client for backend API
frontend_client        # HTTP client for frontend
test_data_generator    # Test data generator
service_health_checker # Service health checking utility
```

## Cache Test Examples

```python
# Using cache fixtures
def test_my_cache_feature(simple_cache):
    simple_cache.set('my_key', 'my_value')
    assert simple_cache.get('my_key') == 'my_value'

def test_recommendations(recommendation_cache):
    recs = {'recommendations': [...], 'count': 2}
    recommendation_cache.set_recommendations('user123', recs)
    cached = recommendation_cache.get_recommendations('user123')
    assert cached['count'] == 2
```

## Report Generation

```bash
# Generate test report
python scripts/test_orchestrator.py report --output test-reports/

# Reports are automatically generated after test runs:
# - test-reports/junit-{suite}.xml
# - test-reports/test_report_{timestamp}.json
# - test-reports/coverage.xml (if --coverage used)
# - test-reports/coverage_html/ (if --coverage used)
```

## Directory Structure

```
tests/
├── conftest.py (or conftest_new.py) - Root fixtures
├── unit/
│   ├── conftest.py                  - Unit test fixtures
│   └── test_cache.py                - Cache tests
├── integration/
│   ├── conftest.py                  - Integration fixtures
│   └── test_*.py                    - Integration tests
└── e2e/
    ├── conftest.py                  - E2E fixtures
    └── test_*.py                    - E2E tests

scripts/
├── test_orchestrator.py             - Unified test orchestrator
└── ci_test_runner.sh                - CI test script

test-reports/                        - Generated reports
├── junit-*.xml
├── test_report_*.json
├── coverage.xml
└── coverage_html/
```

## Troubleshooting

### Tests Not Found
```bash
# Ensure you're in the project root
cd /path/to/career-copilot

# Run pytest with discovery
pytest --collect-only
```

### Import Errors
```bash
# Ensure Python path includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use pytest's conftest.py which handles this
pytest tests/
```

### Parallel Execution Issues
```bash
# Reduce workers if experiencing conflicts
python scripts/test_orchestrator.py run --suite all --parallel --workers 2

# Or disable parallel execution
python scripts/test_orchestrator.py run --suite all
```

### Timeout Issues
```bash
# Increase timeout for slow tests
python scripts/test_orchestrator.py run --suite e2e --timeout 900

# Or mark specific tests as slow
@pytest.mark.slow
def test_long_running_operation():
    ...
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    ./scripts/ci_test_runner.sh --suite all --workers 4

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./test-reports/coverage.xml
```

### Jenkins Example
```groovy
stage('Test') {
    steps {
        sh './scripts/ci_test_runner.sh --suite all --report-dir reports/'
    }
    post {
        always {
            junit 'reports/junit-*.xml'
            publishHTML([
                reportDir: 'reports/coverage_html',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
            ])
        }
    }
}
```

## Best Practices

1. **Use Markers**: Tag tests appropriately for better filtering
   ```python
   @pytest.mark.cache
   @pytest.mark.slow
   def test_large_cache_operations():
       ...
   ```

2. **Use Fixtures**: Leverage the fixture hierarchy
   ```python
   def test_with_user(test_user, simple_cache):
       simple_cache.set(f"user:{test_user['id']}", test_user)
       ...
   ```

3. **Parallel-Safe Tests**: Ensure tests can run in parallel
   - Use unique identifiers
   - Avoid shared state
   - Use fixtures for setup/teardown

4. **Timeout Appropriately**: Set realistic timeouts
   ```python
   @pytest.mark.timeout(60)  # 60 seconds
   def test_slow_operation():
       ...
   ```

5. **Generate Reports**: Always run with reporting for CI
   ```bash
   python scripts/test_orchestrator.py run --suite all --coverage
   ```

## Migration from Old Test Runners

### Old Way
```bash
python scripts/test_runner.py run -s unit --parallel
```

### New Way
```bash
python scripts/test_orchestrator.py run --suite unit --parallel --workers 4
```

### Key Changes
- `run -s` → `run --suite`
- `--parallel` now requires `--workers N`
- Reports auto-generated in `test-reports/`
- Coverage integrated via `--coverage` flag

---

**For full details**, see:
- `PHASE2_IMPLEMENTATION_SUMMARY.md` - Complete implementation overview
- `tests/conftest_new.py` - Fixture documentation
- `scripts/test_orchestrator.py` - Orchestrator source code
