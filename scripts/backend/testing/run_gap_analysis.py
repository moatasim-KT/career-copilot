#!/usr/bin/env python3
"""
Run Frontend-Backend Gap Analysis

This script performs a comprehensive gap analysis between frontend and backend:
1. Discovers all backend endpoints
2. Scans frontend code for API calls
3. Detects integration gaps
4. Generates comprehensive reports
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.testing.endpoint_discovery import EndpointDiscovery
from app.testing.frontend_scanner import FrontendScanner
from app.testing.gap_detector import GapDetector
from app.testing.gap_report_generator import GapReportGenerator


def main():
    """Main function to run gap analysis"""
    parser = argparse.ArgumentParser(description="Run frontend-backend gap analysis")
    parser.add_argument(
        "--frontend-dir",
        type=str,
        default=str(backend_dir.parent / "frontend" / "src"),
        help="Path to frontend source directory",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(backend_dir / "reports" / "gap_analysis"),
        help="Directory to save reports",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["html", "json", "markdown", "csv", "all"],
        default="all",
        help="Report format to generate",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("FRONTEND-BACKEND INTEGRATION GAP ANALYSIS")
    print("=" * 80)

    # Step 1: Discover backend endpoints
    print("\n[1/5] Discovering backend endpoints...")
    discovery = EndpointDiscovery(app)
    backend_endpoints = discovery.discover_endpoints()
    print(f"✓ Discovered {len(backend_endpoints)} backend endpoints")

    if args.verbose:
        stats = discovery.get_statistics()
        print(f"  - Endpoints by method: {stats['endpoints_by_method']}")
        print(f"  - Endpoints requiring auth: {stats['endpoints_requiring_auth']}")

    # Step 2: Scan frontend code
    print("\n[2/5] Scanning frontend code for API calls...")
    scanner = FrontendScanner(args.frontend_dir)
    frontend_calls = scanner.scan_directory()
    print(f"✓ Found {len(frontend_calls)} API calls in frontend")

    if args.verbose:
        stats = scanner.get_statistics()
        print(f"  - Unique endpoints: {stats['unique_endpoints']}")
        print(f"  - Unique components: {stats['unique_components']}")
        print(f"  - Calls by method: {stats['calls_by_method']}")

    # Step 3: Identify feature requirements
    print("\n[3/5] Identifying feature requirements...")
    feature_requirements = scanner.identify_feature_requirements()
    print(f"✓ Identified {len(feature_requirements)} feature requirements")

    if args.verbose:
        for feature in feature_requirements[:5]:  # Show first 5
            print(f"  - {feature.feature_name}: {len(feature.required_endpoints)} endpoints ({feature.priority})")

    # Step 4: Detect gaps
    print("\n[4/5] Detecting integration gaps...")
    detector = GapDetector()
    gaps = detector.compare_frontend_backend(
        frontend_calls=frontend_calls,
        backend_endpoints=backend_endpoints,
        feature_requirements=feature_requirements,
    )
    print(f"✓ Detected {len(gaps)} integration gaps")

    if args.verbose:
        stats = detector.get_statistics()
        print(f"  - Critical: {stats['gaps_by_severity']['critical']}")
        print(f"  - High: {stats['gaps_by_severity']['high']}")
        print(f"  - Medium: {stats['gaps_by_severity']['medium']}")
        print(f"  - Low: {stats['gaps_by_severity']['low']}")

    # Step 5: Generate reports
    print("\n[5/5] Generating reports...")
    generator = GapReportGenerator(detector)

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if args.format == "all":
        reports = generator.generate_all_reports(args.output_dir)
        print("✓ Generated all report formats:")
        for format_type, file_path in reports.items():
            print(f"  - {format_type.upper()}: {file_path}")
    else:
        if args.format == "html":
            file_path = output_path / "gap_analysis.html"
            generator.generate_html_report(str(file_path))
        elif args.format == "json":
            file_path = output_path / "gap_analysis.json"
            generator.generate_json_report(str(file_path))
        elif args.format == "markdown":
            file_path = output_path / "gap_analysis.md"
            generator.generate_markdown_report(str(file_path))
        elif args.format == "csv":
            file_path = output_path / "gap_analysis.csv"
            generator.generate_csv_report(str(file_path))

        print(f"✓ Generated {args.format.upper()} report: {file_path}")

    # Print summary
    generator.print_summary()

    # Export frontend scan results
    frontend_scan_file = output_path / "frontend_api_calls.json"
    scanner.export_to_json(str(frontend_scan_file))
    print(f"✓ Exported frontend scan results: {frontend_scan_file}")

    # Export backend endpoint map
    endpoint_map_file = output_path / "backend_endpoints.json"
    import json

    with open(endpoint_map_file, "w", encoding="utf-8") as f:
        json.dump(discovery.export_to_dict(), f, indent=2)
    print(f"✓ Exported backend endpoint map: {endpoint_map_file}")

    print("\n" + "=" * 80)
    print("GAP ANALYSIS COMPLETE")
    print("=" * 80)

    # Return exit code based on critical gaps
    critical_count = detector.get_statistics()["gaps_by_severity"]["critical"]
    if critical_count > 0:
        print(f"\n⚠️  WARNING: {critical_count} critical gaps detected!")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
