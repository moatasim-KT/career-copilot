"""
Skill analysis service for Career Copilot.

Provides:
- Skill gap analysis
- Learning recommendations
- Career path planning
- Industry trend analysis
"""

from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from ..core.config import get_settings
from ..core.logging import get_logger
from ..models.skills import UserSkill, RequiredSkill, LearningResource
from ..services.ai_service import AIService

logger = get_logger(__name__)

class SkillAnalysisService:
    """Service for analyzing skills and providing recommendations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.ai_service = AIService()

    async def analyze_skill_gaps(self, user_id: int) -> Dict:
        """Analyze skill gaps for a user."""
        try:
            # Get user's current skills
            user_skills = await UserSkill.filter(user_id=user_id).all()
            user_skill_dict = {skill.name: skill.proficiency for skill in user_skills}
            
            # Get required skills from saved job listings
            required_skills = await RequiredSkill.get_from_saved_jobs(user_id)
            
            # Calculate gaps
            gaps = []
            for skill in required_skills:
                if skill.name not in user_skill_dict:
                    gaps.append({
                        "skill": skill.name,
                        "importance": skill.importance,
                        "gap_type": "missing"
                    })
                elif user_skill_dict[skill.name] < skill.required_proficiency:
                    gaps.append({
                        "skill": skill.name,
                        "importance": skill.importance,
                        "gap_type": "improvement_needed",
                        "current_level": user_skill_dict[skill.name],
                        "required_level": skill.required_proficiency
                    })
            
            # Sort gaps by importance
            gaps.sort(key=lambda x: x["importance"], reverse=True)
            
            return {
                "gaps": gaps,
                "total_gaps": len(gaps),
                "critical_gaps": len([g for g in gaps if g["importance"] > 0.8]),
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to analyze skill gaps: {str(e)}")
            return {"error": str(e)}

    async def get_learning_recommendations(self, user_id: int) -> List[Dict]:
        """Get personalized learning recommendations."""
        try:
            # Get skill gaps
            gaps = await self.analyze_skill_gaps(user_id)
            
            recommendations = []
            for gap in gaps.get("gaps", []):
                # Search for learning resources
                resources = await LearningResource.filter(skill_name=gap["skill"]).all()
                
                # Use AI to rank and personalize recommendations
                ranked_resources = await self.ai_service.rank_learning_resources(
                    resources=resources,
                    user_id=user_id,
                    skill_gap=gap
                )
                
                recommendations.append({
                    "skill": gap["skill"],
                    "gap_type": gap["gap_type"],
                    "importance": gap["importance"],
                    "resources": ranked_resources[:5]  # Top 5 recommendations
                })
            
            return recommendations
        except Exception as e:
            logger.error(f"Failed to get learning recommendations: {str(e)}")
            return []

    async def analyze_career_path(self, user_id: int) -> Dict:
        """Analyze and recommend career path options."""
        try:
            # Get user's profile and skills
            user_profile = await UserProfile.get(id=user_id)
            user_skills = await UserSkill.filter(user_id=user_id).all()
            
            # Get industry trends and job market data
            trends = await self.get_industry_trends(user_profile.industry)
            
            # Use AI to analyze career path options
            career_paths = await self.ai_service.analyze_career_paths(
                user_profile=user_profile,
                user_skills=user_skills,
                industry_trends=trends
            )
            
            return {
                "current_role": user_profile.current_role,
                "potential_paths": career_paths,
                "industry_trends": trends,
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to analyze career path: {str(e)}")
            return {"error": str(e)}

    async def get_industry_trends(self, industry: str) -> Dict:
        """Get current industry trends and insights."""
        try:
            # Use external APIs or AI to analyze industry trends
            async with aiohttp.ClientSession() as session:
                # Example: Using a hypothetical market data API
                headers = {'Authorization': f'Bearer {self.settings.MARKET_DATA_API_KEY}'}
                url = f'https://api.marketdata.com/v1/trends/{industry}'
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        trends = await response.json()
                        
                        # Enhance with AI insights
                        enhanced_trends = await self.ai_service.enhance_trend_analysis(trends)
                        
                        return {
                            "trends": enhanced_trends,
                            "last_updated": datetime.utcnow().isoformat()
                        }
                    else:
                        logger.error(f"Failed to get industry trends: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Failed to get industry trends: {str(e)}")
            return {}