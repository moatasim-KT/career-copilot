#!/usr/bin/env python3
"""
Demo Gap Analysis Script

Demonstrates the gap analysis system without requiring full app initialization.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.testing.frontend_scanner import FrontendScanner, ApiCall
from app.testing.gap_detector import GapDetector
from app.testing.gap_report_generator import GapReportGenerator
from app.testing.endpoint_discovery import EndpointInfo, ParameterInfo, ParameterLocation


def create_mock_backend_endpoints():
    """Create mock backend endpoints for demonstration"""
    endpoints = [
        EndpointInfo(
            path="/api/v1/jobs",
            method="GET",
            name="get_jobs",
            tags=["jobs"],
            summary="Get all jobs",
        ),
        EndpointInfo(
            path="/api/v1/jobs/{id}",
            method="GET",
            name="get_job",
            tags=["jobs"],
        ),
        EndpointInfo(
            path="/api/v1/jobs",
            method="POST",
            name="create_job",
            tags=["jobs"],
        ),
        EndpointInfo(
            path="/api/v1/applications",
            method="GET",
            name="get_applications",
            tags=["applications"],
        ),
        EndpointInfo(
            path="/api/v1/applications",
            method="POST",
            name="create_application",
            tags=["applications"],
        ),
        EndpointInfo(
            path="/api/v1/analytics/summary",
            method="GET",
            name="get_analytics_summary",
            tags=["analytics"],
        ),
    ]
    return endpoints


def main():
    """Main demo function"""
    print("=" * 80)
    print("FRONTEND-BACKEND GAP ANALYSIS DEMO")
    print("=" * 80)

    # Step 1: Scan frontend
    print("\n[1/4] Scanning frontend code...")
    frontend_dir = backend_dir.parent / "frontend" / "src"
    
    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        print("Using mock data for demonstration...")
        
        # Create mock frontend calls
        frontend_calls = [
            ApiCall(
                component="pages.JobsPage",
                file_path="pages/JobsPage.tsx",
                line_number=42,
                endpoint="/api/v1/jobs",
                method="GET",
                context="const { data } = useJobs()",
                call_type="hook",
            ),
            ApiCall(
                component="pages.JobsPage",
                file_path="pages/JobsPage.tsx",
                line_number=58,
                endpoint="/api/v1/jobs/search",
                method="GET",
                context="apiClient.searchJobs(query)",
                call_type="direct",
            ),
            ApiCall(
                component="pages.ApplicationsPage",
                file_path="pages/ApplicationsPage.tsx",
                line_number=35,
                endpoint="/api/v1/applications",
                method="GET",
                context="const { data } = useApplications()",
                call_type="hook",
            ),
            ApiCall(
                component="components.Dashboard",
                file_path="components/Dashboard.tsx",
                line_number=28,
                endpoint="/api/v1/analytics/summary",
                method="GET",
                context="apiClient.getAnalyticsSummary()",
                call_type="direct",
            ),
            ApiCall(
                component="components.Dashboard",
                file_path="components/Dashboard.tsx",
                line_number=45,
                endpoint="/api/v1/analytics/comprehensive-dashboard",
                method="GET",
                context="apiClient.getComprehensiveAnalytics()",
                call_type="direct",
            ),
        ]
    else:
        scanner = FrontendScanner(str(frontend_dir))
        frontend_calls = scanner.scan_directory()
        print(f"✓ Found {len(frontend_calls)} API calls")
        
        # Show some examples
        if frontend_calls:
            print("\nExample API calls found:")
            for call in frontend_calls[:5]:
                print(f"  - {call.method} {call.endpoint} in {call.component}")

    # Step 2: Get backend endpoints
    print("\n[2/4] Loading backend endpoints...")
    backend_endpoints = create_mock_backend_endpoints()
    print(f"✓ Loaded {len(backend_endpoints)} backend endpoints")
    print("\nBackend endpoints:")
    for endpoint in backend_endpoints:
        print(f"  - {endpoint.method} {endpoint.path}")

    # Step 3: Detect gaps
    print("\n[3/4] Detecting integration gaps...")
    detector = GapDetector()
    gaps = detector.compare_frontend_backend(
        frontend_calls=frontend_calls,
        backend_endpoints=backend_endpoints,
    )
    print(f"✓ Detected {len(gaps)} integration gaps")

    # Step 4: Generate reports
    print("\n[4/4] Generating reports...")
    generator = GapReportGenerator(detector)
    
    output_dir = backend_dir / "reports" / "gap_analysis_demo"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    reports = generator.generate_all_reports(str(output_dir))
    print("✓ Generated reports:")
    for format_type, file_path in reports.items():
        print(f"  - {format_type.upper()}: {file_path}")

    # Print summary
    generator.print_summary()

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print(f"\nView the HTML report at: {reports['html']}")


if __name__ == "__main__":
    main()
