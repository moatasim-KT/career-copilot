from pydantic import BaseModel
from typing import List, Dict, Any

class SkillGapAnalysisResponse(BaseModel):
    user_skills: List[str]
    missing_skills: Dict[str, int]
    top_market_skills: Dict[str, int]
    skill_coverage_percentage: float
    learning_recommendations: List[str]
    total_jobs_analyzed: int
