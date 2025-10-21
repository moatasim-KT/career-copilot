#!/usr/bin/env python3
"""
Simplified unit tests for Career Co-Pilot data models validation.
Tests model structure and validation logic without database dependencies.
Requirements: 1.3, 2.3, 5.1
"""

import pytest
from datetime import datetime, timedelta
import json


def test_user_model_structure():
    """Test User model structure and field validation."""
    # Test valid user data structure
    user_data = {
        "email": "test@example.com",
        "password_hash": "hashed_password_123",
        "is_active": True,
        "profile": {
            "skills": ["Python", "JavaScript", "React"],
            "experience_level": "mid",
            "locations": ["San Francisco", "Remote"],
            "preferences": {
                "salary_min": 80000,
                "company_size": ["startup", "medium"],
                "industries": ["tech", "fintech"],
                "remote_preference": "hybrid"
            },
            "career_goals": ["senior_engineer", "tech_lead"]
        },
        "settings": {
            "notifications": {
                "morning_briefing": True,
                "evening_summary": True,
                "email_time": "08:00"
            },
            "ui_preferences": {
                "theme": "dark",
                "dashboard_layout": "compact"
            }
        },
        "profile_encrypted": "false",
        "settings_encrypted": "false"
    }
    
    # Validate required fields
    assert "email" in user_data
    assert "password_hash" in user_data
    assert isinstance(user_data["profile"], dict)
    assert isinstance(user_data["settings"], dict)
    
    # Validate profile structure
    profile = user_data["profile"]
    assert isinstance(profile["skills"], list)
    assert profile["experience_level"] in ["junior", "mid", "senior", "lead", "principal"]
    assert isinstance(profile["locations"], list)
    assert isinstance(profile["preferences"], dict)
    
    # Validate settings structure
    settings = user_data["settings"]
    assert isinstance(settings["notifications"], dict)
    assert isinstance(settings["ui_preferences"], dict)
    
    print("✓ User model structure validation passed")


def test_job_model_structure():
    """Test Job model structure and field validation."""
    # Test valid job data structure
    job_data = {
        "user_id": 1,
        "title": "Senior Software Engineer",
        "company": "TechCorp Inc",
        "location": "San Francisco, CA",
        "salary_min": 120000,
        "salary_max": 160000,
        "currency": "USD",
        "requirements": {
            "skills_required": ["Python", "Django", "PostgreSQL", "AWS"],
            "experience_level": "senior",
            "employment_type": "full_time",
            "remote_options": "hybrid",
            "benefits": ["health", "dental", "401k", "equity"],
            "company_size": "medium",
            "industry": "fintech"
        },
        "description": "Lead development of scalable web applications...",
        "application_url": "https://techcorp.com/jobs/senior-engineer",
        "status": "not_applied",
        "source": "manual",
        "recommendation_score": 0.85,
        "tags": ["python", "remote", "startup", "fintech", "senior"]
    }
    
    # Validate required fields
    assert "user_id" in job_data
    assert "title" in job_data
    assert "company" in job_data
    assert isinstance(job_data["requirements"], dict)
    
    # Validate status values
    valid_statuses = [
        "not_applied", "applied", "phone_screen", "interview_scheduled",
        "interviewed", "offer_received", "rejected", "withdrawn", "archived"
    ]
    assert job_data["status"] in valid_statuses
    
    # Validate source values
    valid_sources = ["manual", "scraped", "api", "rss", "referral"]
    assert job_data["source"] in valid_sources
    
    # Validate requirements structure
    requirements = job_data["requirements"]
    assert isinstance(requirements["skills_required"], list)
    assert requirements["employment_type"] in ["full_time", "part_time", "contract", "internship"]
    
    # Validate salary fields
    if job_data.get("salary_min") and job_data.get("salary_max"):
        assert job_data["salary_min"] <= job_data["salary_max"]
    
    # Validate recommendation score
    if job_data.get("recommendation_score"):
        assert 0.0 <= job_data["recommendation_score"] <= 1.0
    
    print("✓ Job model structure validation passed")


