"""
Job Recommendation Integration Test

This test validates the job recommendation testing framework integration
with the existing E2E test infrastructure.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.test_job_recommendation_simple import SimpleJobRecommendationTest


class TestJobRecommendationIntegration:
    """Integration tests for job recommendation testing framework"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_framework = SimpleJobRecommendationTest()
    
    def test_user_profile_creation(self):
        """Test that test user profiles are created correctly"""
        results = self.test_framework.test_user_profile_creation()
        
        assert results["success"] is True
        assert results["users_created"] == 3
        assert len(results["profiles"]) == 3
        
        # Verify profile structure
        for profile in results["profiles"]:
            assert "name" in profile
            assert "skills_count" in profile
            assert "experience_level" in profile
            assert profile["skills_count"] > 0
    
    def test_recommendation_api_client(self):
        """Test recommendation API client functionality"""
        results = self.test_framework.test_recommendation_api_client()
        
        assert results["success"] is True
        assert results["total_recommendations"] > 0
        assert len(results["api_tests"]) == 3
        
        # Verify each user got recommendations
        for api_test in results["api_tests"]:
            assert api_test["success"] is True
            assert api_test["recommendations_count"] > 0
            assert api_test["average_score"] >= 0
    
    def test_recommendation_relevance_validation(self):
        """Test recommendation relevance validation"""
        results = self.test_framework.test_recommendation_relevance()
        
        assert results["success"] is True
        assert len(results["relevance_tests"]) == 3
        assert results["overall_relevance"] >= 0
        
        # Verify relevance metrics
        for relevance_test in results["relevance_tests"]:
            assert relevance_test["success"] is True
            assert relevance_test["total_recommendations"] > 0
            assert 0 <= relevance_test["relevance_score"] <= 1
    
    def test_recommendation_quality_distribution(self):
        """Test recommendation quality distribution analysis"""
        results = self.test_framework.test_recommendation_quality_distribution()
        
        assert results["success"] is True
        assert results["total_recommendations"] > 0
        assert results["average_score"] >= 0
        
        # Verify quality distribution structure
        quality_dist = results["quality_distribution"]
        expected_qualities = ["excellent", "high", "medium", "low"]
        
        for quality in expected_qualities:
            assert quality in quality_dist
            assert quality_dist[quality] >= 0
        
        # Total should match sum of distribution
        total_from_dist = sum(quality_dist.values())
        assert total_from_dist == results["total_recommendations"]
    
    def test_comprehensive_recommendation_test(self):
        """Test comprehensive recommendation testing workflow"""
        results = self.test_framework.run_comprehensive_test()
        
        assert results["overall_success"] is True
        
        # Verify all test components are present
        assert "profile_test" in results
        assert "api_test" in results
        assert "relevance_test" in results
        assert "quality_test" in results
        assert "summary" in results
        
        # Verify summary metrics
        summary = results["summary"]
        assert summary["users_tested"] == 3
        assert summary["total_recommendations"] > 0
        assert 0 <= summary["overall_relevance"] <= 1
        assert summary["average_quality"] >= 0
    
    def test_user_profile_characteristics(self):
        """Test that user profiles have expected characteristics"""
        users = self.test_framework.test_users
        
        # Verify we have different types of users
        experience_levels = [user.experience_level for user in users]
        assert "junior" in experience_levels
        assert "senior" in experience_levels
        assert "mid" in experience_levels
        
        # Verify users have different skill sets
        all_skills = set()
        for user in users:
            all_skills.update(user.skills)
        
        # Should have diverse skills across users
        assert len(all_skills) >= 8  # At least 8 different skills total
        
        # Verify location preferences
        all_locations = set()
        for user in users:
            all_locations.update(user.preferred_locations)
        
        assert "Remote" in all_locations  # All should prefer remote
        assert len(all_locations) > 2  # Should have multiple location preferences
    
    def test_recommendation_scoring_logic(self):
        """Test that recommendation scoring logic works correctly"""
        engine = self.test_framework.recommendation_engine
        
        # Create test user and job with perfect match
        from tests.e2e.test_job_recommendation_simple import MockUser, MockJob
        
        perfect_user = MockUser(
            id=999, name="Perfect Match User", email="perfect@test.com",
            skills=["Python", "Django"], preferred_locations=["Remote"],
            experience_level="senior"
        )
        
        perfect_job = MockJob(
            id=999, user_id=999, title="Senior Python Developer", company="TestCorp",
            location="Remote", description="Perfect match job",
            tech_stack=["Python", "Django"], salary_range="$100k-120k",
            job_type="full-time", remote_option=True
        )
        
        # Calculate match score
        score = engine.calculate_match_score(perfect_user, perfect_job)
        
        # Should be a high score (near 100)
        assert score >= 90, f"Expected high score for perfect match, got {score}"
        
        # Test with poor match
        poor_job = MockJob(
            id=998, user_id=999, title="Junior Java Developer", company="TestCorp",
            location="New York, NY", description="Poor match job",
            tech_stack=["Java", "Spring"], salary_range="$60k-80k",
            job_type="full-time", remote_option=False
        )
        
        poor_score = engine.calculate_match_score(perfect_user, poor_job)
        
        # Should be a lower score
        assert poor_score < score, f"Poor match should score lower than perfect match"
        assert poor_score >= 0, f"Score should not be negative, got {poor_score}"
    
    def test_recommendation_framework_requirements_compliance(self):
        """Test that the framework meets the task requirements"""
        
        # Requirement: Create test user profiles for recommendation testing
        users = self.test_framework.test_users
        assert len(users) >= 3, "Should have multiple test user profiles"
        
        for user in users:
            assert hasattr(user, 'skills'), "Users should have skills"
            assert hasattr(user, 'preferred_locations'), "Users should have location preferences"
            assert hasattr(user, 'experience_level'), "Users should have experience level"
        
        # Requirement: Add API client for job recommendation endpoints
        engine = self.test_framework.recommendation_engine
        assert hasattr(engine, 'get_recommendations'), "Should have recommendation API method"
        assert hasattr(engine, 'calculate_match_score'), "Should have scoring method"
        
        # Test API client functionality
        test_user = users[0]
        recommendations = engine.get_recommendations(test_user, limit=5)
        assert isinstance(recommendations, list), "API should return list of recommendations"
        
        if recommendations:
            rec = recommendations[0]
            assert "job" in rec, "Recommendation should contain job data"
            assert "score" in rec, "Recommendation should contain score"
        
        # Requirement: Implement recommendation relevance validation
        relevance_results = self.test_framework.test_recommendation_relevance()
        assert relevance_results["success"], "Relevance validation should work"
        
        for test_result in relevance_results["relevance_tests"]:
            if test_result["success"]:
                assert "skill_matches" in test_result, "Should validate skill matches"
                assert "location_matches" in test_result, "Should validate location matches"
                assert "experience_matches" in test_result, "Should validate experience matches"
                assert "relevance_score" in test_result, "Should calculate relevance score"


