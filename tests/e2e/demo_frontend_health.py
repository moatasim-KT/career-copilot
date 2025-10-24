#!/usr/bin/env python3
"""
Demo script for frontend health checker.

This script demonstrates the frontend health checking functionality
by running various health checks against the Next.js frontend application.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.frontend_health_checker import FrontendHealthChecker, FrontendHealthTest


async def demo_individual_checks():
    """Demonstrate individual health check methods."""
    print("=" * 60)
    print("FRONTEND HEALTH CHECKER DEMO - Individual Checks")
    print("=" * 60)
    
    # Initialize health checker
    health_checker = FrontendHealthChecker(
        base_url="http://localhost:3000",
        timeout=15.0
    )
    
    print(f"Testing frontend at: {health_checker.base_url}")
    print(f"Timeout: {health_checker.timeout}s")
    print()
    
    # Test 1: Frontend Accessibility
    print("1. Testing Frontend Accessibility...")
    print("-" * 40)
    try:
        result = await health_checker.check_frontend_accessibility()
        print(f"Status: {'✅ HEALTHY' if result.healthy else '❌ UNHEALTHY'}")
        print(f"Response Time: {result.response_time_ms:.2f}ms")
        print(f"Status Code: {result.status_code}")
        print(f"Message: {result.message}")
        if result.error:
            print(f"Error: {result.error}")
        if result.details:
            print(f"Content Length: {result.details.get('content_length', 'N/A')}")
            print(f"Content Type: {result.details.get('content_type', 'N/A')}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    print()
    
    # Test 2: Page Rendering
    print("2. Testing Page Rendering...")
    print("-" * 40)
    try:
        result = await health_checker.check_page_rendering()
        print(f"Status: {'✅ HEALTHY' if result.healthy else '❌ UNHEALTHY'}")
        print(f"Response Time: {result.response_time_ms:.2f}ms")
        print(f"Message: {result.message}")
        if result.details:
            print(f"Rendering Score: {result.details.get('rendering_score', 'N/A')}%")
            print(f"Checks Passed: {result.details.get('checks_passed', 'N/A')}/{result.details.get('total_checks', 'N/A')}")
            print(f"Has Next.js Markers: {result.details.get('has_next_js_markers', 'N/A')}")
            
            # Show individual check results
            check_results = result.details.get('check_results', {})
            if check_results:
                print("Individual Checks:")
                for check_name, passed in check_results.items():
                    status = "✅" if passed else "❌"
                    print(f"  {status} {check_name}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    print()
    
    # Test 3: JavaScript Error Detection
    print("3. Testing JavaScript Error Detection...")
    print("-" * 40)
    try:
        result = await health_checker.check_javascript_errors()
        print(f"Status: {'✅ HEALTHY' if result.healthy else '❌ UNHEALTHY'}")
        print(f"Response Time: {result.response_time_ms:.2f}ms")
        print(f"Message: {result.message}")
        if result.details:
            print(f"Pages Checked: {result.details.get('pages_checked', 'N/A')}")
            print(f"Pages with Errors: {result.details.get('pages_with_errors', 'N/A')}")
            print(f"Error Rate: {result.details.get('error_rate_percent', 'N/A')}%")
            
            error_indicators = result.details.get('error_indicators', [])
            if error_indicators:
                print("Error Indicators Found:")
                for indicator in error_indicators[:3]:  # Show first 3
                    print(f"  Page: {indicator.get('page', 'N/A')}")
                    errors = indicator.get('errors', [])
                    for error in errors[:2]:  # Show first 2 errors per page
                        print(f"    - {error}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    print()
    
    # Test 4: Health Endpoint Check
    print("4. Testing Health Endpoint...")
    print("-" * 40)
    try:
        result = await health_checker.check_health_endpoint()
        print(f"Status: {'✅ HEALTHY' if result.healthy else '❌ UNHEALTHY'}")
        print(f"Response Time: {result.response_time_ms:.2f}ms")
        print(f"Message: {result.message}")
        if result.details:
            endpoint = result.details.get('endpoint')
            if endpoint:
                print(f"Found Endpoint: {endpoint}")
                health_data = result.details.get('health_data')
                if health_data:
                    print(f"Health Data: {json.dumps(health_data, indent=2)}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    print()


async def demo_comprehensive_check():
    """Demonstrate comprehensive health check."""
    print("=" * 60)
    print("FRONTEND HEALTH CHECKER DEMO - Comprehensive Check")
    print("=" * 60)
    
    # Initialize health checker
    health_checker = FrontendHealthChecker(
        base_url="http://localhost:3000",
        timeout=15.0
    )
    
    print("Running comprehensive frontend health check...")
    print()
    
    try:
        # Run comprehensive check
        results = await health_checker.comprehensive_frontend_check()
        
        # Generate summary
        summary = health_checker.get_health_summary(results)
        
        # Display summary
        print("HEALTH SUMMARY")
        print("-" * 30)
        print(f"Overall Status: {'✅ HEALTHY' if summary['overall_healthy'] else '❌ UNHEALTHY'}")
        print(f"Success Rate: {summary['success_rate']}%")
        print(f"Healthy Components: {summary['healthy_components']}/{summary['total_components']}")
        
        if summary['unhealthy_components']:
            print(f"Unhealthy Components: {', '.join(summary['unhealthy_components'])}")
        
        print()
        
        # Display individual results
        print("COMPONENT DETAILS")
        print("-" * 30)
        for component_name, result in results.items():
            status_icon = "✅" if result.healthy else "❌"
            print(f"{status_icon} {component_name.upper()}")
            print(f"   Response Time: {result.response_time_ms:.2f}ms")
            print(f"   Message: {result.message}")
            if result.error:
                print(f"   Error: {result.error}")
            print()
        
        # Save detailed results to file
        output_file = Path(__file__).parent / "frontend_health_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                "summary": summary,
                "detailed_results": {name: result.dict() for name, result in results.items()}
            }, f, indent=2, default=str)
        
        print(f"Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ COMPREHENSIVE CHECK FAILED: {e}")
        import traceback
        traceback.print_exc()


async def demo_startup_verification():
    """Demonstrate startup verification."""
    print("=" * 60)
    print("FRONTEND HEALTH CHECKER DEMO - Startup Verification")
    print("=" * 60)
    
    # Initialize health checker
    health_checker = FrontendHealthChecker(
        base_url="http://localhost:3000",
        timeout=15.0
    )
    
    print("Testing frontend startup verification...")
    print("This will attempt to verify the frontend is fully started and operational.")
    print()
    
    try:
        result = await health_checker.verify_frontend_startup(
            max_attempts=3,
            retry_delay=2.0
        )
        
        print(f"Status: {'✅ STARTUP VERIFIED' if result.healthy else '❌ STARTUP FAILED'}")
        print(f"Total Time: {result.response_time_ms:.2f}ms")
        print(f"Message: {result.message}")
        
        if result.details:
            attempts = result.details.get('attempts', 'N/A')
            print(f"Attempts Used: {attempts}")
            
            if result.healthy:
                print("Startup verification successful!")
                accessibility_status = result.details.get('accessibility_status', {})
                rendering_status = result.details.get('rendering_status', {})
                
                print(f"Accessibility Check: {'✅' if accessibility_status.get('healthy') else '❌'}")
                print(f"Rendering Check: {'✅' if rendering_status.get('healthy') else '❌'}")
        
        if result.error:
            print(f"Error: {result.error}")
            
    except Exception as e:
        print(f"❌ STARTUP VERIFICATION FAILED: {e}")


async def demo_health_test_class():
    """Demonstrate the FrontendHealthTest class."""
    print("=" * 60)
    print("FRONTEND HEALTH CHECKER DEMO - Test Class")
    print("=" * 60)
    
    print("Testing FrontendHealthTest class (E2E test integration)...")
    print()
    
    try:
        # Initialize test class
        health_test = FrontendHealthTest(base_url="http://localhost:3000")
        
        # Run the complete test
        result = await health_test.execute()
        
        print("TEST EXECUTION RESULTS")
        print("-" * 30)
        print(f"Test Class: {result.get('test_class', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Test Name: {result.get('test_name', 'N/A')}")
        print(f"Message: {result.get('message', 'N/A')}")
        
        if result.get('status') == 'failed' and 'error' in result:
            print(f"Error: {result['error']}")
        
        # Show summary if available
        summary = result.get('summary')
        if summary:
            print()
            print("HEALTH SUMMARY")
            print("-" * 20)
            print(f"Overall Healthy: {summary.get('overall_healthy', 'N/A')}")
            print(f"Success Rate: {summary.get('success_rate', 'N/A')}%")
            print(f"Components: {summary.get('healthy_components', 'N/A')}/{summary.get('total_components', 'N/A')}")
        
        # Show unhealthy services
        unhealthy = result.get('unhealthy_components', [])
        if unhealthy:
            print(f"Unhealthy Components: {', '.join(unhealthy)}")
            
    except Exception as e:
        print(f"❌ TEST CLASS DEMO FAILED: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main demo function."""
    print("🚀 Frontend Health Checker Demo")
    print("This demo will test the frontend health checking functionality.")
    print("Make sure the frontend is running on http://localhost:3000")
    print()
    
    # Run all demos
    demos = [
        ("Individual Health Checks", demo_individual_checks),
        ("Comprehensive Health Check", demo_comprehensive_check),
        ("Startup Verification", demo_startup_verification),
        ("Health Test Class", demo_health_test_class)
    ]
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n🔍 Running: {demo_name}")
            await demo_func()
            print(f"✅ Completed: {demo_name}")
        except KeyboardInterrupt:
            print(f"\n⏹️  Demo interrupted by user")
            break
        except Exception as e:
            print(f"❌ Demo failed: {demo_name} - {e}")
            import traceback
            traceback.print_exc()
        
        # Small delay between demos
        await asyncio.sleep(1)
    
    print("\n🏁 Frontend Health Checker Demo Complete!")
    print("Check the generated frontend_health_results.json file for detailed results.")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())