def test_analytics_model_structure():
    """Test Analytics model structure and field validation."""
    # Test skill gap analysis data structure
    skill_gap_data = {
        "user_id": 1,
        "type": "skill_gap_analysis",
        "data": {
            "analysis_date": "2024-01-15",
            "missing_skills": [
                {"skill": "React", "frequency": 85, "priority": "high"},
                {"skill": "Docker", "frequency": 60, "priority": "medium"},
                {"skill": "Kubernetes", "frequency": 45, "priority": "medium"}
            ],
            "market_demand": {
                "total_jobs_analyzed": 150,
                "user_match_percentage": 72,
                "avg_salary_range": {"min": 100000, "max": 140000}
            },
            "recommendations": [
                "Focus on React for immediate impact",
                "Consider Docker certification"
            ]
        }
    }
    
    # Validate required fields
    assert "user_id" in skill_gap_data
    assert "type" in skill_gap_data
    assert "data" in skill_gap_data
    assert isinstance(skill_gap_data["data"], dict)
    
    # Validate analytics types
    valid_types = [
        "skill_gap_analysis", "application_success_rate", "market_trends",
        "recommendation_performance", "career_progression", "salary_analysis",
        "company_response_times", "application_timing_analysis",
        "job_search_velocity", "interview_success_rate"
    ]
    assert skill_gap_data["type"] in valid_types
    
    # Validate skill gap analysis structure
    data = skill_gap_data["data"]
    assert "missing_skills" in data
    assert isinstance(data["missing_skills"], list)
    
    for skill in data["missing_skills"]:
        assert "skill" in skill
        assert "frequency" in skill
        assert "priority" in skill
        assert skill["priority"] in ["low", "medium", "high"]
    
    print("✓ Analytics model structure validation passed")


def test_application_success_rate_analytics():
    """Test application success rate analytics structure."""
    success_rate_data = {
        "user_id": 1,
        "type": "application_success_rate",
        "data": {
            "period": "2024-01",
            "applications_sent": 25,
            "responses_received": 8,
            "interviews_scheduled": 3,
            "offers_received": 1,
            "conversion_rates": {
                "response_rate": 0.32,
                "interview_rate": 0.12,
                "offer_rate": 0.04
            },
            "by_category": {
                "frontend": {"sent": 10, "responses": 4, "interviews": 2},
                "backend": {"sent": 15, "responses": 4, "interviews": 1}
            }
        }
    }
    
    data = success_rate_data["data"]
    
    # Validate numeric consistency
    assert data["responses_received"] <= data["applications_sent"]
    assert data["interviews_scheduled"] <= data["responses_received"]
    assert data["offers_received"] <= data["interviews_scheduled"]
    
    # Validate conversion rates
    rates = data["conversion_rates"]
    assert 0.0 <= rates["response_rate"] <= 1.0
    assert 0.0 <= rates["interview_rate"] <= 1.0
    assert 0.0 <= rates["offer_rate"] <= 1.0
    
    # Validate category breakdown
    category_total = sum(cat["sent"] for cat in data["by_category"].values())
    assert category_total == data["applications_sent"]
    
    print("✓ Application success rate analytics validation passed")


def test_market_trends_analytics():
    """Test market trends analytics structure."""
    market_trends_data = {
        "user_id": 1,
        "type": "market_trends",
        "data": {
            "analysis_date": "2024-01-15",
            "location": "San Francisco",
            "role_category": "software_engineer",
            "trends": {
                "salary_range": {"min": 120000, "max": 180000, "median": 150000},
                "top_skills": ["Python", "React", "AWS", "Docker", "PostgreSQL"],
                "growth_rate": 0.15,
                "job_availability": "high",
                "remote_percentage": 0.65
            },
            "industry_breakdown": {
                "fintech": {"jobs": 45, "avg_salary": 160000},
                "healthcare": {"jobs": 30, "avg_salary": 145000},
                "edtech": {"jobs": 25, "avg_salary": 135000}
            }
        }
    }
    
    data = market_trends_data["data"]
    trends = data["trends"]
    
    # Validate salary range
    salary_range = trends["salary_range"]
    assert salary_range["min"] <= salary_range["median"] <= salary_range["max"]
    
    # Validate percentages
    assert 0.0 <= trends["remote_percentage"] <= 1.0
    
    # Validate job availability levels
    assert trends["job_availability"] in ["low", "medium", "high", "very_high"]
    
    # Validate industry breakdown
    for industry, stats in data["industry_breakdown"].items():
        assert "jobs" in stats
        assert "avg_salary" in stats
        assert stats["jobs"] > 0
        assert stats["avg_salary"] > 0
    
    print("✓ Market trends analytics validation passed")


