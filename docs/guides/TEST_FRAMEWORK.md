# Test Framework Documentation

## Overview

This document provides comprehensive guidance for using the CareerCopilot test framework, updated to reflect the consolidated architecture with streamlined services and reduced file count. The framework has been optimized to work with the new consolidated service structure while maintaining comprehensive test coverage.

## Table of Contents

1. [Installation](#installation)
2. [CLI Usage](#cli-usage)
3. [Test Configuration](#test-configuration)
4. [Consolidated Architecture Testing](#consolidated-architecture-testing)
5. [CI/CD Integration](#cicd-integration)
6. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip
- virtualenv or venv

### Setup

1. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

## CLI Usage

The test framework provides a command-line interface for running tests:

### Basic Usage

```bash
# Run all tests
python scripts/test_runner.py run

# Run specific test suite
python scripts/test_runner.py run --suite unit

# Run multiple suites
python scripts/test_runner.py run --suite unit --suite integration

# Run tests with specific markers
python scripts/test_runner.py run --marker slow --marker important
```

### Advanced Options

- `--parallel/--no-parallel`: Enable/disable parallel test execution
- `--workers N`: Set number of worker processes
- `--report DIR`: Specify report directory
- `--verbose`: Enable verbose output
- `--fail-fast`: Stop on first failure
- `--config FILE`: Use custom config file
- `--timeout SECONDS`: Set test timeout

## Test Configuration

### Configuration File

Create a `test_config.json` file:

```json
{
    "test_paths": ["tests"],
    "markers": ["important"],
    "parallel": true,
    "max_workers": 4,
    "report_path": "test-reports",
    "verbose": false,
    "fail_fast": false,
    "timeout": 300
}
```

### Environment Variables

Important environment variables:

- `PYTEST_TIMEOUT`: Global test timeout
- `TEST_ENV`: Test environment (test/staging/prod)
- `DB_URL`: Database connection URL
- `API_KEY`: API authentication key
- `TEST_CONSOLIDATED_SERVICES`: Enable testing of consolidated services
- `COMPATIBILITY_LAYER_ENABLED`: Test compatibility layer functionality

## Consolidated Architecture Testing

### Testing Consolidated Services

The consolidated architecture requires specific testing approaches:

#### Service Integration Testing

```python
# Test consolidated analytics service
def test_analytics_service_consolidation():
    """Test that consolidated AnalyticsService maintains all functionality."""
    from backend.app.services.analytics_service import AnalyticsService
    
    service = AnalyticsService()
    
    # Test core analytics functionality (from original analytics.py)
    assert service.collect_event("test_event", {"data": "value"})
    
    # Test data collection functionality (from analytics_data_collection_service.py)
    assert service.process_analytics(batch_size=10)
    
    # Test metrics functionality
    metrics = service.get_metrics("user_engagement", "daily")
    assert metrics is not None
```

#### Import Compatibility Testing

```python
# Test backward compatibility
def test_import_compatibility():
    """Test that old import paths still work through compatibility layer."""
    # This should work but show deprecation warning
    with pytest.warns(DeprecationWarning):
        from backend.app.services.analytics import Analytics
    
    # New import should work without warnings
    from backend.app.services.analytics_service import AnalyticsService
```

#### Consolidated Service Coverage

Test suites now focus on:

- **Core Service Functionality**: Test main consolidated service interfaces
- **Specialized Service Features**: Test domain-specific consolidated services  
- **Migration Compatibility**: Ensure old interfaces still work
- **Performance Impact**: Verify consolidation doesn't degrade performance

### E2E Test Consolidation

E2E tests have been reduced from 40+ to 15 files while maintaining coverage:

```bash
# Run consolidated E2E tests
python scripts/test_runner.py run --suite e2e

# Test specific consolidated workflows
python scripts/test_runner.py run --suite e2e --marker job_management
python scripts/test_runner.py run --suite e2e --marker analytics_flow
```

## CI/CD Integration

### GitHub Actions Integration

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Run Tests
        run: |
          bash scripts/ci_test_runner.sh --suite all
```

### Jenkins Pipeline Integration

```groovy
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh 'bash scripts/ci_test_runner.sh --suite all --report jenkins-reports'
            }
            post {
                always {
                    junit 'jenkins-reports/junit.xml'
                }
            }
        }
    }
}
```

## Troubleshooting

### Common Issues

1. **Tests Hanging**
   - Check test timeouts
   - Verify database connections
   - Check for deadlocks in parallel execution

2. **Database Connection Issues**
   - Verify environment variables
   - Check database service is running
   - Confirm network connectivity

3. **Parallel Test Failures**
   - Reduce number of workers
   - Check for resource contention
   - Verify test isolation

4. **Consolidated Service Import Errors**
   - Verify new import paths are correct
   - Check compatibility layer is enabled
   - Ensure consolidated services are properly initialized

5. **Missing Test Coverage After Consolidation**
   - Review consolidated test suites
   - Check that all original functionality is covered
   - Verify E2E tests cover consolidated workflows

### Debug Mode

Enable debug mode for more detailed output:

```bash
python scripts/test_runner.py run --verbose --debug
```

### Logs

Test logs are stored in:

- `test-reports/test.log`: General test log
- `test-reports/debug.log`: Debug information
- `test-reports/error.log`: Error traces

### Getting Help

For additional help:

```bash
python scripts/test_runner.py --help
python scripts/test_runner.py run --help
```

## Best Practices

1. **Test Organization**
   - Keep tests in appropriate suites
   - Use meaningful markers
   - Maintain test isolation

2. **Configuration Management**
   - Use environment-specific config files
   - Don't commit sensitive data
   - Version control test configs

3. **CI/CD Integration**
   - Regular test execution
   - Maintain build artifacts
   - Monitor test trends

## Contributing

To contribute to the test framework:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

For support:

- Create an issue in the repository
- Contact the development team
- Check the internal documentation