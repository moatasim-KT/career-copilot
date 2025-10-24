from pydantic import BaseModel
from typing import List, Dict, Any

class SkillGapAnalysisResponse(BaseModel):
    user_skills: List[str]
    missing_skills: List[str]
    top_market_skills: List[str]
    skill_coverage_percentage: float
    recommendations: List[str]