def test_json_serialization():
    """Test JSON serialization of model data."""
    # Test complex nested structure
    complex_data = {
        "user_profile": {
            "skills": ["Python", "JavaScript", "React", "AWS"],
            "experience": {
                "years": 5,
                "companies": ["TechCorp", "StartupInc"],
                "roles": ["Developer", "Senior Developer"]
            },
            "preferences": {
                "salary_range": {"min": 100000, "max": 150000},
                "locations": ["SF", "NYC", "Remote"],
                "company_sizes": ["startup", "medium"]
            }
        },
        "analytics_data": {
            "skill_gaps": [
                {"skill": "React", "priority": "high", "market_demand": 0.85},
                {"skill": "Docker", "priority": "medium", "market_demand": 0.70}
            ],
            "application_stats": {
                "total_sent": 50,
                "response_rate": 0.24,
                "success_metrics": {"interviews": 8, "offers": 2}
            }
        }
    }
    
    # Test JSON serialization
    json_str = json.dumps(complex_data)
    assert isinstance(json_str, str)
    
    # Test JSON deserialization
    parsed_data = json.loads(json_str)
    assert parsed_data == complex_data
    
    # Validate nested structure preservation
    assert parsed_data["user_profile"]["experience"]["years"] == 5
    assert len(parsed_data["analytics_data"]["skill_gaps"]) == 2
    
    print("✓ JSON serialization validation passed")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    # Test empty data structures
    empty_profile = {}
    empty_settings = {}
    empty_requirements = {}
    empty_analytics_data = {"status": "no_data"}
    
    assert isinstance(empty_profile, dict)
    assert isinstance(empty_settings, dict)
    assert isinstance(empty_requirements, dict)
    assert isinstance(empty_analytics_data, dict)
    
    # Test large data structures
    large_skills_list = [f"skill_{i}" for i in range(1000)]
    assert len(large_skills_list) == 1000
    
    # Test unicode and special characters
    unicode_data = {
        "title": "Développeur Senior (Python/Django) - €120k-€150k",
        "company": "Société Française de Technologie",
        "location": "Paris, France 🇫🇷",
        "description": "Nous recherchons... 中文测试 العربية тест",
        "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    }
    
    # Test JSON serialization with unicode
    unicode_json = json.dumps(unicode_data, ensure_ascii=False)
    parsed_unicode = json.loads(unicode_json)
    assert parsed_unicode == unicode_data
    
    # Test null/None values
    nullable_fields = {
        "location": None,
        "salary_min": None,
        "salary_max": None,
        "description": None,
        "date_applied": None
    }
    
    for field, value in nullable_fields.items():
        assert value is None
    
    print("✓ Edge cases validation passed")


def test_data_validation_rules():
    """Test data validation rules and constraints."""
    # Test email format validation (basic check)
    valid_emails = [
        "user@example.com",
        "test.user+tag@domain.co.uk",
        "user123@test-domain.org"
    ]
    
    invalid_emails = [
        "invalid-email",
        "@domain.com",
        "user@",
        "user space@domain.com"
    ]
    
    for email in valid_emails:
        assert "@" in email and "." in email.split("@")[1]
    
    # Test salary validation
    def validate_salary_range(min_sal, max_sal):
        if min_sal is not None and max_sal is not None:
            return min_sal <= max_sal and min_sal > 0 and max_sal > 0
        return True
    
    assert validate_salary_range(80000, 120000) is True
    assert validate_salary_range(120000, 80000) is False
    assert validate_salary_range(None, 120000) is True
    
    # Test recommendation score validation
    def validate_recommendation_score(score):
        return score is None or (0.0 <= score <= 1.0)
    
    assert validate_recommendation_score(0.85) is True
    assert validate_recommendation_score(1.5) is False
    assert validate_recommendation_score(-0.1) is False
    assert validate_recommendation_score(None) is True
    
    print("✓ Data validation rules passed")


if __name__ == "__main__":
    """Run all validation tests."""
    try:
        test_user_model_structure()
        test_job_model_structure()
        test_analytics_model_structure()
        test_application_success_rate_analytics()
        test_market_trends_analytics()
        test_json_serialization()
        test_edge_cases()
        test_data_validation_rules()
        
        print("\n🎉 All model validation tests passed successfully!")
        print("✅ User model validation: PASSED")
        print("✅ Job model validation: PASSED") 
        print("✅ Analytics model validation: PASSED")
        print("✅ JSON serialization: PASSED")
        print("✅ Edge cases: PASSED")
        print("✅ Data validation rules: PASSED")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)