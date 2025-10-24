"""
Demo script for database health checker.

This script demonstrates the database health checking functionality
and can be used to test the implementation manually.
"""

import asyncio
import json
import sys
from datetime import datetime

from .database_health_checker import DatabaseHealthChecker


async def demo_basic_health_check():
    """Demonstrate basic database health check."""
    print("=" * 60)
    print("DATABASE HEALTH CHECK DEMO")
    print("=" * 60)
    
    # Create health checker with default settings
    health_checker = DatabaseHealthChecker()
    
    print(f"Initializing database health checker...")
    print(f"Database URL: {health_checker.database_url}")
    print(f"Backend URL: {health_checker.backend_url}")
    
    await health_checker.setup()
    
    print("\nRunning comprehensive database health check...")
    start_time = datetime.now()
    
    try:
        result = await health_checker.run_test()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\nHealth check completed in {duration:.2f} seconds")
        print(f"Overall Status: {result['status'].upper()}")
        print(f"Total Checks: {result['total_checks']}")
        print(f"Unhealthy Services: {len(result['unhealthy_services'])}")
        
        if result['unhealthy_services']:
            print(f"Failed Services: {', '.join(result['unhealthy_services'])}")
        
        print("\nDetailed Results:")
        print("-" * 40)
        
        for service_name, service_result in result["health_results"].items():
            status_icon = "✅" if service_result["healthy"] else "❌"
            print(f"{status_icon} {service_name.replace('_', ' ').title()}")
            print(f"   Response Time: {service_result['response_time']:.3f}s")
            
            if "details" in service_result and service_result["details"]:
                details = service_result["details"]
                
                if "status" in details:
                    print(f"   Status: {details['status']}")
                
                if "connection_time_ms" in details:
                    print(f"   Connection Time: {details['connection_time_ms']:.1f}ms")
                
                if "database_type" in details:
                    print(f"   Database Type: {details['database_type']}")
                
                if "collections_count" in details:
                    print(f"   Collections: {details['collections_count']}")
                
                if "warnings" in details and details["warnings"]:
                    print(f"   Warnings: {', '.join(details['warnings'])}")
                
                if "error" in details:
                    print(f"   Error: {details['error']}")
            
            print()
        
        return result
        
    except Exception as e:
        print(f"\n❌ Health check failed with error: {e}")
        return None


