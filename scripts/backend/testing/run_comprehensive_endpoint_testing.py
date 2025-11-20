#!/usr/bin/env python3
"""
Comprehensive Endpoint Testing Script

This script runs all phases of endpoint testing:
1. Endpoint discovery
2. Automated endpoint tests
3. Frontend-backend integration verification
4. Final test report generation
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.testing.endpoint_discovery import EndpointDiscovery, EndpointInfo
from app.testing.endpoint_tester import EndpointTester, TestResult
from app.testing.frontend_scanner import FrontendScanner
from app.testing.gap_detector import GapDetector


def run_endpoint_discovery() -> Tuple[EndpointDiscovery, List[EndpointInfo]]:
	"""Phase 1: Execute endpoint discovery.

	Returns:
		Tuple containing the discovery engine and the list of endpoint metadata.
	"""
	print("=" * 80)
	print("PHASE 1: ENDPOINT DISCOVERY")
	print("=" * 80)

	discovery = EndpointDiscovery(app)
	endpoints = discovery.discover_endpoints()

	print(f"\n✓ Discovered {len(endpoints)} endpoints")

	# Generate endpoint map
	endpoint_map = discovery.generate_endpoint_map()
	print(f"✓ Generated endpoint map with {len(endpoint_map)} entries")

	# Categorize endpoints
	categorized = discovery.categorize_endpoints()
	print(f"✓ Categorized endpoints into {len(categorized)} categories")

	# Get statistics
	stats = discovery.get_statistics()
	print("\nEndpoint Statistics:")
	print(f"  Total endpoints: {stats['total_endpoints']}")
	print(f"  Endpoints by method: {stats['endpoints_by_method']}")
	print(f"  Endpoints requiring auth: {stats['endpoints_requiring_auth']}")
	print(f"  Deprecated endpoints: {stats['deprecated_endpoints']}")

	# Export endpoint map
	output_dir = backend_dir / "reports"
	output_dir.mkdir(exist_ok=True)

	endpoint_map_file = output_dir / "endpoint_map.json"
	with open(endpoint_map_file, "w") as f:
		json.dump(discovery.export_to_dict(), f, indent=2)
	print(f"\n✓ Exported endpoint map to {endpoint_map_file}")

	# Export categorized endpoints
	categorized_file = output_dir / "endpoints_by_category.json"
	categorized_data = {
		category: [{"path": e.path, "method": e.method, "name": e.name, "requires_auth": e.requires_auth} for e in endpoints_list]
		for category, endpoints_list in categorized.items()
	}
	with open(categorized_file, "w") as f:
		json.dump(categorized_data, f, indent=2)
	print(f"✓ Exported categorized endpoints to {categorized_file}")

	return discovery, endpoints


def run_automated_endpoint_tests(_discovery: EndpointDiscovery) -> Tuple[EndpointTester, List[TestResult]]:
	"""Phase 2: Run automated endpoint tests.

	Args:
		_discovery: Endpoint discovery instance (unused placeholder for future coordination).

	Returns:
		Tuple with the tester instance and the list of test results.
	"""
	print("\n" + "=" * 80)
	print("PHASE 2: AUTOMATED ENDPOINT TESTING")
	print("=" * 80)

	tester = EndpointTester(app)

	print("\nTesting all endpoints...")
	results = tester.test_all_endpoints(skip_deprecated=True, skip_auth_required=False)

	print(f"\n✓ Completed {len(results)} endpoint tests")

	# Get test statistics
	passed = len([r for r in results if r.status.value == "passed"])
	failed = len([r for r in results if r.status.value == "failed"])
	errors = len([r for r in results if r.status.value == "error"])

	print(f"\nTest Results:")
	print(f"  Passed: {passed}")
	print(f"  Failed: {failed}")
	print(f"  Errors: {errors}")
	print(f"  Pass Rate: {(passed / len(results) * 100):.1f}%")

	# Check for slow tests
	slow_tests = tester.get_slow_tests(threshold=1.0)
	if slow_tests:
		print(f"\n⚠ Found {len(slow_tests)} slow tests (>1s):")
		for test in slow_tests[:5]:  # Show first 5
			print(f"    {test.method} {test.endpoint}: {test.response_time:.3f}s")

	# Export results
	output_dir = backend_dir / "reports"

	json_file = output_dir / "endpoint_test_results.json"
	tester.export_results_to_json(str(json_file))
	print(f"\n✓ Exported JSON results to {json_file}")

	html_file = output_dir / "endpoint_test_results.html"
	tester.export_results_to_html(str(html_file))
	print(f"✓ Exported HTML report to {html_file}")

	return tester, results


def run_frontend_backend_verification(_discovery: EndpointDiscovery) -> Tuple[Optional[FrontendScanner], Optional[GapDetector]]:
	"""Phase 3: Verify frontend-backend integration.

	Args:
		_discovery: Endpoint discovery instance (currently unused, reserved for future correlation).

	Returns:
		Tuple containing the frontend scanner (if available) and the gap detector instance.
	"""
	print("\n" + "=" * 80)
	print("PHASE 3: FRONTEND-BACKEND INTEGRATION VERIFICATION")
	print("=" * 80)

	# Scan frontend code
	frontend_dir = backend_dir.parent / "frontend" / "src"

	if not frontend_dir.exists():
		print(f"\n⚠ Frontend directory not found at {frontend_dir}")
		print("  Skipping frontend analysis")
		return None, None

	print(f"\nScanning frontend directory: {frontend_dir}")
	scanner = FrontendScanner(str(frontend_dir))
	api_calls = scanner.scan_directory()

	print(f"✓ Found {len(api_calls)} API calls in frontend code")

	# Identify feature requirements
	feature_requirements = scanner.identify_feature_requirements()
	print(f"✓ Identified {len(feature_requirements)} feature requirements")

	# Get statistics
	stats = scanner.get_statistics()
	print(f"\nFrontend API Call Statistics:")
	print(f"  Total API calls: {stats['total_api_calls']}")
	print(f"  Unique endpoints: {stats['unique_endpoints']}")
	print(f"  Unique components: {stats['unique_components']}")
	print(f"  Calls by method: {stats['calls_by_method']}")

	# Export frontend scan results
	output_dir = backend_dir / "reports"
	frontend_scan_file = output_dir / "frontend_api_calls.json"
	scanner.export_to_json(str(frontend_scan_file))
	print(f"\n✓ Exported frontend scan results to {frontend_scan_file}")

	# Run gap detection
	print("\nRunning gap detection...")
	gap_detector = GapDetector(discovery, scanner)
	gaps = gap_detector.detect_gaps()

	print(f"✓ Detected {len(gaps)} integration gaps")

	# Categorize gaps
	categorized_gaps = gap_detector.categorize_gaps()
	print(f"\nGaps by type:")
	for gap_type, gap_list in categorized_gaps.items():
		print(f"  {gap_type}: {len(gap_list)}")

	# Prioritize gaps
	prioritized_gaps = gap_detector.prioritize_gaps()
	critical_gaps = [g for g in prioritized_gaps if g.priority == "critical"]
	high_gaps = [g for g in prioritized_gaps if g.priority == "high"]

	if critical_gaps:
		print(f"\n⚠ Found {len(critical_gaps)} CRITICAL gaps:")
		for gap in critical_gaps[:5]:  # Show first 5
			print(f"    {gap.expected_method} {gap.expected_endpoint}")
			print(f"      Component: {gap.frontend_component}")

	if high_gaps:
		print(f"\n⚠ Found {len(high_gaps)} HIGH priority gaps:")
		for gap in high_gaps[:5]:  # Show first 5
			print(f"    {gap.expected_method} {gap.expected_endpoint}")
			print(f"      Component: {gap.frontend_component}")

	# Export gap analysis
	gap_report_file = output_dir / "integration_gap_analysis.json"
	gap_detector.export_to_json(str(gap_report_file))
	print(f"\n✓ Exported gap analysis to {gap_report_file}")

	# Generate HTML gap report
	gap_html_file = output_dir / "integration_gap_analysis.html"
	gap_detector.export_to_html(str(gap_html_file))
	print(f"✓ Exported HTML gap report to {gap_html_file}")

	return scanner, gap_detector


def generate_final_report(
	discovery: EndpointDiscovery,
	tester: EndpointTester,
	scanner: Optional[FrontendScanner],
	gap_detector: Optional[GapDetector],
) -> Dict[str, Any]:
	"""Phase 4: Generate final comprehensive report.

	Args:
		discovery: Endpoint discovery engine populated with backend metadata.
		tester: Tester that holds endpoint execution results.
		scanner: Optional frontend scanner results.
		gap_detector: Optional gap detector summarizing integration gaps.

	Returns:
		Dictionary containing the aggregated report payload.
	"""
	print("\n" + "=" * 80)
	print("PHASE 4: FINAL COMPREHENSIVE REPORT")
	print("=" * 80)

	output_dir = backend_dir / "reports"

	# Compile all results
	report = {
		"timestamp": tester.test_results[0].timestamp if tester.test_results else "",
		"summary": {
			"total_backend_endpoints": len(discovery._endpoints),
			"total_frontend_api_calls": len(scanner.api_calls) if scanner else 0,
			"total_integration_gaps": len(gap_detector.gaps) if gap_detector else 0,
			"endpoint_tests": {
				"total": len(tester.test_results),
				"passed": len([r for r in tester.test_results if r.status.value == "passed"]),
				"failed": len([r for r in tester.test_results if r.status.value == "failed"]),
				"errors": len([r for r in tester.test_results if r.status.value == "error"]),
				"pass_rate": (len([r for r in tester.test_results if r.status.value == "passed"]) / len(tester.test_results) * 100)
				if tester.test_results
				else 0,
			},
		},
		"endpoint_discovery": discovery.get_statistics(),
		"endpoint_testing": tester.generate_test_report(output_format="dict"),
		"frontend_analysis": scanner.get_statistics() if scanner else {},
		"gap_analysis": {
			"total_gaps": len(gap_detector.gaps) if gap_detector else 0,
			"gaps_by_type": {gap_type: len(gaps) for gap_type, gaps in (gap_detector.categorize_gaps().items() if gap_detector else {})},
			"gaps_by_priority": {
				"critical": len([g for g in (gap_detector.gaps if gap_detector else []) if g.priority == "critical"]),
				"high": len([g for g in (gap_detector.gaps if gap_detector else []) if g.priority == "high"]),
				"medium": len([g for g in (gap_detector.gaps if gap_detector else []) if g.priority == "medium"]),
				"low": len([g for g in (gap_detector.gaps if gap_detector else []) if g.priority == "low"]),
			},
		},
		"performance_metrics": {
			"average_response_time": sum(r.response_time for r in tester.test_results) / len(tester.test_results) if tester.test_results else 0,
			"slow_tests_count": len(tester.get_slow_tests(threshold=1.0)),
			"fastest_endpoint": min(tester.test_results, key=lambda r: r.response_time).endpoint if tester.test_results else None,
			"slowest_endpoint": max(tester.test_results, key=lambda r: r.response_time).endpoint if tester.test_results else None,
		},
		"action_items": [],
	}

	# Generate action items
	if tester.get_failed_tests():
		report["action_items"].append(
			{
				"priority": "high",
				"category": "failed_tests",
				"description": f"Fix {len(tester.get_failed_tests())} failed endpoint tests",
				"count": len(tester.get_failed_tests()),
			}
		)

	if tester.get_error_tests():
		report["action_items"].append(
			{
				"priority": "critical",
				"category": "error_tests",
				"description": f"Fix {len(tester.get_error_tests())} endpoint tests with errors",
				"count": len(tester.get_error_tests()),
			}
		)

	if gap_detector:
		critical_gaps = [g for g in gap_detector.gaps if g.priority == "critical"]
		if critical_gaps:
			report["action_items"].append(
				{
					"priority": "critical",
					"category": "integration_gaps",
					"description": f"Implement {len(critical_gaps)} critical missing endpoints",
					"count": len(critical_gaps),
				}
			)

	# Export final report
	final_report_file = output_dir / "comprehensive_test_report.json"
	with open(final_report_file, "w") as f:
		json.dump(report, f, indent=2)
	print(f"\n✓ Exported comprehensive report to {final_report_file}")

	# Generate HTML summary
	html_summary = generate_html_summary(report)
	html_summary_file = output_dir / "comprehensive_test_report.html"
	with open(html_summary_file, "w") as f:
		f.write(html_summary)
	print(f"✓ Exported HTML summary to {html_summary_file}")

	# Print summary
	print("\n" + "=" * 80)
	print("COMPREHENSIVE TEST SUMMARY")
	print("=" * 80)
	print(f"\nBackend Endpoints: {report['summary']['total_backend_endpoints']}")
	print(f"Frontend API Calls: {report['summary']['total_frontend_api_calls']}")
	print(f"Integration Gaps: {report['summary']['total_integration_gaps']}")
	print(f"\nEndpoint Tests:")
	print(f"  Total: {report['summary']['endpoint_tests']['total']}")
	print(f"  Passed: {report['summary']['endpoint_tests']['passed']}")
	print(f"  Failed: {report['summary']['endpoint_tests']['failed']}")
	print(f"  Errors: {report['summary']['endpoint_tests']['errors']}")
	print(f"  Pass Rate: {report['summary']['endpoint_tests']['pass_rate']:.1f}%")

	if report["action_items"]:
		print(f"\n⚠ Action Items: {len(report['action_items'])}")
		for item in report["action_items"]:
			print(f"  [{item['priority'].upper()}] {item['description']}")

	print("\n" + "=" * 80)
	print("All reports generated successfully!")
	print("=" * 80)

	return report


def generate_html_summary(report: Dict[str, Any]) -> str:
	"""Generate HTML summary report.

	Args:
		report: Final report dictionary produced by :func:`generate_final_report`.

	Returns:
		Rendered HTML summary string.
	"""
	summary = report["summary"]
	endpoint_tests = summary["endpoint_tests"]

	html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Comprehensive Test Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-card.primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .stat-card.success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }}
        .stat-card.warning {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}
        .stat-card.info {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }}
        .stat-card h3 {{
            margin: 0;
            font-size: 3em;
            font-weight: bold;
        }}
        .stat-card p {{
            margin: 10px 0 0 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background-color: #ecf0f1;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s ease;
        }}
        .action-items {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .action-item {{
            padding: 10px;
            margin: 10px 0;
            background-color: white;
            border-radius: 5px;
            border-left: 3px solid #ffc107;
        }}
        .action-item.critical {{
            border-left-color: #dc3545;
        }}
        .action-item.high {{
            border-left-color: #fd7e14;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 10px;
        }}
        .badge.critical {{
            background-color: #dc3545;
            color: white;
        }}
        .badge.high {{
            background-color: #fd7e14;
            color: white;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Comprehensive Endpoint Testing Report</h1>
        <p class="timestamp">Generated: {report.get("timestamp", "N/A")}</p>
        
        <h2>📊 Overview</h2>
        <div class="summary-grid">
            <div class="stat-card primary">
                <h3>{summary["total_backend_endpoints"]}</h3>
                <p>Backend Endpoints</p>
            </div>
            <div class="stat-card info">
                <h3>{summary["total_frontend_api_calls"]}</h3>
                <p>Frontend API Calls</p>
            </div>
            <div class="stat-card warning">
                <h3>{summary["total_integration_gaps"]}</h3>
                <p>Integration Gaps</p>
            </div>
        </div>
        
        <h2>✅ Endpoint Test Results</h2>
        <div class="summary-grid">
            <div class="stat-card success">
                <h3>{endpoint_tests["passed"]}</h3>
                <p>Passed</p>
            </div>
            <div class="stat-card warning">
                <h3>{endpoint_tests["failed"]}</h3>
                <p>Failed</p>
            </div>
            <div class="stat-card warning">
                <h3>{endpoint_tests["errors"]}</h3>
                <p>Errors</p>
            </div>
            <div class="stat-card primary">
                <h3>{endpoint_tests["total"]}</h3>
                <p>Total Tests</p>
            </div>
        </div>
        
        <h2>📈 Pass Rate</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {endpoint_tests["pass_rate"]:.1f}%">
                {endpoint_tests["pass_rate"]:.1f}%
            </div>
        </div>
"""

	# Add action items if any
	if report.get("action_items"):
		html += """
        <h2>⚠️ Action Items</h2>
        <div class="action-items">
"""
		for item in report["action_items"]:
			html += f"""
            <div class="action-item {item["priority"]}">
                <span class="badge {item["priority"]}">{item["priority"].upper()}</span>
                {item["description"]}
            </div>
"""
		html += """
        </div>
"""

	# Add performance metrics
	perf = report.get("performance_metrics", {})
	if perf:
		html += f"""
        <h2>⚡ Performance Metrics</h2>
        <div class="summary-grid">
            <div class="stat-card info">
                <h3>{perf.get("average_response_time", 0):.3f}s</h3>
                <p>Avg Response Time</p>
            </div>
            <div class="stat-card warning">
                <h3>{perf.get("slow_tests_count", 0)}</h3>
                <p>Slow Tests (&gt;1s)</p>
            </div>
        </div>
"""

	html += """
        <h2>📁 Generated Reports</h2>
        <ul>
            <li><strong>endpoint_map.json</strong> - Complete endpoint catalog</li>
            <li><strong>endpoints_by_category.json</strong> - Endpoints grouped by category</li>
            <li><strong>endpoint_test_results.json</strong> - Detailed test results</li>
            <li><strong>endpoint_test_results.html</strong> - Interactive test report</li>
            <li><strong>frontend_api_calls.json</strong> - Frontend API usage analysis</li>
            <li><strong>integration_gap_analysis.json</strong> - Gap detection results</li>
            <li><strong>integration_gap_analysis.html</strong> - Interactive gap report</li>
            <li><strong>comprehensive_test_report.json</strong> - This summary in JSON format</li>
        </ul>
    </div>
</body>
</html>
"""

	return html


def main() -> int:
	"""Main execution function."""
	print("\n" + "=" * 80)
	print("COMPREHENSIVE ENDPOINT TESTING")
	print("=" * 80)
	print("\nThis script will:")
	print("  1. Discover all backend endpoints")
	print("  2. Run automated tests on all endpoints")
	print("  3. Scan frontend code for API calls")
	print("  4. Detect integration gaps")
	print("  5. Generate comprehensive reports")
	print("\n" + "=" * 80)

	try:
		# Phase 1: Endpoint Discovery
		discovery, _endpoints = run_endpoint_discovery()

		# Phase 2: Automated Endpoint Tests
		tester, _test_results = run_automated_endpoint_tests(discovery)

		# Phase 3: Frontend-Backend Verification
		scanner, gap_detector = run_frontend_backend_verification(discovery)

		# Phase 4: Final Report
		final_report = generate_final_report(discovery, tester, scanner, gap_detector)

		print("\n✅ All testing phases completed successfully!")
		return 0

	except Exception as e:
		print(f"\n❌ Error during testing: {e}")
		import traceback

		traceback.print_exc()
		return 1


if __name__ == "__main__":
	sys.exit(main())
