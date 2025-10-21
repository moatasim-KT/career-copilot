"""
Skill gap analysis API endpoints
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.skill_gap_analysis_service import skill_gap_analysis_service

router = APIRouter()


class SkillGapRequest(BaseModel):
    """Request model for skill gap analysis"""
    target_roles: Optional[List[str]] = Field(default=None, description="Target job roles to analyze")
    include_trends: bool = Field(default=True, description="Include market trend analysis")
    analysis_period_days: int = Field(default=60, ge=7, le=365, description="Days of job data to analyze")


class LearningRecommendationResponse(BaseModel):
    """Response model for learning recommendations"""
    skill: str
    priority: str
    market_demand: str
    salary_impact: str
    learning_path: Dict[str, Any]
    next_steps: List[str]


class SkillGapAnalysisResponse(BaseModel):
    """Response model for skill gap analysis"""
    user_id: int
    skill_analysis: Dict[str, Any]
    learning_recommendations: List[LearningRecommendationResponse]
    market_insights: Dict[str, Any]
    market_trends: Optional[Dict[str, Any]] = None
    generated_at: str


@router.get("/analysis", response_model=SkillGapAnalysisResponse)
async def get_skill_gap_analysis(
    request: SkillGapRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive skill gap analysis for the current user
    
    Analyzes user's current skills against market demand and provides:
    - Skill coverage assessment
    - Priority skill gaps identification
    - Personalized learning recommendations
    - Market trend insights
    """
    try:
        analysis = skill_gap_analysis_service.get_comprehensive_skill_analysis(
            db=db,
            user_id=current_user.id,
            include_trends=request.include_trends
        )
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate skill gap analysis: {str(e)}"
        )


