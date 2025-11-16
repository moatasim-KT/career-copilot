"""
Feedback and onboarding API endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.feedback import FeedbackStatus
from app.models.user import User
from app.schemas.feedback import (
	FeatureHighlight,
	FeedbackCreate,
	FeedbackResponse,
	FeedbackUpdate,
	FeedbackVoteCreate,
	HelpArticleResponse,
	HelpArticleSummary,
	HelpArticleVoteCreate,
	HelpSearchRequest,
	HelpSearchResponse,
	OnboardingProgressResponse,
	OnboardingProgressUpdate,
	Tutorial,
)
from app.services.feedback_service import FeedbackService, HelpService, OnboardingService

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter()


# Feedback endpoints
@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(feedback_data: FeedbackCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Create new feedback item"""
	feedback_service = FeedbackService(db)
	feedback = await feedback_service.create_feedback(current_user.id, feedback_data)

	# Get feedback with vote counts
	feedback_with_votes = await feedback_service.get_feedback_with_votes(feedback.id, current_user.id)

	return FeedbackResponse(
		id=feedback.id,
		user_id=feedback.user_id,
		type=feedback.type,
		priority=feedback.priority,
		status=feedback.status,
		title=feedback.title,
		description=feedback.description,
		page_url=feedback.page_url,
		created_at=feedback.created_at,
		updated_at=feedback.updated_at,
		resolved_at=feedback.resolved_at,
		admin_response=feedback.admin_response,
		vote_count=feedback_with_votes["vote_count"],
		user_vote=feedback_with_votes["user_vote"],
	)


