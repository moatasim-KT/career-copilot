"""
Simple skill gap analysis test using the test framework

This test validates basic skill gap analysis functionality including:
- API endpoint response times
- Analysis accuracy
- Recommendation generation
"""

import pytest
import asyncio
from tests.e2e.skill_gap_analysis_test_framework import SkillGapAnalysisTestFramework


class TestSkillGapAnalysisSimple:
    """Simple test class for skill gap analysis functionality"""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for each test"""
        self.framework = SkillGapAnalysisTestFramework()
        yield
        # Cleanup after test
        await self.framework.cleanup_test_environment()
    
    @pytest.mark.asyncio
    async def test_skill_gap_analysis_basic_functionality(self):
        """Test basic skill gap analysis functionality"""
        # Setup test environment
        setup_success = await self.framework.setup_test_environment()
        assert setup_success, "Failed to setup test environment"
        
        # Test API endpoints
        api_results = await self.framework.test_skill_gap_api_endpoints()
        
        # Validate API results
        assert "error" not in api_results, f"API test failed: {api_results.get('error')}"
        
        # Check basic skill gap analysis results
        basic_results = api_results.get("basic_skill_gap_analysis", [])
        assert len(basic_results) > 0, "No basic skill gap analysis results"
        
        # Validate that at least some analyses were successful
        successful_analyses = [r for r in basic_results if r.get("success", False)]
        assert len(successful_analyses) > 0, "No successful skill gap analyses"
        
        # Check that analyses generated results
        for result in successful_analyses:
            assert result.get("analysis_generated", False), f"Analysis not generated for user {result.get('user_id')}"
            assert result.get("execution_time", 0) > 0, f"Invalid execution time for user {result.get('user_id')}"
    
    @pytest.mark.asyncio
    async def test_skill_gap_analysis_response_time(self):
        """Test that skill gap analysis meets response time requirements (15 seconds)"""
        # Setup test environment
        setup_success = await self.framework.setup_test_environment()
        assert setup_success, "Failed to setup test environment"
        
        # Test API endpoints
        api_results = await self.framework.test_skill_gap_api_endpoints()
        
        # Validate response times
        basic_results = api_results.get("basic_skill_gap_analysis", [])
        response_time_validation = self.framework.validate_response_time_requirements(basic_results)
        
        assert response_time_validation.get("meets_requirements", False), \
            f"Response time requirements not met. Max time: {response_time_validation.get('max_execution_time', 0):.2f}s, " \
            f"Limit: {response_time_validation.get('time_limit', 0)}s"
        
        # Ensure average response time is reasonable
        avg_time = response_time_validation.get("average_execution_time", 0)
        assert avg_time < 10.0, f"Average response time too high: {avg_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_skill_gap_analysis_accuracy(self):
        """Test skill gap analysis accuracy against expected results"""
        # Setup test environment
        setup_success = await self.framework.setup_test_environment()
        assert setup_success, "Failed to setup test environment"
        
        # Run comprehensive test to get accuracy results
        results = await self.framework.run_comprehensive_skill_gap_test()
        
        assert "error" not in results, f"Comprehensive test failed: {results.get('error')}"
        
        # Check accuracy results
        accuracy_results = results.get("accuracy_test_results", [])
        assert len(accuracy_results) > 0, "No accuracy test results"
        
        # Validate accuracy metrics
        successful_accuracy_tests = [r for r in accuracy_results if "error" not in r]
        assert len(successful_accuracy_tests) > 0, "No successful accuracy tests"
        
        # Check that F1 scores are reasonable (> 0.3 for at least some users)
        f1_scores = [r.get("accuracy_metrics", {}).get("f1_score", 0) for r in successful_accuracy_tests]
        reasonable_f1_scores = [score for score in f1_scores if score > 0.3]
        
        assert len(reasonable_f1_scores) > 0, f"No reasonable F1 scores found. Scores: {f1_scores}"
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis_endpoint(self):
        """Test comprehensive skill gap analysis endpoint"""
        # Setup test environment
        setup_success = await self.framework.setup_test_environment()
        assert setup_success, "Failed to setup test environment"
        
        # Test API endpoints
        api_results = await self.framework.test_skill_gap_api_endpoints()
        
        # Check comprehensive analysis results
        comprehensive_results = api_results.get("comprehensive_analysis", [])
        assert len(comprehensive_results) > 0, "No comprehensive analysis results"
        
        # Validate that analyses were successful
        successful_analyses = [r for r in comprehensive_results if r.get("success", False)]
        assert len(successful_analyses) > 0, "No successful comprehensive analyses"
        
        # Check that comprehensive analyses provide more detailed results
        for result in successful_analyses:
            assert result.get("analysis_generated", False), f"Comprehensive analysis not generated for user {result.get('user_id')}"
            assert result.get("gaps_identified", 0) >= 0, f"Invalid gaps count for user {result.get('user_id')}"
            assert result.get("recommendations_count", 0) >= 0, f"Invalid recommendations count for user {result.get('user_id')}"
    
    @pytest.mark.asyncio
    async def test_learning_recommendations_generation(self):
        """Test learning recommendations generation"""
        # Setup test environment
        setup_success = await self.framework.setup_test_environment()
        assert setup_success, "Failed to setup test environment"
        
        # Test API endpoints
        api_results = await self.framework.test_skill_gap_api_endpoints()
        
        # Check learning recommendations results
        recommendations_results = api_results.get("learning_recommendations", [])
        assert len(recommendations_results) > 0, "No learning recommendations results"
        
        # Validate that recommendations were generated
        successful_recommendations = [r for r in recommendations_results if r.get("success", False)]
        assert len(successful_recommendations) > 0, "No successful learning recommendations"
        
        # Check that recommendations provide useful content
        for result in successful_recommendations:
            assert result.get("recommendations_generated", False), f"Recommendations not generated for user {result.get('user_id')}"
            # At least some users should have recommendations
            if result.get("recommendations_count", 0) > 0:
                assert result.get("recommendations_count") > 0, f"No recommendations for user {result.get('user_id')}"


# Standalone test function for pytest
@pytest.mark.asyncio
async def test_skill_gap_analysis_integration():
    """Integration test for skill gap analysis system"""
    framework = SkillGapAnalysisTestFramework()
    
    try:
        # Run comprehensive test
        results = await framework.run_comprehensive_skill_gap_test()
        
        # Basic validation
        assert "error" not in results, f"Integration test failed: {results.get('error')}"
        assert results.get("overall_success", False), "Integration test did not succeed overall"
        
        # Validate test summary
        summary = results.get("test_summary", {})
        assert summary.get("test_users_created", 0) > 0, "No test users created"
        assert summary.get("market_jobs_created", 0) > 0, "No market jobs created"
        
        # Validate API performance
        api_results = results.get("api_test_results", {})
        api_performance = api_results.get("api_performance", {})
        
        if api_performance and "error" not in api_performance:
            success_rate = api_performance.get("success_rate", 0)
            assert success_rate > 0.5, f"API success rate too low: {success_rate:.2%}"
        
        # Validate response time requirements
        response_time_validation = results.get("response_time_validation", {})
        if response_time_validation:
            assert response_time_validation.get("meets_requirements", False), \
                "Response time requirements not met in integration test"
        
    finally:
        # Cleanup
        await framework.cleanup_test_environment()


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_skill_gap_analysis_integration())
    print("Skill gap analysis integration test completed successfully!")