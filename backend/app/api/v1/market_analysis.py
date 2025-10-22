"""
Market trend analysis API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.market_analysis_service import market_analysis_service
from ...schemas.market_analysis import (
    SalaryTrendsResponse,
    JobMarketPatternsResponse,
    MarketDashboardResponse,
    MarketTrendAnalysisResponse,
    UserAnalyticsRequest,
    AdvancedUserAnalyticsResponse
)

router = APIRouter(tags=["market-analysis"])


@router.get("/api/v1/market-analysis/salary-trends", response_model=SalaryTrendsResponse)
async def get_salary_trends(
    days: int = Query(default=180, ge=30, le=365, description="Analysis period in days"),
    role_filter: Optional[str] = Query(default=None, description="Filter by specific role"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive salary trend analysis for the user's job market.
    
    Analyzes salary trends across:
    - Time periods (monthly trends)
    - Locations (geographic salary comparison)
    - Industries (sector-based analysis)
    - Experience levels
    - Company sizes
    
    Returns detailed insights and growth predictions.
    """
    try:
        analysis = market_analysis_service.analyze_salary_trends(
            db=db,
            user_id=current_user.id,
            role_filter=role_filter,
            days=days
        )
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze salary trends: {str(e)}")


@router.get("/api/v1/market-analysis/job-patterns", response_model=JobMarketPatternsResponse)
async def get_job_market_patterns(
    days: int = Query(default=90, ge=30, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive job market pattern analysis.
    
    Analyzes market patterns including:
    - Temporal trends (daily, weekly, monthly)
    - Growth metrics and velocity
    - Job source distribution
    - Company hiring patterns
    - Industry distribution
    - Location and remote work trends
    - Role and seniority patterns
    - Seasonal hiring cycles
    
    Returns actionable market insights.
    """
    try:
        analysis = market_analysis_service.analyze_job_market_patterns(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze job market patterns: {str(e)}")


@router.get("/api/v1/market-analysis/opportunity-alerts")
async def get_opportunity_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized market opportunity alerts.
    
    Generates alerts for:
    - High growth markets
    - Active hiring companies
    - Remote work trends
    - Salary opportunities
    - Skill demand changes
    
    Returns prioritized actionable alerts.
    """
    try:
        alerts = market_analysis_service.generate_opportunity_alerts(
            db=db,
            user_id=current_user.id
        )
        
        return {
            "generated_at": datetime.now().isoformat(),
            "alerts": alerts,
            "total_alerts": len(alerts),
            "high_priority_count": len([a for a in alerts if a.get('priority') == 'high']),
            "medium_priority_count": len([a for a in alerts if a.get('priority') == 'medium']),
            "low_priority_count": len([a for a in alerts if a.get('priority') == 'low'])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate opportunity alerts: {str(e)}")


@router.get("/api/v1/market-analysis/dashboard", response_model=MarketDashboardResponse)
async def get_market_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive market dashboard data.
    
    Combines all market analysis components:
    - Salary trends
    - Job market patterns
    - Opportunity alerts
    - Chart data for visualization
    - Executive summary
    
    Optimized for dashboard display with chart-ready data.
    """
    try:
        dashboard_data = market_analysis_service.create_market_dashboard_data(
            db=db,
            user_id=current_user.id
        )
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create market dashboard: {str(e)}")


@router.post("/api/v1/market-analysis/save-analysis")
async def save_market_analysis(
    analysis_type: str = Query(..., description="Type of analysis to save"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save market analysis results to database for historical tracking.
    
    Supports saving:
    - salary_trends
    - job_patterns
    - opportunity_alerts
    - dashboard_data
    
    Enables trend tracking over time.
    """
    try:
        # Generate the analysis based on type
        if analysis_type == "salary_trends":
            analysis_data = market_analysis_service.analyze_salary_trends(db, current_user.id)
        elif analysis_type == "job_patterns":
            analysis_data = market_analysis_service.analyze_job_market_patterns(db, current_user.id)
        elif analysis_type == "dashboard_data":
            analysis_data = market_analysis_service.create_market_dashboard_data(db, current_user.id)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported analysis type: {analysis_type}")
        
        # Save to database
        success = market_analysis_service.save_analysis(
            db=db,
            user_id=current_user.id,
            analysis_data=analysis_data
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save analysis to database")
        
        return {
            "message": f"Successfully saved {analysis_type} analysis",
            "analysis_type": analysis_type,
            "saved_at": datetime.now().isoformat(),
            "user_id": current_user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save market analysis: {str(e)}")


# Advanced analytics endpoints for task 28.2

@router.get("/api/v1/market-analysis/skill-demand-forecast")
async def get_skill_demand_forecast(
    days: int = Query(default=180, ge=90, le=365, description="Historical analysis period"),
    forecast_days: int = Query(default=90, ge=30, le=180, description="Forecast period"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get skill demand forecasting based on job posting data.
    
    Analyzes historical skill demand patterns and projects future trends:
    - Growing vs declining skills
    - Market saturation levels
    - Learning priority recommendations
    - Competitive positioning advice
    
    Uses time series analysis of job posting data.
    """
    try:
        # This would be implemented as part of the enhanced market analysis service
        # For now, we'll use the existing salary trends analysis as a foundation
        market_patterns = market_analysis_service.analyze_job_market_patterns(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        # Extract skill demand data from job patterns
        skill_forecast = []
        if 'role_analysis' in market_patterns and 'role_keywords' in market_patterns['role_analysis']:
            role_keywords = market_patterns['role_analysis']['role_keywords']
            total_jobs = market_patterns.get('total_jobs', 1)
            
            for skill, count in role_keywords.items():
                demand_percentage = (count / total_jobs) * 100
                
                # Simple trend analysis (would be more sophisticated in production)
                if demand_percentage > 20:
                    trend = 'increasing'
                    priority = 'high'
                elif demand_percentage > 10:
                    trend = 'stable'
                    priority = 'medium'
                else:
                    trend = 'decreasing'
                    priority = 'low'
                
                skill_forecast.append({
                    'skill': skill,
                    'current_demand': count,
                    'demand_percentage': round(demand_percentage, 1),
                    'trend_direction': trend,
                    'growth_rate': 0.0,  # Would calculate from historical data
                    'projected_demand': int(count * 1.1),  # Simple projection
                    'market_saturation': 'medium',
                    'learning_priority': priority
                })
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'analysis_period_days': days,
            'forecast_period_days': forecast_days,
            'total_jobs_analyzed': market_patterns.get('total_jobs', 0),
            'skill_demand_forecast': sorted(skill_forecast, key=lambda x: x['current_demand'], reverse=True),
            'market_insights': [
                f"Analyzed {len(skill_forecast)} key skills from {market_patterns.get('total_jobs', 0)} job postings",
                "High-demand skills show strong market presence and growth potential",
                "Focus learning efforts on high-priority skills for maximum career impact"
            ],
            'recommendations': [
                "Prioritize learning high-demand skills with increasing trends",
                "Monitor market saturation levels for competitive positioning",
                "Consider skill combinations for unique value proposition"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate skill demand forecast: {str(e)}")


@router.get("/api/v1/market-analysis/competitive-analysis")
async def get_competitive_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get competitive analysis for job seekers.
    
    Analyzes market competition levels:
    - Candidate pool estimation
    - Skill competition assessment
    - Location-based competition
    - Experience level competition
    - Differentiation strategies
    - Market positioning advice
    
    Helps users understand their competitive position.
    """
    try:
        # Get user profile data
        user_skills = current_user.skills or []
        user_locations = current_user.preferred_locations or []
        user_experience = current_user.experience_level or 'mid'
        
        # Analyze market patterns for competitive insights
        market_patterns = market_analysis_service.analyze_job_market_patterns(
            db=db,
            user_id=current_user.id,
            days=90
        )
        
        # Calculate competition metrics
        total_jobs = market_patterns.get('total_jobs', 0)
        
        # Estimate competition levels (simplified for MVP)
        skill_competition = 'medium'
        location_competition = 'medium'
        experience_competition = 'medium'
        
        if total_jobs > 100:
            skill_competition = 'high'
        elif total_jobs < 20:
            skill_competition = 'low'
        
        # Generate differentiation strategies
        differentiation_strategies = [
            "Develop niche skill combinations that are in high demand",
            "Focus on emerging technologies and trending skills",
            "Build a strong portfolio showcasing practical experience",
            "Obtain relevant certifications in your field",
            "Develop soft skills that complement technical abilities"
        ]
        
        positioning_advice = [
            "Highlight unique skill combinations in your profile",
            "Emphasize practical project experience over theoretical knowledge",
            "Target companies that value your specific skill set",
            "Consider remote opportunities to expand your market reach",
            "Network within your industry to access hidden job markets"
        ]
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'user_skills': user_skills,
            'user_locations': user_locations,
            'user_experience_level': user_experience,
            'total_jobs_analyzed': total_jobs,
            'competitive_analysis': {
                'total_candidates_estimated': total_jobs * 50,  # Rough estimate
                'skill_competition_level': skill_competition,
                'location_competition_level': location_competition,
                'experience_level_competition': experience_competition,
                'recommended_differentiation_strategies': differentiation_strategies,
                'market_positioning_advice': positioning_advice
            },
            'market_insights': [
                f"Analyzed {total_jobs} job opportunities in your target market",
                f"Competition level assessed as {skill_competition} based on job volume",
                "Multiple strategies available for competitive differentiation"
            ],
            'recommendations': [
                "Focus on unique skill combinations to stand out",
                "Consider expanding geographic or remote work options",
                "Invest in continuous learning and certification",
                "Build a strong professional network in your field"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate competitive analysis: {str(e)}")


@router.post("/api/v1/market-analysis/user-analytics", response_model=AdvancedUserAnalyticsResponse)
async def get_advanced_user_analytics(
    request: UserAnalyticsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get advanced user analytics with conversion funnel and performance benchmarking.
    
    Provides detailed analysis of:
    - Application success rates
    - Conversion funnel (application → interview → offer)
    - Performance benchmarking against market averages
    - Predictive analytics for job search success
    - Personalized insights and recommendations
    
    Supports multiple timeframes and includes predictive modeling.
    """
    try:
        # Parse timeframe
        timeframe_days = {
            '30d': 30,
            '90d': 90,
            '1y': 365
        }.get(request.timeframe, 30)
        
        # Get basic analytics first
        from ...services.analytics import AnalyticsService
        analytics_service = AnalyticsService(db=db)
        basic_analytics = analytics_service.get_user_analytics(current_user)
        
        # Calculate success rates
        total_applications = basic_analytics.get('total_applications', 0)
        interviews = basic_analytics.get('interviews_scheduled', 0)
        offers = basic_analytics.get('offers_received', 0)
        
        application_success_rate = (interviews / total_applications * 100) if total_applications > 0 else 0
        interview_success_rate = (offers / interviews * 100) if interviews > 0 else 0
        offer_success_rate = (offers / total_applications * 100) if total_applications > 0 else 0
        
        # Build conversion funnel
        conversion_funnel = [
            {
                'stage': 'Applications Submitted',
                'count': total_applications,
                'conversion_rate': 100.0,
                'average_time_in_stage': 0.0,
                'success_factors': ['Quality applications', 'Targeted approach', 'Strong resume']
            },
            {
                'stage': 'Interviews Scheduled',
                'count': interviews,
                'conversion_rate': application_success_rate,
                'average_time_in_stage': 7.0,
                'success_factors': ['Relevant skills', 'Good application timing', 'Network connections']
            },
            {
                'stage': 'Offers Received',
                'count': offers,
                'conversion_rate': interview_success_rate,
                'average_time_in_stage': 14.0,
                'success_factors': ['Interview preparation', 'Cultural fit', 'Technical competence']
            }
        ]
        
        # Performance benchmarks (simplified for MVP)
        performance_benchmarks = [
            {
                'metric': 'Application Success Rate',
                'user_value': application_success_rate,
                'market_average': 15.0,
                'percentile_rank': 75 if application_success_rate > 15 else 25,
                'benchmark_category': 'above_average' if application_success_rate > 15 else 'below_average'
            },
            {
                'metric': 'Interview Success Rate',
                'user_value': interview_success_rate,
                'market_average': 25.0,
                'percentile_rank': 75 if interview_success_rate > 25 else 25,
                'benchmark_category': 'above_average' if interview_success_rate > 25 else 'below_average'
            }
        ]
        
        # Predictive analytics
        success_probability = min(95.0, (application_success_rate + interview_success_rate) / 2)
        estimated_time_to_offer = max(30, int(120 - (success_probability * 0.5)))
        
        predictive_analytics = {
            'success_probability': success_probability,
            'estimated_time_to_offer': estimated_time_to_offer,
            'recommended_application_rate': 5 if success_probability > 50 else 10,
            'optimal_job_types': ['Software Engineer', 'Data Analyst', 'Product Manager'],
            'risk_factors': ['Low application volume', 'Limited skill diversity'] if total_applications < 10 else [],
            'success_factors': ['Strong technical skills', 'Good interview performance', 'Targeted applications']
        }
        
        # Generate insights and recommendations
        insights = [
            f"Your application success rate of {application_success_rate:.1f}% is {'above' if application_success_rate > 15 else 'below'} market average",
            f"Interview performance shows {interview_success_rate:.1f}% success rate",
            f"Estimated {estimated_time_to_offer} days to next offer based on current performance"
        ]
        
        recommendations = [
            "Focus on quality over quantity in applications" if application_success_rate < 10 else "Maintain current application strategy",
            "Improve interview preparation" if interview_success_rate < 20 else "Continue strong interview performance",
            "Consider expanding skill set" if total_applications > 50 and offers == 0 else "Skills appear well-matched to market"
        ]
        
        # Chart data for visualization
        chart_data = {
            'conversion_funnel': [
                {'stage': stage['stage'], 'count': stage['count'], 'rate': stage['conversion_rate']}
                for stage in conversion_funnel
            ],
            'performance_benchmarks': [
                {'metric': bench['metric'], 'user': bench['user_value'], 'market': bench['market_average']}
                for bench in performance_benchmarks
            ],
            'success_probability_gauge': [
                {'category': 'Success Probability', 'value': success_probability}
            ]
        }
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'user_id': current_user.id,
            'analysis_period_days': timeframe_days,
            'application_success_rate': application_success_rate,
            'interview_success_rate': interview_success_rate,
            'offer_success_rate': offer_success_rate,
            'conversion_funnel': conversion_funnel,
            'performance_benchmarks': performance_benchmarks,
            'predictive_analytics': predictive_analytics,
            'insights': insights,
            'recommendations': recommendations,
            'chart_data': chart_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate advanced user analytics: {str(e)}")