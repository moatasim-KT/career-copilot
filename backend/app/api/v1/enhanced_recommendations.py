"""
Enhanced recommendation API endpoints with advanced personalization and caching
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.enhanced_recommendation_service import enhanced_recommendation_service
from app.core.cache import job_recommendation_cache

router = APIRouter()


class RecommendationFilters(BaseModel):
    """Filters for recommendation requests"""
    min_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum recommendation score")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    include_applied: bool = Field(default=False, description="Include jobs already applied to")
    location_types: Optional[List[str]] = Field(default=None, description="Filter by location types: remote, hybrid, onsite")
    experience_levels: Optional[List[str]] = Field(default=None, description="Filter by experience levels")
    salary_min: Optional[int] = Field(default=None, description="Minimum salary requirement")
    company_sizes: Optional[List[str]] = Field(default=None, description="Filter by company sizes")
    industries: Optional[List[str]] = Field(default=None, description="Filter by industries")


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    recommendations: List[Dict[str, Any]]
    total_analyzed: int
    filters_applied: Dict[str, Any]
    generation_time_ms: int
    cache_hit: bool
    metadata: Dict[str, Any]


@router.get("/enhanced", response_model=RecommendationResponse)
async def get_enhanced_recommendations(
    filters: RecommendationFilters = Depends(),
    force_refresh: bool = Query(default=False, description="Force cache refresh"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get enhanced personalized job recommendations with advanced scoring
    
    This endpoint uses an advanced multi-factor scoring algorithm that considers:
    - Skill matching with semantic analysis
    - Experience level alignment and career trajectory
    - Location preferences and remote work compatibility
    - Company culture and size preferences
    - Career growth potential
    - Market timing and job posting recency
    - Salary alignment with expectations
    """
    start_time = datetime.now()
    
    try:
        # Check cache first (unless force refresh)
        cache_key = f"enhanced_recs_{current_user.id}_{hash(str(filters.dict()))}"
        cached_result = None
        
        if not force_refresh:
            cached_result = job_recommendation_cache.get(cache_key)
        
        if cached_result:
            return RecommendationResponse(
                recommendations=cached_result['recommendations'],
                total_analyzed=cached_result['total_analyzed'],
                filters_applied=filters.dict(),
                generation_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                cache_hit=True,
                metadata=cached_result.get('metadata', {})
            )
        
        # Generate fresh recommendations
        recommendations = enhanced_recommendation_service.get_personalized_recommendations(
            db=db,
            user_id=current_user.id,
            limit=filters.max_results,
            min_score=filters.min_score,
            include_applied=filters.include_applied
        )
        
        # Apply additional filters
        filtered_recommendations = _apply_recommendation_filters(recommendations, filters)
        
        # Prepare response data
        result_data = {
            'recommendations': filtered_recommendations,
            'total_analyzed': len(recommendations),
            'metadata': {
                'algorithm_version': '3.0_enhanced',
                'personalization_factors': 7,
                'generated_at': datetime.now().isoformat(),
                'user_profile_completeness': _calculate_profile_completeness(current_user)
            }
        }
        
        # Cache the result
        job_recommendation_cache.set(cache_key, result_data, timeout=1800)  # 30 minutes
        
        generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return RecommendationResponse(
            recommendations=filtered_recommendations,
            total_analyzed=len(recommendations),
            filters_applied=filters.dict(),
            generation_time_ms=generation_time,
            cache_hit=False,
            metadata=result_data['metadata']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate enhanced recommendations: {str(e)}"
        )


