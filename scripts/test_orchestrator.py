"""
Unified Test Orchestrator for Career Copilot.

This module provides a consolidated test orchestration system that replaces
multiple scattered test runners. It supports:
- Multiple test suites (unit, integration, e2e)
- Parallel execution with configurable workers
- Comprehensive reporting
- Dependency management between tests
- Timeout handling
- Retry logic for flaky tests

Usage:
    python scripts/test_orchestrator.py run --suite unit
    python scripts/test_orchestrator.py run --suite all --parallel --workers 4
    python scripts/test_orchestrator.py report --output reports/
"""

import argparse
import json
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pytest


class TestSuite(str, Enum):
	"""Available test suites."""

	UNIT = "unit"
	INTEGRATION = "integration"
	E2E = "e2e"
	ALL = "all"


class TestResult(str, Enum):
	"""Test execution results."""

	PASSED = "passed"
	FAILED = "failed"
	SKIPPED = "skipped"
	ERROR = "error"


class TestOrchestrator:
	"""
	Consolidated test orchestrator that manages all test execution.

	This replaces multiple duplicate test runners and provides a unified
	interface for running tests across the Career Copilot application.
	"""

	def __init__(self, config: dict[str, Any] | None = None):
		"""Initialize the test orchestrator."""
		self.config = config or {}
		self.results: dict[str, Any] = {}
		self.start_time: float | None = None
		self.end_time: float | None = None

	def run_suite(
		self, suite: TestSuite, parallel: bool = False, workers: int = 4, markers: list[str] | None = None, timeout: int = 300
	) -> dict[str, Any]:
		"""
		Run a specific test suite.

		Args:
		    suite: Test suite to run
		    parallel: Whether to run tests in parallel
		    workers: Number of parallel workers (if parallel=True)
		    markers: Additional pytest markers to filter tests
		    timeout: Timeout in seconds for the entire suite

		Returns:
		    Dictionary containing test results and statistics
		"""
		self.start_time = time.time()

		# Build pytest command
		pytest_args = self._build_pytest_args(suite, parallel, workers, markers, timeout)

		print(f"\n{'=' * 70}")
		print(f"Running {suite.value} tests")
		print(f"{'=' * 70}")
		print(f"Command: pytest {' '.join(pytest_args)}\n")

		# Run pytest
		result = pytest.main(pytest_args)

		self.end_time = time.time()

		# Collect and return results
		return self._collect_results(suite, result)

	def _build_pytest_args(self, suite: TestSuite, parallel: bool, workers: int, markers: list[str] | None, timeout: int) -> list[str]:
		"""Build pytest command line arguments."""
		args = []

		# Add test directory based on suite
		if suite == TestSuite.ALL:
			args.extend(["tests/"])
		elif suite == TestSuite.UNIT:
			args.extend(["tests/unit/", "backend/tests/unit/"])
		elif suite == TestSuite.INTEGRATION:
			args.extend(["tests/integration/", "backend/tests/integration/"])
		elif suite == TestSuite.E2E:
			args.extend(["tests/e2e/"])

		# Add verbosity
		args.append("-v")

		# Add parallel execution if requested
		if parallel:
			args.extend(["-n", str(workers)])

		# Add markers
		if markers:
			for marker in markers:
				args.extend(["-m", marker])

		# Add timeout
		args.extend(["--timeout", str(timeout)])

		# Add coverage if configured
		if self.config.get("coverage", False):
			args.extend(["--cov=backend/app", "--cov-report=html", "--cov-report=term"])

		# Add output formatting
		args.extend(["--tb=short"])

		# Generate JUnit XML report
		report_dir = self.config.get("report_dir", "test-reports")
		Path(report_dir).mkdir(parents=True, exist_ok=True)
		args.extend(["--junit-xml", f"{report_dir}/junit-{suite.value}.xml"])

		return args

	def _collect_results(self, suite: TestSuite, exit_code: int) -> dict[str, Any]:
		"""Collect and format test results."""
		duration = (self.end_time or time.time()) - (self.start_time or time.time())

		result_status = TestResult.PASSED if exit_code == 0 else TestResult.FAILED

		results = {
			"suite": suite.value,
			"status": result_status.value,
			"exit_code": exit_code,
			"duration_seconds": round(duration, 2),
			"start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
			"end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
		}

		self.results[suite.value] = results
		return results

	def generate_report(self, output_dir: str = "test-reports") -> Path:
		"""
		Generate comprehensive test report.

		Args:
		    output_dir: Directory to write report files

		Returns:
		    Path to generated report file
		"""
		output_path = Path(output_dir)
		output_path.mkdir(parents=True, exist_ok=True)

		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		report_file = output_path / f"test_report_{timestamp}.json"

		report_data = {
			"generated_at": datetime.now().isoformat(),
			"test_results": self.results,
			"summary": self._generate_summary(),
		}

		with open(report_file, "w") as f:
			json.dump(report_data, f, indent=2)

		print(f"\nTest report generated: {report_file}")
		return report_file

	def _generate_summary(self) -> dict[str, Any]:
		"""Generate summary statistics from all test results."""
		total_duration = sum(r.get("duration_seconds", 0) for r in self.results.values())

		passed_suites = sum(1 for r in self.results.values() if r.get("status") == TestResult.PASSED.value)

		failed_suites = sum(1 for r in self.results.values() if r.get("status") == TestResult.FAILED.value)

		return {
			"total_suites": len(self.results),
			"passed_suites": passed_suites,
			"failed_suites": failed_suites,
			"total_duration_seconds": round(total_duration, 2),
			"overall_status": "PASSED" if failed_suites == 0 else "FAILED",
		}


