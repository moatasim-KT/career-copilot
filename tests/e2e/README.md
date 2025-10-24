# E2E Testing Framework for Career Copilot

This directory contains a comprehensive end-to-end testing framework for the Career Copilot application.

## Tech Stack

- **Frontend**: Next.js/React with TypeScript
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL

## Framework Components

### Core Components

- **`orchestrator.py`**: Main test orchestrator that coordinates test execution
- **`base.py`**: Base test classes for different types of E2E tests
- **`utils.py`**: Utility functions, test data generators, and helper classes
- **`conftest.py`**: Pytest fixtures and configuration for E2E tests

### Test Categories

1. **Configuration Tests**: Validate environment setup and configuration files
2. **Service Health Tests**: Check if all services are running and healthy
3. **Feature Tests**: Test individual application features end-to-end
4. **Integration Tests**: Test complete workflows across multiple components

## Quick Start

### Running the Demo

```bash
# Run the demo script to see the framework in action
PYTHONPATH=. python tests/e2e/demo.py
```

### Running Framework Tests

```bash
# Test the framework itself
python -m pytest tests/e2e/test_framework.py -v
```

### Using the Orchestrator

```python
import asyncio
from tests.e2e.orchestrator import TestOrchestrator

async def run_tests():
    orchestrator = TestOrchestrator()
    
    # Run all tests
    results = await orchestrator.run_full_test_suite()
    
    # Or run specific categories
    results = await orchestrator.run_selective_tests(["configuration", "health"])
    
    # Generate and save report
    report_path = orchestrator.save_report()
    print(f"Report saved to: {report_path}")

asyncio.run(run_tests())
```

## Configuration

### Environment Variables

- `E2E_BACKEND_URL`: Backend API URL (default: http://localhost:8000)
- `E2E_FRONTEND_URL`: Frontend URL (default: http://localhost:3000)
- `E2E_DATABASE_URL`: Database connection string

### Test Configuration

The framework uses `test_config.json` for detailed test configuration including:
- Test scenarios and methods
- Timeout settings
- Retry policies
- Validation thresholds

## Writing Custom Tests

### Creating a Configuration Test

```python
from tests.e2e.base import ConfigurationTestBase

class MyConfigTest(ConfigurationTestBase):
    async def run_test(self):
        # Your test logic here
        if some_validation_fails:
            self.add_validation_error("Validation failed")
        
        return {
            "test_name": "my_config_test",
            "status": "failed" if self.has_validation_errors() else "passed"
        }
```

### Creating a Service Health Test

```python
from tests.e2e.base import ServiceHealthTestBase

class MyHealthTest(ServiceHealthTestBase):
    async def run_test(self):
        # Check service health
        self.add_health_result("my_service", True, 0.5)
        
        return {
            "test_name": "my_health_test",
            "unhealthy_services": self.get_unhealthy_services()
        }
```

## Test Reports

The framework generates comprehensive test reports in JSON and HTML formats:

- **JSON Reports**: Machine-readable format in `tests/e2e/reports/`
- **HTML Reports**: Human-readable format with visual styling
- **Console Output**: Real-time test progress and summary

## Pytest Integration

The framework integrates seamlessly with pytest:

```bash
# Run E2E tests with pytest
python -m pytest tests/e2e/ -v -m e2e

# Run specific test categories
python -m pytest tests/e2e/ -v -m e2e_config
python -m pytest tests/e2e/ -v -m e2e_health
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Always clean up test data and resources in teardown methods
3. **Timeouts**: Set appropriate timeouts for different types of tests
4. **Error Handling**: Provide meaningful error messages and context
5. **Documentation**: Document test scenarios and expected outcomes

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure to set `PYTHONPATH=.` when running scripts
2. **Service Unavailable**: Ensure backend and frontend services are running
3. **Database Connection**: Verify database connection string and permissions
4. **Timeout Issues**: Adjust timeout settings in configuration

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.getLogger("e2e_orchestrator").setLevel(logging.DEBUG)
```

## Contributing

When adding new E2E tests:

1. Follow the existing patterns and base classes
2. Add appropriate markers for test categorization
3. Update configuration files if needed
4. Document new test scenarios
5. Ensure tests are deterministic and reliable