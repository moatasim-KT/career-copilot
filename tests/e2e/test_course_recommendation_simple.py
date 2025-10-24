"""
Simple Course Recommendation Test

This module provides a simple test for course recommendation functionality
that can be run independently to verify the system works correctly.
"""

import asyncio
import pytest
from tests.e2e.course_recommendation_test_framework import CourseRecommendationTestFramework


class TestCourseRecommendationSimple:
    """Simple test class for course recommendation functionality"""
    
    @pytest.mark.asyncio
    async def test_course_recommendation_basic_functionality(self):
        """Test basic course recommendation functionality"""
        framework = CourseRecommendationTestFramework()
        
        try:
            # Setup test environment
            setup_success = await framework.setup_test_environment()
            assert setup_success, "Failed to setup test environment"
            
            # Test API endpoints
            api_results = await framework.test_course_recommendation_api_endpoints()
            
            # Verify we got results
            assert "error" not in api_results, f"API test failed: {api_results.get('error')}"
            
            # Check learning recommendations
            learning_results = api_results.get("learning_recommendations", [])
            assert len(learning_results) > 0, "No learning recommendation results"
            
            # Verify at least one successful recommendation
            successful_recommendations = [r for r in learning_results if r.success]
            assert len(successful_recommendations) > 0, "No successful course recommendations generated"
            
            # Check response times
            for result in successful_recommendations:
                assert result.execution_time <= 10.0, f"Response time {result.execution_time}s exceeds 10s limit"
            
            # Check recommendation quality
            for result in successful_recommendations:
                assert result.recommendations_count > 0, "No recommendations returned"
                assert result.average_relevance_score > 0, "Zero relevance score"
            
            print(f"✓ Course recommendation test passed with {len(successful_recommendations)} successful results")
            
        finally:
            # Cleanup
            await framework.cleanup_test_environment()
    
    @pytest.mark.asyncio
    async def test_course_recommendation_response_times(self):
        """Test that course recommendations meet response time requirements"""
        framework = CourseRecommendationTestFramework()
        
        try:
            # Setup test environment
            setup_success = await framework.setup_test_environment()
            assert setup_success, "Failed to setup test environment"
            
            # Test API endpoints
            api_results = await framework.test_course_recommendation_api_endpoints()
            
            # Collect all results
            all_results = []
            for endpoint_results in api_results.values():
                if isinstance(endpoint_results, list):
                    all_results.extend(endpoint_results)
            
            # Validate response times
            response_time_validation = framework.validate_response_time_requirements(all_results)
            
            assert response_time_validation.get("meets_requirements", False), \
                f"Response time requirements not met: max time {response_time_validation.get('max_execution_time', 0):.3f}s"
            
            print(f"✓ Response time validation passed: max {response_time_validation.get('max_execution_time', 0):.3f}s")
            
        finally:
            # Cleanup
            await framework.cleanup_test_environment()
    
    @pytest.mark.asyncio
    async def test_course_recommendation_quality_validation(self):
        """Test course recommendation quality and relevance"""
        framework = CourseRecommendationTestFramework()
        
        try:
            # Setup test environment
            setup_success = await framework.setup_test_environment()
            assert setup_success, "Failed to setup test environment"
            
            # Test skill-based course recommendations
            api_results = await framework.test_course_recommendation_api_endpoints()
            skill_courses_results = api_results.get("skill_based_courses", [])
            
            # Verify quality metrics
            successful_results = [r for r in skill_courses_results if r.success]
            assert len(successful_results) > 0, "No successful skill-based course recommendations"
            
            # Check relevance scores
            total_relevance = sum(r.average_relevance_score for r in successful_results)
            average_relevance = total_relevance / len(successful_results)
            
            assert average_relevance > 0.5, f"Low average relevance score: {average_relevance:.2f}"
            
            # Check high quality matches
            total_high_quality = sum(r.high_quality_matches for r in successful_results)
            assert total_high_quality > 0, "No high quality course matches found"
            
            print(f"✓ Quality validation passed: avg relevance {average_relevance:.2f}, "
                  f"{total_high_quality} high quality matches")
            
        finally:
            # Cleanup
            await framework.cleanup_test_environment()


# Standalone test function for manual execution
async def run_simple_course_recommendation_test():
    """Run a simple course recommendation test manually"""
    print("Running Simple Course Recommendation Test...")
    print("=" * 50)
    
    framework = CourseRecommendationTestFramework()
    
    try:
        # Setup
        print("Setting up test environment...")
        setup_success = await framework.setup_test_environment()
        if not setup_success:
            print("❌ Failed to setup test environment")
            return False
        
        print(f"✓ Created {len(framework.test_users)} test users")
        
        # Test API endpoints
        print("Testing course recommendation API endpoints...")
        api_results = await framework.test_course_recommendation_api_endpoints()
        
        if "error" in api_results:
            print(f"❌ API test failed: {api_results['error']}")
            return False
        
        # Check results
        learning_results = api_results.get("learning_recommendations", [])
        skill_results = api_results.get("skill_based_courses", [])
        path_results = api_results.get("personalized_learning_paths", [])
        
        successful_learning = [r for r in learning_results if r.success]
        successful_skill = [r for r in skill_results if r.success]
        successful_path = [r for r in path_results if r.success]
        
        print(f"✓ Learning recommendations: {len(successful_learning)}/{len(learning_results)} successful")
        print(f"✓ Skill-based courses: {len(successful_skill)}/{len(skill_results)} successful")
        print(f"✓ Learning paths: {len(successful_path)}/{len(path_results)} successful")
        
        # Check response times
        all_results = learning_results + skill_results + path_results
        response_time_validation = framework.validate_response_time_requirements(all_results)
        
        if response_time_validation.get("meets_requirements", False):
            print(f"✓ Response times meet requirements (max: {response_time_validation.get('max_execution_time', 0):.3f}s)")
        else:
            print(f"⚠️  Response times exceed requirements (max: {response_time_validation.get('max_execution_time', 0):.3f}s)")
        
        # Performance summary
        api_performance = api_results.get("api_performance", {})
        if api_performance and "error" not in api_performance:
            print(f"✓ Overall success rate: {api_performance.get('success_rate', 0):.1%}")
            print(f"✓ Average relevance score: {api_performance.get('average_relevance_score', 0):.2f}")
        
        print("\n✅ Course recommendation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Cleanup
        print("Cleaning up test environment...")
        await framework.cleanup_test_environment()


if __name__ == "__main__":
    # Run the simple test when executed directly
    asyncio.run(run_simple_course_recommendation_test())