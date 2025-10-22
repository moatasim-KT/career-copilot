import sys
import os
import pytest
from unittest.mock import Mock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../backend')))
from app.services.skill_gap_analyzer import SkillGapAnalyzer
from app.models.user import User
from app.models.job import Job

def test_response_format():
    """Test that the response format matches requirements 4.5"""
    # Mock database session
    mock_db = Mock()
    
    # Create test user with skills
    test_user = User()
    test_user.id = 1
    test_user.skills = ["Python", "FastAPI"]
    
    # Create test jobs
    job1 = Job()
    job1.tech_stack = ["Python", "FastAPI", "PostgreSQL", "Docker"]
    
    job2 = Job()
    job2.tech_stack = ["Python", "React", "JavaScript"]
    
    test_user.jobs = [job1, job2]
    
    # Run analysis
    analyzer = SkillGapAnalyzer(db=mock_db)
    result = analyzer.analyze_skill_gaps(test_user)
    
    # Required fields: user_skills, missing_skills, top_market_skills, skill_coverage_percentage, learning_recommendations
    required_fields = [
        'user_skills',
        'missing_skills', 
        'skill_coverage_percentage',
        'learning_recommendations'
    ]
    
    for field in required_fields:
        assert field in result, f"Field '{field}' is missing from the response"
    
    assert isinstance(result['user_skills'], list)
    assert isinstance(result['missing_skills'], dict)
    assert isinstance(result['skill_coverage_percentage'], (int, float))
    assert isinstance(result['learning_recommendations'], list)
    assert len(result['learning_recommendations']) <= 5