"""Minimal Recommendation Service stub for skill-related recommendations."""

from __future__ import annotations

from typing import Any, Dict, List


class RecommendationService:
	async def get_learning_recommendations(self, user_id: int, skill_gaps: List[Dict]):
		return []

	async def generate_recommendations(
		self,
		user_id: int,
		current_skills: List[Any],
		gaps: List[Any],
		market_demand: Dict[str, float],
	):
		return []
