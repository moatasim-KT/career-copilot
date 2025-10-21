"""
Analytics API endpoints
"""

from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.skill_analysis_service import skill_analysis_service
from app.services.application_analytics_service import application_analytics_service
from app.services.market_analysis_service import market_analysis_service
from app.services.analytics_data_collection_service import analytics_data_collection_service
from app.services.reporting_insights_service import reporting_insights_service

router = APIRouter()


@router.get("/skill-gap")
async def get_skill_gap_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh: bool = Query(False, description="Force refresh analysis")
):
    """Get skill gap analysis for current user"""
    if refresh:
        # Generate new analysis
        analysis = skill_analysis_service.analyze_skill_gap(db, current_user.id)
        if 'error' not in analysis:
            skill_analysis_service.save_analysis(db, current_user.id, analysis)
        return analysis
    else:
        # Try to get cached analysis first
        cached = skill_analysis_service.get_latest_analysis(db, current_user.id)
        if cached:
            return cached
        
        # Generate new if no cache
        analysis = skill_analysis_service.analyze_skill_gap(db, current_user.id)
        if 'error' not in analysis:
            skill_analysis_service.save_analysis(db, current_user.id, analysis)
        return analysis


@router.get("/market-demand")
async def get_market_demand(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Analysis period in days")
):
    """Get market demand analysis for skills"""
    return skill_analysis_service.analyze_market_demand(db, current_user.id, days)


@router.get("/application-success")
async def get_application_success_rates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get application success rates and conversion metrics"""
    return application_analytics_service.calculate_conversion_rates(db, current_user.id, days)


@router.get("/application-categories")
async def get_application_by_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get application success rates by job category"""
    return application_analytics_service.analyze_by_category(db, current_user.id, days)


@router.get("/application-timing")
async def get_application_timing_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get application timing patterns and recommendations"""
    return application_analytics_service.analyze_timing_patterns(db, current_user.id)


@router.get("/company-responses")
async def get_company_response_times(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get company response time analysis"""
    return application_analytics_service.track_company_response_times(db, current_user.id)


@router.get("/application-report")
async def get_comprehensive_application_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get comprehensive application analytics report"""
    report = application_analytics_service.get_comprehensive_report(db, current_user.id, days)
    
    if 'error' not in report:
        # Save the report
        application_analytics_service.save_analysis(db, current_user.id, "application_success_rate", report)
    
    return report


@router.get("/success-trends")
async def get_success_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    months: int = Query(6, description="Number of months to analyze")
):
    """Get application success rate trends over time"""
    return application_analytics_service.get_success_trends(db, current_user.id, months)


@router.get("/historical-analysis/{analysis_type}")
async def get_historical_analysis(
    analysis_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of historical records to return")
):
    """Get historical analysis data for trend tracking"""
    valid_types = [
        'application_success_rate', 'company_response_times', 
        'timing_patterns', 'category_analysis', 'comprehensive_application_report'
    ]
    
    if analysis_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid analysis type. Must be one of: {valid_types}")
    
    return application_analytics_service.get_historical_analysis(db, current_user.id, analysis_type, limit)


@router.get("/salary-trends")
async def get_salary_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role: Optional[str] = Query(None, description="Filter by role/title"),
    days: int = Query(180, description="Analysis period in days")
):
    """Get enhanced salary trend analysis with temporal insights"""
    analysis = market_analysis_service.analyze_salary_trends(db, current_user.id, role, days)
    
    # Save analysis if successful
    if 'error' not in analysis:
        market_analysis_service.save_analysis(db, current_user.id, {
            'type': 'salary_trends',
            'data': analysis
        })
    
    return analysis


@router.get("/market-patterns")
async def get_market_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get comprehensive job market patterns and trends"""
    analysis = market_analysis_service.analyze_job_market_patterns(db, current_user.id, days)
    
    # Save analysis if successful
    if 'error' not in analysis:
        market_analysis_service.save_analysis(db, current_user.id, {
            'type': 'market_patterns',
            'data': analysis
        })
    
    return analysis


