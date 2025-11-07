"""
Service layer for feedback and onboarding system
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.feedback import Feedback, FeedbackStatus, FeedbackVote, HelpArticle, HelpArticleVote, OnboardingProgress
from app.schemas.feedback import (
	FeedbackCreate,
	FeedbackUpdate,
	FeedbackVoteCreate,
	HelpArticleCreate,
	HelpArticleUpdate,
	HelpArticleVoteCreate,
	HelpSearchRequest,
	OnboardingProgressUpdate,
)


class FeedbackService:
	"""Service for managing user feedback and feature requests"""

	def __init__(self, db: Session):
		self.db = db

	def create_feedback(self, user_id: int, feedback_data: FeedbackCreate) -> Feedback:
		"""Create new feedback item"""
		feedback = Feedback(
			user_id=user_id,
			type=feedback_data.type,
			priority=feedback_data.priority,
			title=feedback_data.title,
			description=feedback_data.description,
			page_url=feedback_data.page_url,
			user_agent=feedback_data.user_agent,
			screen_resolution=feedback_data.screen_resolution,
			browser_info=feedback_data.browser_info or {},
			extra_data=feedback_data.metadata or {},
		)

		self.db.add(feedback)
		self.db.commit()
		self.db.refresh(feedback)
		return feedback

	def get_feedback(self, feedback_id: int, user_id: Optional[int] = None) -> Optional[Feedback]:
		"""Get feedback by ID"""
		query = self.db.query(Feedback).filter(Feedback.id == feedback_id)
		if user_id:
			query = query.filter(Feedback.user_id == user_id)
		return query.first()

	def get_user_feedback(self, user_id: int, status: Optional[FeedbackStatus] = None, limit: int = 50, offset: int = 0) -> List[Feedback]:
		"""Get user's feedback items"""
		query = self.db.query(Feedback).filter(Feedback.user_id == user_id)

		if status:
			query = query.filter(Feedback.status == status)

		return query.order_by(desc(Feedback.created_at)).offset(offset).limit(limit).all()

	def get_all_feedback(
		self, status: Optional[FeedbackStatus] = None, feedback_type: Optional[str] = None, limit: int = 100, offset: int = 0
	) -> List[Feedback]:
		"""Get all feedback items (admin function)"""
		query = self.db.query(Feedback)

		if status:
			query = query.filter(Feedback.status == status)
		if feedback_type:
			query = query.filter(Feedback.type == feedback_type)

		return query.order_by(desc(Feedback.created_at)).offset(offset).limit(limit).all()

	def update_feedback(self, feedback_id: int, feedback_data: FeedbackUpdate, user_id: Optional[int] = None) -> Optional[Feedback]:
		"""Update feedback item"""
		query = self.db.query(Feedback).filter(Feedback.id == feedback_id)
		if user_id:
			query = query.filter(Feedback.user_id == user_id)

		feedback = query.first()
		if not feedback:
			return None

		update_data = feedback_data.dict(exclude_unset=True)

		# Set resolved_at when status changes to resolved
		if "status" in update_data and update_data["status"] == FeedbackStatus.RESOLVED:
			update_data["resolved_at"] = datetime.now(timezone.utc)

		for field, value in update_data.items():
			setattr(feedback, field, value)

		self.db.commit()
		self.db.refresh(feedback)
		return feedback

	def vote_on_feedback(self, feedback_id: int, user_id: int, vote_data: FeedbackVoteCreate) -> bool:
		"""Vote on feedback item"""
		# Check if user already voted
		existing_vote = self.db.query(FeedbackVote).filter(and_(FeedbackVote.feedback_id == feedback_id, FeedbackVote.user_id == user_id)).first()

		if existing_vote:
			if vote_data.vote == 0:
				# Remove vote
				self.db.delete(existing_vote)
			else:
				# Update vote
				existing_vote.vote = vote_data.vote
		else:
			if vote_data.vote != 0:
				# Create new vote
				vote = FeedbackVote(feedback_id=feedback_id, user_id=user_id, vote=vote_data.vote)
				self.db.add(vote)

		self.db.commit()
		return True

	async def get_feedback_with_votes(self, feedback_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
		"""Get feedback with vote counts and user's vote"""
		result = await self.db.execute(select(Feedback).filter(Feedback.id == feedback_id))
		feedback = result.scalar_one_or_none()
		if not feedback:
			return None

		# Calculate vote counts
		result = await self.db.execute(select(func.sum(FeedbackVote.vote)).filter(FeedbackVote.feedback_id == feedback_id))
		vote_count = result.scalar() or 0

		# Get user's vote if user_id provided
		user_vote = None
		if user_id:
			user_vote_obj = self.db.query(FeedbackVote).filter(and_(FeedbackVote.feedback_id == feedback_id, FeedbackVote.user_id == user_id)).first()
			user_vote = user_vote_obj.vote if user_vote_obj else None

		return {"feedback": feedback, "vote_count": vote_count, "user_vote": user_vote}


class OnboardingService:
	"""Service for managing user onboarding and tutorials"""

	def __init__(self, db: Session):
		self.db = db

	def get_or_create_progress(self, user_id: int) -> OnboardingProgress:
		"""Get or create onboarding progress for user"""
		progress = self.db.query(OnboardingProgress).filter(OnboardingProgress.user_id == user_id).first()

		if not progress:
			progress = OnboardingProgress(user_id=user_id, steps_completed=[], tutorials_completed=[], features_discovered=[], help_topics_viewed=[])
			self.db.add(progress)
			self.db.commit()
			self.db.refresh(progress)

		return progress

	def update_progress(self, user_id: int, progress_data: OnboardingProgressUpdate) -> OnboardingProgress:
		"""Update onboarding progress"""
		progress = self.get_or_create_progress(user_id)

		update_data = progress_data.dict(exclude_unset=True)

		# Handle list fields specially to avoid overwriting
		for field in ["steps_completed", "tutorials_completed", "features_discovered", "help_topics_viewed"]:
			if field in update_data:
				current_list = getattr(progress, field) or []
				new_items = update_data[field]
				# Merge lists and remove duplicates while preserving order
				merged = current_list + [item for item in new_items if item not in current_list]
				setattr(progress, field, merged)
				del update_data[field]

		# Update other fields
		for field, value in update_data.items():
			setattr(progress, field, value)

		# Set completed_at when onboarding is completed
		if progress_data.onboarding_completed and not progress.completed_at:
			progress.completed_at = datetime.now(timezone.utc)

		self.db.commit()
		self.db.refresh(progress)
		return progress

	def mark_step_completed(self, user_id: int, step_id: str) -> OnboardingProgress:
		"""Mark a specific onboarding step as completed"""
		progress = self.get_or_create_progress(user_id)

		if step_id not in (progress.steps_completed or []):
			steps = progress.steps_completed or []
			steps.append(step_id)
			progress.steps_completed = steps

			self.db.commit()
			self.db.refresh(progress)

		return progress

	def mark_tutorial_completed(self, user_id: int, tutorial_id: str) -> OnboardingProgress:
		"""Mark a tutorial as completed"""
		progress = self.get_or_create_progress(user_id)

		if tutorial_id not in (progress.tutorials_completed or []):
			tutorials = progress.tutorials_completed or []
			tutorials.append(tutorial_id)
			progress.tutorials_completed = tutorials

			self.db.commit()
			self.db.refresh(progress)

		return progress

	def mark_feature_discovered(self, user_id: int, feature_id: str) -> OnboardingProgress:
		"""Mark a feature as discovered"""
		progress = self.get_or_create_progress(user_id)

		if feature_id not in (progress.features_discovered or []):
			features = progress.features_discovered or []
			features.append(feature_id)
			progress.features_discovered = features

			self.db.commit()
			self.db.refresh(progress)

		return progress

	def track_help_topic_view(self, user_id: int, topic_id: str) -> OnboardingProgress:
		"""Track that user viewed a help topic"""
		progress = self.get_or_create_progress(user_id)

		if topic_id not in (progress.help_topics_viewed or []):
			topics = progress.help_topics_viewed or []
			topics.append(topic_id)
			progress.help_topics_viewed = topics

			self.db.commit()
			self.db.refresh(progress)

		return progress


class HelpService:
	"""Service for managing help articles and documentation"""

	def __init__(self, db: Session):
		self.db = db

	def create_article(self, article_data: HelpArticleCreate) -> HelpArticle:
		"""Create new help article"""
		article = HelpArticle(
			title=article_data.title,
			slug=article_data.slug,
			content=article_data.content,
			excerpt=article_data.excerpt,
			category=article_data.category,
			tags=article_data.tags or [],
			meta_description=article_data.meta_description,
			search_keywords=article_data.search_keywords or [],
			is_published=article_data.is_published,
			published_at=datetime.now(timezone.utc) if article_data.is_published else None,
		)

		self.db.add(article)
		self.db.commit()
		self.db.refresh(article)
		return article

	def get_article(self, article_id: int) -> Optional[HelpArticle]:
		"""Get help article by ID"""
		return self.db.query(HelpArticle).filter(HelpArticle.id == article_id).first()

	def get_article_by_slug(self, slug: str) -> Optional[HelpArticle]:
		"""Get help article by slug"""
		article = self.db.query(HelpArticle).filter(and_(HelpArticle.slug == slug, HelpArticle.is_published == True)).first()

		if article:
			# Increment view count
			article.view_count += 1
			self.db.commit()

		return article

	def get_articles(self, category: Optional[str] = None, published_only: bool = True, limit: int = 50, offset: int = 0) -> List[HelpArticle]:
		"""Get help articles"""
		query = self.db.query(HelpArticle)

		if published_only:
			query = query.filter(HelpArticle.is_published == True)
		if category:
			query = query.filter(HelpArticle.category == category)

		return query.order_by(desc(HelpArticle.created_at)).offset(offset).limit(limit).all()

	def search_articles(self, search_request: HelpSearchRequest) -> Dict[str, Any]:
		"""Search help articles"""
		query = self.db.query(HelpArticle).filter(HelpArticle.is_published == True)

		# Text search in title and content
		search_term = f"%{search_request.query}%"
		query = query.filter(
			or_(HelpArticle.title.ilike(search_term), HelpArticle.content.ilike(search_term), HelpArticle.excerpt.ilike(search_term))
		)

		# Filter by category
		if search_request.category:
			query = query.filter(HelpArticle.category == search_request.category)

		# Filter by tags
		if search_request.tags:
			for tag in search_request.tags:
				query = query.filter(HelpArticle.tags.contains([tag]))

		total_count = query.count()
		articles = query.order_by(desc(HelpArticle.view_count)).limit(search_request.limit).all()

		return {
			"articles": articles,
			"total_count": total_count,
			"query": search_request.query,
			"suggestions": [],  # Could implement search suggestions later
		}

	def update_article(self, article_id: int, article_data: HelpArticleUpdate) -> Optional[HelpArticle]:
		"""Update help article"""
		article = self.db.query(HelpArticle).filter(HelpArticle.id == article_id).first()
		if not article:
			return None

		update_data = article_data.dict(exclude_unset=True)

		# Set published_at when article is published
		if "is_published" in update_data and update_data["is_published"] and not article.published_at:
			update_data["published_at"] = datetime.now(timezone.utc)

		for field, value in update_data.items():
			setattr(article, field, value)

		self.db.commit()
		self.db.refresh(article)
		return article

	def vote_on_article(self, article_id: int, user_id: int, vote_data: HelpArticleVoteCreate) -> bool:
		"""Vote on help article"""
		# Check if user already voted
		existing_vote = (
			self.db.query(HelpArticleVote).filter(and_(HelpArticleVote.article_id == article_id, HelpArticleVote.user_id == user_id)).first()
		)

		article = self.db.query(HelpArticle).filter(HelpArticle.id == article_id).first()
		if not article:
			return False

		if existing_vote:
			# Update vote counts
			if existing_vote.is_helpful and not vote_data.is_helpful:
				article.helpful_votes -= 1
				article.unhelpful_votes += 1
			elif not existing_vote.is_helpful and vote_data.is_helpful:
				article.unhelpful_votes -= 1
				article.helpful_votes += 1

			existing_vote.is_helpful = vote_data.is_helpful
		else:
			# Create new vote
			vote = HelpArticleVote(article_id=article_id, user_id=user_id, is_helpful=vote_data.is_helpful)
			self.db.add(vote)

			# Update vote counts
			if vote_data.is_helpful:
				article.helpful_votes += 1
			else:
				article.unhelpful_votes += 1

		self.db.commit()
		return True

	def get_article_with_vote(self, article_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
		"""Get article with user's vote"""
		article = self.db.query(HelpArticle).filter(HelpArticle.id == article_id).first()
		if not article:
			return None

		user_vote = None
		if user_id:
			vote_obj = (
				self.db.query(HelpArticleVote).filter(and_(HelpArticleVote.article_id == article_id, HelpArticleVote.user_id == user_id)).first()
			)
			user_vote = vote_obj.is_helpful if vote_obj else None

		return {"article": article, "user_vote": user_vote}

	def get_categories(self) -> List[str]:
		"""Get all article categories"""
		categories = self.db.query(HelpArticle.category).filter(HelpArticle.is_published == True).distinct().all()
		return [cat[0] for cat in categories]

	def get_popular_articles(self, limit: int = 10) -> List[HelpArticle]:
		"""Get most popular articles by view count"""
		return self.db.query(HelpArticle).filter(HelpArticle.is_published == True).order_by(desc(HelpArticle.view_count)).limit(limit).all()
