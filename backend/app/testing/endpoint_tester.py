"""
Endpoint Testing Framework

Provides comprehensive testing capabilities for FastAPI endpoints.
"""

import json
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger

from .endpoint_discovery import EndpointDiscovery, EndpointInfo
from .test_data_generator import TestDataGenerator, TestDataType

logger = get_logger(__name__)


class TestStatus(str, Enum):
	"""Status of a test execution"""

	PASSED = "passed"
	FAILED = "failed"
	ERROR = "error"
	SKIPPED = "skipped"


@dataclass
class ValidationResult:
	"""Result of response validation."""

	is_valid: bool
	errors: List[str] = field(default_factory=list)
	warnings: List[str] = field(default_factory=list)

	def add_error(self, error: str) -> None:
		"""Add an error message and mark the validation as failed."""
		self.errors.append(error)
		self.is_valid = False

	def add_warning(self, warning: str) -> None:
		"""Record a warning while leaving validity unchanged."""
		self.warnings.append(warning)


@dataclass
class TestResult:
	"""Comprehensive result of an endpoint test"""

	endpoint: str
	method: str
	status: TestStatus
	status_code: int
	response_time: float
	test_type: str = "valid"
	error_message: Optional[str] = None
	request_data: Optional[Dict[str, Any]] = None
	response_data: Optional[Any] = None
	validation_result: Optional[ValidationResult] = None
	timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

	def __repr__(self) -> str:
		return f"<TestResult {self.method} {self.endpoint}: {self.status.value} ({self.status_code})>"

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for serialization."""
		return {
			"endpoint": self.endpoint,
			"method": self.method,
			"status": self.status.value,
			"status_code": self.status_code,
			"response_time": self.response_time,
			"test_type": self.test_type,
			"error_message": self.error_message,
			"request_data": self.request_data,
			"response_data": self.response_data,
			"validation_errors": self.validation_result.errors if self.validation_result else [],
			"validation_warnings": self.validation_result.warnings if self.validation_result else [],
			"timestamp": self.timestamp,
		}


class EndpointTester:
	"""
	Comprehensive endpoint testing framework.

	This class provides automated testing capabilities including:
	- Testing individual endpoints with various data types
	- Validating responses against expected schemas
	- Generating detailed test reports
	- Performance measurement
	"""

	def __init__(self, app: FastAPI, base_url: str = "http://testserver"):
		"""
		Initialize the endpoint tester.

		Args:
		    app: The FastAPI application instance
		    base_url: Base URL for test requests
		"""
		self.app = app
		self.base_url = base_url
		self.client = TestClient(app)
		self.discovery = EndpointDiscovery(app)
		self.data_generator = TestDataGenerator(seed=42)  # Use seed for reproducibility
		self.test_results: List[TestResult] = []

	def test_endpoint(self, endpoint: EndpointInfo, test_data: Optional[Dict[str, Any]] = None, test_type: str = "valid") -> TestResult:
		"""
		Test a single endpoint with provided or generated test data.

		Args:
		    endpoint: The endpoint to test
		    test_data: Test data to use (if None, will be generated)
		    test_type: Type of test being performed

		Returns:
		    TestResult object with test outcome
		"""
		logger.debug("Testing endpoint %s %s with case '%s'", endpoint.method, endpoint.path, test_type)

		# Generate test data if not provided
		if test_data is None:
			test_data = self.data_generator.generate_test_data(endpoint, TestDataType.VALID)

		# Prepare request
		path = self._prepare_path(endpoint.path, test_data)
		query_params = self._extract_query_params(test_data)
		body = test_data.get("body")

		# Execute request and measure time
		start_time = time.time()
		try:
			response = self._execute_request(endpoint.method, path, query_params, body)
			response_time = time.time() - start_time

			# Validate response
			validation_result = self._validate_response(response, endpoint)

			# Determine test status
			if response.status_code >= 500:
				status = TestStatus.ERROR
				error_message = f"Server error: {response.status_code}"
			elif response.status_code >= 400:
				if test_type == "invalid" or test_type == "missing_required":
					# Expected error for invalid data
					status = TestStatus.PASSED
					error_message = None
				else:
					status = TestStatus.FAILED
					error_message = f"Client error: {response.status_code}"
			else:
				if validation_result.is_valid:
					status = TestStatus.PASSED
					error_message = None
				else:
					status = TestStatus.FAILED
					error_message = f"Validation failed: {', '.join(validation_result.errors)}"

			# Parse response data
			try:
				response_data = response.json()
			except Exception:
				response_data = response.text

			result = TestResult(
				endpoint=endpoint.path,
				method=endpoint.method,
				status=status,
				status_code=response.status_code,
				response_time=response_time,
				test_type=test_type,
				error_message=error_message,
				request_data=test_data,
				response_data=response_data,
				validation_result=validation_result,
			)
			logger.info(
				"Test finished for %s %s: status=%s code=%s",
				endpoint.method,
				endpoint.path,
				status.value,
				response.status_code,
			)
			return result

		except Exception as e:
			response_time = time.time() - start_time
			logger.exception("Exception during test for %s %s", endpoint.method, endpoint.path)
			return TestResult(
				endpoint=endpoint.path,
				method=endpoint.method,
				status=TestStatus.ERROR,
				status_code=0,
				response_time=response_time,
				test_type=test_type,
				error_message=f"Exception during test: {e!s}\n{traceback.format_exc()}",
				request_data=test_data,
			)

	def test_all_endpoints(self, skip_deprecated: bool = True, skip_auth_required: bool = False) -> List[TestResult]:
		"""
		Test all discovered endpoints.

		Args:
		    skip_deprecated: Whether to skip deprecated endpoints
		    skip_auth_required: Whether to skip endpoints requiring authentication

		Returns:
		    List of TestResult objects
		"""
		logger.info(
			"Running endpoint test sweep (skip_deprecated=%s, skip_auth_required=%s)",
			skip_deprecated,
			skip_auth_required,
		)
		endpoints = self.discovery.discover_endpoints()
		self.test_results = []
		skipped = 0

		for endpoint in endpoints:
			# Skip based on filters
			if skip_deprecated and endpoint.deprecated:
				skipped += 1
				continue
			if skip_auth_required and endpoint.requires_auth:
				skipped += 1
				continue

			# Skip WebSocket endpoints
			if "/ws" in endpoint.path:
				skipped += 1
				continue

			# Test with valid data
			try:
				result = self.test_endpoint(endpoint, test_type="valid")
				self.test_results.append(result)
			except Exception as e:
				# Record error
				self.test_results.append(
					TestResult(
						endpoint=endpoint.path,
						method=endpoint.method,
						status=TestStatus.ERROR,
						status_code=0,
						response_time=0,
						error_message=f"Failed to test endpoint: {e!s}",
					)
				)

		logger.info(
			"Endpoint sweep complete: %d tested, %d skipped",
			len(self.test_results),
			skipped,
		)
		return self.test_results

	def test_endpoint_with_multiple_cases(self, endpoint: EndpointInfo) -> List[TestResult]:
		"""
		Test an endpoint with multiple test cases (valid, invalid, edge cases).

		Args:
		    endpoint: The endpoint to test

		Returns:
		    List of TestResult objects
		"""
		results: List[TestResult] = []

		# Generate multiple test cases
		test_cases = self.data_generator.generate_multiple_test_cases(endpoint)
		logger.debug(
			"Generated %d test cases for %s %s",
			len(test_cases),
			endpoint.method,
			endpoint.path,
		)

		for test_case in test_cases:
			test_type = test_case.get("type", "valid")
			test_data = test_case.get("data")

			result = self.test_endpoint(endpoint, test_data, test_type)
			results.append(result)

		return results

	def _prepare_path(self, path: str, test_data: Dict[str, Any]) -> str:
		"""
		Prepare the path by replacing path parameters with values.

		Args:
		    path: The endpoint path template
		    test_data: Test data containing parameter values

		Returns:
		    Path with parameters replaced
		"""
		prepared_path = path

		# Replace path parameters
		for key, value in test_data.items():
			if key != "body" and f"{{{key}}}" in prepared_path:
				prepared_path = prepared_path.replace(f"{{{key}}}", str(value))

		return prepared_path

	def _extract_query_params(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Extract query parameters from test data.

		Args:
		    test_data: Test data dictionary

		Returns:
		    Dictionary of query parameters
		"""
		query_params = {}

		for key, value in test_data.items():
			if key != "body" and not isinstance(value, dict):
				query_params[key] = value

		return query_params

	def _execute_request(self, method: str, path: str, query_params: Dict[str, Any], body: Optional[Any]) -> Any:
		"""
		Execute an HTTP request.

		Args:
		    method: HTTP method
		    path: Request path
		    query_params: Query parameters
		    body: Request body

		Returns:
		    Response object
		"""
		method = method.upper()

		logger.debug("Executing %s %s with params=%s", method, path, query_params)

		if method == "GET":
			return self.client.get(path, params=query_params)
		elif method == "POST":
			return self.client.post(path, params=query_params, json=body)
		elif method == "PUT":
			return self.client.put(path, params=query_params, json=body)
		elif method == "PATCH":
			return self.client.patch(path, params=query_params, json=body)
		elif method == "DELETE":
			return self.client.delete(path, params=query_params)
		else:
			raise ValueError(f"Unsupported HTTP method: {method}")

	def _validate_response(self, response: Any, endpoint: EndpointInfo) -> ValidationResult:
		"""
		Validate a response against expected schema.

		Args:
		    response: The response object
		    endpoint: The endpoint information

		Returns:
		    ValidationResult object
		"""
		result = ValidationResult(is_valid=True)

		# Check status code
		if response.status_code != endpoint.status_code and response.status_code < 400:
			result.add_warning(f"Status code {response.status_code} differs from expected {endpoint.status_code}")

		# Check response format
		if response.status_code < 400:
			try:
				response_data = response.json()

				# If response model is defined, validate against it
				if endpoint.response_model:
					try:
						# Try to validate response data
						if isinstance(endpoint.response_model, type) and issubclass(endpoint.response_model, BaseModel):
							# Validate single model
							endpoint.response_model.model_validate(response_data)
						elif hasattr(endpoint.response_model, "__origin__"):
							# Handle List[Model] or other generic types
							pass  # Skip validation for complex generic types
					except ValidationError as e:
						result.add_error(f"Response validation failed: {e!s}")
					except Exception as e:
						result.add_warning(f"Could not validate response: {e!s}")

			except json.JSONDecodeError:
				# Response is not JSON
				if endpoint.response_model:
					result.add_warning("Response is not JSON but model expects JSON")

		return result

	def generate_test_report(self, output_format: str = "dict") -> Union[Dict[str, Any], str]:
		"""
		Generate a comprehensive test report.

		Args:
		    output_format: Format of the report (dict, json, html)

		Returns:
		    Report in requested format
		"""
		if not self.test_results:
			logger.warning("generate_test_report called before any tests were executed")
			return {"error": "No test results available"}

		# Calculate statistics
		total_tests = len(self.test_results)
		passed = len([r for r in self.test_results if r.status == TestStatus.PASSED])
		failed = len([r for r in self.test_results if r.status == TestStatus.FAILED])
		errors = len([r for r in self.test_results if r.status == TestStatus.ERROR])
		skipped = len([r for r in self.test_results if r.status == TestStatus.SKIPPED])

		avg_response_time = sum(r.response_time for r in self.test_results) / total_tests if total_tests > 0 else 0

		# Group by endpoint
		by_endpoint = {}
		for result in self.test_results:
			key = f"{result.method} {result.endpoint}"
			if key not in by_endpoint:
				by_endpoint[key] = []
			by_endpoint[key].append(result)

		# Group by status
		by_status = {
			"passed": [r for r in self.test_results if r.status == TestStatus.PASSED],
			"failed": [r for r in self.test_results if r.status == TestStatus.FAILED],
			"error": [r for r in self.test_results if r.status == TestStatus.ERROR],
			"skipped": [r for r in self.test_results if r.status == TestStatus.SKIPPED],
		}

		report = {
			"summary": {
				"total_tests": total_tests,
				"passed": passed,
				"failed": failed,
				"errors": errors,
				"skipped": skipped,
				"pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
				"average_response_time": avg_response_time,
				"timestamp": datetime.now().isoformat(),
			},
			"results_by_endpoint": {key: [r.to_dict() for r in results] for key, results in by_endpoint.items()},
			"results_by_status": {status: [r.to_dict() for r in results] for status, results in by_status.items()},
			"all_results": [r.to_dict() for r in self.test_results],
		}

		logger.debug("Generated test report in %s format", output_format)
		if output_format == "json":
			return json.dumps(report, indent=2)
		elif output_format == "html":
			return self._generate_html_report(report)
		else:
			return report

	def _generate_html_report(self, report: Dict[str, Any]) -> str:
		"""
		Generate an HTML test report.

		Args:
		    report: Report dictionary

		Returns:
		    HTML string
		"""
		summary = report["summary"]

		html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Endpoint Test Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-card.passed {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }}
        .stat-card.failed {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }}
        .stat-card.error {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
        }}
        .stat-card h3 {{
            margin: 0;
            font-size: 2em;
            color: #333;
        }}
        .stat-card p {{
            margin: 5px 0 0 0;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-passed {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-failed {{
            color: #dc3545;
            font-weight: bold;
        }}
        .status-error {{
            color: #ffc107;
            font-weight: bold;
        }}
        .response-time {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Endpoint Test Report</h1>
        <p>Generated: {summary["timestamp"]}</p>
        
        <div class="summary">
            <div class="stat-card">
                <h3>{summary["total_tests"]}</h3>
                <p>Total Tests</p>
            </div>
            <div class="stat-card passed">
                <h3>{summary["passed"]}</h3>
                <p>Passed</p>
            </div>
            <div class="stat-card failed">
                <h3>{summary["failed"]}</h3>
                <p>Failed</p>
            </div>
            <div class="stat-card error">
                <h3>{summary["errors"]}</h3>
                <p>Errors</p>
            </div>
            <div class="stat-card">
                <h3>{summary["pass_rate"]:.1f}%</h3>
                <p>Pass Rate</p>
            </div>
            <div class="stat-card">
                <h3>{summary["average_response_time"]:.3f}s</h3>
                <p>Avg Response Time</p>
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Endpoint</th>
                    <th>Method</th>
                    <th>Status</th>
                    <th>Status Code</th>
                    <th>Response Time</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
"""

		for result in report["all_results"]:
			status_class = f"status-{result['status']}"
			error_msg = result.get("error_message", "")[:100] if result.get("error_message") else "-"

			html += f"""
                <tr>
                    <td>{result["endpoint"]}</td>
                    <td>{result["method"]}</td>
                    <td class="{status_class}">{result["status"].upper()}</td>
                    <td>{result["status_code"]}</td>
                    <td class="response-time">{result["response_time"]:.3f}s</td>
                    <td>{error_msg}</td>
                </tr>
"""

		html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

		return html

	def get_failed_tests(self) -> List[TestResult]:
		"""Get all failed tests."""
		return [r for r in self.test_results if r.status == TestStatus.FAILED]

	def get_error_tests(self) -> List[TestResult]:
		"""Get all tests with execution errors."""
		return [r for r in self.test_results if r.status == TestStatus.ERROR]

	def get_slow_tests(self, threshold: float = 1.0) -> List[TestResult]:
		"""
		Get tests that exceeded a response time threshold.

		Args:
		    threshold: Response time threshold in seconds

		Returns:
		    List of slow tests
		"""
		return [r for r in self.test_results if r.response_time > threshold]

	def export_results_to_json(self, filepath: str) -> None:
		"""
		Export test results to a JSON file.

		Args:
		    filepath: Path to output file
		"""
		report = self.generate_test_report(output_format="dict")
		with open(filepath, "w", encoding="utf-8") as f:
			json.dump(report, f, indent=2)
		logger.info("Wrote JSON test report to %s", filepath)

	def export_results_to_html(self, filepath: str) -> None:
		"""
		Export test results to an HTML file.

		Args:
		    filepath: Path to output file
		"""
		html = self.generate_test_report(output_format="html")
		with open(filepath, "w", encoding="utf-8") as f:
			f.write(html)
		logger.info("Wrote HTML test report to %s", filepath)
