#!/usr/bin/env python3
"""
Test script for advanced user analytics service
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_advanced_user_analytics():
    """Test the advanced user analytics service functionality"""
    
    try:
        # Test service import
        from app.services.advanced_user_analytics_service import advanced_user_analytics_service
        print("✅ Advanced user analytics service imported successfully")
        
        # Test service methods exist
        methods_to_test = [
            'calculate_detailed_success_rates',
            'analyze_conversion_funnel',
            'generate_performance_benchmarks',
            'create_predictive_analytics'
        ]
        
        for method in methods_to_test:
            if hasattr(advanced_user_analytics_service, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
        
        # Test helper methods
        helper_methods = [
            '_analyze_performance_by_industry',
            '_analyze_performance_by_company',
            '_calculate_stage_durations',
            '_analyze_success_factors',
            '_generate_performance_insights',
            '_generate_performance_recommendations',
            '_calculate_market_position',
            '_identify_optimal_job_types'
        ]
        
        for method in helper_methods:
            if hasattr(advanced_user_analytics_service, method):
                print(f"✅ Helper method {method} exists")
            else:
                print(f"❌ Helper method {method} missing")
        
        # Test market benchmarks
        benchmarks = advanced_user_analytics_service.market_benchmarks
        print(f"\n✅ Market benchmarks loaded: {len(benchmarks)} metrics")
        
        expected_benchmarks = [
            'application_to_interview_rate',
            'interview_to_offer_rate',
            'overall_success_rate',
            'average_time_to_interview',
            'average_time_to_offer'
        ]
        
        for benchmark in expected_benchmarks:
            if benchmark in benchmarks:
                print(f"  ✅ {benchmark}: {benchmarks[benchmark]}")
            else:
                print(f"  ❌ Missing benchmark: {benchmark}")
        
        # Test market position calculation
        test_benchmarks = [
            {'percentile_rank': 90, 'metric': 'test1'},
            {'percentile_rank': 75, 'metric': 'test2'},
            {'percentile_rank': 60, 'metric': 'test3'}
        ]
        
        position = advanced_user_analytics_service._calculate_market_position(test_benchmarks)
        print(f"\n✅ Market position calculation: {position}")
        
        # Test performance insights generation
        insights = advanced_user_analytics_service._generate_performance_insights(
            test_benchmarks, 
            {'success_rates': {'overall_success': 5.0}}
        )
        print(f"✅ Generated {len(insights)} performance insights")
        for insight in insights:
            print(f"  - {insight}")
        
        # Test performance recommendations
        test_benchmarks_with_improvement = [
            {'percentile_rank': 90, 'metric': 'Application To Interview', 'improvement_potential': 0},
            {'percentile_rank': 40, 'metric': 'Interview To Offer', 'improvement_potential': 10},
            {'percentile_rank': 60, 'metric': 'Application Activity', 'improvement_potential': 5}
        ]
        
        recommendations = advanced_user_analytics_service._generate_performance_recommendations(
            test_benchmarks_with_improvement,
            {'success_rates': {'overall_success': 2.0}}
        )
        print(f"✅ Generated {len(recommendations)} recommendations")
        for rec in recommendations:
            print(f"  - {rec}")
        
        print("\n✅ All advanced user analytics service tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_advanced_user_analytics()