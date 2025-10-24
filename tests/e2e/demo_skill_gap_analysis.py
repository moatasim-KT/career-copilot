"""
Demo script for skill gap analysis testing

This script demonstrates the skill gap analysis testing framework
and shows how to validate skill comparison functionality, API performance,
and accuracy metrics.
"""

import asyncio
import json
from datetime import datetime
from tests.e2e.skill_gap_analysis_test_framework import run_skill_gap_analysis_test


async def main():
    """Run skill gap analysis testing demo"""
    print("🔍 Skill Gap Analysis Testing Demo")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Run comprehensive skill gap analysis test
        print("🚀 Running comprehensive skill gap analysis test...")
        results = await run_skill_gap_analysis_test()
        
        if "error" in results:
            print(f"❌ Test failed with error: {results['error']}")
            return
        
        # Display test summary
        print("📊 Test Summary")
        print("-" * 30)
        summary = results.get("test_summary", {})
        print(f"Total execution time: {summary.get('total_execution_time', 0):.2f} seconds")
        print(f"Test users created: {summary.get('test_users_created', 0)}")
        print(f"Market jobs created: {summary.get('market_jobs_created', 0)}")
        print(f"Overall success: {'✅' if results.get('overall_success', False) else '❌'}")
        print()
        
        # Display API performance results
        print("🔧 API Performance Results")
        print("-" * 30)
        api_results = results.get("api_test_results", {})
        api_performance = api_results.get("api_performance", {})
        
        if api_performance and "error" not in api_performance:
            print(f"Total API calls: {api_performance.get('total_api_calls', 0)}")
            print(f"Success rate: {api_performance.get('success_rate', 0):.2%}")
            print(f"Average response time: {api_performance.get('average_response_time', 0):.3f}s")
            print(f"Max response time: {api_performance.get('max_response_time', 0):.3f}s")
            print(f"Min response time: {api_performance.get('min_response_time', 0):.3f}s")
        else:
            print("❌ API performance data not available")
        print()
        
        # Display basic skill gap analysis results
        print("🎯 Basic Skill Gap Analysis Results")
        print("-" * 40)
        basic_results = api_results.get("basic_skill_gap_analysis", [])
        
        if basic_results:
            successful_analyses = [r for r in basic_results if r.get("success", False)]
            print(f"Total analyses: {len(basic_results)}")
            print(f"Successful analyses: {len(successful_analyses)}")
            
            if successful_analyses:
                print("\nDetailed Results:")
                for result in successful_analyses:
                    user_name = result.get("user_name", "Unknown")
                    execution_time = result.get("execution_time", 0)
                    skill_coverage = result.get("skill_coverage", 0)
                    gaps_identified = result.get("gaps_identified", 0)
                    recommendations_count = result.get("recommendations_count", 0)
                    
                    print(f"  👤 {user_name}:")
                    print(f"    ⏱️  Execution time: {execution_time:.3f}s")
                    print(f"    📈 Skill coverage: {skill_coverage:.1f}%")
                    print(f"    🔍 Gaps identified: {gaps_identified}")
                    print(f"    💡 Recommendations: {recommendations_count}")
                    print()
        else:
            print("❌ No basic analysis results available")
        
        # Display comprehensive analysis results
        print("🔬 Comprehensive Analysis Results")
        print("-" * 35)
        comprehensive_results = api_results.get("comprehensive_analysis", [])
        
        if comprehensive_results:
            successful_comprehensive = [r for r in comprehensive_results if r.get("success", False)]
            print(f"Successful comprehensive analyses: {len(successful_comprehensive)}")
            
            if successful_comprehensive:
                avg_coverage = sum(r.get("skill_coverage", 0) for r in successful_comprehensive) / len(successful_comprehensive)
                avg_gaps = sum(r.get("gaps_identified", 0) for r in successful_comprehensive) / len(successful_comprehensive)
                avg_recommendations = sum(r.get("recommendations_count", 0) for r in successful_comprehensive) / len(successful_comprehensive)
                
                print(f"Average skill coverage: {avg_coverage:.1f}%")
                print(f"Average gaps identified: {avg_gaps:.1f}")
                print(f"Average recommendations: {avg_recommendations:.1f}")
        else:
            print("❌ No comprehensive analysis results available")
        print()
        
        # Display response time validation
        print("⏰ Response Time Validation")
        print("-" * 30)
        response_time_validation = results.get("response_time_validation", {})
        
        if response_time_validation:
            meets_requirements = response_time_validation.get("meets_requirements", False)
            max_time = response_time_validation.get("max_execution_time", 0)
            avg_time = response_time_validation.get("average_execution_time", 0)
            time_limit = response_time_validation.get("time_limit", 0)
            within_limit_pct = response_time_validation.get("within_limit_percentage", 0)
            
            print(f"Meets requirements: {'✅' if meets_requirements else '❌'}")
            print(f"Time limit: {time_limit}s")
            print(f"Max execution time: {max_time:.3f}s")
            print(f"Average execution time: {avg_time:.3f}s")
            print(f"Within limit: {within_limit_pct:.1%}")
        else:
            print("❌ Response time validation data not available")
        print()
        
        # Display accuracy test results
        print("🎯 Accuracy Test Results")
        print("-" * 25)
        accuracy_results = results.get("accuracy_test_results", [])
        
        if accuracy_results:
            successful_accuracy = [r for r in accuracy_results if "error" not in r]
            print(f"Successful accuracy tests: {len(successful_accuracy)}")
            
            if successful_accuracy:
                print("\nAccuracy Metrics:")
                for result in successful_accuracy:
                    user_name = result.get("user_name", "Unknown")
                    metrics = result.get("accuracy_metrics", {})
                    
                    precision = metrics.get("precision", 0)
                    recall = metrics.get("recall", 0)
                    f1_score = metrics.get("f1_score", 0)
                    coverage_accuracy = metrics.get("coverage_accuracy", 0)
                    
                    print(f"  👤 {user_name}:")
                    print(f"    🎯 Precision: {precision:.2f}")
                    print(f"    📊 Recall: {recall:.2f}")
                    print(f"    🏆 F1 Score: {f1_score:.2f}")
                    print(f"    📈 Coverage Accuracy: {coverage_accuracy:.2f}")
                    print()
                
                # Calculate overall accuracy metrics
                avg_f1 = sum(r.get("accuracy_metrics", {}).get("f1_score", 0) for r in successful_accuracy) / len(successful_accuracy)
                avg_coverage_accuracy = sum(r.get("accuracy_metrics", {}).get("coverage_accuracy", 0) for r in successful_accuracy) / len(successful_accuracy)
                
                print(f"📊 Overall Metrics:")
                print(f"  Average F1 Score: {avg_f1:.2f}")
                print(f"  Average Coverage Accuracy: {avg_coverage_accuracy:.2f}")
        else:
            print("❌ No accuracy test results available")
        print()
        
        # Display market trends results
        print("📈 Market Trends Analysis")
        print("-" * 25)
        trends_results = api_results.get("market_trends", [])
        
        if trends_results:
            successful_trends = [r for r in trends_results if r.get("success", False)]
            if successful_trends:
                trend_result = successful_trends[0]  # Take first successful result
                print(f"Trends generated: {'✅' if trend_result.get('trends_generated', False) else '❌'}")
                print(f"Trending skills found: {trend_result.get('trending_skills_count', 0)}")
                print(f"Jobs analyzed: {trend_result.get('jobs_analyzed', 0)}")
                print(f"Execution time: {trend_result.get('execution_time', 0):.3f}s")
            else:
                print("❌ No successful trend analyses")
        else:
            print("❌ No market trends results available")
        print()
        
        # Display learning recommendations results
        print("💡 Learning Recommendations")
        print("-" * 28)
        recommendations_results = api_results.get("learning_recommendations", [])
        
        if recommendations_results:
            successful_recommendations = [r for r in recommendations_results if r.get("success", False)]
            print(f"Successful recommendation generations: {len(successful_recommendations)}")
            
            if successful_recommendations:
                total_recommendations = sum(r.get("recommendations_count", 0) for r in successful_recommendations)
                avg_recommendations = total_recommendations / len(successful_recommendations)
                
                print(f"Total recommendations generated: {total_recommendations}")
                print(f"Average recommendations per user: {avg_recommendations:.1f}")
                
                # Show sample recommendations
                for result in successful_recommendations[:2]:  # Show first 2 users
                    user_name = result.get("user_name", "Unknown")
                    rec_count = result.get("recommendations_count", 0)
                    execution_time = result.get("execution_time", 0)
                    
                    print(f"  👤 {user_name}: {rec_count} recommendations ({execution_time:.3f}s)")
        else:
            print("❌ No learning recommendations results available")
        print()
        
        # Final assessment
        print("🏁 Final Assessment")
        print("-" * 20)
        
        # Check if all major components passed
        api_success = api_performance.get("success_rate", 0) > 0.7 if api_performance else False
        response_time_ok = response_time_validation.get("meets_requirements", False) if response_time_validation else False
        accuracy_ok = len([r for r in accuracy_results if "error" not in r and r.get("accuracy_metrics", {}).get("f1_score", 0) > 0.3]) > 0
        
        overall_assessment = api_success and response_time_ok and accuracy_ok
        
        print(f"API Performance: {'✅' if api_success else '❌'}")
        print(f"Response Time Requirements: {'✅' if response_time_ok else '❌'}")
        print(f"Accuracy Requirements: {'✅' if accuracy_ok else '❌'}")
        print(f"Overall Assessment: {'✅ PASS' if overall_assessment else '❌ NEEDS IMPROVEMENT'}")
        
        if overall_assessment:
            print("\n🎉 Skill gap analysis system is working correctly!")
            print("   All core functionality tests passed.")
        else:
            print("\n⚠️  Skill gap analysis system needs attention.")
            print("   Some tests did not meet requirements.")
        
        print()
        print("=" * 60)
        print(f"Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())