# Pytest fixtures and test runner
@pytest.fixture
def recommendation_test_framework():
    """Fixture to provide recommendation test framework"""
    return SimpleJobRecommendationTest()


def test_framework_initialization(recommendation_test_framework):
    """Test that the framework initializes correctly"""
    assert recommendation_test_framework is not None
    assert len(recommendation_test_framework.test_users) > 0
    assert recommendation_test_framework.recommendation_engine is not None


def test_end_to_end_recommendation_workflow(recommendation_test_framework):
    """Test complete end-to-end recommendation workflow"""
    # Run the complete test workflow
    results = recommendation_test_framework.run_comprehensive_test()
    
    # Verify overall success
    assert results["overall_success"] is True
    
    # Verify all components completed successfully
    assert results["profile_test"]["success"] is True
    assert results["api_test"]["success"] is True
    assert results["relevance_test"]["success"] is True
    assert results["quality_test"]["success"] is True


if __name__ == "__main__":
    # Run tests directly
    test_class = TestJobRecommendationIntegration()
    test_class.setup_method()
    
    print("🧪 Running Job Recommendation Integration Tests")
    print("=" * 50)
    
    tests = [
        ("User Profile Creation", test_class.test_user_profile_creation),
        ("API Client", test_class.test_recommendation_api_client),
        ("Relevance Validation", test_class.test_recommendation_relevance_validation),
        ("Quality Distribution", test_class.test_recommendation_quality_distribution),
        ("Comprehensive Test", test_class.test_comprehensive_recommendation_test),
        ("Profile Characteristics", test_class.test_user_profile_characteristics),
        ("Scoring Logic", test_class.test_recommendation_scoring_logic),
        ("Requirements Compliance", test_class.test_recommendation_framework_requirements_compliance)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {str(e)}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")