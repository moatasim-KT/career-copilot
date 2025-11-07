from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.feedback import HelpArticle, HelpArticleVote
from ...models.user import User

router = APIRouter()


# Predefined categories and topics
HELP_CATEGORIES = {
	"getting_started": {
		"name": "Getting Started",
		"description": "Learn the basics of using Career Copilot",
		"icon": "🚀",
		"order": 1,
		"articles_count": 5,
	},
	"job_search": {"name": "Job Search", "description": "Tips and tricks for effective job searching", "icon": "🔍", "order": 2, "articles_count": 8},
	"resume": {"name": "Resume & CV", "description": "Creating and optimizing your resume", "icon": "📄", "order": 3, "articles_count": 6},
	"interview": {"name": "Interview Prep", "description": "Ace your interviews with our guides", "icon": "💼", "order": 4, "articles_count": 7},
	"applications": {"name": "Applications", "description": "Managing and tracking your applications", "icon": "📝", "order": 5, "articles_count": 4},
	"networking": {"name": "Networking", "description": "Build your professional network", "icon": "🤝", "order": 6, "articles_count": 5},
	"career_growth": {
		"name": "Career Growth",
		"description": "Advance your career with expert advice",
		"icon": "📈",
		"order": 7,
		"articles_count": 6,
	},
	"troubleshooting": {"name": "Troubleshooting", "description": "Common issues and solutions", "icon": "🔧", "order": 8, "articles_count": 3},
}


# Sample help articles
SAMPLE_ARTICLES = [
	{
		"id": 1,
		"title": "Getting Started with Career Copilot",
		"slug": "getting-started",
		"category": "getting_started",
		"summary": "Learn how to set up your profile and start your job search",
		"content": "Welcome to Career Copilot! This guide will help you get started...",
		"tags": ["beginner", "setup", "profile"],
		"views": 1523,
		"helpful_votes": 145,
		"created_at": "2024-01-15",
		"updated_at": "2024-11-01",
	},
	{
		"id": 2,
		"title": "How to Upload and Parse Your Resume",
		"slug": "upload-resume",
		"category": "resume",
		"summary": "Step-by-step guide to uploading and parsing your resume",
		"content": "Your resume is the foundation of your profile...",
		"tags": ["resume", "upload", "parsing"],
		"views": 2341,
		"helpful_votes": 234,
		"created_at": "2024-01-16",
		"updated_at": "2024-10-28",
	},
	{
		"id": 3,
		"title": "Setting Up Job Alerts",
		"slug": "job-alerts",
		"category": "job_search",
		"summary": "Configure personalized job alerts to never miss opportunities",
		"content": "Job alerts help you stay on top of new opportunities...",
		"tags": ["alerts", "notifications", "job search"],
		"views": 1876,
		"helpful_votes": 198,
		"created_at": "2024-01-20",
		"updated_at": "2024-11-02",
	},
	{
		"id": 4,
		"title": "Preparing for Technical Interviews",
		"slug": "technical-interviews",
		"category": "interview",
		"summary": "Master technical interviews with our comprehensive guide",
		"content": "Technical interviews can be challenging...",
		"tags": ["interview", "technical", "preparation"],
		"views": 3421,
		"helpful_votes": 456,
		"created_at": "2024-02-01",
		"updated_at": "2024-11-03",
	},
	{
		"id": 5,
		"title": "Tracking Your Applications",
		"slug": "track-applications",
		"category": "applications",
		"summary": "Effectively manage and track all your job applications",
		"content": "Keep track of where you've applied and follow up...",
		"tags": ["applications", "tracking", "organization"],
		"views": 2145,
		"helpful_votes": 276,
		"created_at": "2024-02-10",
		"updated_at": "2024-10-30",
	},
]


