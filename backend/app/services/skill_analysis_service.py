"""Minimal Skill Analysis Service stub.

Provides methods referenced by other services/tasks so imports resolve.
"""

from __future__ import annotations

from typing import Any, Dict, List


class SkillAnalysisService:
	def analyze_skill_gap(self, db, user_id: int) -> Dict[str, Any]:
		return {"user_id": user_id, "gaps": [], "summary": "stub"}

	async def analyze_skill_proficiency(self, skills: List[Any]):
		return {"skills": skills, "analysis": "stub"}

	async def suggest_career_paths(self, user_id: int, current_skills: List[Any], gaps: List[Any]):
		return []

	async def get_market_demand(self, skills: List[str]):
		return {s: 0.0 for s in skills}

	async def analyze_skill_progress(self, history: List[Any]):
		return {"progress": []}

	async def evaluate_learning_effectiveness(self, user_id: int, skill_id: int):
		return {"score": 0.0}


# Convenience singleton for modules that import `skill_analysis_service`
skill_analysis_service = SkillAnalysisService()
