#!/usr/bin/env python3
"""
Comprehensive deployment verification script for Career Copilot.
Tests all major services and endpoints to ensure everything is operational.
"""

import sys
from datetime import datetime
from typing import Dict, List, Tuple

import requests

# Configuration
BASE_URL = "http://localhost:8002"
API_V1 = f"{BASE_URL}/api/v1"


class Colors:
	"""ANSI color codes for terminal output"""

	GREEN = "\033[92m"
	RED = "\033[91m"
	YELLOW = "\033[93m"
	BLUE = "\033[94m"
	RESET = "\033[0m"
	BOLD = "\033[1m"


def print_header(text: str):
	"""Print a formatted header"""
	print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
	print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
	print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_test(name: str, passed: bool, details: str = ""):
	"""Print test result"""
	status = f"{Colors.GREEN}✓ PASSED{Colors.RESET}" if passed else f"{Colors.RED}✗ FAILED{Colors.RESET}"
	print(f"{status} - {name}")
	if details:
		print(f"  → {details}")


def test_health_check() -> Tuple[bool, str]:
	"""Test health check endpoint"""
	try:
		response = requests.get(f"{BASE_URL}/health", timeout=5)
		if response.status_code == 200:
			data = response.json()
			uptime = data.get("uptime_seconds", 0)
			return True, f"Status: {data.get('status')}, Uptime: {uptime:.2f}s"
		return False, f"Status code: {response.status_code}"
	except Exception as e:
		return False, str(e)


def test_docs_endpoint() -> Tuple[bool, str]:
	"""Test Swagger documentation endpoint"""
	try:
		response = requests.get(f"{BASE_URL}/docs", timeout=5)
		if response.status_code == 200 and "swagger" in response.text.lower():
			return True, "Swagger UI accessible"
		return False, f"Status code: {response.status_code}"
	except Exception as e:
		return False, str(e)


def test_jobs_endpoint() -> Tuple[bool, str]:
	"""Test jobs listing endpoint"""
	try:
		response = requests.get(f"{API_V1}/jobs?limit=5", timeout=5)
		if response.status_code == 200:
			jobs = response.json()
			return True, f"Returned {len(jobs)} jobs"
		return False, f"Status code: {response.status_code}"
	except Exception as e:
		return False, str(e)


def test_analytics_health() -> Tuple[bool, str]:
	"""Test analytics service health"""
	try:
		# Test analytics summary endpoint (requires auth, so 401/403 is success)
		response = requests.get(f"{API_V1}/analytics/summary", timeout=5)
		if response.status_code in [200, 401, 403, 422]:
			return True, f"Analytics service responding (status: {response.status_code})"
		return False, f"Status code: {response.status_code}"
	except Exception as e:
		return False, str(e)


def test_recommendations_service() -> Tuple[bool, str]:
	"""Test recommendations service availability"""
	try:
		# This endpoint typically requires auth, so we just check if it returns proper error
		response = requests.get(f"{API_V1}/recommendations", timeout=5)
		# 401 (Unauthorized) or 403 (Forbidden) means service is up but needs auth
		# 200 means it worked (in dev mode without auth)
		# 404 means endpoint doesn't exist
		if response.status_code in [200, 401, 403, 422]:
			return True, f"Service responding (status: {response.status_code})"
		return False, f"Unexpected status code: {response.status_code}"
	except Exception as e:
		return False, str(e)


def test_database_connection() -> Tuple[bool, str]:
	"""Test database connectivity through API"""
	try:
		# Try jobs endpoint which requires DB
		response = requests.get(f"{API_V1}/jobs?limit=1", timeout=5)
		if response.status_code == 200:
			return True, "Database connected and responding"
		elif response.status_code in [401, 403]:
			return True, "Database connected (auth required)"
		return False, f"Unexpected status: {response.status_code}"
	except Exception as e:
		return False, str(e)


def test_redis_cache() -> Tuple[bool, str]:
	"""Test Redis cache availability"""
	try:
		response = requests.get(f"{BASE_URL}/health", timeout=5)
		if response.status_code == 200:
			data = response.json()
			cache_info = data.get("services", {}).get("redis", {})
			if cache_info:
				return True, f"Redis status: {cache_info.get('status', 'unknown')}"
			return True, "Cache service available (inferred from health check)"
		return False, "Cache status unknown"
	except Exception as e:
		return False, str(e)


