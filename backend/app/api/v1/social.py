"""
Career Resources and Learning Endpoints

Provides endpoints for:
- Personalized career resource recommendations
- Learning paths and skill development resources
- Achievement sharing
- Resource feedback

Single-user system for Moatasim
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from app.dependencies import get_current_user
from ...core.logging import get_logger
from ...core.single_user import MOATASIM_EXPERIENCE_LEVEL, MOATASIM_SKILLS, MOATASIM_USER_ID
from ...models.user import User
from ...services.cache_service import cache_service
from ...services.career_resources_service import CareerResourcesService

router = APIRouter(prefix="/social", tags=["career-resources", "social"])
logger = get_logger(__name__)


# Pydantic models for social feed
class SocialPost(BaseModel):
	"""Social feed post creation"""

	content: str = Field(..., min_length=1, max_length=5000, description="Post content")
	post_type: str = Field(default="general", description="Type: general, achievement, milestone, job_update")
	visibility: str = Field(default="public", description="Visibility: public, private")
	tags: List[str] = Field(default_factory=list, description="Post tags")


class SocialPostResponse(BaseModel):
	"""Social feed post response"""

	id: int
	user_id: int
	content: str
	post_type: str
	visibility: str
	tags: List[str]
	likes_count: int = 0
	comments_count: int = 0
	created_at: datetime
	updated_at: datetime


class FeedItem(BaseModel):
	"""Feed item in social feed"""

	id: int
	author_id: int
	author_name: str
	content: str
	post_type: str
	tags: List[str]
	created_at: datetime
	likes_count: int
	comments_count: int
	is_liked: bool = False


# Pydantic models
class CareerResource(BaseModel):
	"""Career resource with relevance score"""

	id: str
	title: str
	description: str
	type: str = Field(..., description="Resource type: course, article, video, book, tool, certification")
	provider: str = Field(..., description="Provider/platform name")
	url: str
	skills: List[str] = Field(default_factory=list, description="Skills covered")
	difficulty: str = Field(..., description="Difficulty level: beginner, intermediate, advanced")
	duration: Optional[str] = Field(None, description="Estimated time: '2 hours', '4 weeks', etc.")
	price: str = Field(..., description="Price: free, paid, $49, etc.")
	rating: Optional[float] = Field(None, ge=0, le=5, description="Rating 0-5")
	relevance_score: int = Field(ge=0, le=100, description="Relevance score 0-100")
	image_url: Optional[str] = None


class ResourceBookmark(BaseModel):
	"""Bookmark a resource for later"""

	resource_id: str = Field(..., description="ID of resource to bookmark")


class ResourceFeedback(BaseModel):
	"""Feedback on a career resource"""

	is_helpful: bool = Field(..., description="Whether resource was helpful")
	completed: bool = Field(default=False, description="Whether user completed the resource")
	rating: Optional[float] = Field(None, ge=0, le=5, description="User's rating 0-5")
	notes: Optional[str] = Field(None, description="Optional notes or review")
	time_spent_hours: Optional[float] = Field(None, ge=0, description="Hours spent on resource")
	would_recommend: Optional[bool] = Field(None, description="Would recommend to others")


class BookmarkUpdate(BaseModel):
	"""Update bookmark details"""

	notes: Optional[str] = None
	priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
	status: Optional[str] = Field(None, pattern="^(to_learn|in_progress|completed|archived)$")
	progress_percentage: Optional[int] = Field(None, ge=0, le=100)


class ResourceStats(BaseModel):
	"""User's learning statistics"""

	total_bookmarks: int
	completed_resources: int
	in_progress: int
	to_learn: int
	total_feedback: int
	average_rating: Optional[float]
	total_learning_hours: float


# Social Feed Endpoints
@router.get("/feed", response_model=List[FeedItem])
async def get_social_feed(
	limit: int = Query(20, ge=1, le=100, description="Number of feed items"),
	offset: int = Query(0, ge=0, description="Offset for pagination"),
	feed_type: Optional[str] = Query(None, description="Filter: general, achievement, milestone, job_update"),
	db: AsyncSession = Depends(get_db),
):
	"""
	Get social feed with career updates, achievements, and community posts.

	Returns personalized feed including:
	- Job application milestones
	- Skill achievements
	- Career progress updates
	- Community posts
	"""
	try:
		from ...models.feedback import Feedback
		from ...models.user import User

		# For single-user system, create feed from feedback and activity
		# This serves as a personal timeline/journal
		query = select(Feedback).order_by(Feedback.created_at.desc()).limit(limit).offset(offset)

		if feed_type:
			query = query.where(Feedback.category == feed_type)

		result = await db.execute(query)
		feedbacks = result.scalars().all()

		# Transform feedback into feed items
		feed_items = []
		for fb in feedbacks:
			# Get user info
			user_result = await db.execute(select(User).where(User.id == fb.user_id))
			user = user_result.scalar_one_or_none()

			feed_items.append(
				FeedItem(
					id=fb.id,
					author_id=fb.user_id,
					author_name=user.username if user else "User",
					content=fb.description or fb.title,
					post_type=fb.category or "general",
					tags=[fb.category] if fb.category else [],
					created_at=fb.created_at,
					likes_count=0,  # Can be extended with likes table
					comments_count=0,  # Can be extended with comments table
					is_liked=False,
				)
			)

		logger.info(f"Retrieved {len(feed_items)} feed items for user {MOATASIM_USER_ID}")
		return feed_items

	except Exception as e:
		logger.error(f"Error retrieving social feed: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve social feed: {e!s}")


