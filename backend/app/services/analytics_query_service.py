"""Production-grade Analytics Query Service.

Features:
- Flexible metric retrieval with filtering
- Time-series data aggregation
- Caching for performance
- Custom query building
- Real-time and historical data access
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AnalyticsQueryService:
	"""
	Comprehensive analytics query and retrieval service.

	Provides flexible querying capabilities for analytics data
	with support for filtering, aggregation, and time-series analysis.
	"""

	def __init__(self, db: Session | None = None) -> None:
		"""
		Initialize analytics query service.

		Args:
		    db: Database session for queries
		"""
		self.db = db
		self._cache: Dict[str, tuple[Any, datetime]] = {}
		self._cache_ttl = timedelta(minutes=5)
		logger.info("AnalyticsQueryService initialized")

	def get_metrics(
		self, user_id: int, timeframe: str | None = None, metric_types: List[str] | None = None, use_cache: bool = True
	) -> Dict[str, Any]:
		"""
		Retrieve analytics metrics for a user.

		Args:
		    user_id: User identifier
		    timeframe: Time period ('day', 'week', 'month', 'year', 'all')
		    metric_types: Specific metrics to retrieve
		    use_cache: Whether to use cached results

		Returns:
		    Dict with requested metrics
		"""
		cache_key = f"metrics_{user_id}_{timeframe}_{metric_types}"

		# Check cache
		if use_cache and cache_key in self._cache:
			cached_data, cache_time = self._cache[cache_key]
			if datetime.now(timezone.utc) - cache_time < self._cache_ttl:
				logger.debug(f"Returning cached metrics for user {user_id}")
				return cached_data

		try:
			# Determine time range
			start_date, end_date = self._parse_timeframe(timeframe)

			if not self.db:
				return {"user_id": user_id, "timeframe": timeframe or "all", "metrics": {}}

			from ..models.application import Application
			from ..models.interview import Interview
			from ..models.job import Job

			# Build metrics
			metrics: Dict[str, Any] = {}

			# Job metrics
			if not metric_types or "jobs" in metric_types:
				job_query = self.db.query(func.count(Job.id)).filter(Job.user_id == user_id)
				if start_date:
					job_query = job_query.filter(Job.date_added >= start_date)
				if end_date:
					job_query = job_query.filter(Job.date_added <= end_date)

				metrics["jobs_saved"] = job_query.scalar() or 0

			# Application metrics
			if not metric_types or "applications" in metric_types:
				app_query = self.db.query(func.count(Application.id)).filter(Application.user_id == user_id)
				if start_date:
					app_query = app_query.filter(Application.created_at >= start_date)
				if end_date:
					app_query = app_query.filter(Application.created_at <= end_date)

				metrics["applications_submitted"] = app_query.scalar() or 0

				# Application status breakdown
				status_query = self.db.query(Application.status, func.count(Application.id)).filter(Application.user_id == user_id)
				if start_date:
					status_query = status_query.filter(Application.created_at >= start_date)
				if end_date:
					status_query = status_query.filter(Application.created_at <= end_date)

				status_counts = dict(status_query.group_by(Application.status).all())
				metrics["application_status_breakdown"] = status_counts

			# Interview metrics
			if not metric_types or "interviews" in metric_types:
				interview_query = self.db.query(func.count(Interview.id)).filter(Interview.user_id == user_id)
				if start_date:
					interview_query = interview_query.filter(Interview.scheduled_at >= start_date)
				if end_date:
					interview_query = interview_query.filter(Interview.scheduled_at <= end_date)

				metrics["interviews_scheduled"] = interview_query.scalar() or 0

			result = {"user_id": user_id, "timeframe": timeframe or "all", "start_date": start_date, "end_date": end_date, "metrics": metrics}

			# Cache result
			self._cache[cache_key] = (result, datetime.now(timezone.utc))

			logger.info(f"Retrieved metrics for user {user_id} (timeframe: {timeframe})")
			return result

		except Exception as e:
			logger.error(f"Failed to get metrics for user {user_id}: {e!s}")
			return {"user_id": user_id, "error": str(e)}

	def get_time_series(self, user_id: int, metric: str, start_date: datetime, end_date: datetime, granularity: str = "day") -> Dict[str, Any]:
		"""
		Get time-series data for a specific metric.

		Args:
		    user_id: User identifier
		    metric: Metric to retrieve
		    start_date: Start of time range
		    end_date: End of time range
		    granularity: Data granularity ('hour', 'day', 'week', 'month')

		Returns:
		    Dict with time-series data points
		"""
		try:
			if not self.db:
				return {"error": "Database connection required"}

			from ..models.application import Application

			# Build time-series query based on granularity
			if metric == "applications":
				query = (
					self.db.query(func.date_trunc(granularity, Application.created_at).label("period"), func.count(Application.id).label("count"))
					.filter(
						and_(
							Application.user_id == user_id,
							Application.created_at >= start_date,
							Application.created_at <= end_date,
						)
					)
					.group_by("period")
					.order_by("period")
				)

				results = query.all()

				return {
					"metric": metric,
					"granularity": granularity,
					"data_points": [{"period": str(period), "value": count} for period, count in results],
					"total": sum(count for _, count in results),
				}

			return {"error": f"Unsupported metric: {metric}"}

		except Exception as e:
			logger.error(f"Failed to get time series: {e!s}")
			return {"error": str(e)}

	def _parse_timeframe(self, timeframe: str | None) -> tuple[datetime | None, datetime | None]:
		"""
		Parse timeframe string into start and end dates.

		Args:
		    timeframe: Timeframe string

		Returns:
		    Tuple of (start_date, end_date)
		"""
		now = datetime.now(timezone.utc)

		if not timeframe or timeframe == "all":
			return (None, None)
		elif timeframe == "day" or timeframe == "today":
			start = now.replace(hour=0, minute=0, second=0, microsecond=0)
			return (start, now)
		elif timeframe == "week":
			start = now - timedelta(days=7)
			return (start, now)
		elif timeframe == "month":
			start = now - timedelta(days=30)
			return (start, now)
		elif timeframe == "year":
			start = now - timedelta(days=365)
			return (start, now)
		else:
			# Try to parse as number of days
			try:
				days = int(timeframe)
				start = now - timedelta(days=days)
				return (start, now)
			except ValueError:
				logger.warning(f"Invalid timeframe: {timeframe}, using 'all'")
				return (None, None)

	def clear_cache(self, user_id: int | None = None) -> None:
		"""
		Clear query cache.

		Args:
		    user_id: Optional user ID to clear specific cache
		"""
		if user_id:
			keys_to_remove = [k for k in self._cache.keys() if f"_{user_id}_" in k]
			for key in keys_to_remove:
				del self._cache[key]
			logger.info(f"Cleared cache for user {user_id}")
		else:
			self._cache.clear()
			logger.info("Cleared all query cache")

	async def health_check(self) -> Dict[str, Any]:
		"""
		Perform health check on query service.

		Returns:
		    Dict with health status
		"""
		try:
			return {
				"status": "healthy",
				"cache_size": len(self._cache),
				"cache_ttl_seconds": self._cache_ttl.total_seconds(),
			}

		except Exception as e:
			logger.error(f"Health check failed: {e!s}")
			return {"status": "unhealthy", "error": str(e)}
