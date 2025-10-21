"""
Configuration for comprehensive integration tests
Defines test parameters, thresholds, and mock data
"""

from datetime import datetime, timedelta
import os

# Test Configuration
TEST_CONFIG = {
    "timeouts": {
        "api_request": 30,
        "database_query": 10,
        "external_api": 60,
        "email_delivery": 120
    },
    
    "performance_thresholds": {
        "api_response_time_ms": 500,
        "database_query_time_ms": 100,
        "job_processing_rate_per_second": 10,
        "recommendation_generation_seconds": 5,
        "success_rate_minimum": 0.90
    },
    
    "load_testing": {
        "concurrent_users": 50,
        "requests_per_user": 5,
        "ramp_up_time_seconds": 10,
        "test_duration_seconds": 60
    },
    
    "error_scenarios": {
        "database_failure_rate": 0.1,
        "external_api_failure_rate": 0.15,
        "network_timeout_rate": 0.05,
        "memory_exhaustion_threshold": 0.9
    }
}

# Mock Data Templates
MOCK_USER_DATA = {
    "id": 1,
    "email": "test@example.com",
    "profile": {
        "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
        "experience_level": "mid",
        "preferred_locations": ["Remote", "San Francisco", "New York"],
        "salary_range": {"min": 80000, "max": 120000},
        "job_types": ["full-time", "contract"]
    },
    "preferences": {
        "email_notifications": True,
        "job_alerts": True,
        "morning_briefing": True,
        "evening_summary": False
    }
}

MOCK_JOB_DATA = [
    {
        "id": 1,
        "title": "Senior Python Developer",
        "company": "TechCorp Inc",
        "location": "San Francisco, CA",
        "salary_min": 100000,
        "salary_max": 130000,
        "job_type": "full-time",
        "skills_required": ["Python", "Django", "PostgreSQL", "AWS"],
        "experience_level": "senior",
        "posted_date": datetime.now().isoformat(),
        "description": "Looking for an experienced Python developer...",
        "url": "https://example.com/job/1"
    },
    {
        "id": 2,
        "title": "Full Stack Engineer",
        "company": "StartupXYZ",
        "location": "Remote",
        "salary_min": 90000,
        "salary_max": 110000,
        "job_type": "full-time",
        "skills_required": ["React", "Node.js", "MongoDB", "Docker"],
        "experience_level": "mid",
        "posted_date": datetime.now().isoformat(),
        "description": "Join our growing team as a full stack engineer...",
        "url": "https://example.com/job/2"
    },
    {
        "id": 3,
        "title": "Backend Developer",
        "company": "Enterprise Solutions",
        "location": "New York, NY",
        "salary_min": 85000,
        "salary_max": 105000,
        "job_type": "full-time",
        "skills_required": ["FastAPI", "Python", "Redis", "Kubernetes"],
        "experience_level": "mid",
        "posted_date": datetime.now().isoformat(),
        "description": "Backend developer role focusing on API development...",
        "url": "https://example.com/job/3"
    }
]

MOCK_RECOMMENDATION_DATA = [
    {
        "job_id": 1,
        "match_score": 0.92,
        "title": "Senior Python Developer",
        "company": "TechCorp Inc",
        "reasons": [
            "Strong Python skills match",
            "Experience level alignment",
            "Location preference match"
        ],
        "skill_gaps": ["AWS", "Django"],
        "salary_match": True
    },
    {
        "job_id": 2,
        "match_score": 0.87,
        "title": "Full Stack Engineer", 
        "company": "StartupXYZ",
        "reasons": [
            "React experience match",
            "Remote work preference",
            "Salary range alignment"
        ],
        "skill_gaps": ["Node.js", "MongoDB"],
        "salary_match": True
    }
]

