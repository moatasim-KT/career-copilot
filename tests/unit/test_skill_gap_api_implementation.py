import os
import json
import requests
import pytest
from datetime import datetime

# Test configuration (should ideally be fixtures or environment variables)
BASE_URL = "http://localhost:8080"
TEST_USER_ID = "test_user_123"

# Test data (moved outside test functions for reusability)
TEST_USER_PROFILE = {
    "user_id": TEST_USER_ID,
    "email": "test@example.com",
    "skills": ["python", "javascript", "html", "css"],
    "locations": ["San Francisco", "Remote"],
    "experience_level": "mid",
    "preferences": {
        "job_types": ["full-time"],
        "salary_range": {"min": 80000, "max": 120000}
    }
}

TEST_JOBS = [
    {
        "user_id": TEST_USER_ID,
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
        "user_id": TEST_USER_ID,
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

# Fixture for setting up test user and jobs
@pytest.fixture(scope="module")
def setup_test_data():
    # This part assumes the backend is running at BASE_URL
    # In a real integration test, you'd start/stop the backend or mock it.
    # For now, we'll just try to create the user and jobs.
    try:
        # Create user
        response = requests.post(f"{BASE_URL}/api/users", json=TEST_USER_PROFILE)
        assert response.status_code in [201, 409] # 409 if user already exists
        
        # Add test jobs
        for job in TEST_JOBS:
            response = requests.post(f"{BASE_URL}/api/jobs", json=job)
            assert response.status_code in [201, 409]
    except requests.exceptions.ConnectionError:
        pytest.skip(f"Backend not running at {BASE_URL}. Skipping integration tests.")


@pytest.mark.integration # Mark as integration test
def test_learning_resources_endpoint(setup_test_data):
    """Test GET /api/users/{user_id}/learning-resources"""
    response = requests.get(f"{BASE_URL}/api/users/{TEST_USER_ID}/learning-resources")
    assert response.status_code == 200
    
    data = response.json()
    required_fields = ['learning_resources', 'learning_path', 'skill_gap_summary']
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    assert isinstance(data['learning_resources'], list)
    if data['learning_resources']:
        resource = data['learning_resources'][0]
        resource_fields = ['skill', 'market_demand_frequency', 'estimated_learning_time', 'resources']
        for field in resource_fields:
            assert field in resource, f"Missing resource field: {field}"

@pytest.mark.integration
def test_skill_trends_endpoint(setup_test_data):
    """Test GET /api/skill-trends"""
    params = {
        'time_period': 30,
        'job_limit': 100,
        'include_salary': 'true',
        'skill_limit': 10
    }
    response = requests.get(f"{BASE_URL}/api/skill-trends", params=params)
    assert response.status_code == 200
    
    data = response.json()
    required_fields = ['skill_trends', 'salary_trends', 'market_insights', 'analysis_parameters']
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    assert 'total_jobs_analyzed' in data['skill_trends']
    if data['salary_trends']:
        assert 'skills_by_salary' in data['salary_trends']

@pytest.mark.integration
def test_comprehensive_analytics_endpoint(setup_test_data):
    """Test GET /api/users/{user_id}/skill-analytics"""
    params = {
        'job_limit': 50,
        'include_learning_resources': 'true',
        'include_market_comparison': 'true',
        'include_salary_insights': 'true'
    }
    response = requests.get(f"{BASE_URL}/api/users/{TEST_USER_ID}/skill-analytics", params=params)
    assert response.status_code == 200
    
    data = response.json()
    required_fields = ['skill_analysis', 'recommendations', 'user_profile', 'analysis_parameters']
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    if params['include_learning_resources'] == 'true':
        assert 'learning_resources' in data
    if params['include_market_comparison'] == 'true':
        assert 'market_comparison' in data
    assert isinstance(data['recommendations'], list)

@pytest.mark.integration
def test_skill_extraction_enhancement(setup_test_data):
    """Test enhanced skill extraction functionality"""
    test_job_data = {
        "title": "Senior Python Developer",
        "requirements": "5+ years Python, Django, PostgreSQL, AWS experience required. Docker and Kubernetes preferred.",
        "responsibilities": "Lead development of scalable web applications using Python, Django, and modern DevOps practices.",
        "tech_stack": ["python", "django", "postgresql", "aws"]
    }
    response = requests.post(f"{BASE_URL}/api/extract-skills", json=test_job_data)
    assert response.status_code == 200
    
    data = response.json()
    required_fields = ['extracted_skills', 'skill_count', 'extraction_date']
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    extracted_skills = data['extracted_skills']
    expected_skills = ['python', 'django', 'postgresql', 'aws']
    found_skills = [skill for skill in expected_skills if skill in extracted_skills]
    assert len(found_skills) >= 2, f"Expected more skills to be extracted. Found: {found_skills}"
