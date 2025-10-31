"""
Query Optimization Helpers
Provides utilities for eager loading and N+1 query prevention
"""

from typing import List, Optional, Type, TypeVar

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Query, Session, joinedload, selectinload

# Type variable for generic model types
ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class QueryOptimizer:
	"""Helper class for optimized database queries with eager loading."""

	@staticmethod
	def get_user_with_relations(
		db: Session, user_id: int, load_jobs: bool = False, load_applications: bool = False, load_feedback: bool = False
	) -> Optional[User]:
		"""
		Get user with eagerly loaded relationships to prevent N+1 queries.

		Args:
		    db: Database session
		    user_id: User ID to fetch
		    load_jobs: Whether to load user's jobs
		    load_applications: Whether to load user's applications
		    load_feedback: Whether to load user's feedback

		Returns:
		    User object with loaded relationships or None
		"""
		query = db.query(User).filter(User.id == user_id)

		# Add eager loading based on requirements
		if load_jobs:
			query = query.options(selectinload(User.jobs))

		if load_applications:
			query = query.options(selectinload(User.applications))

		if load_feedback:
			query = query.options(selectinload(User.feedback))

		return query.first()

	@staticmethod
	def get_users_with_jobs(db: Session, user_ids: Optional[List[int]] = None, limit: Optional[int] = None) -> List[User]:
		"""
		Get multiple users with their jobs eagerly loaded.

		Args:
		    db: Database session
		    user_ids: Optional list of specific user IDs to fetch
		    limit: Optional limit on number of users

		Returns:
		    List of users with jobs loaded
		"""
		query = db.query(User).options(selectinload(User.jobs))

		if user_ids:
			query = query.filter(User.id.in_(user_ids))

		if limit:
			query = query.limit(limit)

		return query.all()

	@staticmethod
	def get_job_with_user(db: Session, job_id: int) -> Optional[Job]:
		"""
		Get job with user relationship eagerly loaded.

		Args:
		    db: Database session
		    job_id: Job ID to fetch

		Returns:
		    Job object with user loaded or None
		"""
		return db.query(Job).options(joinedload(Job.user)).filter(Job.id == job_id).first()

	@staticmethod
	def get_jobs_with_user(db: Session, user_id: Optional[int] = None, limit: int = 100) -> List[Job]:
		"""
		Get jobs with user relationship eagerly loaded.

		Args:
		    db: Database session
		    user_id: Optional user ID to filter by
		    limit: Maximum number of jobs to return

		Returns:
		    List of jobs with user loaded
		"""
		query = db.query(Job).options(joinedload(Job.user))

		if user_id:
			query = query.filter(Job.user_id == user_id)

		return query.limit(limit).all()

	@staticmethod
	def get_jobs_with_applications(db: Session, user_id: int, limit: int = 100) -> List[Job]:
		"""
		Get user's jobs with applications eagerly loaded.

		Args:
		    db: Database session
		    user_id: User ID to fetch jobs for
		    limit: Maximum number of jobs to return

		Returns:
		    List of jobs with applications loaded
		"""
		return db.query(Job).options(selectinload(Job.applications)).filter(Job.user_id == user_id).limit(limit).all()

	@staticmethod
	def get_application_with_relations(db: Session, application_id: int) -> Optional[Application]:
		"""
		Get application with user and job eagerly loaded.

		Args:
		    db: Database session
		    application_id: Application ID to fetch

		Returns:
		    Application with relationships loaded or None
		"""
		return (
			db.query(Application).options(joinedload(Application.user), joinedload(Application.job)).filter(Application.id == application_id).first()
		)

	@staticmethod
	def get_applications_with_jobs(db: Session, user_id: int, limit: int = 100) -> List[Application]:
		"""
		Get user's applications with job details eagerly loaded.

		Args:
		    db: Database session
		    user_id: User ID to fetch applications for
		    limit: Maximum number of applications to return

		Returns:
		    List of applications with jobs loaded
		"""
		return db.query(Application).options(joinedload(Application.job)).filter(Application.user_id == user_id).limit(limit).all()

	@staticmethod
	def get_latest_applications_with_jobs(db: Session, user_id: int, limit: int = 10) -> List[Application]:
		"""
		Get user's latest applications with job details.
		Optimized for dashboard views.

		Args:
		    db: Database session
		    user_id: User ID to fetch applications for
		    limit: Maximum number of applications to return

		Returns:
		    List of recent applications with jobs loaded
		"""
		return (
			db.query(Application)
			.options(joinedload(Application.job))
			.filter(Application.user_id == user_id)
			.order_by(Application.created_at.desc())
			.limit(limit)
			.all()
		)

	@staticmethod
	def optimize_query_for_model(query: Query, model: Type[ModelType], relationships: List[str]) -> Query:
		"""
		Generic method to add eager loading to a query.

		Args:
		    query: SQLAlchemy query object
		    model: Model class being queried
		    relationships: List of relationship names to eager load

		Returns:
		    Query with eager loading applied
		"""
		for rel in relationships:
			# Use selectinload for one-to-many, joinedload for many-to-one
			if hasattr(model, rel):
				rel_property = getattr(model, rel).property
				if rel_property.uselist:
					# One-to-many or many-to-many
					query = query.options(selectinload(getattr(model, rel)))
				else:
					# Many-to-one
					query = query.options(joinedload(getattr(model, rel)))

		return query


# Convenience functions for common patterns


def get_user_dashboard_data(db: Session, user_id: int) -> Optional[User]:
	"""
	Get all data needed for user dashboard in a single optimized query.

	Args:
	    db: Database session
	    user_id: User ID

	Returns:
	    User with all dashboard data loaded
	"""
	return (
		db.query(User)
		.options(
			selectinload(User.jobs).options(selectinload(Job.applications)),
			selectinload(User.applications).options(joinedload(Application.job)),
			selectinload(User.feedback),
		)
		.filter(User.id == user_id)
		.first()
	)


def get_job_details_for_listing(db: Session, job_ids: List[int]) -> List[Job]:
	"""
	Get job details optimized for listing pages.

	Args:
	    db: Database session
	    job_ids: List of job IDs to fetch

	Returns:
	    List of jobs with necessary relationships loaded
	"""
	return db.query(Job).options(joinedload(Job.user)).filter(Job.id.in_(job_ids)).all()


def get_user_profile_data(db: Session, user_id: int) -> Optional[User]:
	"""
	Get all data needed for user profile page.

	Args:
	    db: Database session
	    user_id: User ID

	Returns:
	    User with profile data loaded
	"""
	return db.query(User).options(selectinload(User.jobs), selectinload(User.applications)).filter(User.id == user_id).first()


# Export optimizer instance
query_optimizer = QueryOptimizer()
