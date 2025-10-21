"""
Reporting and Insights API endpoints
"""

from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.reporting_insights_service import reporting_insights_service

router = APIRouter()


@router.get("/weekly-progress")
async def get_weekly_progress_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    week_offset: int = Query(0, description="Week offset (0 = current week, -1 = last week, etc.)")
):
    """Get comprehensive weekly progress report"""
    return reporting_insights_service.generate_weekly_progress_report(db, current_user.id, week_offset)


@router.get("/monthly-progress")
async def get_monthly_progress_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    month_offset: int = Query(0, description="Month offset (0 = current month, -1 = last month, etc.)")
):
    """Get comprehensive monthly progress report"""
    return reporting_insights_service.generate_monthly_progress_report(db, current_user.id, month_offset)


@router.get("/salary-trends-comprehensive")
async def get_comprehensive_salary_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(180, description="Analysis period in days")
):
    """Get comprehensive salary trend analysis with career insights"""
    return reporting_insights_service.analyze_salary_trends_comprehensive(db, current_user.id, days)


@router.get("/career-insights")
async def get_career_insights_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive career insights and progression analysis"""
    return reporting_insights_service.generate_career_insights_report(db, current_user.id)


@router.get("/recommendation-effectiveness")
async def get_recommendation_effectiveness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Track and analyze recommendation system effectiveness"""
    return reporting_insights_service.track_recommendation_effectiveness(db, current_user.id, days)


@router.get("/progress-summary")
async def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get high-level progress summary for dashboard"""
    try:
        # Get current week and month reports
        weekly_report = reporting_insights_service.generate_weekly_progress_report(db, current_user.id, 0)
        monthly_report = reporting_insights_service.generate_monthly_progress_report(db, current_user.id, 0)
        
        # Extract key metrics
        summary = {
            'generated_at': datetime.utcnow().isoformat(),
            'user_id': current_user.id,
            'weekly_metrics': {
                'applications_this_week': weekly_report.get('metrics', {}).get('applications_submitted', 0) if 'error' not in weekly_report else 0,
                'jobs_added_this_week': weekly_report.get('metrics', {}).get('jobs_added_to_tracker', 0) if 'error' not in weekly_report else 0,
                'active_days_this_week': weekly_report.get('metrics', {}).get('active_days', 0) if 'error' not in weekly_report else 0,
                'weekly_trend': weekly_report.get('trends', {}).get('momentum', 'stable') if 'error' not in weekly_report else 'unknown'
            },
            'monthly_metrics': {
                'applications_this_month': monthly_report.get('summary_metrics', {}).get('total_applications', 0) if 'error' not in monthly_report else 0,
                'response_rate': monthly_report.get('summary_metrics', {}).get('response_rate', 0) if 'error' not in monthly_report else 0,
                'interview_rate': monthly_report.get('summary_metrics', {}).get('interview_rate', 0) if 'error' not in monthly_report else 0,
                'avg_apps_per_week': monthly_report.get('summary_metrics', {}).get('avg_applications_per_week', 0) if 'error' not in monthly_report else 0
            },
            'key_insights': [],
            'recommendations': []
        }
        
        # Add insights from reports
        if 'error' not in weekly_report:
            summary['key_insights'].extend(weekly_report.get('insights', [])[:2])
            summary['recommendations'].extend(weekly_report.get('recommendations', [])[:2])
        
        if 'error' not in monthly_report:
            summary['key_insights'].extend(monthly_report.get('insights', [])[:2])
            summary['recommendations'].extend(monthly_report.get('recommendations', [])[:2])
        
        # Limit to top insights and recommendations
        summary['key_insights'] = summary['key_insights'][:3]
        summary['recommendations'] = summary['recommendations'][:3]
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate progress summary: {str(e)}")


@router.get("/career-trajectory")
async def get_career_trajectory_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get focused career trajectory analysis"""
    try:
        career_insights = reporting_insights_service.generate_career_insights_report(db, current_user.id)
        
        if 'error' in career_insights:
            return career_insights
        
        # Extract trajectory-specific data
        trajectory_analysis = {
            'generated_at': datetime.utcnow().isoformat(),
            'user_id': current_user.id,
            'career_trajectory': career_insights.get('career_trajectory', {}),
            'skill_evolution': career_insights.get('skill_evolution', {}),
            'market_positioning': career_insights.get('market_positioning', {}),
            'next_steps': career_insights.get('next_steps', []),
            'career_recommendations': career_insights.get('career_recommendations', [])
        }
        
        return trajectory_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate career trajectory analysis: {str(e)}")


@router.get("/salary-insights")
async def get_salary_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(180, description="Analysis period in days")
):
    """Get focused salary insights and negotiation guidance"""
    try:
        salary_analysis = reporting_insights_service.analyze_salary_trends_comprehensive(db, current_user.id, days)
        
        if 'error' in salary_analysis:
            return salary_analysis
        
        # Extract salary-specific insights
        salary_insights = {
            'generated_at': datetime.utcnow().isoformat(),
            'user_id': current_user.id,
            'analysis_period_days': days,
            'user_salary_profile': salary_analysis.get('user_salary_profile', {}),
            'market_comparison': salary_analysis.get('market_trends', {}),
            'career_insights': salary_analysis.get('career_insights', []),
            'negotiation_strategy': salary_analysis.get('negotiation_strategy', {}),
            'growth_projections': salary_analysis.get('growth_projections', {}),
            'recommendations': salary_analysis.get('recommendations', [])
        }
        
        return salary_insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate salary insights: {str(e)}")


