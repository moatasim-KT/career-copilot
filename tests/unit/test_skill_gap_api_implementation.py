#!/usr/bin/env python3
"""
Test script for Task 6.2: Skill Gap API and Analytics Implementation
Tests the new endpoints for learning resources, skill trends, and comprehensive analytics
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_skill_gap_api_endpoints():
    """Test the new skill gap API endpoints"""
    
    print("🧪 Testing Task 6.2: Skill Gap API and Analytics Implementation")
    print("=" * 70)
    
    # Test configuration
    base_url = "http://localhost:8080"
    test_user_id = "test_user_123"
    
    # Test data
    test_user_profile = {
        "user_id": test_user_id,
        "email": "test@example.com",
        "skills": ["python", "javascript", "html", "css"],
        "locations": ["San Francisco", "Remote"],
        "experience_level": "mid",
        "preferences": {
            "job_types": ["full-time"],
            "salary_range": {"min": 80000, "max": 120000}
        }
    }
    
    test_jobs = [
        {
            "user_id": test_user_id,
            "company": "TechCorp",
            "title": "Senior Software Engineer",
            "location": "San Francisco, CA",
            "tech_stack": ["python", "django", "postgresql", "aws", "docker"],
            "responsibilities": "Lead development of scalable web applications using Python and Django",
            "requirements": "5+ years Python experience, Django, AWS, Docker knowledge required",
            "salary_range": {"min": 100000, "max": 140000},
            "link": "https://example.com/job1"
        },
        {
            "user_id": test_user_id,
            "company": "StartupXYZ",
            "title": "Full Stack Developer",
            "location": "Remote",
            "tech_stack": ["javascript", "react", "node.js", "mongodb", "kubernetes"],
            "responsibilities": "Build modern web applications with React and Node.js",
            "requirements": "3+ years JavaScript, React, Node.js experience, Kubernetes preferred",
            "salary_range": {"min": 90000, "max": 130000},
            "link": "https://example.com/job2"
        }
    ]
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {"passed": 0, "failed": 0, "total": 0}
    }
    
    def run_test(test_name, test_func):
        """Run a test and record results"""
        print(f"\n📋 {test_name}")
        print("-" * 50)
        
        try:
            success, details = test_func()
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"Status: {status}")
            
            results["tests"].append({
                "name": test_name,
                "status": "passed" if success else "failed",
                "details": details
            })
            
            if success:
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
                
        except Exception as e:
            print(f"Status: ❌ FAILED - Exception: {str(e)}")
            results["tests"].append({
                "name": test_name,
                "status": "failed",
                "details": {"error": str(e)}
            })
            results["summary"]["failed"] += 1
        
        results["summary"]["total"] += 1
    
    def test_learning_resources_endpoint():
        """Test GET /api/users/{user_id}/learning-resources"""
        
        # First create user and jobs
        try:
            # Create user
            response = requests.post(f"{base_url}/api/users", json=test_user_profile)
            if response.status_code not in [201, 409]:  # 409 if user already exists
                return False, {"error": f"Failed to create user: {response.status_code}"}
            
            # Add test jobs
            for job in test_jobs:
                response = requests.post(f"{base_url}/api/jobs", json=job)
                if response.status_code not in [201, 409]:
                    return False, {"error": f"Failed to create job: {response.status_code}"}
            
            # Test learning resources endpoint
            response = requests.get(f"{base_url}/api/users/{test_user_id}/learning-resources")
            
            if response.status_code != 200:
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['learning_resources', 'learning_path', 'skill_gap_summary']
            for field in required_fields:
                if field not in data:
                    return False, {"error": f"Missing field: {field}"}
            
            # Validate learning resources structure
            if not isinstance(data['learning_resources'], list):
                return False, {"error": "learning_resources should be a list"}
            
            if data['learning_resources']:
                resource = data['learning_resources'][0]
                resource_fields = ['skill', 'market_demand_frequency', 'estimated_learning_time', 'resources']
                for field in resource_fields:
                    if field not in resource:
                        return False, {"error": f"Missing resource field: {field}"}
            
            return True, {
                "resources_count": len(data['learning_resources']),
                "skill_coverage": data['skill_gap_summary'].get('skill_coverage_percentage', 0),
                "sample_resource": data['learning_resources'][0] if data['learning_resources'] else None
            }
            
        except requests.exceptions.ConnectionError:
            return False, {"error": "Could not connect to server. Make sure the backend is running on localhost:8080"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_skill_trends_endpoint():
        """Test GET /api/skill-trends"""
        
        try:
            # Test skill trends endpoint
            params = {
                'time_period': 30,
                'job_limit': 100,
                'include_salary': 'true',
                'skill_limit': 10
            }
            
            response = requests.get(f"{base_url}/api/skill-trends", params=params)
            
            if response.status_code != 200:
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['skill_trends', 'salary_trends', 'market_insights', 'analysis_parameters']
            for field in required_fields:
                if field not in data:
                    return False, {"error": f"Missing field: {field}"}
            
            # Validate skill trends structure
            if 'total_jobs_analyzed' not in data['skill_trends']:
                return False, {"error": "Missing total_jobs_analyzed in skill_trends"}
            
            # Validate salary trends structure (if included)
            if data['salary_trends'] and 'skills_by_salary' not in data['salary_trends']:
                return False, {"error": "Missing skills_by_salary in salary_trends"}
            
            return True, {
                "jobs_analyzed": data['skill_trends'].get('total_jobs_analyzed', 0),
                "salary_trends_included": data['salary_trends'] is not None,
                "market_insights_count": len(data.get('market_insights', [])),
                "analysis_parameters": data['analysis_parameters']
            }
            
        except requests.exceptions.ConnectionError:
            return False, {"error": "Could not connect to server. Make sure the backend is running on localhost:8080"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_comprehensive_analytics_endpoint():
        """Test GET /api/users/{user_id}/skill-analytics"""
        
        try:
            # Test comprehensive skill analytics endpoint
            params = {
                'job_limit': 50,
                'include_learning_resources': 'true',
                'include_market_comparison': 'true',
                'include_salary_insights': 'true'
            }
            
            response = requests.get(f"{base_url}/api/users/{test_user_id}/skill-analytics", params=params)
            
            if response.status_code != 200:
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['skill_analysis', 'recommendations', 'user_profile', 'analysis_parameters']
            for field in required_fields:
                if field not in data:
                    return False, {"error": f"Missing field: {field}"}
            
            # Validate optional fields based on parameters
            if params['include_learning_resources'] == 'true' and 'learning_resources' not in data:
                return False, {"error": "Missing learning_resources (should be included)"}
            
            if params['include_market_comparison'] == 'true' and 'market_comparison' not in data:
                return False, {"error": "Missing market_comparison (should be included)"}
            
            # Validate recommendations structure
            if not isinstance(data['recommendations'], list):
                return False, {"error": "recommendations should be a list"}
            
            return True, {
                "skill_analysis_included": 'skill_analysis' in data,
                "learning_resources_included": 'learning_resources' in data,
                "market_comparison_included": 'market_comparison' in data,
                "salary_insights_included": 'salary_insights' in data,
                "recommendations_count": len(data.get('recommendations', [])),
                "jobs_analyzed": data['analysis_parameters'].get('applied_jobs_analyzed', 0) + 
                               data['analysis_parameters'].get('recommended_jobs_analyzed', 0)
            }
            
        except requests.exceptions.ConnectionError:
            return False, {"error": "Could not connect to server. Make sure the backend is running on localhost:8080"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_skill_extraction_enhancement():
        """Test enhanced skill extraction functionality"""
        
        try:
            # Test skill extraction endpoint
            test_job_data = {
                "title": "Senior Python Developer",
                "requirements": "5+ years Python, Django, PostgreSQL, AWS experience required. Docker and Kubernetes preferred.",
                "responsibilities": "Lead development of scalable web applications using Python, Django, and modern DevOps practices.",
                "tech_stack": ["python", "django", "postgresql", "aws"]
            }
            
            response = requests.post(f"{base_url}/api/extract-skills", json=test_job_data)
            
            if response.status_code != 200:
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['extracted_skills', 'skill_count', 'extraction_date']
            for field in required_fields:
                if field not in data:
                    return False, {"error": f"Missing field: {field}"}
            
            # Validate that some expected skills were extracted
            extracted_skills = data['extracted_skills']
            expected_skills = ['python', 'django', 'postgresql', 'aws']
            
            found_skills = [skill for skill in expected_skills if skill in extracted_skills]
            
            if len(found_skills) < 2:  # At least 2 expected skills should be found
                return False, {"error": f"Expected more skills to be extracted. Found: {found_skills}"}
            
            return True, {
                "extracted_skills": extracted_skills,
                "skill_count": data['skill_count'],
                "expected_skills_found": found_skills,
                "experience_level": data.get('experience_level')
            }
            
        except requests.exceptions.ConnectionError:
            return False, {"error": "Could not connect to server. Make sure the backend is running on localhost:8080"}
        except Exception as e:
            return False, {"error": str(e)}
    
    # Run all tests
    run_test("Learning Resources API Endpoint", test_learning_resources_endpoint)
    run_test("Skill Trends with Salary Analysis", test_skill_trends_endpoint)
    run_test("Comprehensive Skill Analytics", test_comprehensive_analytics_endpoint)
    run_test("Enhanced Skill Extraction", test_skill_extraction_enhancement)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']} ✅")
    print(f"Failed: {results['summary']['failed']} ❌")
    
    if results['summary']['failed'] == 0:
        print("\n🎉 All tests passed! Task 6.2 implementation is working correctly.")
        print("\n📋 IMPLEMENTED FEATURES:")
        print("✅ Learning resource recommendations API")
        print("✅ Skill trend analysis with salary insights")
        print("✅ Comprehensive skill gap analytics dashboard")
        print("✅ Enhanced skill extraction functionality")
        print("\n📋 REQUIREMENTS SATISFIED:")
        print("✅ Requirement 5.3: Skill gaps displayed in analytics section")
        print("✅ Requirement 5.5: Learning resources suggested for skill gaps")
        print("✅ Requirement 6.4: Salary trend insights provided")
    else:
        print(f"\n⚠️  {results['summary']['failed']} test(s) failed. Please check the implementation.")
    
    # Save detailed results
    with open('skill_gap_api_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: skill_gap_api_test_results.json")
    
    return results['summary']['failed'] == 0

if __name__ == "__main__":
    success = test_skill_gap_api_endpoints()
    sys.exit(0 if success else 1)