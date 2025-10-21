#!/usr/bin/env python3
"""
Test script for job API integration
Tests the Adzuna API client and job data transformation
"""
import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.utils.job_apis import AdzunaAPIClient, JobDataTransformer, JobAPIManager, JobAPIError
from backend.config import get_config

def test_adzuna_api_client():
    """Test Adzuna API client functionality"""
    print("Testing Adzuna API Client...")
    
    config = get_config()
    
    # Check if credentials are available
    if not config.ADZUNA_APP_ID or not config.ADZUNA_API_KEY:
        print("❌ Adzuna API credentials not configured")
        print("Set ADZUNA_APP_ID and ADZUNA_API_KEY environment variables")
        return False
    
    try:
        # Initialize client
        client = AdzunaAPIClient(config.ADZUNA_APP_ID, config.ADZUNA_API_KEY)
        print("✅ Adzuna client initialized successfully")
        
        # Test search
        print("Testing job search...")
        results = client.search_jobs(
            what="python developer",
            where="San Francisco",
            results_per_page=5
        )
        
        print(f"✅ Search successful. Found {results.get('count', 0)} jobs")
        
        # Display sample results
        jobs = results.get('results', [])
        if jobs:
            print("\nSample job:")
            sample_job = jobs[0]
            print(f"  Title: {sample_job.get('title', 'N/A')}")
            print(f"  Company: {sample_job.get('company', {}).get('display_name', 'N/A')}")
            print(f"  Location: {sample_job.get('location', {}).get('display_name', 'N/A')}")
            print(f"  Salary: ${sample_job.get('salary_min', 'N/A')} - ${sample_job.get('salary_max', 'N/A')}")
        
        return True
        
    except JobAPIError as e:
        print(f"❌ Adzuna API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_job_data_transformer():
    """Test job data transformation"""
    print("\nTesting Job Data Transformer...")
    
    # Sample Adzuna job data
    sample_job_data = {
        'id': '12345',
        'title': 'Senior Python Developer',
        'company': {
            'display_name': 'TechCorp Inc'
        },
        'location': {
            'display_name': 'San Francisco, CA'
        },
        'description': 'We are looking for a Senior Python Developer with experience in Django, PostgreSQL, AWS, and React. Must have 5+ years of experience.',
        'salary_min': 100000,
        'salary_max': 140000,
        'redirect_url': 'https://example.com/job/12345'
    }
    
    try:
        # Transform job data
        job = JobDataTransformer.transform_adzuna_job(sample_job_data, 'test_user_123')
        
        print("✅ Job transformation successful")
        print(f"  Job ID: {job.job_id}")
        print(f"  Title: {job.title}")
        print(f"  Company: {job.company}")
        print(f"  Location: {job.location}")
        print(f"  Tech Stack: {job.tech_stack}")
        print(f"  Salary Range: {job.salary_range.min if job.salary_range else 'N/A'} - {job.salary_range.max if job.salary_range else 'N/A'}")
        print(f"  Source: {job.source}")
        
        # Test validation
        if job.validate():
            print("✅ Job validation passed")
        else:
            print("❌ Job validation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Job transformation error: {e}")
        return False


def test_job_api_manager():
    """Test job API manager"""
    print("\nTesting Job API Manager...")
    
    try:
        # Initialize manager
        manager = JobAPIManager()
        
        # Check available sources
        sources = manager.get_available_sources()
        print(f"✅ Available sources: {sources}")
        
        # Test connections
        print("Testing API connections...")
        connection_results = manager.test_connections()
        
        for source, status in connection_results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {source}: {'Connected' if status else 'Failed'}")
        
        # Test job search if any APIs are available
        if sources:
            print("Testing job search...")
            jobs = manager.search_jobs(
                user_id='test_user_123',
                keywords='python developer',
                location='San Francisco',
                max_results=3
            )
            
            print(f"✅ Found {len(jobs)} jobs")
            
            for i, job in enumerate(jobs[:2], 1):
                print(f"  Job {i}: {job.title} at {job.company}")
        
        return True
        
    except Exception as e:
        print(f"❌ Job API manager error: {e}")
        return False


def test_rate_limiter():
    """Test rate limiting functionality"""
    print("\nTesting Rate Limiter...")
    
    try:
        from backend.utils.job_apis import RateLimiter
        
        # Create rate limiter with low limits for testing
        limiter = RateLimiter(max_requests=3, time_window=10)
        
        # Test normal operation
        for i in range(3):
            if limiter.can_make_request():
                limiter.record_request()
                print(f"✅ Request {i+1} allowed")
            else:
                print(f"❌ Request {i+1} blocked unexpectedly")
                return False
        
        # Test rate limiting
        if not limiter.can_make_request():
            wait_time = limiter.wait_time()
            print(f"✅ Rate limiting working. Wait time: {wait_time} seconds")
        else:
            print("❌ Rate limiting not working")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiter error: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Job API Integration Tests")
    print("=" * 50)
    
    tests = [
        test_rate_limiter,
        test_job_data_transformer,
        test_adzuna_api_client,
        test_job_api_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and network connectivity.")
        return 1


if __name__ == '__main__':
    exit(main())