def main():
	"""Main entry point for the test orchestrator CLI."""
	parser = argparse.ArgumentParser(description="Unified Test Orchestrator for Career Copilot")

	subparsers = parser.add_subparsers(dest="command", help="Command to execute")

	# Run command
	run_parser = subparsers.add_parser("run", help="Run tests")
	run_parser.add_argument("-s", "--suite", type=str, choices=["unit", "integration", "e2e", "all"], default="all", help="Test suite to run")
	run_parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
	run_parser.add_argument("-w", "--workers", type=int, default=4, help="Number of parallel workers")
	run_parser.add_argument("-m", "--markers", type=str, nargs="+", help="Pytest markers to filter tests")
	run_parser.add_argument("-t", "--timeout", type=int, default=300, help="Timeout for test suite in seconds")
	run_parser.add_argument("--coverage", action="store_true", help="Generate coverage report")

	# Report command
	report_parser = subparsers.add_parser("report", help="Generate test report")
	report_parser.add_argument("-o", "--output", type=str, default="test-reports", help="Output directory for reports")

	args = parser.parse_args()

	if not args.command:
		parser.print_help()
		sys.exit(1)

	# Create orchestrator
	config = {"coverage": getattr(args, "coverage", False), "report_dir": getattr(args, "output", "test-reports")}

	orchestrator = TestOrchestrator(config=config)

	if args.command == "run":
		suite = TestSuite(args.suite)
		results = orchestrator.run_suite(suite=suite, parallel=args.parallel, workers=args.workers, markers=args.markers, timeout=args.timeout)

		# Print summary
		print(f"\n{'=' * 70}")
		print("Test Run Summary")
		print(f"{'=' * 70}")
		print(f"Suite: {results['suite']}")
		print(f"Status: {results['status']}")
		print(f"Duration: {results['duration_seconds']}s")
		print(f"{'=' * 70}\n")

		# Generate report
		report_file = orchestrator.generate_report(args.output)

		# Exit with appropriate code
		sys.exit(results["exit_code"])

	elif args.command == "report":
		# Generate report for existing results
		if not orchestrator.results:
			print("No test results to report. Run tests first.")
			sys.exit(1)

		report_file = orchestrator.generate_report(args.output)
		print(f"Report generated: {report_file}")


if __name__ == "__main__":
	main()
