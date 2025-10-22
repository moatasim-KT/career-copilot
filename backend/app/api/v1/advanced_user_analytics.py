"""
Advanced User Analytics API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.advanced_user_analytics_service import advanced_user_analytics_service

router = APIRouter(tags=["advanced-user-analytics"])


@router.get("/api/v1/analytics/success-rates")
async def get_detailed_success_rates(
    days: int = Query(default=90, ge=30, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed application success rate analysis.
    
    Provides comprehensive analysis of:
    - Application to interview conversion rates
    - Interview to offer conversion rates
    - Overall success rates and rejection rates
    - Weekly performance trends
    - Industry and company performance breakdown
    - Temporal analysis with trend identification
    
    Returns actionable insights for improving success rates.
    """
    try:
        analysis = advanced_user_analytics_service.calculate_detailed_success_rates(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate success rates: {str(e)}")


@router.get("/api/v1/analytics/conversion-funnel")
async def get_conversion_funnel_analysis(
    days: int = Query(default=90, ge=30, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed conversion funnel analysis.
    
    Analyzes the complete job application funnel:
    - Applications submitted
    - Initial screening pass rate
    - Interview scheduling rate
    - Offer conversion rate
    - Offer acceptance rate
    
    Includes:
    - Stage-by-stage conversion rates
    - Average time spent in each stage
    - Bottleneck identification
    - Success factor analysis
    - Improvement recommendations
    
    Essential for optimizing the job search process.
    """
    try:
        analysis = advanced_user_analytics_service.analyze_conversion_funnel(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze conversion funnel: {str(e)}")


@router.get("/api/v1/analytics/performance-benchmarks")
async def get_performance_benchmarks(
    days: int = Query(default=90, ge=30, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized performance benchmarking against market averages.
    
    Compares user performance to market benchmarks:
    - Application success rates vs market average
    - Interview conversion rates vs peers
    - Activity levels vs recommended rates
    - Percentile rankings across key metrics
    - Performance category classification
    
    Provides:
    - Detailed benchmark comparisons
    - Percentile rankings
    - Performance insights and recommendations
    - Market position assessment
    - Improvement potential analysis
    
    Helps users understand their competitive position.
    """
    try:
        analysis = advanced_user_analytics_service.generate_performance_benchmarks(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate performance benchmarks: {str(e)}")


@router.get("/api/v1/analytics/predictive-analytics")
async def get_predictive_analytics(
    days: int = Query(default=90, ge=30, le=365, description="Historical analysis period"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get predictive analytics for job search success.
    
    Uses historical performance data to predict:
    - Success probability for future applications
    - Estimated time to next job offer
    - Recommended application rate for optimal results
    - Optimal job types based on past success
    - Risk factors that may impact success
    - Success factors to leverage
    
    Includes:
    - Machine learning-based predictions
    - Confidence levels and model accuracy
    - Personalized recommendations
    - Strategic guidance for job search optimization
    
    Enables data-driven job search strategy.
    """
    try:
        analysis = advanced_user_analytics_service.create_predictive_analytics(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate predictive analytics: {str(e)}")


@router.get("/api/v1/analytics/comprehensive-dashboard")
async def get_comprehensive_analytics_dashboard(
    days: int = Query(default=90, ge=30, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics dashboard combining all advanced analytics.
    
    Provides a complete view of user performance including:
    - Detailed success rates and trends
    - Conversion funnel analysis
    - Performance benchmarking
    - Predictive analytics
    - Market insights
    - Actionable recommendations
    
    Optimized for dashboard visualization with:
    - Chart-ready data formats
    - Key performance indicators
    - Executive summary metrics
    - Trend analysis
    - Comparative insights
    
    The ultimate analytics endpoint for comprehensive performance tracking.
    """
    try:
        # Get all analytics components
        success_rates = advanced_user_analytics_service.calculate_detailed_success_rates(
            db=db, user_id=current_user.id, days=days
        )
        
        conversion_funnel = advanced_user_analytics_service.analyze_conversion_funnel(
            db=db, user_id=current_user.id, days=days
        )
        
        benchmarks = advanced_user_analytics_service.generate_performance_benchmarks(
            db=db, user_id=current_user.id, days=days
        )
        
        predictive = advanced_user_analytics_service.create_predictive_analytics(
            db=db, user_id=current_user.id, days=days
        )
        
        # Check for errors in any component
        components = [success_rates, conversion_funnel, benchmarks, predictive]
        for component in components:
            if 'error' in component:
                raise HTTPException(status_code=404, detail=component['error'])
        
        # Create comprehensive dashboard data
        dashboard = {
            'generated_at': datetime.now().isoformat(),
            'user_id': current_user.id,
            'analysis_period_days': days,
            
            # Executive summary
            'executive_summary': {
                'overall_success_rate': success_rates['success_rates']['overall_success'],
                'total_applications': success_rates['total_applications'],
                'interview_rate': success_rates['success_rates']['application_to_interview'],
                'offer_rate': success_rates['success_rates']['interview_to_offer'],
                'performance_score': benchmarks['overall_performance_score'],
                'market_position': benchmarks['market_position'],
                'success_probability': predictive['predictive_analytics']['success_probability'],
                'estimated_time_to_offer': predictive['predictive_analytics']['estimated_time_to_offer']
            },
            
            # Detailed analytics
            'success_rates': success_rates,
            'conversion_funnel': conversion_funnel,
            'performance_benchmarks': benchmarks,
            'predictive_analytics': predictive,
            
            # Chart data for visualization
            'chart_data': {
                'weekly_performance': success_rates.get('weekly_performance', []),
                'funnel_stages': [
                    {
                        'stage': stage['stage'],
                        'count': stage['count'],
                        'conversion_rate': stage['conversion_rate']
                    }
                    for stage in conversion_funnel.get('funnel_stages', [])
                ],
                'benchmark_comparison': [
                    {
                        'metric': benchmark['metric'],
                        'user_value': benchmark['user_value'],
                        'market_average': benchmark['market_average'],
                        'percentile_rank': benchmark['percentile_rank']
                    }
                    for benchmark in benchmarks.get('benchmarks', [])
                ],
                'success_probability_gauge': [
                    {
                        'category': 'Success Probability',
                        'value': predictive['predictive_analytics']['success_probability']
                    }
                ]
            },
            
            # Consolidated insights and recommendations
            'key_insights': (
                success_rates.get('trends', {}).get('trend_direction', 'stable') + ' performance trend, ' +
                f"{benchmarks.get('market_position', 'average').replace('_', ' ')} market position"
            ),
            'top_recommendations': (
                benchmarks.get('recommendations', [])[:3] + 
                predictive.get('recommendations', [])[:2]
            )[:5],
            
            # Action items
            'action_items': [
                f"Apply to {predictive['predictive_analytics']['recommended_application_rate']} jobs per week",
                f"Focus on improving {benchmarks['benchmarks'][0]['metric'].lower()} (current: {benchmarks['benchmarks'][0]['user_value']}%, target: {benchmarks['benchmarks'][0]['market_average']}%)",
                "Monitor weekly performance trends and adjust strategy accordingly"
            ]
        }
        
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comprehensive analytics dashboard: {str(e)}")


@router.get("/api/v1/analytics/performance-trends")
async def get_performance_trends(
    days: int = Query(default=180, ge=90, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get long-term performance trends analysis.
    
    Analyzes performance trends over extended periods:
    - Monthly performance evolution
    - Seasonal patterns in success rates
    - Long-term improvement trajectories
    - Performance volatility analysis
    - Trend forecasting
    
    Helps identify:
    - Performance improvement over time
    - Seasonal hiring patterns
    - Strategy effectiveness
    - Areas of consistent strength/weakness
    
    Essential for long-term career strategy planning.
    """
    try:
        # Get performance data for trend analysis
        success_rates = advanced_user_analytics_service.calculate_detailed_success_rates(
            db=db, user_id=current_user.id, days=days
        )
        
        if 'error' in success_rates:
            raise HTTPException(status_code=404, detail=success_rates['error'])
        
        # Extract trend data
        weekly_performance = success_rates.get('weekly_performance', [])
        
        # Calculate trend metrics
        if len(weekly_performance) >= 8:  # At least 8 weeks of data
            recent_performance = weekly_performance[-4:]  # Last 4 weeks
            early_performance = weekly_performance[:4]    # First 4 weeks
            
            recent_avg_success = sum(w['success_rate'] for w in recent_performance) / len(recent_performance)
            early_avg_success = sum(w['success_rate'] for w in early_performance) / len(early_performance)
            
            improvement_rate = recent_avg_success - early_avg_success
            
            # Calculate volatility (standard deviation of weekly success rates)
            all_success_rates = [w['success_rate'] for w in weekly_performance]
            if len(all_success_rates) > 1:
                import statistics
                volatility = statistics.stdev(all_success_rates)
            else:
                volatility = 0
        else:
            improvement_rate = 0
            volatility = 0
        
        # Trend analysis
        trend_analysis = {
            'analysis_period_days': days,
            'total_weeks_analyzed': len(weekly_performance),
            'performance_improvement_rate': round(improvement_rate, 2),
            'performance_volatility': round(volatility, 2),
            'trend_direction': 'improving' if improvement_rate > 1 else 'declining' if improvement_rate < -1 else 'stable',
            'consistency_rating': 'high' if volatility < 5 else 'medium' if volatility < 15 else 'low',
            'weekly_performance_data': weekly_performance
        }
        
        # Generate trend insights
        insights = []
        if improvement_rate > 2:
            insights.append("Strong upward performance trend - strategy is working well")
        elif improvement_rate < -2:
            insights.append("Declining performance trend - consider strategy adjustment")
        else:
            insights.append("Stable performance - consistent execution")
        
        if volatility < 5:
            insights.append("Highly consistent performance week-to-week")
        elif volatility > 15:
            insights.append("High performance variability - focus on consistency")
        
        trend_analysis['insights'] = insights
        
        return trend_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze performance trends: {str(e)}")