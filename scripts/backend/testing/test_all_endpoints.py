#!/usr/bin/env python3
"""
Comprehensive Endpoint Testing Script

This script uses the endpoint discovery and testing framework to:
1. Discover all FastAPI endpoints
2. Generate test data for each endpoint
3. Test all endpoints with various test cases
4. Generate detailed test reports
"""

import argparse
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import create_app
from app.testing import EndpointDiscovery, EndpointTester, TestDataGenerator


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Test all FastAPI endpoints")
    parser.add_argument("--output", "-o", default="test_report.json", help="Output file for test report")
    parser.add_argument("--format", "-f", choices=["json", "html", "both"], default="both", help="Output format")
    parser.add_argument("--skip-deprecated", action="store_true", help="Skip deprecated endpoints")
    parser.add_argument("--skip-auth", action="store_true", help="Skip endpoints requiring authentication")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--discover-only", action="store_true", help="Only discover endpoints, don't test")
    parser.add_argument("--endpoint", "-e", help="Test specific endpoint (e.g., 'GET /api/v1/jobs')")

    args = parser.parse_args()

    # Create FastAPI app
    print("🚀 Creating FastAPI application...")
    app = create_app()

    # Initialize discovery and testing
    print("🔍 Initializing endpoint discovery...")
    discovery = EndpointDiscovery(app)
    tester = EndpointTester(app)

    # Discover endpoints
    print("📡 Discovering endpoints...")
    endpoints = discovery.discover_endpoints()
    print(f"✅ Discovered {len(endpoints)} endpoints")

    if args.verbose:
        print("\n📋 Endpoint Summary:")
        stats = discovery.get_statistics()
        print(f"  Total endpoints: {stats['total_endpoints']}")
        print(f"  Endpoints by method:")
        for method, count in stats["endpoints_by_method"].items():
            print(f"    {method}: {count}")
        print(f"  Endpoints requiring auth: {stats['endpoints_requiring_auth']}")
        print(f"  Deprecated endpoints: {stats['deprecated_endpoints']}")

    # Export endpoint map
    endpoint_map_file = args.output.replace(".json", "_endpoint_map.json").replace(".html", "_endpoint_map.json")
    print(f"\n💾 Exporting endpoint map to {endpoint_map_file}...")
    endpoint_data = discovery.export_to_dict()
    with open(endpoint_map_file, "w") as f:
        json.dump(endpoint_data, f, indent=2)
    print(f"✅ Endpoint map saved")

    if args.discover_only:
        print("\n✨ Discovery complete!")
        return

    # Test endpoints
    print("\n🧪 Testing endpoints...")

    if args.endpoint:
        # Test specific endpoint
        method, path = args.endpoint.split(" ", 1)
        endpoint_info = discovery.get_endpoint_by_path(method, path)
        if not endpoint_info:
            print(f"❌ Endpoint not found: {args.endpoint}")
            return

        print(f"Testing {args.endpoint}...")
        results = tester.test_endpoint_with_multiple_cases(endpoint_info)
        tester.test_results = results
    else:
        # Test all endpoints
        results = tester.test_all_endpoints(skip_deprecated=args.skip_deprecated, skip_auth_required=args.skip_auth)

    print(f"✅ Completed {len(results)} tests")

    # Generate report
    print("\n📊 Generating test report...")
    report = tester.generate_test_report(output_format="dict")

    summary = report["summary"]
    print(f"\n📈 Test Summary:")
    print(f"  Total tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']} ({summary['pass_rate']:.1f}%)")
    print(f"  Failed: {summary['failed']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Average response time: {summary['average_response_time']:.3f}s")

    # Show failed tests
    failed_tests = tester.get_failed_tests()
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test in failed_tests[:10]:  # Show first 10
            print(f"  {test.method} {test.endpoint}: {test.error_message}")

    # Show error tests
    error_tests = tester.get_error_tests()
    if error_tests:
        print(f"\n⚠️  Error Tests ({len(error_tests)}):")
        for test in error_tests[:10]:  # Show first 10
            print(f"  {test.method} {test.endpoint}: {test.error_message}")

    # Show slow tests
    slow_tests = tester.get_slow_tests(threshold=1.0)
    if slow_tests:
        print(f"\n🐌 Slow Tests (>{1.0}s) ({len(slow_tests)}):")
        for test in slow_tests[:10]:  # Show first 10
            print(f"  {test.method} {test.endpoint}: {test.response_time:.3f}s")

    # Export reports
    if args.format in ["json", "both"]:
        json_file = args.output if args.output.endswith(".json") else f"{args.output}.json"
        print(f"\n💾 Exporting JSON report to {json_file}...")
        tester.export_results_to_json(json_file)
        print(f"✅ JSON report saved")

    if args.format in ["html", "both"]:
        html_file = args.output.replace(".json", ".html") if args.output.endswith(".json") else f"{args.output}.html"
        print(f"\n💾 Exporting HTML report to {html_file}...")
        tester.export_results_to_html(html_file)
        print(f"✅ HTML report saved")

    print("\n✨ Testing complete!")

    # Exit with error code if tests failed
    if summary["failed"] > 0 or summary["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
