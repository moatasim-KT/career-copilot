"""
Profile service for Career Co-Pilot system with Redis caching
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.core.cache import cached, user_profile_cache
from app.models.application import Application
# from app.models.document import Document  # TODO: Create document model
# from app.models.goal import Goal, Milestone  # TODO: Create goal model
from app.models.job import Job
from app.models.user import User
from app.schemas.profile import (
	ApplicationHistoryItem,
	ApplicationHistoryResponse,
	DocumentManagementResponse,
	DocumentSummary,
	ProgressTrackingStats,
	UserProfileResponse,
	UserProfileUpdate,
	UserSettingsUpdate,
)

logger = logging.getLogger(__name__)


class ProfileService:
	"""Service for managing user profiles and dashboard data"""

	def __init__(self, db: Session):
		self.db = db

	def get_user_profile(self, user_id: int) -> Optional[UserProfileResponse]:
		"""Get user profile with completion percentage (cached)"""

		# Try to get from cache first
		cached_profile = user_profile_cache.get_profile(user_id)
		if cached_profile:
			logger.debug(f"Profile cache hit for user {user_id}")
			return UserProfileResponse(**cached_profile)

		user = self.db.query(User).filter(User.id == user_id).first()
		if not user:
			return None

		profile_data = user.profile or {}

		# Calculate profile completion percentage
		completion_score = self._calculate_profile_completion(profile_data)

		profile_response = UserProfileResponse(
			first_name=profile_data.get("first_name"),
			last_name=profile_data.get("last_name"),
			phone=profile_data.get("phone"),
			linkedin_url=profile_data.get("linkedin_url"),
			portfolio_url=profile_data.get("portfolio_url"),
			github_url=profile_data.get("github_url"),
			current_title=profile_data.get("current_title"),
			current_company=profile_data.get("current_company"),
			years_experience=profile_data.get("years_experience"),
			education_level=profile_data.get("education_level"),
			skills=profile_data.get("skills", []),
			location_preferences=profile_data.get("location_preferences", []),
			career_preferences=profile_data.get("career_preferences", {}),
			career_goals=profile_data.get("career_goals", {}),
			profile_completion=completion_score,
			last_updated=user.updated_at,
		)

		# Cache the profile data
		user_profile_cache.set_profile(user_id, profile_response.dict())
		logger.debug(f"Profile cached for user {user_id}")

		return profile_response

	def update_user_profile(self, user_id: int, profile_update: UserProfileUpdate) -> Optional[UserProfileResponse]:
		"""Update user profile and invalidate cache"""

		user = self.db.query(User).filter(User.id == user_id).first()
		if not user:
			return None

		# Get current profile or initialize empty dict
		current_profile = user.profile or {}

		# Update profile with new data
		update_data = profile_update.dict(exclude_unset=True)
		for key, value in update_data.items():
			if value is not None:
				current_profile[key] = value

		# Update user record
		user.profile = current_profile
		user.updated_at = datetime.now(timezone.utc)

		self.db.commit()
		self.db.refresh(user)

		# Invalidate cache after update
		user_profile_cache.invalidate_profile(user_id)
		logger.debug(f"Profile cache invalidated for user {user_id}")

		return self.get_user_profile(user_id)

	def update_user_settings(self, user_id: int, settings_update: UserSettingsUpdate) -> bool:
		"""Update user settings and invalidate cache"""

		user = self.db.query(User).filter(User.id == user_id).first()
		if not user:
			return False

		# Get current settings or initialize empty dict
		current_settings = user.settings or {}

		# Update settings with new data
		update_data = settings_update.dict(exclude_unset=True)
		for key, value in update_data.items():
			if value is not None:
				current_settings[key] = value

		# Update user record
		user.settings = current_settings
		user.updated_at = datetime.now(timezone.utc)

		self.db.commit()

		# Invalidate settings cache
		user_profile_cache.cache.delete(f"cc:user_profile_settings:{user_id}")
		logger.debug(f"Settings cache invalidated for user {user_id}")

		return True

	def get_application_history(
		self,
		user_id: int,
		page: int = 1,
		per_page: int = 20,
		status_filter: Optional[str] = None,
		date_from: Optional[datetime] = None,
		date_to: Optional[datetime] = None,
	) -> ApplicationHistoryResponse:
		"""Get user's application history with filtering and pagination"""

		# Base query
		query = (
			self.db.query(
				Application.id,
				Application.job_id,
				Application.status,
				Application.applied_at,
				Application.response_date,
				Application.notes,
				Application.documents,
				Application.application_metadata,
				Job.title.label("job_title"),
				Job.company.label("company_name"),
			)
			.join(Job, Application.job_id == Job.id)
			.filter(Application.user_id == user_id)
		)

		# Apply filters
		if status_filter:
			query = query.filter(Application.status == status_filter)

		if date_from:
			query = query.filter(Application.applied_at >= date_from)

		if date_to:
			query = query.filter(Application.applied_at <= date_to)

		# Get total count
		total_count = query.count()

		# Apply pagination and ordering
		applications_data = query.order_by(desc(Application.applied_at)).offset((page - 1) * per_page).limit(per_page).all()

		# Convert to response format
		applications = []
		for app_data in applications_data:
			# Count interview rounds
			interview_rounds = 0
			if app_data.application_metadata and "interview_rounds" in app_data.application_metadata:
				interview_rounds = len(app_data.application_metadata["interview_rounds"])

			application_item = ApplicationHistoryItem(
				id=app_data.id,
				job_id=app_data.job_id,
				job_title=app_data.job_title,
				company_name=app_data.company_name,
				status=app_data.status,
				applied_at=app_data.applied_at,
				response_date=app_data.response_date,
				notes=app_data.notes,
				documents_count=len(app_data.documents) if app_data.documents else 0,
				interview_rounds=interview_rounds,
			)
			applications.append(application_item)

		# Calculate summary statistics
		stats = self._calculate_application_stats(user_id)

		return ApplicationHistoryResponse(
			applications=applications,
			total_count=total_count,
			page=page,
			per_page=per_page,
			total_applications=stats["total_applications"],
			applications_this_month=stats["applications_this_month"],
			interviews_scheduled=stats["interviews_scheduled"],
			offers_received=stats["offers_received"],
			success_rate=stats["success_rate"],
		)

	@cached(ttl=1800, key_prefix="progress_stats")  # Cache for 30 minutes
	def get_progress_tracking_stats(self, user_id: int) -> ProgressTrackingStats:
		"""Get comprehensive progress tracking statistics (cached)"""

		now = datetime.now(timezone.utc)
		week_start = now - timedelta(days=now.weekday())
		month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

		# Basic application counts
		total_applications = self.db.query(Application).filter(Application.user_id == user_id).count()

		applications_this_week = self.db.query(Application).filter(and_(Application.user_id == user_id, Application.applied_at >= week_start)).count()

		applications_this_month = (
			self.db.query(Application).filter(and_(Application.user_id == user_id, Application.applied_at >= month_start)).count()
		)

		# Response and success rates
		applications_with_response = (
			self.db.query(Application).filter(and_(Application.user_id == user_id, Application.response_date.isnot(None))).count()
		)

		interviews = (
			self.db.query(Application)
			.filter(
				and_(
					Application.user_id == user_id,
					Application.status.in_(
						["phone_screen_scheduled", "phone_screen_completed", "interview_scheduled", "interview_completed", "final_round"]
					),
				)
			)
			.count()
		)

		offers = (
			self.db.query(Application)
			.filter(and_(Application.user_id == user_id, Application.status.in_(["offer_received", "offer_accepted"])))
			.count()
		)

		# Calculate rates
		response_rate = (applications_with_response / total_applications * 100) if total_applications > 0 else 0
		interview_rate = (interviews / total_applications * 100) if total_applications > 0 else 0
		offer_rate = (offers / total_applications * 100) if total_applications > 0 else 0

		# Response time analysis
		response_times = (
			self.db.query(func.extract("epoch", Application.response_date - Application.applied_at) / 86400)
			.filter(and_(Application.user_id == user_id, Application.response_date.isnot(None)))
			.all()
		)

		avg_response_time = None
		fastest_response = None
		if response_times:
			response_days = [rt[0] for rt in response_times if rt[0] is not None]
			if response_days:
				avg_response_time = sum(response_days) / len(response_days)
				fastest_response = int(min(response_days))

		# Weekly trend data (last 12 weeks)
		weekly_trend = self._get_weekly_application_trend(user_id, 12)

		# Status distribution
		status_distribution = self._get_status_distribution(user_id)

		# Goal tracking - get from user's active weekly application goal
		weekly_application_goal = (
			self.db.query(Goal).filter(and_(Goal.user_id == user_id, Goal.is_active == True, Goal.goal_type == "weekly_applications")).first()
		)

		weekly_goal = weekly_application_goal.target_value if weekly_application_goal else 5
		goal_completion_rate = (applications_this_week / weekly_goal * 100) if weekly_goal > 0 else 0

		# Additional goal metrics
		active_goals_count = self.db.query(Goal).filter(and_(Goal.user_id == user_id, Goal.is_active == True)).count()

		completed_goals_this_month = (
			self.db.query(Goal).filter(and_(Goal.user_id == user_id, Goal.is_completed == True, Goal.completed_at >= month_start)).count()
		)

		# Calculate current streak (consecutive days with goal progress)
		current_streak_days = self._calculate_current_streak(user_id)

		# Milestones achieved this month
		milestones_achieved_this_month = (
			self.db.query(Milestone).filter(and_(Milestone.user_id == user_id, Milestone.achievement_date >= month_start)).count()
		)

		return ProgressTrackingStats(
			total_applications=total_applications,
			applications_this_week=applications_this_week,
			applications_this_month=applications_this_month,
			response_rate=round(response_rate, 1),
			interview_rate=round(interview_rate, 1),
			offer_rate=round(offer_rate, 1),
			avg_response_time_days=round(avg_response_time, 1) if avg_response_time else None,
			fastest_response_days=fastest_response,
			weekly_application_goal=weekly_goal,
			weekly_applications_completed=applications_this_week,
			goal_completion_rate=round(goal_completion_rate, 1),
			active_goals_count=active_goals_count,
			completed_goals_this_month=completed_goals_this_month,
			current_streak_days=current_streak_days,
			milestones_achieved_this_month=milestones_achieved_this_month,
			weekly_application_trend=weekly_trend,
			status_distribution=status_distribution,
		)

	def get_document_management_summary(self, user_id: int) -> DocumentManagementResponse:
		"""Get document management summary and statistics"""

		# If Document ORM is not available in this environment, try to build a
		# document summary from the user's stored settings (if any). This keeps
		# the endpoint functional in development setups without the Document model.
		if Document is None:
			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				return DocumentManagementResponse(
					documents=[], total_count=0, total_documents=0, documents_by_type={}, total_storage_used=0, most_used_document=None
				)

			settings_docs = (user.settings or {}).get("documents", [])
			document_summaries = []
			total_storage = 0
			documents_by_type = {}
			most_used_doc = None
			max_usage = 0

			for d in settings_docs:
				summary = DocumentSummary(
					id=d.get("document_id"),
					filename=d.get("filename"),
					document_type=d.get("type"),
					file_size=d.get("file_size", 0),
					usage_count=d.get("usage_count", 0),
					last_used=d.get("last_used"),
					created_at=d.get("created_at"),
				)
				document_summaries.append(summary)
				total_storage += d.get("file_size", 0)
				documents_by_type[d.get("type")] = documents_by_type.get(d.get("type"), 0) + 1
				if d.get("usage_count", 0) > max_usage:
					max_usage = d.get("usage_count", 0)
					most_used_doc = summary

			return DocumentManagementResponse(
				documents=document_summaries,
				total_count=len(document_summaries),
				total_documents=len(document_summaries),
				documents_by_type=documents_by_type,
				total_storage_used=total_storage,
				most_used_document=most_used_doc,
			)

		# Normal path when Document model exists
		documents = self.db.query(Document).filter(Document.user_id == user_id).order_by(desc(Document.created_at)).all()

		# Convert to summary format
		document_summaries = []
		total_storage = 0
		documents_by_type = {}
		most_used_doc = None
		max_usage = 0

		for doc in documents:
			summary = DocumentSummary(
				id=doc.id,
				filename=doc.original_filename,
				document_type=doc.document_type,
				file_size=doc.file_size,
				usage_count=doc.usage_count,
				last_used=doc.last_used,
				created_at=doc.created_at,
			)
			document_summaries.append(summary)

			# Update statistics
			total_storage += doc.file_size
			documents_by_type[doc.document_type] = documents_by_type.get(doc.document_type, 0) + 1

			if doc.usage_count > max_usage:
				max_usage = doc.usage_count
				most_used_doc = summary

		return DocumentManagementResponse(
			documents=document_summaries,
			total_count=len(documents),
			total_documents=len(documents),
			documents_by_type=documents_by_type,
			total_storage_used=total_storage,
			most_used_document=most_used_doc,
		)

	def _calculate_profile_completion(self, profile_data: Dict[str, Any]) -> int:
		"""Calculate profile completion percentage"""

		# Define required fields and their weights
		fields_weights = {
			"first_name": 5,
			"last_name": 5,
			"current_title": 10,
			"years_experience": 10,
			"skills": 20,
			"location_preferences": 15,
			"career_preferences": 15,
			"career_goals": 10,
			"linkedin_url": 5,
			"education_level": 5,
		}

		total_weight = sum(fields_weights.values())
		completed_weight = 0

		for field, weight in fields_weights.items():
			value = profile_data.get(field)
			if value:
				# Check if it's a meaningful value (not empty list/dict)
				if isinstance(value, (list, dict)):
					if len(value) > 0:
						completed_weight += weight
				else:
					completed_weight += weight

		return int((completed_weight / total_weight) * 100)

	def _calculate_application_stats(self, user_id: int) -> Dict[str, Any]:
		"""Calculate application statistics for summary"""

		now = datetime.now(timezone.utc)
		month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

		total_applications = self.db.query(Application).filter(Application.user_id == user_id).count()

		applications_this_month = (
			self.db.query(Application).filter(and_(Application.user_id == user_id, Application.applied_at >= month_start)).count()
		)

		interviews_scheduled = (
			self.db.query(Application)
			.filter(
				and_(
					Application.user_id == user_id,
					Application.status.in_(
						["phone_screen_scheduled", "phone_screen_completed", "interview_scheduled", "interview_completed", "final_round"]
					),
				)
			)
			.count()
		)

		offers_received = (
			self.db.query(Application)
			.filter(and_(Application.user_id == user_id, Application.status.in_(["offer_received", "offer_accepted"])))
			.count()
		)

		success_rate = (offers_received / total_applications * 100) if total_applications > 0 else 0

		return {
			"total_applications": total_applications,
			"applications_this_month": applications_this_month,
			"interviews_scheduled": interviews_scheduled,
			"offers_received": offers_received,
			"success_rate": round(success_rate, 1),
		}

	def _get_weekly_application_trend(self, user_id: int, weeks: int) -> List[Dict[str, Any]]:
		"""Get weekly application trend data"""

		trend_data = []
		now = datetime.now(timezone.utc)

		for i in range(weeks):
			week_start = now - timedelta(weeks=i + 1)
			week_end = now - timedelta(weeks=i)

			count = (
				self.db.query(Application)
				.filter(and_(Application.user_id == user_id, Application.applied_at >= week_start, Application.applied_at < week_end))
				.count()
			)

			trend_data.append({"week_start": week_start.strftime("%Y-%m-%d"), "applications": count})

		return list(reversed(trend_data))

	def _get_status_distribution(self, user_id: int) -> Dict[str, int]:
		"""Get distribution of application statuses"""

		status_counts = (
			self.db.query(Application.status, func.count(Application.id)).filter(Application.user_id == user_id).group_by(Application.status).all()
		)

		return {status: count for status, count in status_counts}

	def _calculate_current_streak(self, user_id: int) -> int:
		"""Calculate current consecutive days with goal progress"""
		from app.models.goal import GoalProgress

		streak = 0
		current_date = datetime.now(timezone.utc).date()

		while True:
			# Check if there was progress on this date
			progress_exists = (
				self.db.query(GoalProgress).filter(and_(GoalProgress.user_id == user_id, GoalProgress.progress_date == current_date)).first()
			)

			if progress_exists:
				streak += 1
				current_date -= timedelta(days=1)
			else:
				break

		return streak
