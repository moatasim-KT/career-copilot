# Endpoint Discovery and Testing Framework

A comprehensive framework for discovering, testing, and validating FastAPI endpoints in the Career Copilot application.

## Overview

This framework provides three main components:

1. **Endpoint Discovery** - Automatically discovers all FastAPI routes and extracts metadata
2. **Test Data Generation** - Generates valid, invalid, and edge case test data
3. **Endpoint Testing** - Tests endpoints with various data types and generates reports

## Components

### EndpointDiscovery

Discovers and catalogs all FastAPI endpoints with their metadata.

```python
from app.testing import EndpointDiscovery
from app.main import create_app

app = create_app()
discovery = EndpointDiscovery(app)

# Discover all endpoints
endpoints = discovery.discover_endpoints()

# Get statistics
stats = discovery.get_statistics()
print(f"Total endpoints: {stats['total_endpoints']}")

# Categorize by tags
categorized = discovery.categorize_endpoints()

# Get specific endpoint
endpoint = discovery.get_endpoint_by_path("GET", "/api/v1/jobs")
```

### TestDataGenerator

Generates test data for endpoint parameters.

```python
from app.testing import TestDataGenerator, TestDataType

generator = TestDataGenerator(seed=42)

# Generate valid job data
job_data = generator.generate_valid_job_data()

# Generate test data for an endpoint
test_data = generator.generate_test_data(endpoint, TestDataType.VALID)

# Generate multiple test cases
test_cases = generator.generate_multiple_test_cases(endpoint)
```

### EndpointTester

Tests endpoints and generates comprehensive reports.

```python
from app.testing import EndpointTester
from app.main import create_app

app = create_app()
tester = EndpointTester(app)

# Test all endpoints
results = tester.test_all_endpoints()

# Generate report
report = tester.generate_test_report(output_format="dict")

# Export to files
tester.export_results_to_json("test_results.json")
tester.export_results_to_html("test_results.html")

# Get failed tests
failed = tester.get_failed_tests()
```

## Usage

### Command Line

Use the provided script to test all endpoints:

```bash
# Test all endpoints and generate reports
python backend/scripts/testing/test_all_endpoints.py

# Generate HTML report
python backend/scripts/testing/test_all_endpoints.py --format html

# Test specific endpoint
python backend/scripts/testing/test_all_endpoints.py --endpoint "GET /api/v1/jobs"

# Skip deprecated endpoints
python backend/scripts/testing/test_all_endpoints.py --skip-deprecated

# Verbose output
python backend/scripts/testing/test_all_endpoints.py --verbose
```

### Programmatic Usage

```python
from app.main import create_app
from app.testing import EndpointDiscovery, EndpointTester

# Create app
app = create_app()

# Discover endpoints
discovery = EndpointDiscovery(app)
endpoints = discovery.discover_endpoints()

print(f"Discovered {len(endpoints)} endpoints")

# Test endpoints
tester = EndpointTester(app)
results = tester.test_all_endpoints()

# Generate report
report = tester.generate_test_report()
print(f"Pass rate: {report['summary']['pass_rate']:.1f}%")

# Export results
tester.export_results_to_json("results.json")
tester.export_results_to_html("results.html")
```

## Features

### Endpoint Discovery

- Automatically discovers all registered FastAPI routes
- Extracts comprehensive metadata:
  - Path and HTTP method
  - Parameters (path, query, body)
  - Request and response models
  - Authentication requirements
  - Tags and documentation
- Categorizes endpoints by tags
- Generates endpoint maps for reference

### Test Data Generation

- Generates contextual test data based on parameter names
- Supports multiple data types:
  - Integers (IDs, counts, limits)
  - Strings (emails, names, URLs)
  - Booleans
  - Floats (salaries, rates)
  - Dates and times
  - Lists and arrays
- Generates three types of test data:
  - **Valid**: Should pass validation
  - **Invalid**: Should fail validation
  - **Edge cases**: Boundary values, empty strings, etc.
- Provides pre-built generators for common entities:
  - Jobs
  - Applications
  - Users
  - Search queries

### Endpoint Testing

- Tests endpoints with generated or custom data
- Measures response times
- Validates responses against expected schemas
- Categorizes test results:
  - **Passed**: Successful test
  - **Failed**: Test failed validation
  - **Error**: Server error or exception
  - **Skipped**: Test was skipped
- Generates comprehensive reports:
  - Summary statistics
  - Results by endpoint
  - Results by status
  - Failed and error details
- Exports to multiple formats:
  - JSON (machine-readable)
  - HTML (human-readable)
  - Dictionary (programmatic access)

## Test Report Structure

### Summary

