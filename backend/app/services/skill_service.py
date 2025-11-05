"""
Unified skill analysis and gap detection service.
Integrates skill analysis, gap detection, and learning recommendations.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from ..core.logging import get_logger
from .notification_service import NotificationService
from .recommendation_service import RecommendationService
from .skill_analysis_service import SkillAnalysisService
from .skill_gap_analyzer import SkillGapAnalyzer

# Provide a lightweight fallback for UserSkill to avoid import errors
# when the dedicated Skill model isn't present in this codebase.
try:
	from ..models.skill import UserSkill  # type: ignore
except Exception:  # pragma: no cover - fallback shim

	class UserSkill:  # minimal stub
		@classmethod
		async def filter(cls, user_id: int):
			return []

		@classmethod
		async def get_history(cls, user_id: int, skill_id: int):
			return []


logger = get_logger(__name__)


class UnifiedSkillService:
	"""
	Unified service for skill analysis, gap detection, and recommendations.
	Integrates various skill-related services into a cohesive system.
	"""

	def __init__(self):
		self.analyzer = SkillAnalysisService()
		self.gap_detector = SkillGapAnalyzer()
		self.recommender = RecommendationService()
		self.notification = NotificationService()

	async def analyze_user_skills(self, user_id: int) -> Dict[str, Any]:
		"""
		Comprehensive skill analysis for a user.

		Args:
		    user_id: ID of the user to analyze

		Returns:
		    Dictionary containing analysis results
		"""
		try:
			# Get user's current skills and job preferences
			current_skills = await UserSkill.filter(user_id=user_id).all()

			# Analyze current skill proficiency
			skill_analysis = await self.analyzer.analyze_skill_proficiency(skills=current_skills)

			# Detect skill gaps
			gaps = await self.gap_detector.detect_gaps(user_id=user_id, current_skills=current_skills)

			# Get learning recommendations
			recommendations = await self.recommender.get_learning_recommendations(user_id=user_id, skill_gaps=gaps)

			# Generate career path suggestions
			career_paths = await self.analyzer.suggest_career_paths(user_id=user_id, current_skills=current_skills, gaps=gaps)

			# Prepare comprehensive report
			report = {
				"current_skills": skill_analysis,
				"skill_gaps": gaps,
				"learning_recommendations": recommendations,
				"career_paths": career_paths,
				"analysis_date": datetime.now(timezone.utc).isoformat(),
			}

			# Notify user of significant changes
			await self._notify_significant_changes(user_id, report)

			return report

		except Exception as e:
			logger.error(f"Error analyzing skills for user {user_id}: {e!s}")
			return {"error": str(e)}

	async def track_skill_progress(self, user_id: int, skill_id: int) -> Dict[str, Any]:
		"""
		Track progress for a specific skill.

		Args:
		    user_id: ID of the user
		    skill_id: ID of the skill to track

		Returns:
		    Dictionary containing progress data
		"""
		try:
			# Get historical skill data
			history = await UserSkill.get_history(user_id=user_id, skill_id=skill_id)

			# Analyze progress
			progress = await self.analyzer.analyze_skill_progress(history)

			# Get learning effectiveness
			effectiveness = await self.analyzer.evaluate_learning_effectiveness(user_id=user_id, skill_id=skill_id)

			return {"skill_id": skill_id, "progress": progress, "effectiveness": effectiveness, "history": history}

		except Exception as e:
			logger.error(f"Error tracking skill progress: {e!s}")
			return {"error": str(e)}

	async def update_skill_recommendations(self, user_id: int) -> Dict[str, Any]:
		"""
		Update skill-based recommendations for a user.

		Args:
		    user_id: ID of the user

		Returns:
		    Dictionary containing updated recommendations
		"""
		try:
			# Get current skills and gaps
			current_skills = await UserSkill.filter(user_id=user_id).all()
			gaps = await self.gap_detector.detect_gaps(user_id=user_id, current_skills=current_skills)

			# Get market demand data
			market_demand = await self.analyzer.get_market_demand(skills=[skill.name for skill in current_skills])

			# Generate recommendations
			recommendations = await self.recommender.generate_recommendations(
				user_id=user_id, current_skills=current_skills, gaps=gaps, market_demand=market_demand
			)

			return {"recommendations": recommendations, "market_demand": market_demand, "updated_at": datetime.now(timezone.utc).isoformat()}

		except Exception as e:
			logger.error(f"Error updating recommendations: {e!s}")
			return {"error": str(e)}

	async def _notify_significant_changes(self, user_id: int, report: Dict[str, Any]):
		"""
		Notify user of significant changes in their skill analysis.
		"""
		significant_changes = []

		# Check for critical skill gaps
		critical_gaps = [g for g in report["skill_gaps"] if g["importance"] > 0.8]
		if critical_gaps:
			significant_changes.append(f"Found {len(critical_gaps)} critical skill gaps")

		# Check for high-demand skills
		high_demand = [r for r in report["learning_recommendations"] if r["market_demand"] > 0.8]
		if high_demand:
			significant_changes.append(f"Identified {len(high_demand)} high-demand skills to learn")

		if significant_changes:
			await self.notification.create_notification(
				user_id=user_id,
				type="skill_analysis_update",
				title="Important Updates to Your Skill Analysis",
				message="\n".join(significant_changes),
				data={"report": report},
			)