@router.post("/post", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
async def create_social_post(
	post: SocialPost,
	db: AsyncSession = Depends(get_db),
):
	"""
	Create a new social feed post.

	Share career achievements, milestones, or general updates.
	Posts can be tagged and categorized for better organization.
	"""
	try:
		from ...models.feedback import Feedback, FeedbackPriority, FeedbackStatus, FeedbackType

		# Map post_type to FeedbackType
		feedback_type_map = {
			"achievement": FeedbackType.GENERAL,
			"milestone": FeedbackType.GENERAL,
			"job_update": FeedbackType.JOB_RECOMMENDATION,
			"general": FeedbackType.GENERAL,
		}

		# Create feedback entry as social post (using feedback table for now)
		new_post = Feedback(
			user_id=MOATASIM_USER_ID,
			type=feedback_type_map.get(post.post_type, FeedbackType.GENERAL),
			title=post.post_type,
			description=post.content,
			status=FeedbackStatus.OPEN,
			priority=FeedbackPriority.LOW,
			created_at=datetime.utcnow(),
			updated_at=datetime.utcnow(),
		)

		db.add(new_post)
		await db.commit()
		await db.refresh(new_post)

		logger.info(f"Created social post {new_post.id} for user {MOATASIM_USER_ID}")

		return SocialPostResponse(
			id=new_post.id,
			user_id=new_post.user_id,
			content=post.content,
			post_type=post.post_type,
			visibility=post.visibility,
			tags=post.tags,
			likes_count=0,
			comments_count=0,
			created_at=new_post.created_at,
			updated_at=new_post.updated_at,
		)

	except Exception as e:
		logger.error(f"Error creating social post: {e}")
		await db.rollback()
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create social post: {e!s}")


@router.get("/me/resources", response_model=List[Dict])
async def get_career_resources(
	resource_type: Optional[str] = Query(None, description="Filter by type: course, article, video, book, tool, certification"),
	skill: Optional[str] = Query(None, description="Filter by skill"),
	difficulty: Optional[str] = Query(None, description="Filter by difficulty: beginner, intermediate, advanced"),
	limit: int = Query(20, ge=1, le=100, description="Number of resources to return"),
	offset: int = Query(0, ge=0, description="Offset for pagination"),
	db: AsyncSession = Depends(get_db),
):
	"""
	Get personalized career resource recommendations.

	Returns learning resources tailored to user's skills and career goals:
	- Online courses (Coursera, Udemy, Pluralsight, etc.)
	- Technical articles and tutorials
	- YouTube videos and channels
	- Books and documentation
	- Tools and frameworks
	- Professional certifications

	Uses intelligent matching based on:
	- User's skills and skill gaps
	- Experience level and career goals
	- Previous feedback and completions
	- Resource popularity and ratings
	"""
	try:
		service = CareerResourcesService(db)
		resources = await service.get_personalized_resources(
			user_id=MOATASIM_USER_ID,
			user_skills=MOATASIM_SKILLS,
			experience_level=MOATASIM_EXPERIENCE_LEVEL,
			resource_type=resource_type,
			skill=skill,
			difficulty=difficulty,
			limit=limit,
			offset=offset,
		)

		logger.info(f"Returned {len(resources)} personalized resources for Moatasim")
		return resources

	except Exception as e:
		logger.error(f"Error getting career resources: {e}", exc_info=True)
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve career resources: {e!s}")


@router.post("/me/bookmarks", status_code=status.HTTP_201_CREATED)
async def bookmark_resource(
	bookmark: ResourceBookmark,
	db: AsyncSession = Depends(get_db),
):
	"""
	Bookmark a career resource for later.

	Creates a bookmark for tracking learning resources.
	Allows organizing resources by priority and status.
	"""
	try:
		service = CareerResourcesService(db)
		result = await service.create_bookmark(
			user_id=MOATASIM_USER_ID,
			resource_id=bookmark.resource_id,
		)

		return {
			"message": "Resource bookmarked successfully",
			"bookmark_id": str(result.id),
			"user_id": MOATASIM_USER_ID,
			"resource_id": bookmark.resource_id,
			"status": result.status,
			"created_at": result.created_at.isoformat() if result.created_at else None,
		}

	except ValueError as e:
		logger.warning(f"Bookmark validation error: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.error(f"Error bookmarking resource: {e}", exc_info=True)
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to bookmark resource")


@router.post("/resources/{resource_id}/feedback", status_code=status.HTTP_201_CREATED)
async def submit_resource_feedback(
	resource_id: str,
	feedback: ResourceFeedback,
	db: AsyncSession = Depends(get_db),
):
	"""
	Submit feedback on a career resource.

	Tracks resource helpfulness, completion, and ratings.
	Used to improve recommendations and help other users.

	Feedback contributes to:
	- Personalized recommendation refinement
	- Resource quality metrics
	- Learning progress tracking
	"""
	try:
		service = CareerResourcesService(db)
		result = await service.submit_feedback(
			user_id=MOATASIM_USER_ID,
			resource_id=resource_id,
			is_helpful=feedback.is_helpful,
			completed=feedback.completed,
			rating=feedback.rating,
			notes=feedback.notes,
			time_spent_hours=feedback.time_spent_hours,
			would_recommend=feedback.would_recommend,
		)

		status_message = "completed and reviewed" if feedback.completed else "reviewed"

		return {
			"message": f"Resource {status_message} successfully",
			"feedback_id": str(result.id),
			"resource_id": resource_id,
			"is_helpful": result.is_helpful,
			"completed": result.completed,
			"rating": result.rating,
			"created_at": result.created_at.isoformat() if result.created_at else None,
		}

	except ValueError as e:
		logger.warning(f"Feedback validation error: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.error(f"Error submitting resource feedback: {e}", exc_info=True)
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit resource feedback")


@router.get("/me/bookmarks", response_model=List[Dict])
async def get_user_bookmarks(
	resource_type: Optional[str] = Query(None, description="Filter by resource type"),
	status: Optional[str] = Query(None, description="Filter by status: to_learn, in_progress, completed, archived"),
	db: AsyncSession = Depends(get_db),
):
	"""
	Get user's bookmarked resources.

	Returns all bookmarked resources with their details and progress status.
	Supports filtering by resource type and bookmark status.
	"""
	try:
		service = CareerResourcesService(db)
		bookmarks = await service.get_bookmarks(
			user_id=MOATASIM_USER_ID,
			resource_type=resource_type,
			status=status,
		)

		logger.info(f"Retrieved {len(bookmarks)} bookmarks for Moatasim")
		return bookmarks

	except Exception as e:
		logger.error(f"Error retrieving bookmarks: {e}", exc_info=True)
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve bookmarks")


@router.patch("/me/bookmarks/{resource_id}")
async def update_bookmark(
	resource_id: str,
	update: BookmarkUpdate,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Update bookmark details and progress.

	Allows updating:
	- Notes and priority
	- Status (to_learn, in_progress, completed, archived)
	- Progress percentage
	"""
	try:
		service = CareerResourcesService(db)
		result = await service.update_bookmark(
			user_id=current_user.id,
			resource_id=resource_id,
			notes=update.notes,
			priority=update.priority,
			status=update.status,
			progress_percentage=update.progress_percentage,
		)

		return {
			"message": "Bookmark updated successfully",
			"bookmark_id": str(result.id),
			"progress_percentage": result.progress_percentage,
			"status": result.status,
			"updated_at": result.updated_at.isoformat() if result.updated_at else None,
		}

	except ValueError as e:
		logger.warning(f"Bookmark update validation error: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.error(f"Error updating bookmark: {e}", exc_info=True)
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update bookmark")


@router.get("/me/stats", response_model=ResourceStats)
async def get_user_learning_stats(
	db: AsyncSession = Depends(get_db),
):
	"""
	Get user's learning statistics and progress.

	Returns comprehensive metrics including:
	- Total bookmarks by status
	- Completed resources
	- Average ratings given
	- Total learning hours
	"""
	try:
		service = CareerResourcesService(db)
		stats = await service.get_user_stats(MOATASIM_USER_ID)

		logger.info(f"Retrieved learning stats for Moatasim")
		return ResourceStats(**stats)

	except Exception as e:
		logger.error(f"Error getting user stats: {e}", exc_info=True)
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve learning statistics")