```json
{
  "summary": {
    "total_tests": 150,
    "passed": 140,
    "failed": 8,
    "errors": 2,
    "skipped": 0,
    "pass_rate": 93.3,
    "average_response_time": 0.125,
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

### Test Result

```json
{
  "endpoint": "/api/v1/jobs/{job_id}",
  "method": "GET",
  "status": "passed",
  "status_code": 200,
  "response_time": 0.045,
  "test_type": "valid",
  "error_message": null,
  "request_data": {"job_id": 123},
  "response_data": {"id": 123, "title": "Software Engineer"},
  "validation_errors": [],
  "validation_warnings": [],
  "timestamp": "2024-01-15T10:30:00"
}
```

## Running Tests

### Unit Tests

Test the framework itself:

```bash
# Test endpoint discovery
pytest backend/tests/test_endpoint_discovery.py -v

# Test data generator
pytest backend/tests/test_test_data_generator.py -v

# Test endpoint tester
pytest backend/tests/test_endpoint_tester.py -v

# Run all framework tests
pytest backend/tests/test_endpoint*.py backend/tests/test_test_data*.py -v
```

### Integration Tests

Test actual endpoints:

```bash
# Test all endpoints
python backend/scripts/testing/test_all_endpoints.py

# Generate detailed report
python backend/scripts/testing/test_all_endpoints.py --verbose --format both
```

## Configuration

### Test Data Generator

```python
# Use seed for reproducible tests
generator = TestDataGenerator(seed=42)

# Generate specific data types
job_data = generator.generate_valid_job_data()
user_data = generator.generate_valid_user_data()
search_data = generator.generate_search_query_data()
```

### Endpoint Tester

```python
# Configure test execution
tester = EndpointTester(app)

# Skip deprecated endpoints
results = tester.test_all_endpoints(skip_deprecated=True)

# Skip auth-required endpoints
results = tester.test_all_endpoints(skip_auth_required=True)

# Test with custom data
custom_data = {"job_id": 123}
result = tester.test_endpoint(endpoint, test_data=custom_data)
```

## Best Practices

1. **Run tests regularly** - Integrate into CI/CD pipeline
2. **Review failed tests** - Investigate and fix issues promptly
3. **Monitor response times** - Identify slow endpoints
4. **Use seeds for reproducibility** - Makes debugging easier
5. **Export reports** - Keep historical records
6. **Test edge cases** - Ensure robust error handling
7. **Validate responses** - Ensure data integrity

## Troubleshooting

### Common Issues

**Issue**: Tests fail with authentication errors

**Solution**: Use `skip_auth_required=True` or ensure test user exists

```python
results = tester.test_all_endpoints(skip_auth_required=True)
```

**Issue**: Slow test execution

**Solution**: Skip deprecated endpoints or test specific endpoints

```python
results = tester.test_all_endpoints(skip_deprecated=True)
```

**Issue**: Invalid test data

**Solution**: Use custom test data or adjust generator

```python
custom_data = {"job_id": 1, "status": "active"}
result = tester.test_endpoint(endpoint, test_data=custom_data)
```

## Examples

### Example 1: Discover and Test All Endpoints

```python
from app.main import create_app
from app.testing import EndpointDiscovery, EndpointTester

app = create_app()

# Discover
discovery = EndpointDiscovery(app)
endpoints = discovery.discover_endpoints()
print(f"Found {len(endpoints)} endpoints")

# Test
tester = EndpointTester(app)
results = tester.test_all_endpoints()

# Report
report = tester.generate_test_report()
print(f"Pass rate: {report['summary']['pass_rate']:.1f}%")
```

### Example 2: Test Specific Endpoint

```python
from app.main import create_app
from app.testing import EndpointDiscovery, EndpointTester

app = create_app()
discovery = EndpointDiscovery(app)
tester = EndpointTester(app)

# Get specific endpoint
endpoint = discovery.get_endpoint_by_path("GET", "/api/v1/jobs")

# Test with multiple cases
results = tester.test_endpoint_with_multiple_cases(endpoint)

for result in results:
    print(f"{result.test_type}: {result.status.value}")
```

### Example 3: Generate Custom Test Data

```python
from app.testing import TestDataGenerator

generator = TestDataGenerator(seed=42)

# Generate bulk data
jobs = generator.generate_bulk_operation_data(count=10)

# Generate edge cases
edge_strings = generator.generate_edge_case_strings()
edge_numbers = generator.generate_edge_case_numbers()
```

## API Reference

See the docstrings in each module for detailed API documentation:

- `endpoint_discovery.py` - Endpoint discovery classes and functions
- `test_data_generator.py` - Test data generation utilities
- `endpoint_tester.py` - Endpoint testing and reporting

## Contributing

When adding new features:

1. Add tests in `backend/tests/`
2. Update this README
3. Follow existing code patterns
4. Document new functionality

## License

Part of the Career Copilot application.
