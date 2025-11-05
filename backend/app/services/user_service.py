"""Production-grade User Service with comprehensive user management capabilities.

Handles user CRUD operations, profile management, preferences, analytics integration,
and user activity tracking with proper error handling and logging.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UserProfile(BaseModel):
	"""User profile schema with comprehensive fields"""

	user_id: int
	username: str | None = None
	email: str | None = None
	title: str | None = None
	skills: List[str] = Field(default_factory=list)
	experience_years: int | None = None
	experience_level: str | None = None
	preferred_locations: List[str] = Field(default_factory=list)
	preferred_industries: List[str] = Field(default_factory=list)
	salary_expectation: str | None = None
	job_types: List[str] = Field(default_factory=list)
	daily_application_goal: int = 10
	is_admin: bool = False
	oauth_provider: str | None = None
	profile_picture_url: str | None = None
	created_at: datetime | None = None
	updated_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)


class UserPreferences(BaseModel):
	"""User notification and application preferences"""

	email_notifications: bool = True
	push_notifications: bool = True
	morning_briefing: bool = True
	evening_summary: bool = True
	job_alerts: bool = True
	application_reminders: bool = True
	weekly_analytics: bool = True
	notification_frequency: str = "daily"  # immediate, daily, weekly

	model_config = ConfigDict(from_attributes=True)


class UserStats(BaseModel):
	"""User statistics and activity metrics"""

	total_applications: int = 0
	active_applications: int = 0
	interviews_scheduled: int = 0
	offers_received: int = 0
	total_jobs_saved: int = 0
	profile_views: int = 0
	search_history_count: int = 0
	last_active: datetime | None = None

	model_config = ConfigDict(from_attributes=True)


class UserService:
	"""
	Comprehensive user service for managing user data, profiles, preferences, and analytics.

	Features:
	- Full CRUD operations with database persistence
	- User profile management
	- Preference handling
	- Activity tracking
	- Statistics aggregation
	- Error handling and logging
	- Transaction management
	"""

	def __init__(self, db: Session) -> None:
		"""
		Initialize user service with database session.

		Args:
		    db: SQLAlchemy database session
		"""
		if db is None:
			raise ValueError("Database session is required for UserService")
		self.db = db
		logger.info("UserService initialized")

	async def create_user_profile(self, profile_data: Dict[str, Any]) -> UserProfile:
		"""
		Create a new user profile with validation and database persistence.

		Args:
		    profile_data: Dictionary containing user profile information

		Returns:
		    UserProfile: Created user profile

		Raises:
		    IntegrityError: If user already exists or constraints violated
		    ValueError: If required fields are missing
		"""
		try:
			from ..models.user import User

			# Validate required fields
			if not profile_data.get("user_id") and not (profile_data.get("email") or profile_data.get("username")):
				raise ValueError("Either user_id or email/username is required")

			# Check if user already exists
			if profile_data.get("user_id"):
				existing = self.db.query(User).filter(User.id == profile_data["user_id"]).first()
				if existing:
					logger.warning(f"User {profile_data['user_id']} already exists")
					return UserProfile.model_validate(existing)

			# Create new user
			user = User(
				username=profile_data.get("username", f"user_{profile_data.get('user_id', 'temp')}"),
				email=profile_data.get("email"),
				skills=profile_data.get("skills", []),
				preferred_locations=profile_data.get("preferred_locations", []),
				experience_level=profile_data.get("experience_level"),
				daily_application_goal=profile_data.get("daily_application_goal", 10),
				is_admin=profile_data.get("is_admin", False),
				oauth_provider=profile_data.get("oauth_provider"),
				profile_picture_url=profile_data.get("profile_picture_url"),
				created_at=datetime.now(timezone.utc),
				updated_at=datetime.now(timezone.utc),
			)

			self.db.add(user)
			self.db.commit()
			self.db.refresh(user)

			logger.info(f"Created user profile for user {user.id}")
			return UserProfile.model_validate(user)

		except IntegrityError as e:
			self.db.rollback()
			logger.error(f"Integrity error creating user profile: {e}")
			raise
		except SQLAlchemyError as e:
			self.db.rollback()
			logger.error(f"Database error creating user profile: {e}")
			raise
		except Exception as e:
			self.db.rollback()
			logger.error(f"Unexpected error creating user profile: {e}")
			raise

	async def get_user_profile(self, user_id: int) -> UserProfile | None:
		"""
		Retrieve user profile by ID.

		Args:
		    user_id: User ID

		Returns:
		    UserProfile or None if not found
		"""
		try:
			from ..models.user import User

			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				logger.warning(f"User {user_id} not found")
				return None

			return UserProfile.model_validate(user)
		except Exception as e:
			logger.error(f"Error retrieving user profile {user_id}: {e}")
			return None

	async def update_user_profile(self, user_id: int, updates: Dict[str, Any]) -> UserProfile | None:
		"""
		Update user profile with validation.

		Args:
		    user_id: User ID
		    updates: Dictionary of fields to update

		Returns:
		    Updated UserProfile or None if not found
		"""
		try:
			from ..models.user import User

			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				logger.warning(f"User {user_id} not found for update")
				return None

			# Update allowed fields
			allowed_fields = {
				"username",
				"email",
				"skills",
				"preferred_locations",
				"experience_level",
				"daily_application_goal",
				"profile_picture_url",
			}

			for key, value in updates.items():
				if key in allowed_fields and hasattr(user, key):
					setattr(user, key, value)

			user.updated_at = datetime.now(timezone.utc)

			self.db.commit()
			self.db.refresh(user)

			logger.info(f"Updated user profile for user {user_id}")
			return UserProfile.model_validate(user)

		except SQLAlchemyError as e:
			self.db.rollback()
			logger.error(f"Database error updating user {user_id}: {e}")
			return None
		except Exception as e:
			self.db.rollback()
			logger.error(f"Error updating user {user_id}: {e}")
			return None

	async def delete_user(self, user_id: int) -> bool:
		"""
		Delete user and all associated data (cascade).

		Args:
		    user_id: User ID

		Returns:
		    bool: True if deleted, False if not found
		"""
		try:
			from ..models.user import User

			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				logger.warning(f"User {user_id} not found for deletion")
				return False

			self.db.delete(user)
			self.db.commit()

			logger.info(f"Deleted user {user_id}")
			return True

		except SQLAlchemyError as e:
			self.db.rollback()
			logger.error(f"Error deleting user {user_id}: {e}")
			return False

	async def get_user_stats(self, user_id: int) -> UserStats:
		"""
		Get comprehensive user statistics.

		Args:
		    user_id: User ID

		Returns:
		    UserStats with aggregated metrics
		"""
		try:
			from ..models.application import Application
			from ..models.job import Job
			from ..models.user import User

			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				logger.warning(f"User {user_id} not found for stats")
				return UserStats()

			# Aggregate statistics
			total_apps = self.db.query(func.count(Application.id)).filter(Application.user_id == user_id).scalar() or 0

			active_apps = (
				self.db.query(func.count(Application.id))
				.filter(and_(Application.user_id == user_id, Application.status.in_(["applied", "interviewing"])))
				.scalar()
				or 0
			)

			total_jobs = self.db.query(func.count(Job.id)).filter(Job.user_id == user_id).scalar() or 0

			return UserStats(total_applications=total_apps, active_applications=active_apps, total_jobs_saved=total_jobs, last_active=user.updated_at)

		except Exception as e:
			logger.error(f"Error getting stats for user {user_id}: {e}")
			return UserStats()

	async def search_users(
		self, query: str | None = None, skills: List[str] | None = None, experience_level: str | None = None, limit: int = 50, offset: int = 0
	) -> List[UserProfile]:
		"""
		Search users with filters.

		Args:
		    query: Text search in username/email
		    skills: Filter by skills
		    experience_level: Filter by experience level
		    limit: Maximum results
		    offset: Pagination offset

		Returns:
		    List of matching UserProfile objects
		"""
		try:
			from ..models.user import User

			filters = []

			if query:
				filters.append(or_(User.username.ilike(f"%{query}%"), User.email.ilike(f"%{query}%")))

			if experience_level:
				filters.append(User.experience_level == experience_level)

			query_obj = self.db.query(User)

			if filters:
				query_obj = query_obj.filter(and_(*filters))

			# Skills filter (JSON contains)
			if skills:
				for skill in skills:
					query_obj = query_obj.filter(User.skills.contains([skill]))

			users = query_obj.limit(limit).offset(offset).all()

			return [UserProfile.model_validate(u) for u in users]

		except Exception as e:
			logger.error(f"Error searching users: {e}")
			return []

	async def record_activity(self, user_id: int, activity_type: str, metadata: Dict[str, Any] | None = None) -> bool:
		"""
		Record user activity for analytics.

		Args:
		    user_id: User ID
		    activity_type: Type of activity (login, job_view, application, etc.)
		    metadata: Additional activity data

		Returns:
		    bool: True if recorded successfully
		"""
		try:
			from ..models.user import User

			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				return False

			user.updated_at = datetime.now(timezone.utc)
			self.db.commit()

			logger.debug(f"Recorded {activity_type} activity for user {user_id}")
			return True

		except Exception as e:
			self.db.rollback()
			logger.error(f"Error recording activity for user {user_id}: {e}")
			return False

	async def get_user_by_email(self, email: str) -> UserProfile | None:
		"""Get user by email address."""
		try:
			from ..models.user import User

			user = self.db.query(User).filter(User.email == email).first()
			if not user:
				return None

			return UserProfile.model_validate(user)
		except Exception as e:
			logger.error(f"Error retrieving user by email {email}: {e}")
			return None

	async def get_user_by_oauth(self, provider: str, oauth_id: str) -> UserProfile | None:
		"""Get user by OAuth provider and ID."""
		try:
			from ..models.user import User

			user = self.db.query(User).filter(and_(User.oauth_provider == provider, User.oauth_id == oauth_id)).first()

			if not user:
				return None

			return UserProfile.model_validate(user)
		except Exception as e:
			logger.error(f"Error retrieving user by OAuth {provider}/{oauth_id}: {e}")
			return None
