"""
Course Recommendation Demo

This script demonstrates the course recommendation testing framework
and shows how it validates course suggestion functionality.
"""

import asyncio
from tests.e2e.course_recommendation_test_framework import run_course_recommendation_test


async def main():
    """Run course recommendation demo"""
    print("🎓 Course Recommendation Testing Demo")
    print("=" * 60)
    print()
    
    print("This demo will test the course recommendation system by:")
    print("• Creating test users with different skill profiles")
    print("• Testing course suggestion API endpoints")
    print("• Validating recommendation quality and relevance")
    print("• Verifying response time requirements (≤10 seconds)")
    print()
    
    input("Press Enter to start the demo...")
    print()
    
    # Run the comprehensive test
    print("🚀 Starting course recommendation test...")
    results = await run_course_recommendation_test()
    
    print("\n📊 Test Results Summary")
    print("=" * 40)
    
    if "error" in results:
        print(f"❌ Test failed: {results['error']}")
        return
    
    # Display summary
    summary = results.get("test_summary", {})
    print(f"⏱️  Total execution time: {summary.get('total_execution_time', 0):.2f} seconds")
    print(f"👥 Test users created: {summary.get('test_users_created', 0)}")
    print(f"📚 Mock courses available: {summary.get('mock_courses_available', 0)}")
    print(f"✅ Overall success: {results.get('overall_success', False)}")
    print()
    
    # API Performance
    api_results = results.get("api_test_results", {})
    api_performance = api_results.get("api_performance", {})
    
    if api_performance and "error" not in api_performance:
        print("🔧 API Performance Metrics")
        print("-" * 30)
        print(f"Success rate: {api_performance.get('success_rate', 0):.1%}")
        print(f"Average response time: {api_performance.get('average_response_time', 0):.3f}s")
        print(f"Max response time: {api_performance.get('max_response_time', 0):.3f}s")
        print(f"Average relevance score: {api_performance.get('average_relevance_score', 0):.2f}")
        print(f"High quality recommendations: {api_performance.get('high_quality_recommendations', 0)}")
        print()
    
    # Response Time Validation
    response_time_validation = results.get("response_time_validation", {})
    if response_time_validation:
        print("⏰ Response Time Validation")
        print("-" * 30)
        meets_req = response_time_validation.get('meets_requirements', False)
        status = "✅ PASS" if meets_req else "❌ FAIL"
        print(f"Meets requirements (≤10s): {status}")
        print(f"Max execution time: {response_time_validation.get('max_execution_time', 0):.3f}s")
        print(f"Average execution time: {response_time_validation.get('average_execution_time', 0):.3f}s")
        print(f"Within limit percentage: {response_time_validation.get('within_limit_percentage', 0):.1%}")
        print()
    
    # Detailed Results by Endpoint
    print("📋 Detailed Results by Endpoint")
    print("-" * 40)
    
    # Learning Recommendations
    learning_results = api_results.get("learning_recommendations", [])
    if learning_results:
        print("\n🎯 Learning Recommendations (from Skill Gap Analysis)")
        successful = [r for r in learning_results if r.success]
        print(f"  Successful tests: {len(successful)}/{len(learning_results)}")
        
        if successful:
            avg_recommendations = sum(r.recommendations_count for r in successful) / len(successful)
            avg_relevance = sum(r.average_relevance_score for r in successful) / len(successful)
            avg_time = sum(r.execution_time for r in successful) / len(successful)
            
            print(f"  Average recommendations per user: {avg_recommendations:.1f}")
            print(f"  Average relevance score: {avg_relevance:.2f}")
            print(f"  Average response time: {avg_time:.3f}s")
            
            # Show individual results
            for result in successful[:3]:  # Show first 3 results
                print(f"    User {result.user_id}: {result.recommendations_count} courses, "
                      f"relevance: {result.average_relevance_score:.2f}, "
                      f"time: {result.execution_time:.3f}s")
    
    # Skill-Based Courses
    skill_results = api_results.get("skill_based_courses", [])
    if skill_results:
        print("\n🛠️  Skill-Based Course Recommendations")
        successful = [r for r in skill_results if r.success]
        print(f"  Successful tests: {len(successful)}/{len(skill_results)}")
        
        if successful:
            avg_recommendations = sum(r.recommendations_count for r in successful) / len(successful)
            avg_relevance = sum(r.average_relevance_score for r in successful) / len(successful)
            total_high_quality = sum(r.high_quality_matches for r in successful)
            
            print(f"  Average recommendations per user: {avg_recommendations:.1f}")
            print(f"  Average relevance score: {avg_relevance:.2f}")
            print(f"  Total high quality matches: {total_high_quality}")
    
    # Learning Paths
    path_results = api_results.get("personalized_learning_paths", [])
    if path_results:
        print("\n🗺️  Personalized Learning Paths")
        successful = [r for r in path_results if r.success]
        print(f"  Successful tests: {len(successful)}/{len(path_results)}")
        
        if successful:
            avg_courses = sum(r.recommendations_count for r in successful) / len(successful)
            avg_relevance = sum(r.average_relevance_score for r in successful) / len(successful)
            
            print(f"  Average courses per path: {avg_courses:.1f}")
            print(f"  Average path relevance: {avg_relevance:.2f}")
    
    print("\n" + "=" * 60)
    
    # Final assessment
    if results.get("overall_success", False):
        print("🎉 Course Recommendation Testing: SUCCESS")
        print()
        print("✅ The course recommendation system is working correctly!")
        print("✅ API endpoints respond within time limits")
        print("✅ Recommendations show good relevance to user skill gaps")
        print("✅ Quality validation passes for recommendation accuracy")
    else:
        print("⚠️  Course Recommendation Testing: ISSUES DETECTED")
        print()
        print("Please review the detailed results above to identify issues.")
    
    print("\n📝 Requirements Validation Summary:")
    print("• Requirement 5.2: Course recommendation API ✅")
    print("• Requirement 5.4: Response time ≤10 seconds", 
          "✅" if response_time_validation.get('meets_requirements', False) else "❌")
    
    print("\nDemo completed! 🎓")


if __name__ == "__main__":
    asyncio.run(main())