@router.get("/market-trends")
async def get_market_trends(
    days_back: int = Query(default=90, ge=7, le=365, description="Days of data to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current market trends for skills and technologies
    
    Provides insights into:
    - Trending skills in the job market
    - Salary correlations with skills
    - Market demand indicators
    - Growth trends over time
    """
    try:
        trends = skill_gap_analysis_service.analyze_market_trends(
            db=db,
            days_back=days_back
        )
        
        if 'error' in trends:
            raise HTTPException(status_code=404, detail=trends['error'])
        
        return trends
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze market trends: {str(e)}"
        )


@router.get("/learning-recommendations")
async def get_learning_recommendations(
    skill_focus: Optional[str] = Query(default=None, description="Focus on specific skill area"),
    priority_level: str = Query(default="all", regex="^(high|medium|low|all)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized learning recommendations based on skill gaps
    
    Returns curated learning paths including:
    - Recommended courses and certifications
    - Estimated time investment
    - Expected salary impact
    - Next steps and action items
    """
    try:
        # Get user's skill gap analysis
        analysis = skill_gap_analysis_service.get_comprehensive_skill_analysis(
            db=db,
            user_id=current_user.id,
            include_trends=False
        )
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        recommendations = analysis.get('learning_recommendations', [])
        
        # Filter by priority if specified
        if priority_level != 'all':
            recommendations = [
                rec for rec in recommendations 
                if rec['priority'] == priority_level
            ]
        
        # Filter by skill focus if specified
        if skill_focus:
            recommendations = [
                rec for rec in recommendations
                if skill_focus.lower() in rec['skill'].lower()
            ]
        
        return {
            'recommendations': recommendations,
            'total_count': len(recommendations),
            'filters_applied': {
                'priority_level': priority_level,
                'skill_focus': skill_focus
            },
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get learning recommendations: {str(e)}"
        )


@router.get("/skill-frequency")
async def get_skill_frequency_analysis(
    min_job_percentage: float = Query(default=5.0, ge=0.0, le=100.0),
    sort_by: str = Query(default="market_score", regex="^(frequency|market_score|avg_salary)$"),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get skill frequency analysis across job market
    
    Provides detailed statistics on:
    - Skill demand frequency
    - Average salaries by skill
    - Market importance scores
    - Job percentage coverage
    """
    try:
        from app.models.job import Job
        from datetime import timedelta
        
        # Get recent jobs
        recent_jobs = db.query(Job).filter(
            Job.status == 'active',
            Job.date_posted >= datetime.now() - timedelta(days=60)
        ).limit(1000).all()
        
        if not recent_jobs:
            raise HTTPException(status_code=404, detail="No recent jobs found for analysis")
        
        # Extract and analyze skills
        skill_data = skill_gap_analysis_service.extract_skills_from_jobs(recent_jobs)
        market_analysis = skill_gap_analysis_service.analyze_skill_frequency(skill_data)
        
        # Filter and sort results
        skill_stats = market_analysis['skill_stats']
        filtered_skills = {
            skill: stats for skill, stats in skill_stats.items()
            if stats['job_percentage'] >= min_job_percentage
        }
        
        # Sort by specified criteria
        sorted_skills = sorted(
            filtered_skills.items(),
            key=lambda x: x[1][sort_by],
            reverse=True
        )
        
        return {
            'skill_frequency': dict(sorted_skills[:limit]),
            'analysis_summary': {
                'total_jobs_analyzed': len(recent_jobs),
                'total_unique_skills': len(skill_stats),
                'skills_meeting_threshold': len(filtered_skills),
                'min_job_percentage': min_job_percentage
            },
            'sort_criteria': sort_by,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze skill frequency: {str(e)}"
        )


@router.get("/skill-coverage")
async def get_user_skill_coverage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's skill coverage analysis compared to market demand
    
    Shows how well the user's skills align with current market needs
    including coverage percentage and gap identification.
    """
    try:
        from app.models.job import Job
        from datetime import timedelta
        
        # Get user skills
        user_profile = current_user.profile or {}
        user_skills = user_profile.get('skills', [])
        
        if not user_skills:
            return {
                'message': 'No skills found in user profile',
                'coverage_percentage': 0,
                'recommendations': ['Add skills to your profile to get coverage analysis']
            }
        
        # Get recent jobs for market analysis
        recent_jobs = db.query(Job).filter(
            Job.status == 'active',
            Job.date_posted >= datetime.now() - timedelta(days=60)
        ).limit(500).all()
        
        if not recent_jobs:
            raise HTTPException(status_code=404, detail="No recent jobs found for analysis")
        
        # Analyze skill coverage
        skill_data = skill_gap_analysis_service.extract_skills_from_jobs(recent_jobs)
        market_analysis = skill_gap_analysis_service.analyze_skill_frequency(skill_data)
        skill_gaps = skill_gap_analysis_service.identify_skill_gaps(user_skills, market_analysis)
        
        # Calculate detailed coverage metrics
        user_skills_lower = set(s.lower() for s in user_skills)
        market_skills = set(market_analysis['skill_stats'].keys())
        
        covered_skills = user_skills_lower.intersection(market_skills)
        high_demand_skills = {
            skill for skill, stats in market_analysis['skill_stats'].items()
            if stats['job_percentage'] > 20  # Skills in >20% of jobs
        }
        
        high_demand_coverage = len(covered_skills.intersection(high_demand_skills))
        
        return {
            'user_id': current_user.id,
            'skill_coverage': skill_gaps['skill_coverage'],
            'detailed_metrics': {
                'total_user_skills': len(user_skills),
                'market_relevant_skills': len(covered_skills),
                'high_demand_skills_covered': high_demand_coverage,
                'total_high_demand_skills': len(high_demand_skills),
                'high_demand_coverage_percentage': (high_demand_coverage / len(high_demand_skills)) * 100 if high_demand_skills else 0
            },
            'top_missing_skills': skill_gaps['missing_skills'][:5],
            'analysis_date': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze skill coverage: {str(e)}"
        )


@router.post("/update-learning-progress")
async def update_learning_progress(
    skill: str,
    progress_percentage: int = Query(..., ge=0, le=100),
    notes: Optional[str] = Query(default=None, max_length=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update learning progress for a specific skill
    
    Allows users to track their progress on skill development
    and receive updated recommendations based on their learning journey.
    """
    try:
        # In a production system, this would update a learning_progress table
        # For now, we'll return a success response with updated recommendations
        
        progress_data = {
            'user_id': current_user.id,
            'skill': skill.lower().strip(),
            'progress_percentage': progress_percentage,
            'notes': notes,
            'updated_at': datetime.now().isoformat()
        }
        
        # Generate updated recommendations based on progress
        if progress_percentage >= 80:
            next_steps = [
                f"Consider advanced {skill} topics",
                f"Build a portfolio project using {skill}",
                f"Look for {skill} job opportunities"
            ]
        elif progress_percentage >= 50:
            next_steps = [
                f"Continue with intermediate {skill} concepts",
                f"Practice {skill} through coding exercises",
                f"Join {skill} community discussions"
            ]
        else:
            next_steps = [
                f"Focus on {skill} fundamentals",
                f"Set aside regular practice time for {skill}",
                f"Find a {skill} study buddy or mentor"
            ]
        
        return {
            'message': 'Learning progress updated successfully',
            'progress_data': progress_data,
            'next_steps': next_steps,
            'milestone_reached': progress_percentage >= 100,
            'updated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update learning progress: {str(e)}"
        )