@router.get("/market-trends-comprehensive")
async def get_comprehensive_market_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get comprehensive market trend analysis combining salary and job patterns"""
    try:
        # Get both salary trends and market patterns
        salary_analysis = market_analysis_service.analyze_salary_trends(db, current_user.id, None, days)
        market_patterns = market_analysis_service.analyze_job_market_patterns(db, current_user.id, days)
        opportunity_alerts = market_analysis_service.generate_opportunity_alerts(db, current_user.id)
        
        # Combine into comprehensive report
        comprehensive_report = {
            'generated_at': datetime.now().isoformat(),
            'analysis_period_days': days,
            'user_id': current_user.id,
            'salary_trends': salary_analysis,
            'market_patterns': market_patterns,
            'opportunity_alerts': opportunity_alerts,
            'summary': {
                'total_jobs_analyzed': market_patterns.get('total_jobs', 0) if 'error' not in market_patterns else 0,
                'salary_growth_rate': salary_analysis.get('salary_growth_rate', 0) if 'error' not in salary_analysis else 0,
                'market_growth_rate': market_patterns.get('growth_metrics', {}).get('weekly_growth_rate', 0) if 'error' not in market_patterns else 0,
                'active_alerts': len(opportunity_alerts),
                'avg_salary': salary_analysis.get('overall_salary_range', {}).get('average', 0) if 'error' not in salary_analysis else 0
            }
        }
        
        # Save comprehensive analysis
        market_analysis_service.save_analysis(db, current_user.id, {
            'type': 'comprehensive_market_trends',
            'data': comprehensive_report
        })
        
        return comprehensive_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comprehensive market analysis: {str(e)}")


@router.get("/industry-analysis")
async def get_industry_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get detailed industry analysis and trends"""
    market_patterns = market_analysis_service.analyze_job_market_patterns(db, current_user.id, days)
    
    if 'error' in market_patterns:
        return market_patterns
    
    # Extract and enhance industry data
    industry_data = market_patterns.get('industry_distribution', {})
    
    # Add growth trends and insights for each industry
    enhanced_industry_analysis = {}
    for industry, data in industry_data.items():
        enhanced_industry_analysis[industry] = {
            **data,
            'market_share': data.get('percentage', 0),
            'growth_potential': 'high' if data.get('recent_count', 0) > data.get('count', 0) * 0.3 else 'moderate',
            'competitiveness': 'high' if data.get('avg_jobs_per_company', 0) > 3 else 'moderate'
        }
    
    return {
        'analysis_date': datetime.now().isoformat(),
        'analysis_period_days': days,
        'industry_breakdown': enhanced_industry_analysis,
        'top_industries': sorted(enhanced_industry_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:5],
        'fastest_growing': sorted(enhanced_industry_analysis.items(), key=lambda x: x[1].get('recent_count', 0), reverse=True)[:3],
        'insights': [
            f"Technology sector dominates with {enhanced_industry_analysis.get('technology', {}).get('percentage', 0)}% of jobs" if 'technology' in enhanced_industry_analysis else "Diverse industry representation in job market",
            f"Most competitive industry: {max(enhanced_industry_analysis.items(), key=lambda x: x[1]['avg_jobs_per_company'])[0].title()}" if enhanced_industry_analysis else "No industry data available"
        ]
    }


@router.get("/opportunity-alerts")
async def get_opportunity_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get market opportunity alerts"""
    return market_analysis_service.generate_opportunity_alerts(db, current_user.id)


@router.get("/market-dashboard")
async def get_market_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive market dashboard data"""
    dashboard_data = market_analysis_service.create_market_dashboard_data(db, current_user.id)
    
    # Save the analysis
    market_analysis_service.save_analysis(db, current_user.id, dashboard_data)
    
    return dashboard_data


@router.get("/user-activity")
async def track_user_activity(
    activity_type: str = Query(..., description="Type of user activity to track"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    metadata: Optional[Dict] = None
):
    """Track user activity for analytics"""
    success = analytics_data_collection_service.track_user_activity(
        db, current_user.id, activity_type, metadata
    )
    return {"success": success, "activity_type": activity_type, "timestamp": datetime.now().isoformat()}


@router.get("/user-engagement")
async def get_user_engagement_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Analysis period in days")
):
    """Get comprehensive user engagement metrics"""
    return analytics_data_collection_service.collect_user_engagement_metrics(db, current_user.id, days)


@router.get("/application-success-monitoring")
async def get_application_success_monitoring(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get detailed application success rate monitoring with comprehensive metrics"""
    return analytics_data_collection_service.monitor_application_success_rates(db, current_user.id, days)


@router.get("/market-trends-analysis")
async def get_market_trends_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get comprehensive market trend analysis from job data"""
    return analytics_data_collection_service.analyze_market_trends(db, current_user.id, days)


@router.get("/comprehensive-analytics-report")
async def get_comprehensive_analytics_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get comprehensive analytics report combining user activity, application success, and market trends"""
    return analytics_data_collection_service.get_comprehensive_analytics_report(db, current_user.id, days)


@router.get("/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get high-level analytics summary for dashboard"""
    # Get key metrics from each service
    skill_gap = skill_analysis_service.get_latest_analysis(db, current_user.id)
    conversion_rates = application_analytics_service.calculate_conversion_rates(db, current_user.id, 30)
    market_patterns = market_analysis_service.analyze_job_market_patterns(db, current_user.id, 30)
    
    # Get engagement metrics from new service
    engagement_metrics = analytics_data_collection_service.collect_user_engagement_metrics(db, current_user.id, 30)
    
    # Get progress summary from reporting service
    progress_summary = reporting_insights_service.generate_weekly_progress_report(db, current_user.id, 0)
    
    return {
        'skill_match_percentage': skill_gap.get('match_percentage', 0) if skill_gap else 0,
        'missing_skills_count': len(skill_gap.get('missing_skills', [])) if skill_gap else 0,
        'application_response_rate': conversion_rates.get('conversion_rates', {}).get('response_rate', 0) if 'error' not in conversion_rates else 0,
        'monthly_job_count': market_patterns.get('total_jobs', 0) if 'error' not in market_patterns else 0,
        'market_growth_rate': market_patterns.get('growth_rate', 0) if 'error' not in market_patterns else 0,
        'engagement_score': engagement_metrics.get('engagement_score', 0) if 'error' not in engagement_metrics else 0,
        'weekly_applications': progress_summary.get('metrics', {}).get('applications_submitted', 0) if 'error' not in progress_summary else 0,
        'weekly_trend': progress_summary.get('trends', {}).get('momentum', 'stable') if 'error' not in progress_summary else 'unknown',
        'last_updated': skill_gap.get('analysis_date') if skill_gap else None
    }