@router.get("/job/{job_id}/analysis")
async def get_job_recommendation_analysis(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed recommendation analysis for a specific job
    
    Provides comprehensive scoring breakdown and personalized insights
    for why a specific job was or wasn't recommended.
    """
    try:
        from app.models.job import Job
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Generate detailed analysis
        analysis = enhanced_recommendation_service.generate_enhanced_recommendation(
            db=db,
            user_id=current_user.id,
            job=job
        )
        
        if not analysis:
            raise HTTPException(status_code=500, detail="Failed to generate job analysis")
        
        # Add additional insights
        analysis['insights'] = _generate_job_insights(analysis, current_user)
        analysis['improvement_suggestions'] = _generate_improvement_suggestions(analysis)
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze job recommendation: {str(e)}"
        )


@router.get("/insights/profile")
async def get_recommendation_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get insights about user's recommendation patterns and profile optimization suggestions
    
    Analyzes the user's profile and recent recommendations to provide
    actionable insights for improving job match quality.
    """
    try:
        # Get recent recommendations for analysis
        recent_recommendations = enhanced_recommendation_service.get_personalized_recommendations(
            db=db,
            user_id=current_user.id,
            limit=20,
            min_score=0.0  # Include all for analysis
        )
        
        # Analyze recommendation patterns
        insights = _analyze_recommendation_patterns(recent_recommendations, current_user)
        
        # Generate profile optimization suggestions
        optimization_suggestions = _generate_profile_optimization_suggestions(
            current_user, recent_recommendations
        )
        
        # Calculate market competitiveness
        market_analysis = _analyze_market_competitiveness(recent_recommendations)
        
        return {
            'profile_insights': insights,
            'optimization_suggestions': optimization_suggestions,
            'market_analysis': market_analysis,
            'recommendation_quality': {
                'average_score': insights.get('average_score', 0),
                'high_quality_matches': insights.get('high_quality_count', 0),
                'total_analyzed': len(recent_recommendations)
            },
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendation insights: {str(e)}"
        )


@router.post("/feedback")
async def submit_recommendation_feedback(
    job_id: int,
    feedback_type: str = Query(..., regex="^(helpful|not_helpful|applied|not_interested)$"),
    feedback_details: Optional[str] = Query(default=None, max_length=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on recommendation quality
    
    Helps improve future recommendations by learning from user preferences
    and feedback on recommended jobs.
    """
    try:
        # Store feedback for future algorithm improvements
        feedback_data = {
            'user_id': current_user.id,
            'job_id': job_id,
            'feedback_type': feedback_type,
            'feedback_details': feedback_details,
            'timestamp': datetime.now().isoformat()
        }
        
        # In a production system, this would be stored in a feedback table
        # For now, we'll use cache to store recent feedback
        feedback_key = f"rec_feedback_{current_user.id}_{job_id}"
        job_recommendation_cache.set(feedback_key, feedback_data, timeout=86400 * 30)  # 30 days
        
        # Invalidate user's recommendation cache to trigger refresh
        user_cache_pattern = f"enhanced_recs_{current_user.id}_*"
        # Note: In production, implement cache pattern deletion
        
        return {
            'message': 'Feedback submitted successfully',
            'feedback_type': feedback_type,
            'job_id': job_id,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/performance/metrics")
async def get_recommendation_performance_metrics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recommendation system performance metrics for the user
    
    Provides analytics on recommendation accuracy, user engagement,
    and system performance over the specified time period.
    """
    try:
        # Calculate performance metrics
        metrics = _calculate_recommendation_metrics(current_user.id, days)
        
        return {
            'user_id': current_user.id,
            'analysis_period_days': days,
            'metrics': metrics,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate performance metrics: {str(e)}"
        )


@router.post("/cache/refresh")
async def refresh_recommendation_cache(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh recommendation cache for the current user
    
    Triggers background regeneration of personalized recommendations
    with the latest algorithm and user profile data.
    """
    try:
        # Add background task to regenerate recommendations
        background_tasks.add_task(
            _regenerate_user_recommendations,
            db, current_user.id
        )
        
        return {
            'message': 'Recommendation cache refresh initiated',
            'user_id': current_user.id,
            'status': 'processing',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh recommendation cache: {str(e)}"
        )


# Helper functions

def _apply_recommendation_filters(
    recommendations: List[Dict[str, Any]], 
    filters: RecommendationFilters
) -> List[Dict[str, Any]]:
    """Apply additional filters to recommendations"""
    filtered = recommendations
    
    # Filter by location types
    if filters.location_types:
        filtered = [
            rec for rec in filtered
            if _matches_location_filter(rec, filters.location_types)
        ]
    
    # Filter by experience levels
    if filters.experience_levels:
        filtered = [
            rec for rec in filtered
            if _matches_experience_filter(rec, filters.experience_levels)
        ]
    
    # Filter by salary
    if filters.salary_min:
        filtered = [
            rec for rec in filtered
            if _matches_salary_filter(rec, filters.salary_min)
        ]
    
    # Filter by company sizes
    if filters.company_sizes:
        filtered = [
            rec for rec in filtered
            if _matches_company_size_filter(rec, filters.company_sizes)
        ]
    
    # Filter by industries
    if filters.industries:
        filtered = [
            rec for rec in filtered
            if _matches_industry_filter(rec, filters.industries)
        ]
    
    return filtered


def _matches_location_filter(recommendation: Dict[str, Any], location_types: List[str]) -> bool:
    """Check if recommendation matches location type filter"""
    location_details = recommendation.get('score_breakdown', {}).get('location_preference', {}).get('details', {})
    match_type = location_details.get('match_type', '')
    
    if 'remote' in location_types and 'remote' in match_type:
        return True
    if 'hybrid' in location_types and 'hybrid' in match_type:
        return True
    if 'onsite' in location_types and 'location' in match_type:
        return True
    
    return False


def _matches_experience_filter(recommendation: Dict[str, Any], experience_levels: List[str]) -> bool:
    """Check if recommendation matches experience level filter"""
    # This would need to be implemented based on job requirements
    return True  # Placeholder


def _matches_salary_filter(recommendation: Dict[str, Any], min_salary: int) -> bool:
    """Check if recommendation matches salary filter"""
    salary_details = recommendation.get('score_breakdown', {}).get('salary_alignment', {}).get('details', {})
    job_range = salary_details.get('job_range', '')
    
    if job_range and job_range != 'Not specified':
        # Extract minimum salary from range string
        try:
            salary_str = job_range.split('-')[0].replace('$', '').replace(',', '')
            job_min_salary = int(salary_str)
            return job_min_salary >= min_salary
        except (ValueError, IndexError):
            pass
    
    return True  # If salary not specified, don't filter out


def _matches_company_size_filter(recommendation: Dict[str, Any], company_sizes: List[str]) -> bool:
    """Check if recommendation matches company size filter"""
    # This would need to be implemented based on job requirements
    return True  # Placeholder


def _matches_industry_filter(recommendation: Dict[str, Any], industries: List[str]) -> bool:
    """Check if recommendation matches industry filter"""
    # This would need to be implemented based on job requirements
    return True  # Placeholder


def _calculate_profile_completeness(user: User) -> float:
    """Calculate user profile completeness score"""
    profile = user.profile or {}
    
    completeness_factors = [
        bool(profile.get('skills')),
        bool(profile.get('experience_level')),
        bool(profile.get('locations')),
        bool(profile.get('career_goals')),
        bool(profile.get('preferences')),
        bool(profile.get('salary_expectations')),
        bool(profile.get('industry_experience'))
    ]
    
    return sum(completeness_factors) / len(completeness_factors)


def _generate_job_insights(analysis: Dict[str, Any], user: User) -> List[str]:
    """Generate additional insights for job analysis"""
    insights = []
    
    overall_score = analysis.get('overall_score', 0)
    score_breakdown = analysis.get('score_breakdown', {})
    
    # Identify strongest and weakest factors
    factor_scores = {
        name: details.get('score', 0)
        for name, details in score_breakdown.items()
    }
    
    strongest_factor = max(factor_scores.items(), key=lambda x: x[1])
    weakest_factor = min(factor_scores.items(), key=lambda x: x[1])
    
    insights.append(f"Strongest match factor: {strongest_factor[0].replace('_', ' ').title()} ({strongest_factor[1]:.1%})")
    
    if weakest_factor[1] < 0.5:
        insights.append(f"Area for improvement: {weakest_factor[0].replace('_', ' ').title()} ({weakest_factor[1]:.1%})")
    
    # Add specific insights based on scores
    if score_breakdown.get('skill_match', {}).get('score', 0) > 0.8:
        insights.append("Excellent technical skill alignment - you're well-qualified")
    
    if score_breakdown.get('market_timing', {}).get('details', {}).get('days_old', 30) <= 3:
        insights.append("Very recent posting - apply quickly for best chances")
    
    return insights


def _generate_improvement_suggestions(analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate suggestions for improving match score"""
    suggestions = []
    score_breakdown = analysis.get('score_breakdown', {})
    
    # Skill improvement suggestions
    skill_details = score_breakdown.get('skill_match', {}).get('details', {})
    missing_skills = skill_details.get('missing_skills', [])
    
    if missing_skills:
        suggestions.append({
            'category': 'Skills',
            'suggestion': f"Learn {', '.join(missing_skills[:3])} to improve technical match",
            'impact': 'High',
            'effort': 'Medium to High'
        })
    
    # Experience suggestions
    exp_details = score_breakdown.get('experience_alignment', {}).get('details', {})
    level_diff = exp_details.get('level_difference', 0)
    
    if level_diff > 1:
        suggestions.append({
            'category': 'Experience',
            'suggestion': 'Highlight relevant projects and achievements to bridge experience gap',
            'impact': 'Medium',
            'effort': 'Low'
        })
    
    # Location suggestions
    loc_details = score_breakdown.get('location_preference', {}).get('details', {})
    if loc_details.get('score', 0) < 0.5:
        suggestions.append({
            'category': 'Location',
            'suggestion': 'Consider remote work options or expanding location preferences',
            'impact': 'Medium',
            'effort': 'Low'
        })
    
    return suggestions


def _analyze_recommendation_patterns(
    recommendations: List[Dict[str, Any]], 
    user: User
) -> Dict[str, Any]:
    """Analyze patterns in user's recommendations"""
    if not recommendations:
        return {'average_score': 0, 'high_quality_count': 0, 'patterns': []}
    
    scores = [rec.get('overall_score', 0) for rec in recommendations]
    average_score = sum(scores) / len(scores)
    high_quality_count = len([s for s in scores if s >= 0.7])
    
    # Analyze common weak points
    weak_factors = []
    for rec in recommendations:
        score_breakdown = rec.get('score_breakdown', {})
        for factor, details in score_breakdown.items():
            if details.get('score', 0) < 0.5:
                weak_factors.append(factor)
    
    from collections import Counter
    common_weaknesses = Counter(weak_factors).most_common(3)
    
    patterns = [
        f"Average match score: {average_score:.1%}",
        f"High-quality matches: {high_quality_count}/{len(recommendations)}",
    ]
    
    if common_weaknesses:
        top_weakness = common_weaknesses[0][0].replace('_', ' ').title()
        patterns.append(f"Most common weakness: {top_weakness}")
    
    return {
        'average_score': average_score,
        'high_quality_count': high_quality_count,
        'patterns': patterns,
        'common_weaknesses': [w[0] for w in common_weaknesses]
    }


def _generate_profile_optimization_suggestions(
    user: User, 
    recommendations: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """Generate suggestions for optimizing user profile"""
    suggestions = []
    profile = user.profile or {}
    
    # Check profile completeness
    if not profile.get('skills'):
        suggestions.append({
            'category': 'Profile Completeness',
            'suggestion': 'Add your technical skills to improve job matching accuracy',
            'priority': 'High',
            'impact': 'Significantly improves recommendation quality'
        })
    
    if not profile.get('career_goals'):
        suggestions.append({
            'category': 'Career Direction',
            'suggestion': 'Define your career goals to get better growth-oriented recommendations',
            'priority': 'Medium',
            'impact': 'Helps identify career advancement opportunities'
        })
    
    if not profile.get('salary_expectations'):
        suggestions.append({
            'category': 'Compensation',
            'suggestion': 'Set salary expectations to filter jobs that meet your requirements',
            'priority': 'Medium',
            'impact': 'Filters out jobs with misaligned compensation'
        })
    
    # Analyze recommendation patterns for additional suggestions
    if recommendations:
        avg_skill_score = sum(
            rec.get('score_breakdown', {}).get('skill_match', {}).get('score', 0)
            for rec in recommendations
        ) / len(recommendations)
        
        if avg_skill_score < 0.6:
            suggestions.append({
                'category': 'Skill Development',
                'suggestion': 'Consider developing in-demand skills to improve job match quality',
                'priority': 'High',
                'impact': 'Significantly increases number of suitable opportunities'
            })
    
    return suggestions


def _analyze_market_competitiveness(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze user's competitiveness in the job market"""
    if not recommendations:
        return {'competitiveness': 'Unknown', 'insights': []}
    
    scores = [rec.get('overall_score', 0) for rec in recommendations]
    avg_score = sum(scores) / len(scores)
    
    if avg_score >= 0.75:
        competitiveness = 'Highly Competitive'
        insights = ['You match well with most opportunities', 'Consider applying to premium positions']
    elif avg_score >= 0.6:
        competitiveness = 'Competitive'
        insights = ['Good match with many opportunities', 'Focus on skill development for premium roles']
    elif avg_score >= 0.45:
        competitiveness = 'Moderately Competitive'
        insights = ['Some good matches available', 'Skill development could significantly improve options']
    else:
        competitiveness = 'Developing'
        insights = ['Focus on skill and experience development', 'Consider entry-level or growth opportunities']
    
    return {
        'competitiveness': competitiveness,
        'average_match_score': avg_score,
        'insights': insights,
        'market_position': _calculate_market_position(avg_score)
    }


def _calculate_market_position(avg_score: float) -> str:
    """Calculate user's position in the job market"""
    if avg_score >= 0.8:
        return 'Top 20% - Premium candidate'
    elif avg_score >= 0.65:
        return 'Top 40% - Strong candidate'
    elif avg_score >= 0.5:
        return 'Top 60% - Solid candidate'
    else:
        return 'Developing candidate - Focus on growth'


def _calculate_recommendation_metrics(user_id: int, days: int) -> Dict[str, Any]:
    """Calculate recommendation performance metrics"""
    # In a production system, this would query actual metrics from database
    # For now, return mock metrics
    return {
        'recommendations_generated': 45,
        'average_score': 0.68,
        'high_quality_matches': 12,
        'user_interactions': 8,
        'applications_from_recommendations': 3,
        'cache_hit_rate': 0.75,
        'algorithm_performance': {
            'accuracy': 0.82,
            'precision': 0.78,
            'user_satisfaction': 0.85
        }
    }


async def _regenerate_user_recommendations(db: Session, user_id: int):
    """Background task to regenerate user recommendations"""
    try:
        # Clear existing cache
        cache_pattern = f"enhanced_recs_{user_id}_*"
        # In production, implement cache pattern clearing
        
        # Generate fresh recommendations
        enhanced_recommendation_service.get_personalized_recommendations(
            db=db,
            user_id=user_id,
            limit=20,
            min_score=0.3
        )
        
        logger.info(f"Successfully regenerated recommendations for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to regenerate recommendations for user {user_id}: {e}")