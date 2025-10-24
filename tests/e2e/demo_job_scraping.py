#!/usr/bin/env python3
"""
Demo script for Job Scraping Test Framework

This script demonstrates the job scraping test framework capabilities including:
- Celery task triggering and monitoring
- Database verification for new job records
- Data quality validation checks

Usage:
    python tests/e2e/demo_job_scraping.py
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from tests.e2e.job_scraping_test_framework import (
    JobScrapingTestFramework,
    run_job_scraping_test,
    trigger_job_scraping_for_user
)


def print_separator(title: str):
    """Print a formatted separator with title"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_json_pretty(data, title: str = ""):
    """Print JSON data in a formatted way"""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))


def demo_basic_framework_setup():
    """Demonstrate basic framework setup and teardown"""
    print_separator("DEMO: Basic Framework Setup")
    
    framework = JobScrapingTestFramework()
    
    try:
        print("Setting up test environment...")
        setup_result = framework.setup_test_environment()
        
        if setup_result:
            print(f"✅ Test environment setup successful!")
            print(f"   Test User ID: {framework.test_user_id}")
            print(f"   Initial Job Count: {framework.initial_job_count}")
        else:
            print("❌ Test environment setup failed!")
            return
        
        print("\nCleaning up test data...")
        cleanup_result = framework.cleanup_test_data()
        
        if cleanup_result:
            print("✅ Test data cleanup successful!")
        else:
            print("❌ Test data cleanup failed!")
            
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        framework.cleanup_test_data()


def demo_job_scraping_task_trigger():
    """Demonstrate job scraping task triggering"""
    print_separator("DEMO: Job Scraping Task Trigger")
    
    framework = JobScrapingTestFramework()
    
    try:
        print("Setting up test environment...")
        if not framework.setup_test_environment():
            print("❌ Failed to setup test environment")
            return
        
        print(f"Triggering job scraping task for user {framework.test_user_id}...")
        print("⏳ This may take a few minutes...")
        
        # Trigger job scraping with timeout handling
        scraping_result = framework.trigger_job_scraping_task()
        
        print("\n📊 Job Scraping Results:")
        print(f"   Success: {'✅' if scraping_result.success else '❌'}")
        print(f"   Task ID: {scraping_result.task_id}")
        print(f"   Jobs Found: {scraping_result.jobs_found}")
        print(f"   Jobs Added: {scraping_result.jobs_added}")
        print(f"   Execution Time: {scraping_result.execution_time:.2f}s")
        print(f"   Data Quality Score: {scraping_result.data_quality_score:.1f}%")
        
        if scraping_result.error_message:
            print(f"   Error: {scraping_result.error_message}")
        
        if scraping_result.validation_errors:
            print("   Validation Errors:")
            for error in scraping_result.validation_errors:
                print(f"     - {error}")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
    finally:
        framework.cleanup_test_data()


def demo_database_verification():
    """Demonstrate database verification functionality"""
    print_separator("DEMO: Database Verification")
    
    framework = JobScrapingTestFramework()
    
    try:
        print("Setting up test environment...")
        if not framework.setup_test_environment():
            print("❌ Failed to setup test environment")
            return
        
        print("Performing database verification...")
        verification_result = framework.verify_database_changes(expected_min_jobs=0)
        
        print("\n📊 Database Verification Results:")
        print_json_pretty(verification_result)
        
        if verification_result["success"]:
            print("\n✅ Database verification passed!")
        else:
            print("\n❌ Database verification failed!")
            if verification_result.get("integrity_issues"):
                print("   Integrity Issues:")
                for issue in verification_result["integrity_issues"]:
                    print(f"     - {issue}")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
    finally:
        framework.cleanup_test_data()