@router.get("/recommendation-performance")
async def get_recommendation_performance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """Get recommendation system performance summary"""
    try:
        effectiveness_analysis = reporting_insights_service.track_recommendation_effectiveness(db, current_user.id, days)
        
        if 'error' in effectiveness_analysis:
            return effectiveness_analysis
        
        # Extract performance summary
        performance_summary = {
            'generated_at': datetime.utcnow().isoformat(),
            'user_id': current_user.id,
            'analysis_period_days': days,
            'overall_effectiveness_score': effectiveness_analysis.get('effectiveness_score', 0),
            'key_metrics': effectiveness_analysis.get('overall_metrics', {}),
            'conversion_performance': effectiveness_analysis.get('conversion_analysis', {}),
            'improvement_areas': effectiveness_analysis.get('improvement_areas', []),
            'system_recommendations': effectiveness_analysis.get('recommendations', [])
        }
        
        return performance_summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation performance summary: {str(e)}")


@router.get("/comprehensive-report")
async def get_comprehensive_insights_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    period: str = Query("monthly", description="Report period: 'weekly' or 'monthly'")
):
    """Get comprehensive insights report combining all analysis types"""
    try:
        if period not in ['weekly', 'monthly']:
            raise HTTPException(status_code=400, detail="Period must be 'weekly' or 'monthly'")
        
        # Get all reports
        if period == 'weekly':
            progress_report = reporting_insights_service.generate_weekly_progress_report(db, current_user.id, 0)
        else:
            progress_report = reporting_insights_service.generate_monthly_progress_report(db, current_user.id, 0)
        
        salary_analysis = reporting_insights_service.analyze_salary_trends_comprehensive(db, current_user.id, 180)
        career_insights = reporting_insights_service.generate_career_insights_report(db, current_user.id)
        recommendation_effectiveness = reporting_insights_service.track_recommendation_effectiveness(db, current_user.id, 90)
        
        # Combine into comprehensive report
        comprehensive_report = {
            'report_type': f'comprehensive_{period}_insights',
            'generated_at': datetime.utcnow().isoformat(),
            'user_id': current_user.id,
            'progress_analysis': progress_report,
            'salary_analysis': salary_analysis,
            'career_insights': career_insights,
            'recommendation_effectiveness': recommendation_effectiveness,
            'executive_summary': {
                'key_achievements': [],
                'primary_concerns': [],
                'top_recommendations': [],
                'overall_assessment': 'unknown'
            }
        }
        
        # Generate executive summary
        executive_summary = comprehensive_report['executive_summary']
        
        # Extract key achievements
        if 'error' not in progress_report:
            achievements = progress_report.get('achievements', []) or progress_report.get('goals_and_achievements', {}).get('achievements', [])
            executive_summary['key_achievements'].extend(achievements[:3])
        
        # Extract primary concerns and recommendations
        all_recommendations = []
        if 'error' not in progress_report:
            all_recommendations.extend(progress_report.get('recommendations', []))
        if 'error' not in salary_analysis:
            all_recommendations.extend(salary_analysis.get('recommendations', []))
        if 'error' not in career_insights:
            all_recommendations.extend(career_insights.get('career_recommendations', []))
        
        executive_summary['top_recommendations'] = all_recommendations[:5]
        
        # Overall assessment
        if 'error' not in progress_report:
            apps_count = progress_report.get('metrics', {}).get('applications_submitted', 0) or progress_report.get('summary_metrics', {}).get('total_applications', 0)
            response_rate = progress_report.get('summary_metrics', {}).get('response_rate', 0) if period == 'monthly' else 0
            
            if apps_count >= 10 and response_rate >= 0.2:
                executive_summary['overall_assessment'] = 'strong_performance'
            elif apps_count >= 5 and response_rate >= 0.1:
                executive_summary['overall_assessment'] = 'moderate_performance'
            else:
                executive_summary['overall_assessment'] = 'needs_improvement'
        
        return comprehensive_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comprehensive report: {str(e)}")


@router.get("/historical-reports/{report_type}")
async def get_historical_reports(
    report_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of historical reports to return")
):
    """Get historical reports for trend analysis"""
    valid_types = [
        'weekly_progress_report', 'monthly_progress_report', 
        'salary_trends_analysis', 'career_insights_report', 
        'recommendation_effectiveness'
    ]
    
    if report_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid report type. Must be one of: {valid_types}")
    
    try:
        from app.models.analytics import Analytics
        
        historical_reports = db.query(Analytics).filter(
            Analytics.user_id == current_user.id,
            Analytics.type == report_type
        ).order_by(Analytics.generated_at.desc()).limit(limit).all()
        
        reports = []
        for report in historical_reports:
            reports.append({
                'id': report.id,
                'generated_at': report.generated_at.isoformat(),
                'data': report.data
            })
        
        return {
            'report_type': report_type,
            'total_reports': len(reports),
            'reports': reports
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve historical reports: {str(e)}")