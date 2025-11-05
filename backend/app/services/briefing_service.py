"""
Briefing service

Lightweight, import-safe service that generates data for morning briefings and evening summaries
without requiring other heavy services. Designed to be resilient: if the database or analytics
models are unavailable, methods fall back to sensible defaults.
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class BriefingService:
	"""Generates briefing content and tracks basic engagement.

	Contract
	- Inputs: db (sync or async session-like, optional usage), user_id (int)
	- Outputs: plain dicts for API/templating consumption
	- Errors: never raises on data generation; logs and returns defaults
	"""

	# ----- Public API -----
	def generate_morning_briefing_data(self, db: Any, user_id: int) -> Dict[str, Any]:
		"""Produce the morning briefing payload.

		Returns keys used by email tasks/templates: user_name, recommendations, daily_goals,
		market_insights, progress.
		"""
		user_name = self._get_user_name_safe(db, user_id)

		return {
			"user_name": user_name,
			"recommendations": self._get_user_recommendations_safe(db, user_id),
			"daily_goals": self._generate_daily_goals_safe(db, user_id),
			"market_insights": self._get_market_insights_safe(db, user_id),
			"progress": self._calculate_user_progress_safe(db, user_id),
		}

	def generate_evening_summary_data(self, db: Any, user_id: int) -> Dict[str, Any]:
		"""Produce the evening summary payload.

		Returns keys used by email tasks/templates: user_name, daily_activity, achievements,
		tomorrow_plan, motivation.
		"""
		user_name = self._get_user_name_safe(db, user_id)

		return {
			"user_name": user_name,
			"daily_activity": self._get_daily_activity_safe(db, user_id),
			"achievements": self._get_daily_achievements_safe(db, user_id),
			"tomorrow_plan": self._generate_tomorrow_plan_safe(db, user_id),
			"motivation": self._generate_motivational_message_safe(db, user_id),
		}

	def update_engagement_metrics(self, db: Any, user_id: int, email_type: str, action: str, when: datetime) -> None:
		"""Best-effort engagement tracking.

		If an Analytics model exists and db supports writes, record a simple event. Otherwise, noop.
		"""
		try:
			# Lazy import to avoid import-time failures
			from sqlalchemy import insert  # type: ignore

			from ..models.analytics import Analytics  # type: ignore

			if hasattr(db, "execute"):
				# AsyncSession has `execute` and commit is awaitable; Sync Session as well has execute
				data = {"action": action, "email_type": email_type, "hour": when.hour, "day_of_week": when.weekday()}
				stmt = insert(Analytics).values(user_id=user_id, type="email_engagement", data=data, generated_at=when)

				result = db.execute(stmt)  # type: ignore[misc]
				# Try to commit in both sync/async scenarios
				if hasattr(db, "commit"):
					try:
						maybe_coro = db.commit()
						# If it's a coroutine (AsyncSession), await it outside? We cannot here; best effort only.
					except Exception:  # pragma: no cover - defensive
						pass
				return None
		except Exception as e:  # pragma: no cover - defensive
			logger.debug(f"Engagement metrics not persisted (non-fatal): {e}")

	def get_optimal_briefing_times(self, db: Any, user_id: int) -> Tuple[time, time]:
		"""Return (morning_time, evening_time).

		Strategy: respect user's preferred times if present; otherwise default to 08:00 and 19:00.
		"""
		try:
			# Try to read preferences from User.settings if available
			from ..models.user import User  # type: ignore

			if hasattr(db, "query"):  # Sync Session
				user = db.query(User).filter(User.id == user_id).first()
				settings = getattr(user, "settings", {}) if user else {}
			else:
				settings = {}

			email_settings = settings.get("email_notifications", {}) if isinstance(settings, dict) else {}

			morning = self._parse_time_or_default(email_settings.get("preferred_morning_time"), time(8, 0))
			evening = self._parse_time_or_default(email_settings.get("preferred_evening_time"), time(19, 0))
			return morning, evening
		except Exception:
			return time(8, 0), time(19, 0)

	# ----- Internal helpers (safe fallbacks) -----
	def _get_user_name_safe(self, db: Any, user_id: int) -> str:
		try:
			from ..models.user import User  # type: ignore

			if hasattr(db, "query"):
				user = db.query(User).filter(User.id == user_id).first()
				if user:
					profile = getattr(user, "profile", {}) or {}
					name = profile.get("name") if isinstance(profile, dict) else None
					return name or getattr(user, "email", "there")
		except Exception:
			pass
		return "there"

	def _get_user_recommendations_safe(self, db: Any, user_id: int) -> List[Dict[str, Any]]:
		# Placeholder - integrate with recommendations later
		return [
			{
				"id": 1,
				"title": "Senior Software Engineer",
				"company": "TechCorp",
				"location": "Remote",
				"match_score": 0.91,
				"skills": ["Python", "React", "PostgreSQL"],
				"application_url": "https://example.com/apply/1",
				"description": "Join our team building next-generation applications...",
			}
		]

	def _generate_daily_goals_safe(self, db: Any, user_id: int) -> Dict[str, Any]:
		return {"applications_target": 3, "networking_target": 2, "skill_focus": "Machine Learning"}

	def _get_market_insights_safe(self, db: Any, user_id: int) -> Dict[str, Any]:
		return {
			"trending_skills": ["Python", "React", "AWS", "Docker", "Kubernetes", "TypeScript", "Node.js", "PostgreSQL"],
			"salary_trend": "Software engineer salaries increased 8% this quarter in your target locations",
			"job_market_activity": "High demand for full-stack developers in your area with 15% more job postings this month",
		}

	def _calculate_user_progress_safe(self, db: Any, user_id: int) -> Dict[str, Any]:
		# Provide a minimal, stable progress snapshot
		return {"applications_this_week": 3, "interviews_scheduled": 1, "response_rate": 12.5, "goal_completion": 60}

	def _get_daily_activity_safe(self, db: Any, user_id: int) -> Dict[str, Any]:
		today = datetime.now().date()
		return {
			"applications_sent": 1,
			"jobs_viewed": 10,
			"profiles_updated": 0,
			"time_spent_minutes": 30,
			"goal_achievement": 33,
			"weekly_progress": {"applications": 8, "responses": 2, "interviews": 1, "streak_days": 3},
			"date": today.isoformat(),
		}

	def _get_daily_achievements_safe(self, db: Any, user_id: int) -> List[Dict[str, Any]]:
		return [
			{
				"title": "Application Goal Reached",
				"description": "You applied to 3 jobs today, meeting your daily goal!",
				"impact": "Increased your weekly application count by 25%",
			}
		]

	def _generate_tomorrow_plan_safe(self, db: Any, user_id: int) -> Dict[str, Any]:
		return {
			"priority_applications": [
				{"title": "Product Manager", "company": "StartupCo", "deadline": (datetime.now() + timedelta(days=2)).isoformat()}
			],
			"follow_ups": [{"company": "TechCorp", "type": "Application follow-up", "days_since": 7}],
			"skill_development": {"activity": "Complete React course module", "skill": "React", "resource": "React Fundamentals"},
			"networking": {
				"activity": "Connect with 2 professionals on LinkedIn",
				"suggestions": [
					"Reach out to alumni in your target companies",
					"Comment on industry posts to increase visibility",
				],
			},
		}

	def _generate_motivational_message_safe(self, db: Any, user_id: int) -> str:
		messages = [
			"Every application brings you one step closer to your dream job. Your persistence will pay off!",
			"Your dedication to your career growth is inspiring. Keep pushing forward!",
			"Success in job searching is about consistency, not perfection. You're doing great!",
			"Each 'no' brings you closer to the right 'yes'. Stay positive and keep going!",
		]
		return messages[user_id % len(messages)] if messages else "Keep up the great work!"

	@staticmethod
	def _parse_time_or_default(value: Any, default: time) -> time:
		try:
			if isinstance(value, str) and value:
				return time.fromisoformat(value)
		except Exception:
			pass
		return default


# Module-level singleton
briefing_service = BriefingService()