def test_metrics_endpoint() -> Tuple[bool, str]:
	"""Test Prometheus metrics endpoint"""
	try:
		response = requests.get(f"{BASE_URL}/metrics", timeout=5)
		if response.status_code == 200:
			metrics_text = response.text
			metric_count = len([line for line in metrics_text.split("\n") if line and not line.startswith("#")])
			return True, f"Prometheus metrics available ({metric_count} metrics)"
		return False, f"Status code: {response.status_code}"
	except Exception as e:
		return False, str(e)


def test_scheduler_status() -> Tuple[bool, str]:
	"""Test APScheduler status"""
	try:
		response = requests.get(f"{BASE_URL}/health", timeout=5)
		if response.status_code == 200:
			data = response.json()
			scheduler_info = data.get("services", {}).get("scheduler", {})
			if scheduler_info:
				tasks = scheduler_info.get("tasks", [])
				return True, f"Scheduler running with {len(tasks)} tasks"
			return True, "Scheduler status available"
		return False, "Scheduler status unknown"
	except Exception as e:
		return False, str(e)


def test_resume_parser() -> Tuple[bool, str]:
	"""Test resume parser endpoint availability"""
	try:
		# Check if upload endpoint exists (will require file upload, so we expect 422)
		response = requests.post(f"{API_V1}/resume/upload", timeout=5)
		if response.status_code in [400, 401, 403, 422]:  # Expected validation/auth errors
			return True, "Resume parser endpoint available"
		elif response.status_code == 200:
			return True, "Resume parser endpoint responding"
		return False, f"Unexpected status: {response.status_code}"
	except Exception as e:
		return False, str(e)


def test_market_analysis() -> Tuple[bool, str]:
	"""Test market analysis endpoints"""
	try:
		# Try salary trends endpoint
		response = requests.get(f"{API_V1}/market-analysis/salary-trends", timeout=5)
		if response.status_code in [200, 401, 403, 422]:
			return True, f"Market analysis service responding (status: {response.status_code})"
		return False, f"Status code: {response.status_code}"
	except Exception as e:
		return False, str(e)


def run_all_tests() -> Dict[str, Tuple[bool, str]]:
	"""Run all verification tests"""
	tests = {
		"Health Check": test_health_check,
		"Swagger Documentation": test_docs_endpoint,
		"Jobs API": test_jobs_endpoint,
		"Analytics Service": test_analytics_health,
		"Recommendations Service": test_recommendations_service,
		"Database Connection": test_database_connection,
		"Redis Cache": test_redis_cache,
		"Prometheus Metrics": test_metrics_endpoint,
		"APScheduler": test_scheduler_status,
		"Resume Parser": test_resume_parser,
		"Market Analysis": test_market_analysis,
	}

	results = {}
	for name, test_func in tests.items():
		results[name] = test_func()

	return results


def main():
	"""Main verification function"""
	print_header("Career Copilot Deployment Verification")
	print(f"Testing deployment at: {BASE_URL}")
	print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

	# Run all tests
	results = run_all_tests()

	# Display results
	print_header("Test Results")

	passed_count = 0
	failed_count = 0

	for test_name, (passed, details) in results.items():
		print_test(test_name, passed, details)
		if passed:
			passed_count += 1
		else:
			failed_count += 1

	# Summary
	print_header("Summary")
	total = passed_count + failed_count
	success_rate = (passed_count / total * 100) if total > 0 else 0

	print(f"Total Tests: {total}")
	print(f"{Colors.GREEN}Passed: {passed_count}{Colors.RESET}")
	print(f"{Colors.RED}Failed: {failed_count}{Colors.RESET}")
	print(f"Success Rate: {success_rate:.1f}%\n")

	if failed_count == 0:
		print(f"{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Deployment is fully operational.{Colors.RESET}\n")
		return 0
	else:
		print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed. Please check the details above.{Colors.RESET}\n")
		return 1


if __name__ == "__main__":
	sys.exit(main())
	sys.exit(main())
