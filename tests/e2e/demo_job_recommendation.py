#!/usr/bin/env python3
"""
Demo script for Job Recommendation Testing Framework

This script demonstrates the job recommendation testing capabilities including:
- Creating test user profiles with different characteristics
- Testing recommendation API endpoints
- Validating recommendation relevance and quality
- Measuring recommendation performance
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Add the project root to the Python path for tests
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.job_recommendation_test_framework import JobRecommendationTestFramework


async def demo_job_recommendation_testing():
    """Demonstrate job recommendation testing capabilities"""
    
    print("🎯 Job Recommendation Testing Framework Demo")
    print("=" * 60)
    
    framework = JobRecommendationTestFramework()
    
    try:
        # 1. Setup Test Environment
        print("\n📋 Setting up test environment...")
        setup_success = await framework.setup_test_environment()
        
        if not setup_success:
            print("❌ Failed to setup test environment")
            return
        
        print(f"✅ Created {len(framework.test_users)} test users")
        print(f"✅ Created {len(framework.test_jobs)} sample jobs")
        
        # Display test user profiles
        print("\n👥 Test User Profiles:")
        for i, profile in enumerate(framework.test_profiles, 1):
            print(f"  {i}. {profile.name}")
            print(f"     Skills: {', '.join(profile.skills[:3])}...")
            print(f"     Experience: {profile.experience_level}")
            print(f"     Location: {', '.join(profile.preferred_locations)}")
        
        # 2. Test API Endpoints
        print("\n🔗 Testing recommendation API endpoints...")
        api_results = await framework.test_recommendation_api_endpoints()
        
        if "error" in api_results:
            print(f"❌ API testing failed: {api_results['error']}")
        else:
            # Display API performance metrics
            api_performance = api_results.get("api_performance", {})
            print(f"✅ API Success Rate: {api_performance.get('success_rate', 0):.1%}")
            print(f"✅ Average Response Time: {api_performance.get('average_response_time', 0):.3f}s")
            
            # Show basic recommendations results
            basic_results = api_results.get("basic_recommendations", [])
            if basic_results:
                print(f"\n📊 Basic Recommendations Results:")
                for result in basic_results:
                    if result.get("success"):
                        print(f"  {result['user_name']}: {result['recommendations_count']} recommendations "
                              f"(avg score: {result['average_score']:.2f})")
                    else:
                        print(f"  {result['user_name']}: ❌ {result.get('error_message', 'Unknown error')}")
            
            # Show enhanced recommendations results
            enhanced_results = api_results.get("enhanced_recommendations", [])
            if enhanced_results:
                print(f"\n🚀 Enhanced Recommendations Results:")
                for result in enhanced_results:
                    if result.get("success"):
                        print(f"  {result['user_name']}: {result['recommendations_count']} recommendations "
                              f"(avg score: {result['average_score']:.2f})")
                    else:
                        print(f"  {result['user_name']}: ❌ {result.get('error_message', 'Unknown error')}")
        
        # 3. Test Recommendation Relevance
        print("\n🎯 Testing recommendation relevance...")
        
        from backend.app.services.recommendation_engine import RecommendationEngine
        
        relevance_summary = []
        
        for user in framework.test_users:
            try:
                # Get recommendations for this user
                recommendation_engine = RecommendationEngine(framework.db)
                recommendations = recommendation_engine.get_recommendations(user, limit=10)
                
                # Validate relevance
                relevance_metrics = framework.validate_recommendation_relevance(user, recommendations)
                
                relevance_summary.append({
                    "user_name": user.name,
                    "total_recommendations": relevance_metrics.total_recommendations,
                    "relevance_score": relevance_metrics.overall_relevance_score,
                    "skill_matches": relevance_metrics.skill_matches,
                    "location_matches": relevance_metrics.location_matches,
                    "quality_distribution": relevance_metrics.quality_distribution
                })
                
                print(f"  {user.name}:")
                print(f"    📈 Relevance Score: {relevance_metrics.overall_relevance_score:.1%}")
                print(f"    🎯 Skill Matches: {relevance_metrics.skill_matches}/{relevance_metrics.total_recommendations}")
                print(f"    📍 Location Matches: {relevance_metrics.location_matches}/{relevance_metrics.total_recommendations}")
                print(f"    ⭐ Quality: {relevance_metrics.quality_distribution['excellent']} excellent, "
                      f"{relevance_metrics.quality_distribution['high']} high")
                
            except Exception as e:
                print(f"  {user.name}: ❌ Error - {str(e)}")
        
        # 4. Overall Summary
        print(f"\n📊 Overall Test Summary:")
        print("=" * 40)
        
        if relevance_summary:
            avg_relevance = sum(r["relevance_score"] for r in relevance_summary) / len(relevance_summary)
            total_recommendations = sum(r["total_recommendations"] for r in relevance_summary)
            total_skill_matches = sum(r["skill_matches"] for r in relevance_summary)
            
            print(f"Average Relevance Score: {avg_relevance:.1%}")
            print(f"Total Recommendations Generated: {total_recommendations}")
            print(f"Overall Skill Match Rate: {total_skill_matches/total_recommendations:.1%}" if total_recommendations > 0 else "No recommendations generated")
            
            # Quality distribution summary
            quality_totals = {"excellent": 0, "high": 0, "medium": 0, "low": 0}
            for summary in relevance_summary:
                for quality, count in summary["quality_distribution"].items():
                    quality_totals[quality] += count
            
            print(f"Quality Distribution:")
            for quality, count in quality_totals.items():
                percentage = count / total_recommendations * 100 if total_recommendations > 0 else 0
                print(f"  {quality.title()}: {count} ({percentage:.1f}%)")
        
        # 5. Test Specific User Profile Matching
        print(f"\n🔍 Testing Profile-Specific Matching:")
        print("-" * 40)
        
        # Test junior developer profile
        junior_user = next((u for u in framework.test_users if "Junior" in u.name), None)
        if junior_user:
            recommendation_engine = RecommendationEngine(framework.db)
            junior_recs = recommendation_engine.get_recommendations(junior_user, limit=5)
            
            print(f"Junior Developer ({junior_user.name}):")
            for i, rec in enumerate(junior_recs[:3], 1):
                job = rec["job"]
                score = rec["score"]
                print(f"  {i}. {job.title} at {job.company} (Score: {score:.1f})")
        
        # Test senior developer profile
        senior_user = next((u for u in framework.test_users if "Senior" in u.name), None)
        if senior_user:
            recommendation_engine = RecommendationEngine(framework.db)
            senior_recs = recommendation_engine.get_recommendations(senior_user, limit=5)
            
            print(f"\nSenior Developer ({senior_user.name}):")
            for i, rec in enumerate(senior_recs[:3], 1):
                job = rec["job"]
                score = rec["score"]
                print(f"  {i}. {job.title} at {job.company} (Score: {score:.1f})")
        
        print(f"\n✅ Job recommendation testing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test environment...")
        cleanup_success = await framework.cleanup_test_environment()
        if cleanup_success:
            print("✅ Cleanup completed successfully")
        else:
            print("⚠️  Cleanup encountered some issues")


def main():
    """Main function to run the demo"""
    try:
        asyncio.run(demo_job_recommendation_testing())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()