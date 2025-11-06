"""
Career Resources Service

Enterprise-grade service for managing career resources, bookmarks, and learning paths.
Single-user system for Moatasim.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..core.single_user import MOATASIM_USER_ID
from ..models.career_resources import (
	CareerResourceModel,
	LearningPath,
	LearningPathEnrollment,
	ResourceBookmarkModel,
	ResourceFeedbackModel,
	ResourceView,
)
from ..services.cache_service import cache_service

logger = get_logger(__name__)


class CareerResourcesService:
	"""Service for managing career resources and learning paths."""

	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_personalized_resources(
		self,
		user_id: int = MOATASIM_USER_ID,
		user_skills: Optional[List[str]] = None,
		experience_level: str = "senior",
		resource_type: Optional[str] = None,
		skill: Optional[str] = None,
		difficulty: Optional[str] = None,
		limit: int = 20,
		offset: int = 0,
	) -> List[Dict]:
		"""
		Get personalized career resources for a user.

		Uses multiple signals:
		- User's skills and preferences
		- Previous feedback and completions
		- Resource popularity and ratings
		- Skill gap analysis
		"""
		user_skills = user_skills or []

		# Build cache key
		cache_key = f"resources:user:{user_id}:type:{resource_type}:skill:{skill}:diff:{difficulty}:limit:{limit}:offset:{offset}"
		cached = cache_service.get(cache_key)
		if cached:
			logger.info(f"Cache hit for resources: user {user_id}")
			return cached

		try:
			# Build query
			stmt = select(CareerResourceModel).where(CareerResourceModel.is_active == True)

			# Apply filters
			if resource_type:
				stmt = stmt.where(CareerResourceModel.type == resource_type)
			if skill:
				stmt = stmt.where(CareerResourceModel.skills.contains([skill]))
			if difficulty:
				stmt = stmt.where(CareerResourceModel.difficulty == difficulty)

			# Get resources
			result = await self.db.execute(stmt)
			resources = result.scalars().all()

			# Calculate personalized relevance scores
			scored_resources = []

			for resource in resources:
				score = await self._calculate_relevance_score(resource, user_id, user_skills, experience_level)
				resource_dict = {
					"id": resource.id,
					"title": resource.title,
					"description": resource.description,
					"type": resource.type,
					"provider": resource.provider,
					"url": resource.url,
					"skills": resource.skills,
					"difficulty": resource.difficulty,
					"duration": resource.duration,
					"price": resource.price,
					"rating": resource.rating,
					"relevance_score": score,
					"image_url": resource.image_url,
					"tags": resource.tags,
					"prerequisites": resource.prerequisites,
					"learning_outcomes": resource.learning_outcomes,
				}
				scored_resources.append(resource_dict)

			# Sort by relevance
			scored_resources.sort(key=lambda x: x["relevance_score"], reverse=True)

			# Apply pagination
			paginated = scored_resources[offset : offset + limit]

			# Cache for 6 hours
			cache_service.set(cache_key, paginated, ttl=21600)

			logger.info(f"Generated {len(paginated)} personalized resources for user {user_id}")
			return paginated

		except Exception as e:
			logger.error(f"Error getting personalized resources: {e}", exc_info=True)
			raise

	async def _calculate_relevance_score(
		self, resource: CareerResourceModel, user_id: int, user_skills: List[str], experience_level: str = "senior"
	) -> int:
		"""
		Calculate personalized relevance score for a resource.

		Factors:
		- Skill overlap (40 points)
		- User's experience level match (20 points)
		- Resource rating (15 points)
		- Previous feedback (15 points)
		- Completion rate (10 points)
		"""
		score = resource.base_relevance_score or 50

		# Skill overlap bonus (max +40)
		if user_skills and resource.skills:
			matching_skills = set(user_skills) & set(resource.skills)
			skill_overlap_ratio = len(matching_skills) / len(resource.skills)
			score += int(skill_overlap_ratio * 40)

		# Experience level match (max +20)
		difficulty_match = {
			("entry", "beginner"): 20,
			("entry", "intermediate"): 10,
			("mid", "intermediate"): 20,
			("mid", "beginner"): 15,
			("mid", "advanced"): 10,
			("senior", "advanced"): 20,
			("senior", "intermediate"): 15,
		}
		score += difficulty_match.get((experience_level, resource.difficulty), 0)

		# Rating bonus (max +15)
		if resource.rating:
			score += int((resource.rating / 5.0) * 15)

		# Check user's previous feedback
		stmt = select(ResourceFeedbackModel).where(and_(ResourceFeedbackModel.user_id == user_id, ResourceFeedbackModel.resource_id == resource.id))
		result = await self.db.execute(stmt)
		feedback = result.scalar_one_or_none()

		if feedback:
			# Boost if user found similar resources helpful
			if feedback.is_helpful:
				score += 15
			# Penalize if already completed
			if feedback.completed:
				score -= 30

		# Cap at 100
		return min(score, 100)

	async def create_bookmark(self, user_id: int, resource_id: str, notes: Optional[str] = None, priority: str = "medium") -> ResourceBookmarkModel:
		"""Create a bookmark for a resource."""
		try:
			# Check if bookmark already exists
			stmt = select(ResourceBookmarkModel).where(
				and_(ResourceBookmarkModel.user_id == user_id, ResourceBookmarkModel.resource_id == resource_id)
			)
			result = await self.db.execute(stmt)
			existing = result.scalar_one_or_none()

			if existing:
				# Update existing bookmark
				existing.notes = notes if notes else existing.notes
				existing.priority = priority
				existing.updated_at = datetime.now(timezone.utc)
				await self.db.commit()
				await self.db.refresh(existing)
				logger.info(f"Updated bookmark: user {user_id}, resource {resource_id}")
				return existing

			# Create new bookmark
			bookmark = ResourceBookmarkModel(user_id=user_id, resource_id=resource_id, notes=notes, priority=priority, status="to_learn")
			self.db.add(bookmark)
			await self.db.commit()
			await self.db.refresh(bookmark)

			# Invalidate cache
			self._invalidate_bookmark_cache(user_id)

			logger.info(f"Created bookmark: user {user_id}, resource {resource_id}")
			return bookmark

		except Exception as e:
			await self.db.rollback()
			logger.error(f"Error creating bookmark: {e}", exc_info=True)
			raise

	async def get_bookmarks(self, user_id: int, resource_type: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
		"""Get user's bookmarked resources."""
		cache_key = f"bookmarks:user:{user_id}:type:{resource_type}:status:{status}"
		cached = cache_service.get(cache_key)
		if cached:
			return cached

		try:
			# Build query
			stmt = (
				select(ResourceBookmarkModel, CareerResourceModel)
				.join(CareerResourceModel, ResourceBookmarkModel.resource_id == CareerResourceModel.id)
				.where(ResourceBookmarkModel.user_id == user_id)
				.order_by(desc(ResourceBookmarkModel.created_at))
			)

			# Apply filters
			if resource_type:
				stmt = stmt.where(CareerResourceModel.type == resource_type)
			if status:
				stmt = stmt.where(ResourceBookmarkModel.status == status)

			result = await self.db.execute(stmt)
			rows = result.all()

			bookmarks = []
			for bookmark, resource in rows:
				bookmarks.append(
					{
						"bookmark_id": str(bookmark.id),
						"resource": {
							"id": resource.id,
							"title": resource.title,
							"description": resource.description,
							"type": resource.type,
							"provider": resource.provider,
							"url": resource.url,
							"skills": resource.skills,
							"difficulty": resource.difficulty,
							"duration": resource.duration,
							"price": resource.price,
							"rating": resource.rating,
							"image_url": resource.image_url,
						},
						"bookmark_details": {
							"notes": bookmark.notes,
							"priority": bookmark.priority,
							"status": bookmark.status,
							"progress_percentage": bookmark.progress_percentage,
							"created_at": bookmark.created_at.isoformat() if bookmark.created_at else None,
							"completed_at": bookmark.completed_at.isoformat() if bookmark.completed_at else None,
						},
					}
				)

			# Cache for 1 hour
			cache_service.set(cache_key, bookmarks, ttl=3600)
			return bookmarks

		except Exception as e:
			logger.error(f"Error getting bookmarks: {e}", exc_info=True)
			raise

	async def submit_feedback(
		self,
		user_id: int,
		resource_id: str,
		is_helpful: bool,
		completed: bool = False,
		rating: Optional[float] = None,
		notes: Optional[str] = None,
		time_spent_hours: Optional[float] = None,
		would_recommend: Optional[bool] = None,
	) -> ResourceFeedbackModel:
		"""Submit feedback on a resource."""
		try:
			# Check if feedback already exists
			stmt = select(ResourceFeedbackModel).where(
				and_(ResourceFeedbackModel.user_id == user_id, ResourceFeedbackModel.resource_id == resource_id)
			)
			result = await self.db.execute(stmt)
			existing = result.scalar_one_or_none()

			now = datetime.now(timezone.utc)

			if existing:
				# Update existing feedback
				existing.is_helpful = is_helpful
				existing.completed = completed
				existing.rating = rating if rating is not None else existing.rating
				existing.notes = notes if notes else existing.notes
				existing.time_spent_hours = time_spent_hours if time_spent_hours is not None else existing.time_spent_hours
				existing.would_recommend = would_recommend if would_recommend is not None else existing.would_recommend
				existing.updated_at = now
				if completed and not existing.completed_at:
					existing.completed_at = now
				await self.db.commit()
				await self.db.refresh(existing)
				logger.info(f"Updated feedback: user {user_id}, resource {resource_id}")
				return existing

			# Create new feedback
			feedback = ResourceFeedbackModel(
				user_id=user_id,
				resource_id=resource_id,
				is_helpful=is_helpful,
				completed=completed,
				rating=rating,
				notes=notes,
				time_spent_hours=time_spent_hours,
				would_recommend=would_recommend,
				completed_at=now if completed else None,
			)
			self.db.add(feedback)

			# Update bookmark if it exists
			if completed:
				stmt = select(ResourceBookmarkModel).where(
					and_(ResourceBookmarkModel.user_id == user_id, ResourceBookmarkModel.resource_id == resource_id)
				)
				result = await self.db.execute(stmt)
				bookmark = result.scalar_one_or_none()
				if bookmark:
					bookmark.status = "completed"
					bookmark.progress_percentage = 100
					bookmark.completed_at = now

			await self.db.commit()
			await self.db.refresh(feedback)

			# Invalidate caches
			self._invalidate_feedback_cache(user_id, resource_id)

			logger.info(f"Created feedback: user {user_id}, resource {resource_id}, helpful={is_helpful}, completed={completed}")
			return feedback

		except Exception as e:
			await self.db.rollback()
			logger.error(f"Error submitting feedback: {e}", exc_info=True)
			raise

	async def track_resource_view(
		self, user_id: int, resource_id: str, clicked_through: bool = False, source: str = "recommendation"
	) -> ResourceView:
		"""Track when a user views a resource."""
		try:
			view = ResourceView(user_id=user_id, resource_id=resource_id, clicked_through=clicked_through, source=source)
			self.db.add(view)
			await self.db.commit()
			await self.db.refresh(view)
			logger.debug(f"Tracked view: user {user_id}, resource {resource_id}, source={source}")
			return view
		except Exception as e:
			await self.db.rollback()
			logger.error(f"Error tracking view: {e}", exc_info=True)
			raise

	async def get_user_stats(self, user_id: int) -> Dict:
		"""Get user's learning statistics."""
		try:
			# Total bookmarks
			stmt = select(func.count(ResourceBookmarkModel.id)).where(ResourceBookmarkModel.user_id == user_id)
			result = await self.db.execute(stmt)
			total_bookmarks = result.scalar() or 0

			# Completed resources
			stmt = select(func.count(ResourceBookmarkModel.id)).where(
				and_(ResourceBookmarkModel.user_id == user_id, ResourceBookmarkModel.status == "completed")
			)
			result = await self.db.execute(stmt)
			completed = result.scalar() or 0

			# In progress
			stmt = select(func.count(ResourceBookmarkModel.id)).where(
				and_(ResourceBookmarkModel.user_id == user_id, ResourceBookmarkModel.status == "in_progress")
			)
			result = await self.db.execute(stmt)
			in_progress = result.scalar() or 0

			# Total feedback given
			stmt = select(func.count(ResourceFeedbackModel.id)).where(ResourceFeedbackModel.user_id == user_id)
			result = await self.db.execute(stmt)
			total_feedback = result.scalar() or 0

			# Average rating given
			stmt = select(func.avg(ResourceFeedbackModel.rating)).where(
				and_(ResourceFeedbackModel.user_id == user_id, ResourceFeedbackModel.rating.isnot(None))
			)
			result = await self.db.execute(stmt)
			avg_rating = result.scalar()

			# Total time spent
			stmt = select(func.sum(ResourceFeedbackModel.time_spent_hours)).where(
				and_(ResourceFeedbackModel.user_id == user_id, ResourceFeedbackModel.time_spent_hours.isnot(None))
			)
			result = await self.db.execute(stmt)
			total_hours = result.scalar() or 0

			return {
				"total_bookmarks": total_bookmarks,
				"completed_resources": completed,
				"in_progress": in_progress,
				"to_learn": total_bookmarks - completed - in_progress,
				"total_feedback": total_feedback,
				"average_rating": float(avg_rating) if avg_rating else None,
				"total_learning_hours": float(total_hours),
			}

		except Exception as e:
			logger.error(f"Error getting user stats: {e}", exc_info=True)
			raise

	async def update_bookmark_progress(self, user_id: int, resource_id: str, progress_percentage: int) -> ResourceBookmarkModel:
		"""Update progress on a bookmarked resource."""
		try:
			stmt = select(ResourceBookmarkModel).where(
				and_(ResourceBookmarkModel.user_id == user_id, ResourceBookmarkModel.resource_id == resource_id)
			)
			result = await self.db.execute(stmt)
			bookmark = result.scalar_one_or_none()

			if not bookmark:
				raise ValueError(f"Bookmark not found for user {user_id}, resource {resource_id}")

			bookmark.progress_percentage = min(progress_percentage, 100)
			bookmark.updated_at = datetime.now(timezone.utc)

			# Auto-update status based on progress
			if progress_percentage == 0:
				bookmark.status = "to_learn"
			elif progress_percentage < 100:
				bookmark.status = "in_progress"
			else:
				bookmark.status = "completed"
				bookmark.completed_at = datetime.now(timezone.utc)

			await self.db.commit()
			await self.db.refresh(bookmark)

			self._invalidate_bookmark_cache(user_id)
			return bookmark

		except Exception as e:
			await self.db.rollback()
			logger.error(f"Error updating bookmark progress: {e}", exc_info=True)
			raise

	def _invalidate_bookmark_cache(self, user_id: int):
		"""Invalidate all bookmark-related caches for a user."""
		patterns = [f"bookmarks:user:{user_id}:*", f"resources:user:{user_id}:*"]
		for pattern in patterns:
			cache_service.delete_pattern(pattern)

	def _invalidate_feedback_cache(self, user_id: int, resource_id: str):
		"""Invalidate feedback-related caches."""
		patterns = [f"resources:user:{user_id}:*", f"feedback:{resource_id}:*"]
		for pattern in patterns:
			cache_service.delete_pattern(pattern)
