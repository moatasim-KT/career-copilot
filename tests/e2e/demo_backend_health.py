"""
Demo script to test the backend health checker against a running backend service.

This script demonstrates how to use the BackendHealthChecker to verify
the health of the FastAPI backend service.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.backend_health_checker import BackendHealthChecker, BackendHealthTest


async def demo_health_checks():
    """Demonstrate backend health checking functionality."""
    print("🔍 Backend Health Checker Demo")
    print("=" * 50)
    
    # Initialize health checker
    checker = BackendHealthChecker()
    print(f"📡 Checking backend at: {checker.base_url}")
    print()
    
    try:
        # Test 1: Check health endpoint
        print("1️⃣ Testing health endpoint...")
        health_result = await checker.check_health_endpoint()
        print(f"   Status: {'✅ Healthy' if health_result.healthy else '❌ Unhealthy'}")
        print(f"   Response time: {health_result.response_time_ms:.1f}ms")
        print(f"   Message: {health_result.message}")
        if health_result.error:
            print(f"   Error: {health_result.error}")
        print()
        
        # Test 2: Check Celery workers
        print("2️⃣ Testing Celery workers...")
        celery_result = await checker.check_celery_workers()
        print(f"   Status: {'✅ Healthy' if celery_result.healthy else '❌ Unhealthy'}")
        print(f"   Response time: {celery_result.response_time_ms:.1f}ms")
        print(f"   Message: {celery_result.message}")
        if celery_result.error:
            print(f"   Error: {celery_result.error}")
        print()
        
        # Test 3: Check database connectivity
        print("3️⃣ Testing database connectivity...")
        db_result = await checker.check_database_connectivity()
        print(f"   Status: {'✅ Healthy' if db_result.healthy else '❌ Unhealthy'}")
        print(f"   Response time: {db_result.response_time_ms:.1f}ms")
        print(f"   Message: {db_result.message}")
        if db_result.error:
            print(f"   Error: {db_result.error}")
        print()
        
        # Test 4: Service startup verification (quick check)
        print("4️⃣ Testing service startup verification...")
        startup_result = await checker.verify_service_startup(max_attempts=1)
        print(f"   Status: {'✅ Healthy' if startup_result.healthy else '❌ Unhealthy'}")
        print(f"   Response time: {startup_result.response_time_ms:.1f}ms")
        print(f"   Message: {startup_result.message}")
        if startup_result.error:
            print(f"   Error: {startup_result.error}")
        print()
        
        # Test 5: Comprehensive health check
        print("5️⃣ Running comprehensive health check...")
        comprehensive_results = await checker.comprehensive_health_check()
        summary = checker.get_health_summary(comprehensive_results)
        
        print(f"   Overall Status: {'✅ Healthy' if summary['overall_healthy'] else '❌ Unhealthy'}")
        print(f"   Success Rate: {summary['success_rate']}%")
        print(f"   Healthy Components: {summary['healthy_components']}/{summary['total_components']}")
        
        if summary['unhealthy_services']:
            print(f"   Unhealthy Services: {', '.join(summary['unhealthy_services'])}")
        print()
        
        # Test 6: E2E Test Class
        print("6️⃣ Testing E2E BackendHealthTest class...")
        health_test = BackendHealthTest()
        await health_test.setup()
        
        test_result = await health_test.run_test()
        print(f"   Test Status: {'✅ Passed' if test_result['status'] == 'passed' else '❌ Failed'}")
        print(f"   Test Message: {test_result['message']}")
        
        if 'summary' in test_result:
            print(f"   Overall Health: {'✅ Healthy' if test_result['summary']['overall_healthy'] else '❌ Unhealthy'}")
        
        await health_test.teardown()
        print()
        
        print("🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {str(e)}")
        print(f"💡 Make sure the backend service is running at {checker.base_url}")


async def quick_health_check():
    """Quick health check for CI/testing purposes."""
    checker = BackendHealthChecker()
    
    try:
        result = await checker.check_health_endpoint()
        if result.healthy:
            print("✅ Backend service is healthy")
            return True
        else:
            print(f"❌ Backend service is unhealthy: {result.message}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick check mode
        result = asyncio.run(quick_health_check())
        sys.exit(0 if result else 1)
    else:
        # Full demo mode
        asyncio.run(demo_health_checks())