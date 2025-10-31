from __future__ import annotations

from pydantic import BaseModel


class SkillGapAnalysisResponse(BaseModel):
	user_skills: list[str]
	missing_skills: list[str]
	top_market_skills: list[str]
	skill_coverage_percentage: float
	recommendations: list[str]
