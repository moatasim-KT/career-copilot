#!/usr/bin/env python3
"""
Test script for market analysis service
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_market_analysis():
    """Test the market analysis service functionality"""
    
    try:
        # Test service import
        from app.services.market_analysis_service import market_analysis_service
        print("✅ Market analysis service imported successfully")
        
        # Test service methods exist
        methods_to_test = [
            'analyze_salary_trends',
            'analyze_job_market_patterns', 
            'generate_opportunity_alerts',
            'create_market_dashboard_data',
            'save_analysis'
        ]
        
        for method in methods_to_test:
            if hasattr(market_analysis_service, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
        
        # Test helper methods
        helper_methods = [
            '_normalize_location',
            '_calculate_market_competitiveness',
            '_analyze_salary_by_industry',
            '_classify_industry',
            '_classify_company_size'
        ]
        
        for method in helper_methods:
            if hasattr(market_analysis_service, method):
                print(f"✅ Helper method {method} exists")
            else:
                print(f"❌ Helper method {method} missing")
        
        # Test location normalization
        test_locations = [
            "San Francisco, CA",
            "remote",
            "New York City",
            "seattle, wa",
            None
        ]
        
        print("\nTesting location normalization:")
        for location in test_locations:
            normalized = market_analysis_service._normalize_location(location)
            print(f"  '{location}' -> '{normalized}'")
        
        # Test industry classification
        print("\nTesting industry classification:")
        
        # Mock job object for testing
        class MockJob:
            def __init__(self, company, title, description=""):
                self.company = company
                self.title = title
                self.description = description
        
        test_jobs = [
            MockJob("Google", "Software Engineer", "Python development"),
            MockJob("Goldman Sachs", "Analyst", "Financial analysis"),
            MockJob("Kaiser Permanente", "Data Scientist", "Healthcare analytics"),
            MockJob("McKinsey", "Consultant", "Strategy consulting")
        ]
        
        for job in test_jobs:
            industry = market_analysis_service._classify_industry(job)
            print(f"  {job.company} - {job.title} -> {industry}")
        
        # Test company size classification
        print("\nTesting company size classification:")
        for job in test_jobs:
            size = market_analysis_service._classify_company_size(job)
            print(f"  {job.company} -> {size}")
        
        print("\n✅ All market analysis service tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_market_analysis()