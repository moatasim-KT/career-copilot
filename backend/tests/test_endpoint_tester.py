"""
Tests for the Endpoint Tester
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from app.testing import EndpointDiscovery, EndpointTester, TestStatus


@pytest.fixture
def app():
    """Create a test FastAPI application"""
    return create_app()


@pytest.fixture
def tester(app):
    """Create an EndpointTester instance"""
    return EndpointTester(app)


@pytest.fixture
def discovery(app):
    """Create an EndpointDiscovery instance"""
    return EndpointDiscovery(app)


def test_endpoint_tester_initialization(app):
    """Test that EndpointTester can be initialized"""
    tester = EndpointTester(app)
    assert tester.app == app
    assert tester.client is not None
    assert tester.discovery is not None
    assert tester.data_generator is not None
    assert tester.test_results == []


def test_test_root_endpoint(tester, discovery):
    """Test the root endpoint"""
    discovery.discover_endpoints()
    root_endpoint = discovery.get_endpoint_by_path("GET", "/")

    if root_endpoint:
        result = tester.test_endpoint(root_endpoint)

        assert result is not None
        assert result.endpoint == "/"
        assert result.method == "GET"
        assert result.status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]
        assert result.status_code > 0
        assert result.response_time >= 0


def test_test_health_endpoint(tester, discovery):
    """Test a health check endpoint"""
    discovery.discover_endpoints()
    health_endpoints = [e for e in discovery._endpoints if "health" in e.path.lower()]

    if health_endpoints:
        result = tester.test_endpoint(health_endpoints[0])

        assert result is not None
        assert result.status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]
        assert result.response_time >= 0


def test_test_result_structure(tester, discovery):
    """Test that TestResult has correct structure"""
    discovery.discover_endpoints()
    if discovery._endpoints:
        result = tester.test_endpoint(discovery._endpoints[0])

        assert hasattr(result, "endpoint")
        assert hasattr(result, "method")
        assert hasattr(result, "status")
        assert hasattr(result, "status_code")
        assert hasattr(result, "response_time")
        assert hasattr(result, "test_type")
        assert hasattr(result, "error_message")
        assert hasattr(result, "request_data")
        assert hasattr(result, "response_data")
        assert hasattr(result, "validation_result")
        assert hasattr(result, "timestamp")


def test_test_result_to_dict(tester, discovery):
    """Test converting TestResult to dictionary"""
    discovery.discover_endpoints()
    if discovery._endpoints:
        result = tester.test_endpoint(discovery._endpoints[0])
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "endpoint" in result_dict
        assert "method" in result_dict
        assert "status" in result_dict
        assert "status_code" in result_dict
        assert "response_time" in result_dict


def test_test_all_endpoints(tester):
    """Test running tests on all endpoints"""
    results = tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(r.status, TestStatus) for r in results)


def test_generate_test_report(tester):
    """Test generating a test report"""
    # Run some tests first
    tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

    # Generate report
    report = tester.generate_test_report(output_format="dict")

    assert isinstance(report, dict)
    assert "summary" in report
    assert "results_by_endpoint" in report
    assert "results_by_status" in report
    assert "all_results" in report

    # Check summary structure
    summary = report["summary"]
    assert "total_tests" in summary
    assert "passed" in summary
    assert "failed" in summary
    assert "errors" in summary
    assert "pass_rate" in summary
    assert "average_response_time" in summary


def test_generate_json_report(tester):
    """Test generating a JSON report"""
    # Run some tests first
    tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

    # Generate JSON report
    json_report = tester.generate_test_report(output_format="json")

    assert isinstance(json_report, str)
    assert len(json_report) > 0

    # Should be valid JSON
    import json

    parsed = json.loads(json_report)
    assert isinstance(parsed, dict)


def test_generate_html_report(tester):
    """Test generating an HTML report"""
    # Run some tests first
    tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

    # Generate HTML report
    html_report = tester.generate_test_report(output_format="html")

    assert isinstance(html_report, str)
    assert len(html_report) > 0
    assert "<!DOCTYPE html>" in html_report
    assert "<html>" in html_report
    assert "</html>" in html_report


def test_get_failed_tests(tester):
    """Test retrieving failed tests"""
    # Run some tests
    tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

    failed_tests = tester.get_failed_tests()

    assert isinstance(failed_tests, list)
    assert all(r.status == TestStatus.FAILED for r in failed_tests)


def test_get_error_tests(tester):
    """Test retrieving error tests"""
    # Run some tests
    tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

    error_tests = tester.get_error_tests()

    assert isinstance(error_tests, list)
    assert all(r.status == TestStatus.ERROR for r in error_tests)


def test_get_slow_tests(tester):
    """Test retrieving slow tests"""
    # Run some tests
    tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

    slow_tests = tester.get_slow_tests(threshold=0.5)

    assert isinstance(slow_tests, list)
    assert all(r.response_time > 0.5 for r in slow_tests)


def test_validation_result_structure():
    """Test ValidationResult structure"""
    from app.testing.endpoint_tester import ValidationResult

    result = ValidationResult(is_valid=True)

    assert result.is_valid is True
    assert result.errors == []
    assert result.warnings == []

    result.add_error("Test error")
    assert result.is_valid is False
    assert len(result.errors) == 1

    result.add_warning("Test warning")
    assert len(result.warnings) == 1


def test_test_status_enum():
    """Test TestStatus enum"""
    assert TestStatus.PASSED.value == "passed"
    assert TestStatus.FAILED.value == "failed"
    assert TestStatus.ERROR.value == "error"
    assert TestStatus.SKIPPED.value == "skipped"


def test_prepare_path(tester):
    """Test path parameter replacement"""
    path = "/api/v1/jobs/{job_id}"
    test_data = {"job_id": 123}

    prepared_path = tester._prepare_path(path, test_data)

    assert prepared_path == "/api/v1/jobs/123"
    assert "{job_id}" not in prepared_path


def test_extract_query_params(tester):
    """Test query parameter extraction"""
    test_data = {"skip": 0, "limit": 10, "query": "test", "body": {"data": "value"}}

    query_params = tester._extract_query_params(test_data)

    assert isinstance(query_params, dict)
    assert "skip" in query_params
    assert "limit" in query_params
    assert "query" in query_params
    assert "body" not in query_params


def test_test_endpoint_with_custom_data(tester, discovery):
    """Test endpoint with custom test data"""
    discovery.discover_endpoints()
    root_endpoint = discovery.get_endpoint_by_path("GET", "/")

    if root_endpoint:
        custom_data = {}
        result = tester.test_endpoint(root_endpoint, test_data=custom_data, test_type="custom")

        assert result is not None
        assert result.test_type == "custom"


def test_test_endpoint_with_multiple_cases(tester, discovery):
    """Test endpoint with multiple test cases"""
    discovery.discover_endpoints()
    root_endpoint = discovery.get_endpoint_by_path("GET", "/")

    if root_endpoint:
        results = tester.test_endpoint_with_multiple_cases(root_endpoint)

        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r.status, TestStatus) for r in results)


def test_export_results_to_json(tester, tmp_path):
    """Test exporting results to JSON file"""
    # Run some tests
    tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

    # Export to file
    output_file = tmp_path / "test_results.json"
    tester.export_results_to_json(str(output_file))

    assert output_file.exists()

    # Verify file content
    import json

    with open(output_file) as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert "summary" in data


def test_export_results_to_html(tester, tmp_path):
    """Test exporting results to HTML file"""
    # Run some tests
    tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

    # Export to file
    output_file = tmp_path / "test_results.html"
    tester.export_results_to_html(str(output_file))

    assert output_file.exists()

    # Verify file content
    with open(output_file) as f:
        content = f.read()

    assert "<!DOCTYPE html>" in content
    assert "<html>" in content


def test_response_time_measurement(tester, discovery):
    """Test that response time is measured"""
    discovery.discover_endpoints()
    if discovery._endpoints:
        result = tester.test_endpoint(discovery._endpoints[0])

        assert result.response_time >= 0
        assert isinstance(result.response_time, float)


def test_test_result_repr(tester, discovery):
    """Test TestResult string representation"""
    discovery.discover_endpoints()
    if discovery._endpoints:
        result = tester.test_endpoint(discovery._endpoints[0])
        repr_str = repr(result)

        assert isinstance(repr_str, str)
        assert result.method in repr_str
        assert result.endpoint in repr_str