@router.get("/articles")
async def list_help_articles(
	category: Optional[str] = None,
	tag: Optional[str] = None,
	search: Optional[str] = None,
	skip: int = 0,
	limit: int = 20,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	List help articles with optional filtering

	- **category**: Filter by category slug
	- **tag**: Filter by tag
	- **search**: Search in title and content
	- **skip**: Number of articles to skip (pagination)
	- **limit**: Maximum number of articles to return
	"""
	# Build query
	query = select(HelpArticle).where(HelpArticle.is_published == True)

	if category:
		query = query.where(HelpArticle.category == category)

	if tag:
		# Search in tags JSON array
		query = query.where(func.json_array_length(HelpArticle.tags) > 0)
		# Note: For proper tag filtering, you'd use PostgreSQL JSON operators
		# For now, we'll filter in Python after fetching

	if search:
		search_term = f"%{search}%"
		query = query.where(or_(HelpArticle.title.ilike(search_term), HelpArticle.content.ilike(search_term), HelpArticle.excerpt.ilike(search_term)))

	# Get total count
	count_query = select(func.count()).select_from(HelpArticle).where(HelpArticle.is_published == True)
	if category:
		count_query = count_query.where(HelpArticle.category == category)
	if search:
		count_query = count_query.where(
			or_(HelpArticle.title.ilike(search_term), HelpArticle.content.ilike(search_term), HelpArticle.excerpt.ilike(search_term))
		)

	total_result = await db.execute(count_query)
	total = total_result.scalar() or 0

	# Get paginated results
	query = query.order_by(HelpArticle.view_count.desc()).offset(skip).limit(limit)
	result = await db.execute(query)
	articles = result.scalars().all()

	# Filter by tag in Python if specified (since JSON querying is complex)
	if tag and articles:
		articles = [a for a in articles if isinstance(a.tags, list) and tag in a.tags]

	# Format response
	articles_data = [
		{
			"id": article.id,
			"title": article.title,
			"slug": article.slug,
			"category": article.category,
			"summary": article.excerpt or "",
			"tags": article.tags if isinstance(article.tags, list) else [],
			"views": article.view_count,
			"helpful_votes": article.helpful_votes,
			"created_at": article.created_at.isoformat() if article.created_at else None,
			"updated_at": article.updated_at.isoformat() if article.updated_at else None,
		}
		for article in articles
	]

	return {
		"articles": articles_data,
		"total": total,
		"skip": skip,
		"limit": limit,
		"message": "Help articles retrieved successfully",
	}


@router.get("/categories")
async def get_help_categories(current_user: User = Depends(get_current_user)):
	"""
	Get all help article categories with metadata

	Returns a list of categories with:
	- Category name and description
	- Icon emoji
	- Display order
	- Article count
	"""
	categories_list = []
	for category_id, category_data in HELP_CATEGORIES.items():
		categories_list.append({"id": category_id, **category_data})

	# Sort by order
	categories_list.sort(key=lambda x: x["order"])

	return {"categories": categories_list, "total": len(categories_list), "message": "Help categories retrieved successfully"}


@router.get("/articles/{article_id}")
async def get_article(article_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get a specific help article by ID and increment view count"""
	result = await db.execute(select(HelpArticle).where(HelpArticle.id == article_id, HelpArticle.is_published == True))
	article = result.scalar_one_or_none()

	if not article:
		raise HTTPException(status_code=404, detail=f"Help article with ID {article_id} not found")

	# Increment view count
	article.view_count += 1
	await db.commit()
	await db.refresh(article)

	return {
		"article": {
			"id": article.id,
			"title": article.title,
			"slug": article.slug,
			"category": article.category,
			"summary": article.excerpt or "",
			"content": article.content,
			"tags": article.tags if isinstance(article.tags, list) else [],
			"views": article.view_count,
			"helpful_votes": article.helpful_votes,
			"meta_description": article.meta_description,
			"created_at": article.created_at.isoformat() if article.created_at else None,
			"updated_at": article.updated_at.isoformat() if article.updated_at else None,
		},
		"message": "Article retrieved successfully",
	}


@router.post("/articles/{article_id}/vote")
async def vote_help_article(
	article_id: int,
	helpful: bool = Query(..., description="Whether the article was helpful"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Vote on whether a help article was helpful

	- **article_id**: ID of the article to vote on
	- **helpful**: True if helpful, False if not helpful
	"""
	# Check if article exists
	article_result = await db.execute(select(HelpArticle).where(HelpArticle.id == article_id))
	article = article_result.scalar_one_or_none()

	if not article:
		raise HTTPException(status_code=404, detail=f"Help article with ID {article_id} not found")

	# Check if user already voted
	existing_vote_result = await db.execute(
		select(HelpArticleVote).where(HelpArticleVote.article_id == article_id, HelpArticleVote.user_id == current_user.id)
	)
	existing_vote = existing_vote_result.scalar_one_or_none()

	if existing_vote:
		# Update existing vote if different
		if existing_vote.is_helpful != helpful:
			# Adjust counts
			if existing_vote.is_helpful:
				article.helpful_votes = max(0, article.helpful_votes - 1)
				article.unhelpful_votes += 1
			else:
				article.unhelpful_votes = max(0, article.unhelpful_votes - 1)
				article.helpful_votes += 1

			existing_vote.is_helpful = helpful
			existing_vote.updated_at = datetime.utcnow()
	else:
		# Create new vote
		new_vote = HelpArticleVote(article_id=article_id, user_id=current_user.id, is_helpful=helpful)
		db.add(new_vote)

		# Update article counts
		if helpful:
			article.helpful_votes += 1
		else:
			article.unhelpful_votes += 1

	await db.commit()
	await db.refresh(article)

	return {
		"success": True,
		"article_id": article_id,
		"helpful_votes": article.helpful_votes,
		"unhelpful_votes": article.unhelpful_votes,
		"message": "Thank you for your feedback!",
	}


@router.get("/search")
async def search_help_articles(
	q: str = Query(..., min_length=2, description="Search query"),
	category: Optional[str] = None,
	limit: int = 10,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Search help articles by keyword

	- **q**: Search query (minimum 2 characters)
	- **category**: Optional category filter
	- **limit**: Maximum number of results
	"""
	search_term = f"%{q}%"
	query = select(HelpArticle).where(
		HelpArticle.is_published == True,
		or_(HelpArticle.title.ilike(search_term), HelpArticle.content.ilike(search_term), HelpArticle.excerpt.ilike(search_term)),
	)

	if category:
		query = query.where(HelpArticle.category == category)

	query = query.order_by(HelpArticle.view_count.desc()).limit(limit)
	result = await db.execute(query)
	articles = result.scalars().all()

	return {
		"results": [
			{
				"id": article.id,
				"title": article.title,
				"slug": article.slug,
				"category": article.category,
				"summary": article.excerpt or "",
				"relevance_score": 0.95,  # TODO: Implement proper relevance scoring
			}
			for article in articles
		],
		"query": q,
		"total": len(articles),
		"message": "Search completed successfully",
	}


@router.get("/popular")
async def get_popular_articles(limit: int = 5, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get most popular help articles based on views

	- **limit**: Number of articles to return (default: 5)
	"""
	query = select(HelpArticle).where(HelpArticle.is_published == True).order_by(HelpArticle.view_count.desc()).limit(limit)

	result = await db.execute(query)
	articles = result.scalars().all()

	return {
		"articles": [
			{
				"id": article.id,
				"title": article.title,
				"slug": article.slug,
				"category": article.category,
				"views": article.view_count,
				"helpful_votes": article.helpful_votes,
			}
			for article in articles
		],
		"total": len(articles),
		"message": "Popular articles retrieved successfully",
	}