MOCK_ANALYTICS_DATA = {
    "user_metrics": {
        "applications_submitted": 5,
        "interviews_scheduled": 2,
        "offers_received": 1,
        "response_rate": 0.4,
        "avg_application_time_days": 3.5
    },
    "market_trends": {
        "python_demand_score": 0.85,
        "remote_job_percentage": 0.65,
        "avg_salary_increase": 0.08,
        "skill_demand": {
            "Python": 0.9,
            "React": 0.8,
            "FastAPI": 0.7,
            "Docker": 0.75
        }
    },
    "system_metrics": {
        "daily_active_users": 150,
        "jobs_processed_today": 500,
        "recommendations_generated": 750,
        "emails_sent": 200,
        "api_response_time_avg": 250
    }
}

# Error Simulation Data
ERROR_SCENARIOS = {
    "database_errors": [
        "Connection timeout",
        "Query execution failed",
        "Transaction rollback",
        "Connection pool exhausted",
        "Lock timeout"
    ],
    
    "external_api_errors": [
        "Rate limit exceeded",
        "API key invalid",
        "Service unavailable",
        "Request timeout",
        "Authentication failed"
    ],
    
    "system_errors": [
        "Memory exhaustion",
        "CPU overload",
        "Disk space full",
        "Network unreachable",
        "Service dependency failure"
    ],
    
    "data_corruption_scenarios": [
        {"type": "missing_fields", "severity": "medium"},
        {"type": "invalid_data_types", "severity": "high"},
        {"type": "malformed_json", "severity": "high"},
        {"type": "sql_injection", "severity": "critical"},
        {"type": "xss_attempt", "severity": "critical"}
    ]
}

# Recovery Test Scenarios
RECOVERY_SCENARIOS = {
    "circuit_breaker": {
        "failure_threshold": 5,
        "recovery_timeout": 60,
        "half_open_max_calls": 3
    },
    
    "retry_policies": {
        "max_retries": 3,
        "backoff_multiplier": 2,
        "max_backoff_seconds": 60
    },
    
    "fallback_strategies": {
        "cache_fallback": True,
        "default_responses": True,
        "graceful_degradation": True
    }
}

# Test Environment Settings
TEST_ENVIRONMENT = {
    "database_url": os.getenv("TEST_DATABASE_URL", "sqlite:///test.db"),
    "redis_url": os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1"),
    "email_backend": "mock",
    "external_apis_mock": True,
    "logging_level": "INFO",
    "debug_mode": True
}

# Validation Rules
VALIDATION_RULES = {
    "data_quality": {
        "min_completeness": 0.95,
        "max_error_rate": 0.05,
        "consistency_threshold": 0.98
    },
    
    "performance": {
        "max_response_time": 1000,
        "min_throughput": 100,
        "max_error_rate": 0.01
    },
    
    "security": {
        "max_failed_auth_attempts": 5,
        "session_timeout_minutes": 30,
        "password_strength_min": 8
    }
}

def get_test_config():
    """Get complete test configuration"""
    return {
        "config": TEST_CONFIG,
        "mock_data": {
            "user": MOCK_USER_DATA,
            "jobs": MOCK_JOB_DATA,
            "recommendations": MOCK_RECOMMENDATION_DATA,
            "analytics": MOCK_ANALYTICS_DATA
        },
        "error_scenarios": ERROR_SCENARIOS,
        "recovery_scenarios": RECOVERY_SCENARIOS,
        "environment": TEST_ENVIRONMENT,
        "validation_rules": VALIDATION_RULES
    }

def get_performance_benchmarks():
    """Get performance benchmark thresholds"""
    return TEST_CONFIG["performance_thresholds"]

def get_mock_user(user_id=1):
    """Get mock user data with specified ID"""
    user_data = MOCK_USER_DATA.copy()
    user_data["id"] = user_id
    user_data["email"] = f"test{user_id}@example.com"
    return user_data

def get_mock_jobs(count=None):
    """Get mock job data"""
    if count is None:
        return MOCK_JOB_DATA
    return MOCK_JOB_DATA[:count]

def get_error_scenario(scenario_type):
    """Get specific error scenario configuration"""
    return ERROR_SCENARIOS.get(scenario_type, [])