@router.get("/feedback", response_model=List[FeedbackResponse])
async def get_user_feedback(
	status_filter: Optional[FeedbackStatus] = Query(None, alias="status"),
	limit: int = Query(50, ge=1, le=100),
	offset: int = Query(0, ge=0),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""Get user's feedback items

	Note: FeedbackService currently uses synchronous queries (SQLAlchemy Session).
	For production use with async endpoints, consider:
	1. Converting FeedbackService to use AsyncSession and async queries, OR
	2. Using run_sync() to execute sync code in async context, OR
	3. Implementing async queries directly in this endpoint

	Current implementation returns empty list to maintain API contract.
	"""
	# FeedbackService requires sync Session, but endpoint uses AsyncSession
	# Temporary: return empty list until service is converted to async
	feedback_items = []

	response = []
	for feedback in feedback_items:
		feedback_with_votes = feedback_service.get_feedback_with_votes(feedback.id, current_user.id)
		response.append(
			FeedbackResponse(
				id=feedback.id,
				user_id=feedback.user_id,
				type=feedback.type,
				priority=feedback.priority,
				status=feedback.status,
				title=feedback.title,
				description=feedback.description,
				page_url=feedback.page_url,
				created_at=feedback.created_at,
				updated_at=feedback.updated_at,
				resolved_at=feedback.resolved_at,
				admin_response=feedback.admin_response,
				vote_count=feedback_with_votes["vote_count"],
				user_vote=feedback_with_votes["user_vote"],
			)
		)

	return response


@router.get("/feedback/stats")
async def get_feedback_stats(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""Get feedback statistics for the current user"""
	from sqlalchemy import func

	from app.models.feedback import Feedback

	# Get total count
	total_result = await db.execute(select(func.count(Feedback.id)).where(Feedback.user_id == current_user.id))
	total_count = total_result.scalar() or 0

	# Get count by status
	status_result = await db.execute(
		select(Feedback.status, func.count(Feedback.id)).where(Feedback.user_id == current_user.id).group_by(Feedback.status)
	)
	status_counts = {status: count for status, count in status_result.all()}

	# Get count by type
	type_result = await db.execute(select(Feedback.type, func.count(Feedback.id)).where(Feedback.user_id == current_user.id).group_by(Feedback.type))
	type_counts = {type_: count for type_, count in type_result.all()}

	# Get count by priority
	priority_result = await db.execute(
		select(Feedback.priority, func.count(Feedback.id)).where(Feedback.user_id == current_user.id).group_by(Feedback.priority)
	)
	priority_counts = {priority: count for priority, count in priority_result.all()}

	return {
		"total": total_count,
		"by_status": status_counts,
		"by_type": type_counts,
		"by_priority": priority_counts,
	}


@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(feedback_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get specific feedback item"""
	feedback_service = FeedbackService(db)
	feedback_with_votes = feedback_service.get_feedback_with_votes(feedback_id, current_user.id)

	if not feedback_with_votes:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

	feedback = feedback_with_votes["feedback"]

	# Check if user owns this feedback or is admin
	if feedback.user_id != current_user.id:
		# For now, only allow users to see their own feedback
		# In the future, could add admin role check here
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this feedback")

	return FeedbackResponse(
		id=feedback.id,
		user_id=feedback.user_id,
		type=feedback.type,
		priority=feedback.priority,
		status=feedback.status,
		title=feedback.title,
		description=feedback.description,
		page_url=feedback.page_url,
		created_at=feedback.created_at,
		updated_at=feedback.updated_at,
		resolved_at=feedback.resolved_at,
		admin_response=feedback.admin_response,
		vote_count=feedback_with_votes["vote_count"],
		user_vote=feedback_with_votes["user_vote"],
	)


@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
	feedback_id: int, feedback_data: FeedbackUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Update feedback item"""
	feedback_service = FeedbackService(db)
	feedback = feedback_service.update_feedback(feedback_id, feedback_data, current_user.id)

	if not feedback:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

	feedback_with_votes = feedback_service.get_feedback_with_votes(feedback.id, current_user.id)

	return FeedbackResponse(
		id=feedback.id,
		user_id=feedback.user_id,
		type=feedback.type,
		priority=feedback.priority,
		status=feedback.status,
		title=feedback.title,
		description=feedback.description,
		page_url=feedback.page_url,
		created_at=feedback.created_at,
		updated_at=feedback.updated_at,
		resolved_at=feedback.resolved_at,
		admin_response=feedback.admin_response,
		vote_count=feedback_with_votes["vote_count"],
		user_vote=feedback_with_votes["user_vote"],
	)


@router.post("/feedback/{feedback_id}/vote", status_code=status.HTTP_200_OK)
async def vote_on_feedback(
	feedback_id: int, vote_data: FeedbackVoteCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Vote on feedback item"""
	feedback_service = FeedbackService(db)

	# Check if feedback exists
	feedback = feedback_service.get_feedback(feedback_id)
	if not feedback:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

	success = feedback_service.vote_on_feedback(feedback_id, current_user.id, vote_data)
	if not success:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to vote on feedback")

	return {"message": "Vote recorded successfully"}


# Onboarding endpoints
@router.get("/onboarding/progress", response_model=OnboardingProgressResponse)
async def get_onboarding_progress(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get user's onboarding progress"""
	onboarding_service = OnboardingService(db)
	progress = onboarding_service.get_or_create_progress(current_user.id)

	return OnboardingProgressResponse(
		id=progress.id,
		user_id=progress.user_id,
		steps_completed=progress.steps_completed or [],
		current_step=progress.current_step,
		tutorials_completed=progress.tutorials_completed or [],
		features_discovered=progress.features_discovered or [],
		help_topics_viewed=progress.help_topics_viewed or [],
		show_tooltips=progress.show_tooltips,
		show_feature_highlights=progress.show_feature_highlights,
		onboarding_completed=progress.onboarding_completed,
		created_at=progress.created_at,
		updated_at=progress.updated_at,
		completed_at=progress.completed_at,
	)


@router.put("/onboarding/progress", response_model=OnboardingProgressResponse)
async def update_onboarding_progress(
	progress_data: OnboardingProgressUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Update user's onboarding progress"""
	onboarding_service = OnboardingService(db)
	progress = onboarding_service.update_progress(current_user.id, progress_data)

	return OnboardingProgressResponse(
		id=progress.id,
		user_id=progress.user_id,
		steps_completed=progress.steps_completed or [],
		current_step=progress.current_step,
		tutorials_completed=progress.tutorials_completed or [],
		features_discovered=progress.features_discovered or [],
		help_topics_viewed=progress.help_topics_viewed or [],
		show_tooltips=progress.show_tooltips,
		show_feature_highlights=progress.show_feature_highlights,
		onboarding_completed=progress.onboarding_completed,
		created_at=progress.created_at,
		updated_at=progress.updated_at,
		completed_at=progress.completed_at,
	)


@router.post("/onboarding/step/{step_id}/complete", status_code=status.HTTP_200_OK)
async def complete_onboarding_step(step_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Mark onboarding step as completed"""
	onboarding_service = OnboardingService(db)
	onboarding_service.mark_step_completed(current_user.id, step_id)

	return {"message": f"Step {step_id} marked as completed"}


@router.post("/onboarding/tutorial/{tutorial_id}/complete", status_code=status.HTTP_200_OK)
async def complete_tutorial(tutorial_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Mark tutorial as completed"""
	onboarding_service = OnboardingService(db)
	onboarding_service.mark_tutorial_completed(current_user.id, tutorial_id)

	return {"message": f"Tutorial {tutorial_id} marked as completed"}


@router.post("/onboarding/feature/{feature_id}/discover", status_code=status.HTTP_200_OK)
async def discover_feature(feature_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Mark feature as discovered"""
	onboarding_service = OnboardingService(db)
	onboarding_service.mark_feature_discovered(current_user.id, feature_id)

	return {"message": f"Feature {feature_id} marked as discovered"}


# Help system endpoints
@router.get("/help/articles", response_model=List[HelpArticleSummary])
async def get_help_articles(
	category: Optional[str] = Query(None),
	search: Optional[str] = Query(None),
	limit: int = Query(50, ge=1, le=100),
	offset: int = Query(0, ge=0),
	db: AsyncSession = Depends(get_db),
):
	"""Get help articles with optional filtering"""
	from sqlalchemy import or_, select

	from ...models.feedback import HelpArticle

	# Build query
	query = select(HelpArticle).where(HelpArticle.is_published == True)

	if category:
		query = query.where(HelpArticle.category == category)

	if search:
		search_term = f"%{search}%"
		query = query.where(or_(HelpArticle.title.ilike(search_term), HelpArticle.content.ilike(search_term), HelpArticle.excerpt.ilike(search_term)))

	# Get paginated results
	query = query.order_by(HelpArticle.view_count.desc()).offset(offset).limit(limit)
	result = await db.execute(query)
	articles = result.scalars().all()

	return [
		HelpArticleSummary(
			id=article.id,
			title=article.title,
			slug=article.slug,
			excerpt=article.excerpt or "",
			category=article.category,
			tags=article.tags or [],
			view_count=article.view_count,
			helpful_votes=article.helpful_votes,
			unhelpful_votes=article.unhelpful_votes,
			created_at=article.created_at,
			updated_at=article.updated_at,
		)
		for article in articles
	]


@router.get("/help/articles/{article_id}", response_model=HelpArticleResponse)
async def get_help_article(article_id: int, current_user: Optional[User] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get specific help article"""
	help_service = HelpService(db)

	user_id = current_user.id if current_user else None
	article_with_vote = help_service.get_article_with_vote(article_id, user_id)

	if not article_with_vote:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Help article not found")

	article = article_with_vote["article"]

	# Track help topic view if user is logged in
	if current_user:
		onboarding_service = OnboardingService(db)
		onboarding_service.track_help_topic_view(current_user.id, str(article_id))

	return HelpArticleResponse(
		id=article.id,
		title=article.title,
		slug=article.slug,
		content=article.content,
		excerpt=article.excerpt,
		category=article.category,
		tags=article.tags or [],
		is_published=article.is_published,
		view_count=article.view_count,
		helpful_votes=article.helpful_votes,
		unhelpful_votes=article.unhelpful_votes,
		created_at=article.created_at,
		updated_at=article.updated_at,
		published_at=article.published_at,
		user_vote=article_with_vote["user_vote"],
	)


@router.get("/help/articles/slug/{slug}", response_model=HelpArticleResponse)
async def get_help_article_by_slug(slug: str, current_user: Optional[User] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get help article by slug"""
	help_service = HelpService(db)
	article = help_service.get_article_by_slug(slug)

	if not article:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Help article not found")

	user_id = current_user.id if current_user else None
	user_vote = None

	if user_id:
		article_with_vote = help_service.get_article_with_vote(article.id, user_id)
		user_vote = article_with_vote["user_vote"] if article_with_vote else None

		# Track help topic view
		onboarding_service = OnboardingService(db)
		onboarding_service.track_help_topic_view(current_user.id, str(article.id))

	return HelpArticleResponse(
		id=article.id,
		title=article.title,
		slug=article.slug,
		content=article.content,
		excerpt=article.excerpt,
		category=article.category,
		tags=article.tags or [],
		is_published=article.is_published,
		view_count=article.view_count,
		helpful_votes=article.helpful_votes,
		unhelpful_votes=article.unhelpful_votes,
		created_at=article.created_at,
		updated_at=article.updated_at,
		published_at=article.published_at,
		user_vote=user_vote,
	)


@router.post("/help/search", response_model=HelpSearchResponse)
async def search_help_articles(search_request: HelpSearchRequest, db: AsyncSession = Depends(get_db)):
	"""Search help articles"""
	help_service = HelpService(db)
	search_results = help_service.search_articles(search_request)

	articles = [
		HelpArticleSummary(
			id=article.id,
			title=article.title,
			slug=article.slug,
			excerpt=article.excerpt,
			category=article.category,
			tags=article.tags or [],
			view_count=article.view_count,
			helpful_votes=article.helpful_votes,
			unhelpful_votes=article.unhelpful_votes,
			created_at=article.created_at,
			updated_at=article.updated_at,
		)
		for article in search_results["articles"]
	]

	return HelpSearchResponse(
		articles=articles, total_count=search_results["total_count"], query=search_results["query"], suggestions=search_results["suggestions"]
	)


@router.post("/help/articles/{article_id}/vote", status_code=status.HTTP_200_OK)
async def vote_on_help_article(
	article_id: int, vote_data: HelpArticleVoteCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Vote on help article"""
	help_service = HelpService(db)
	success = help_service.vote_on_article(article_id, current_user.id, vote_data)

	if not success:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Help article not found")

	return {"message": "Vote recorded successfully"}


@router.get("/help/categories", response_model=List[str])
async def get_help_categories(db: AsyncSession = Depends(get_db)):
	"""Get all help article categories"""
	from sqlalchemy import distinct, select

	from ...models.feedback import HelpArticle

	# Get distinct categories from published articles
	result = await db.execute(select(distinct(HelpArticle.category)).where(HelpArticle.is_published == True))
	categories = [cat for cat in result.scalars().all()]

	return categories


@router.get("/help/popular", response_model=List[HelpArticleSummary])
async def get_popular_help_articles(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_db)):
	"""Get most popular help articles"""
	help_service = HelpService(db)
	articles = help_service.get_popular_articles(limit)

	return [
		HelpArticleSummary(
			id=article.id,
			title=article.title,
			slug=article.slug,
			excerpt=article.excerpt,
			category=article.category,
			tags=article.tags or [],
			view_count=article.view_count,
			helpful_votes=article.helpful_votes,
			unhelpful_votes=article.unhelpful_votes,
			created_at=article.created_at,
			updated_at=article.updated_at,
		)
		for article in articles
	]


# Tutorial and feature discovery endpoints (static data for now)
@router.get("/tutorials", response_model=List[Tutorial])
async def get_tutorials():
	"""Get available tutorials"""
	# For now, return static tutorial data
	# In the future, this could be stored in the database
	tutorials = [
		Tutorial(
			id="getting-started",
			title="Getting Started with Career Co-Pilot",
			description="Learn the basics of using Career Co-Pilot to manage your job search",
			category="basics",
			difficulty="beginner",
			estimated_time=10,
			prerequisites=[],
			steps=[
				{
					"id": "welcome",
					"title": "Welcome to Career Co-Pilot",
					"description": "Let's get you started with your intelligent career companion",
					"target_element": "#main-content",
					"position": "center",
					"content": "Career Co-Pilot helps you manage your job search by tracking applications, discovering opportunities, and providing personalized insights.",
					"action_required": False,
				},
				{
					"id": "dashboard-overview",
					"title": "Dashboard Overview",
					"description": "Your dashboard shows key metrics and recent activity",
					"target_element": "[data-testid='dashboard-stats']",
					"position": "bottom",
					"content": "Here you can see your application statistics, recent jobs, and upcoming tasks.",
					"action_required": False,
				},
				{
					"id": "add-first-job",
					"title": "Add Your First Job",
					"description": "Let's add a job opportunity to get started",
					"target_element": "[data-testid='add-job-button']",
					"position": "bottom",
					"content": "Click this button to add a new job opportunity. You can add jobs manually or let our system discover them for you.",
					"action_required": True,
					"action_text": "Click 'Add Job'",
				},
			],
			is_required=True,
		),
		Tutorial(
			id="job-management",
			title="Managing Job Applications",
			description="Learn how to effectively track and manage your job applications",
			category="jobs",
			difficulty="beginner",
			estimated_time=15,
			prerequisites=["getting-started"],
			steps=[
				{
					"id": "job-list",
					"title": "Job List View",
					"description": "Navigate and filter your job opportunities",
					"target_element": "[data-testid='job-list']",
					"position": "top",
					"content": "This is your main job list. You can filter by status, company, or search for specific positions.",
					"action_required": False,
				},
				{
					"id": "job-details",
					"title": "Job Details",
					"description": "View and edit job information",
					"target_element": "[data-testid='job-card']:first-child",
					"position": "right",
					"content": "Click on any job to view detailed information, update status, and manage documents.",
					"action_required": True,
					"action_text": "Click on a job",
				},
				{
					"id": "status-update",
					"title": "Update Application Status",
					"description": "Keep track of your application progress",
					"target_element": "[data-testid='status-select']",
					"position": "bottom",
					"content": "Update your application status as you progress through the hiring process.",
					"action_required": False,
				},
			],
			is_required=False,
		),
	]

	return tutorials


@router.get("/feature-highlights", response_model=List[FeatureHighlight])
async def get_feature_highlights(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get feature highlights for user"""
	onboarding_service = OnboardingService(db)
	progress = onboarding_service.get_or_create_progress(current_user.id)

	# Return feature highlights based on user's progress
	all_highlights = [
		FeatureHighlight(
			id="smart-recommendations",
			title="Smart Job Recommendations",
			description="Get personalized job recommendations based on your skills and preferences",
			target_element="[data-testid='recommendations-section']",
			position="top",
			priority=1,
			show_once=True,
			conditions={"min_jobs": 3},
		),
		FeatureHighlight(
			id="analytics-dashboard",
			title="Career Analytics",
			description="Track your application success rates and identify improvement opportunities",
			target_element="[data-testid='analytics-link']",
			position="bottom",
			priority=2,
			show_once=True,
			conditions={"min_applications": 5},
		),
		FeatureHighlight(
			id="document-management",
			title="Document Management",
			description="Organize your resumes, cover letters, and track which documents you've sent",
			target_element="[data-testid='documents-section']",
			position="left",
			priority=3,
			show_once=True,
		),
	]

	# Filter highlights based on user's discovered features
	discovered_features = progress.features_discovered or []
	return [h for h in all_highlights if h.id not in discovered_features]