async def demo_comprehensive_health_check():
    """Demonstrate comprehensive database health check."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE DATABASE HEALTH CHECK")
    print("=" * 60)
    
    health_checker = DatabaseHealthChecker()
    await health_checker.setup()
    
    print("Running comprehensive health check...")
    
    try:
        result = await health_checker.check_comprehensive_database_health()
        
        print(f"\nOverall Health: {'✅ HEALTHY' if result['overall_healthy'] else '❌ UNHEALTHY'}")
        print(f"Success Rate: {result['success_rate']:.1f}%")
        print(f"Healthy Components: {result['healthy_components']}/{result['total_components']}")
        
        print("\nComponent Details:")
        print("-" * 40)
        
        for component, details in result["components"].items():
            status_icon = "✅" if details.get("healthy", False) else "❌"
            print(f"{status_icon} {component.replace('_', ' ').title()}")
            print(f"   Response Time: {details.get('response_time', 0):.1f}ms")
            
            if "details" in details:
                comp_details = details["details"]
                
                if "status" in comp_details:
                    print(f"   Status: {comp_details['status']}")
                
                if "statistics" in comp_details:
                    stats = comp_details["statistics"]
                    print(f"   Avg Response: {stats.get('average_response_time_ms', 0):.1f}ms")
                    print(f"   Operations: {stats.get('successful_operations', 0)}/{stats.get('total_operations', 0)}")
                
                if "chromadb_info" in comp_details:
                    chroma_info = comp_details["chromadb_info"]
                    print(f"   ChromaDB Status: {chroma_info.get('status', 'unknown')}")
                
                if "error" in comp_details:
                    print(f"   Error: {comp_details['error']}")
            
            print()
        
        return result
        
    except Exception as e:
        print(f"\n❌ Comprehensive health check failed: {e}")
        return None


async def demo_performance_monitoring():
    """Demonstrate database performance monitoring."""
    print("\n" + "=" * 60)
    print("DATABASE PERFORMANCE MONITORING")
    print("=" * 60)
    
    # Create health checker with custom performance thresholds
    custom_thresholds = {
        "connection_time_warning_ms": 50,
        "connection_time_critical_ms": 200,
        "query_time_warning_ms": 100,
        "query_time_critical_ms": 500,
        "pool_usage_warning": 60.0,
        "pool_usage_critical": 80.0,
    }
    
    health_checker = DatabaseHealthChecker(
        performance_thresholds=custom_thresholds
    )
    
    await health_checker.setup()
    
    print("Custom Performance Thresholds:")
    for threshold, value in custom_thresholds.items():
        print(f"  {threshold}: {value}")
    
    print("\nRunning performance monitoring...")
    
    try:
        result = await health_checker._check_response_time_monitoring()
        
        print(f"\nMonitoring Status: {'✅ HEALTHY' if result['healthy'] else '❌ UNHEALTHY'}")
        print(f"Response Time: {result['response_time']:.1f}ms")
        
        if "details" in result:
            details = result["details"]
            
            if "statistics" in details:
                stats = details["statistics"]
                print(f"\nPerformance Statistics:")
                print(f"  Average Response Time: {stats.get('average_response_time_ms', 0):.1f}ms")
                print(f"  Max Response Time: {stats.get('max_response_time_ms', 0):.1f}ms")
                print(f"  Min Response Time: {stats.get('min_response_time_ms', 0):.1f}ms")
                print(f"  Total Operations: {stats.get('total_operations', 0)}")
                print(f"  Successful Operations: {stats.get('successful_operations', 0)}")
            
            if "operations" in details:
                print(f"\nOperation Details:")
                for op in details["operations"]:
                    status_icon = "✅" if op["status"] == "success" else "❌"
                    print(f"  {status_icon} {op['operation']}: {op['response_time_ms']:.1f}ms")
            
            if "warnings" in details and details["warnings"]:
                print(f"\nWarnings:")
                for warning in details["warnings"]:
                    print(f"  ⚠️  {warning}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Performance monitoring failed: {e}")
        return None


async def demo_individual_checks():
    """Demonstrate individual database health checks."""
    print("\n" + "=" * 60)
    print("INDIVIDUAL DATABASE HEALTH CHECKS")
    print("=" * 60)
    
    health_checker = DatabaseHealthChecker()
    await health_checker.setup()
    
    # Test PostgreSQL health
    print("1. PostgreSQL Health Check")
    print("-" * 30)
    try:
        postgres_result = await health_checker._check_postgresql_health()
        status_icon = "✅" if postgres_result["healthy"] else "❌"
        print(f"{status_icon} PostgreSQL: {postgres_result['response_time']:.1f}ms")
        
        if "details" in postgres_result:
            details = postgres_result["details"]
            if "database_type" in details:
                print(f"   Database Type: {details['database_type']}")
            if "connection_time_ms" in details:
                print(f"   Connection Time: {details['connection_time_ms']:.1f}ms")
    except Exception as e:
        print(f"❌ PostgreSQL check failed: {e}")
    
    # Test ChromaDB health
    print("\n2. ChromaDB Health Check")
    print("-" * 30)
    try:
        chromadb_result = await health_checker._check_chromadb_health()
        status_icon = "✅" if chromadb_result["healthy"] else "❌"
        print(f"{status_icon} ChromaDB: {chromadb_result['response_time']:.1f}ms")
        
        if "details" in chromadb_result:
            details = chromadb_result["details"]
            if "method" in details:
                print(f"   Check Method: {details['method']}")
            if "collections_count" in details:
                print(f"   Collections: {details['collections_count']}")
    except Exception as e:
        print(f"❌ ChromaDB check failed: {e}")
    
    # Test Response Time Monitoring
    print("\n3. Response Time Monitoring")
    print("-" * 30)
    try:
        monitoring_result = await health_checker._check_response_time_monitoring()
        status_icon = "✅" if monitoring_result["healthy"] else "❌"
        print(f"{status_icon} Monitoring: {monitoring_result['response_time']:.1f}ms")
        
        if "details" in monitoring_result and "statistics" in monitoring_result["details"]:
            stats = monitoring_result["details"]["statistics"]
            print(f"   Avg Query Time: {stats.get('average_response_time_ms', 0):.1f}ms")
    except Exception as e:
        print(f"❌ Response time monitoring failed: {e}")


async def main():
    """Main demo function."""
    print("Database Health Checker Demo")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all demo functions
        await demo_basic_health_check()
        await demo_comprehensive_health_check()
        await demo_performance_monitoring()
        await demo_individual_checks()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nDemo finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    # Check if we're running in an environment that supports asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed to run demo: {e}")
        sys.exit(1)