def demo_data_quality_validation():
    """Demonstrate data quality validation"""
    print_separator("DEMO: Data Quality Validation")
    
    framework = JobScrapingTestFramework()
    
    try:
        print("Setting up test environment...")
        if not framework.setup_test_environment():
            print("❌ Failed to setup test environment")
            return
        
        print("Validating scraped data quality...")
        quality_metrics = framework.validate_scraped_data_quality()
        
        print("\n📊 Data Quality Metrics:")
        print(f"   Total Jobs: {quality_metrics.total_jobs}")
        print(f"   Jobs with Title: {quality_metrics.jobs_with_title}")
        print(f"   Jobs with Company: {quality_metrics.jobs_with_company}")
        print(f"   Jobs with Description: {quality_metrics.jobs_with_description}")
        print(f"   Jobs with Location: {quality_metrics.jobs_with_location}")
        print(f"   Jobs with Tech Stack: {quality_metrics.jobs_with_tech_stack}")
        print(f"   Jobs with Salary: {quality_metrics.jobs_with_salary}")
        print(f"   Duplicate Jobs: {quality_metrics.duplicate_jobs}")
        print(f"   Invalid URLs: {quality_metrics.invalid_urls}")
        print(f"   Quality Score: {quality_metrics.quality_score:.1f}%")
        
        if quality_metrics.quality_score >= 70.0:
            print("\n✅ Data quality meets minimum standards (≥70%)")
        else:
            print("\n⚠️  Data quality below minimum standards (<70%)")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
    finally:
        framework.cleanup_test_data()


def demo_comprehensive_test():
    """Demonstrate comprehensive job scraping test"""
    print_separator("DEMO: Comprehensive Job Scraping Test")
    
    print("Running comprehensive job scraping test...")
    print("⏳ This includes setup, task execution, verification, and cleanup...")
    
    try:
        # Use convenience function for comprehensive test
        result = run_job_scraping_test()
        
        print("\n📊 Comprehensive Test Results:")
        print_json_pretty(result)
        
        if result["success"]:
            print("\n✅ Comprehensive job scraping test passed!")
            
            if "summary" in result:
                summary = result["summary"]
                print("\n📋 Test Summary:")
                print(f"   Task Executed: {'✅' if summary.get('task_executed') else '❌'}")
                print(f"   Jobs Added: {summary.get('jobs_added', 0)}")
                print(f"   Data Quality Score: {summary.get('data_quality_score', 0):.1f}%")
                print(f"   Database Integrity: {'✅' if summary.get('database_integrity') else '❌'}")
        else:
            print("\n❌ Comprehensive job scraping test failed!")
            if "error" in result:
                print(f"   Error: {result['error']}")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")


def demo_user_specific_scraping():
    """Demonstrate job scraping for a specific user"""
    print_separator("DEMO: User-Specific Job Scraping")
    
    # Use a mock user ID for demonstration
    test_user_id = 999
    
    print(f"Triggering job scraping for user {test_user_id}...")
    print("⏳ This includes setup, task execution, and cleanup...")
    
    try:
        # Use convenience function for user-specific scraping
        result = trigger_job_scraping_for_user(test_user_id)
        
        print("\n📊 User-Specific Scraping Results:")
        print(f"   Success: {'✅' if result.success else '❌'}")
        print(f"   Task ID: {result.task_id}")
        print(f"   Jobs Found: {result.jobs_found}")
        print(f"   Jobs Added: {result.jobs_added}")
        print(f"   Execution Time: {result.execution_time:.2f}s")
        print(f"   Data Quality Score: {result.data_quality_score:.1f}%")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        
        if result.validation_errors:
            print("   Validation Errors:")
            for error in result.validation_errors:
                print(f"     - {error}")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")


def main():
    """Main demo function"""
    print_separator("JOB SCRAPING TEST FRAMEWORK DEMO")
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    demos = [
        ("Basic Framework Setup", demo_basic_framework_setup),
        ("Database Verification", demo_database_verification),
        ("Data Quality Validation", demo_data_quality_validation),
        ("Job Scraping Task Trigger", demo_job_scraping_task_trigger),
        ("User-Specific Scraping", demo_user_specific_scraping),
        ("Comprehensive Test", demo_comprehensive_test),
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print("  0. Run all demos")
    
    try:
        choice = input("\nSelect demo to run (0-6): ").strip()
        
        if choice == "0":
            # Run all demos
            for name, demo_func in demos:
                print(f"\n🚀 Running: {name}")
                demo_func()
        elif choice.isdigit() and 1 <= int(choice) <= len(demos):
            # Run specific demo
            name, demo_func = demos[int(choice) - 1]
            print(f"\n🚀 Running: {name}")
            demo_func()
        else:
            print("❌ Invalid choice. Please select 0-6.")
            return
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
    
    print_separator("DEMO COMPLETED")
    print(f"Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()