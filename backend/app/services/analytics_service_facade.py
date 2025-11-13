"""Analytics Service Facade - Unified Interface for Analytics Operations.

Provides a unified interface over all analytics services:
- Collection
- Processing
- Querying
- Reporting

Features:
- Simplified API for common operations
- Coordinated health checks
- Backward compatibility
- Transaction management
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

# Removed: from .analytics_collection_service import AnalyticsCollectionService
from .analytics_service import AnalyticsService # Import the consolidated AnalyticsService
from .analytics_processing_service import AnalyticsProcessingService
from .analytics_query_service import AnalyticsQueryService
from .analytics_reporting_service import AnalyticsReportingService

logger = logging.getLogger(__name__)


class AnalyticsServiceFacade:
	"""
	Unified facade for all analytics operations.

	Simplifies analytics usage by providing a single
	interface over collection, processing, query, and reporting.
	"""

	def __init__(self, db: Session | None = None) -> None:
		"""
		Initialize analytics facade with all underlying services.

		Args:
		    db: Database session for all services
		"""
		self.db = db
		self.analytics_service = AnalyticsService(db=db) # Use the consolidated AnalyticsService
		self.processing = AnalyticsProcessingService(db=db)
		self.query = AnalyticsQueryService(db=db)
		self.reporting = AnalyticsReportingService(db=db)
		logger.info("AnalyticsServiceFacade initialized with all services")

	# ========================================
	# Collection Operations (Simplified API)
	# ========================================

	async def track_event( # Made async
		self,
		event_type: str,
		user_id: int | None = None,
		session_id: str | None = None,
		data: Dict[str, Any] | None = None,
	) -> bool:
		"""
		Track a single analytics event.

		Args:
		    event_type: Type of event (e.g., "page_view", "job_search")
		    user_id: Optional user ID
		    session_id: Optional session ID
		    data: Optional event data

		Returns:
		    Success status
		"""
		# Collection service is sync, not async
		if user_id is None:
			user_id = 0  # Default for anonymous users

		return await self.analytics_service.collect_event( # Changed to analytics_service and awaited
			user_id=user_id,
			event_type=event_type,
			event_data=data or {},
			session_id=session_id,
		)

	async def track_page_view(self, user_id: int | None, path: str, session_id: str | None = None) -> bool:
		"""
		Track page view event.

		Args:
		    user_id: User ID (if logged in)
		    path: Page path
		    session_id: Session ID

		Returns:
		    Success status
		"""
		return await self.track_event(
			event_type="page_view",
			user_id=user_id,
			session_id=session_id,
			data={"path": path},
		)

	async def track_job_search(self, user_id: int, query: str, filters: Dict[str, Any] | None = None) -> bool:
		"""
		Track job search event.

		Args:
		    user_id: User ID
		    query: Search query
		    filters: Search filters applied

		Returns:
		    Success status
		"""
		return await self.track_event(
			event_type="job_search",
			user_id=user_id,
			data={"query": query, "filters": filters or {}},
		)

	async def track_job_view(self, user_id: int, job_id: int, source: str | None = None) -> bool:
		"""
		Track job view event.

		Args:
		    user_id: User ID
		    job_id: Job ID viewed
		    source: Source of view (e.g., "search", "recommendations")

		Returns:
		    Success status
		"""
		return await self.track_event(
			event_type="job_view",
			user_id=user_id,
			data={"job_id": job_id, "source": source},
		)

	async def track_application_submitted(self, user_id: int, job_id: int, application_id: int) -> bool:
		"""
		Track application submission event.

		Args:
		    user_id: User ID
		    job_id: Job ID
		    application_id: Application ID

		Returns:
		    Success status
		"""
		return await self.track_event(
			event_type="application_submitted",
			user_id=user_id,
			data={"job_id": job_id, "application_id": application_id},
		)

	# ========================================
	# Processing Operations
	# ========================================

	def get_user_analytics(self, user_id: int, start_date: datetime | None = None, end_date: datetime | None = None) -> Dict[str, Any]:
		"""
		Get comprehensive user analytics.

		Args:
		    user_id: User ID
		    start_date: Optional start date
		    end_date: Optional end date

		Returns:
		    User analytics data
		"""
		return self.processing.get_user_analytics(
			user_id=user_id,
			start_date=start_date,
			end_date=end_date,
		)

	def get_user_funnel(self, user_id: int, start_date: datetime | None = None, end_date: datetime | None = None) -> Dict[str, Any]:
		"""
		Get user conversion funnel.

		Args:
		    user_id: User ID
		    start_date: Optional start date
		    end_date: Optional end date

		Returns:
		    Funnel data with conversion rates
		"""
		return self.processing.process_user_funnel(
			user_id=user_id,
			start_date=start_date,
			end_date=end_date,
		)

	def get_engagement_score(self, user_id: int, start_date: datetime | None = None, end_date: datetime | None = None) -> float:
		"""
		Calculate user engagement score.

		Args:
		    user_id: User ID
		    start_date: Optional start date
		    end_date: Optional end date

		Returns:
		    Engagement score (0-100)
		"""
		return self.processing.calculate_engagement_score(
			user_id=user_id,
			start_date=start_date,
			end_date=end_date,
		)

	# ========================================
	# Query Operations
	# ========================================

	def get_metrics(
		self,
		user_id: int,
		metric_types: List[str] | None = None,
		timeframe: str = "month",
	) -> Dict[str, Any]:
		"""
		Get user metrics.

		Args:
		    user_id: User ID
		    metric_types: Types of metrics to retrieve
		    timeframe: Time period (day/week/month/year/all)

		Returns:
		    Metrics data
		"""
		return self.query.get_metrics(
			user_id=user_id,
			metric_types=metric_types,
			timeframe=timeframe,
		)

	def get_time_series(
		self,
		user_id: int,
		metric_type: str,
		start_date: datetime | None = None,
		end_date: datetime | None = None,
		granularity: str = "day",
	) -> List[Dict[str, Any]]:
		"""
		Get time-series data for a metric.

		Args:
		    user_id: User ID
		    metric_type: Metric type
		    start_date: Optional start date
		    end_date: Optional end date
		    granularity: Aggregation granularity (hour/day/week/month)

		Returns:
		    Time-series data points
		"""
		return self.query.get_time_series(
			user_id=user_id,
			metric_type=metric_type,
			start_date=start_date,
			end_date=end_date,
			granularity=granularity,
		)

	# ========================================
	# Reporting Operations
	# ========================================

	def get_market_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
		"""
		Analyze market trends for user.

		Args:
		    user_id: User ID
		    days: Number of days to analyze

		Returns:
		    Market trend analysis
		"""
		return self.reporting.analyze_market_trends(user_id=user_id, days=days)

	def get_user_insights(self, user_id: int, days: int = 30) -> Dict[str, Any]:
		"""
		Generate personalized user insights.

		Args:
		    user_id: User ID
		    days: Number of days to analyze

		Returns:
		    User insights and recommendations
		"""
		return self.reporting.generate_user_insights(user_id=user_id, days=days)

	def get_weekly_summary(self, user_id: int) -> Dict[str, Any]:
		"""
		Generate weekly summary for user.

		Args:
		    user_id: User ID

		Returns:
		    Weekly activity summary
		"""
		return self.reporting.generate_weekly_summary(user_id=user_id)

	# ========================================
	# Dashboard Operations (Convenience Methods)
	# ========================================

	def get_dashboard_data(self, user_id: int) -> Dict[str, Any]:
		"""
		Get comprehensive dashboard data for user.

		Combines analytics, metrics, and insights in one call.

		Args:
		    user_id: User ID

		Returns:
		    Complete dashboard data
		"""
		try:
			# Get current analytics
			analytics = self.get_user_analytics(user_id=user_id)

			# Get engagement score
			engagement = self.get_engagement_score(user_id=user_id)

			# Get conversion funnel
			funnel = self.get_user_funnel(user_id=user_id)

			# Get recent metrics
			metrics = self.get_metrics(user_id=user_id, timeframe="week")

			# Get insights
			insights = self.get_user_insights(user_id=user_id, days=7)

			return {
				"user_id": user_id,
				"analytics": analytics,
				"engagement_score": engagement,
				"funnel": funnel,
				"metrics": metrics,
				"insights": insights,
				"generated_at": datetime.now(timezone.utc).isoformat(),
			}

		except Exception as e:
			logger.error(f"Failed to get dashboard data for user {user_id}: {e!s}")
			return {"error": str(e)}

	# ========================================
	# Health & Maintenance
	# ========================================

	async def health_check(self) -> Dict[str, Any]:
		"""
		Perform health check on all analytics services.

		Returns:
		    Dict with health status of all services
		"""
		try:
			collection_health = await self.analytics_service.health_check_collection() # Changed and awaited
			processing_health = await self.processing.health_check()
			query_health = await self.query.health_check()
			reporting_health = await self.reporting.health_check()

			all_healthy = all(h.get("status") == "healthy" for h in [collection_health, processing_health, query_health, reporting_health])

			return {
				"status": "healthy" if all_healthy else "degraded",
				"services": {
					"collection": collection_health,
					"processing": processing_health,
					"query": query_health,
					"reporting": reporting_health,
				},
			}

		except Exception as e:
			logger.error(f"Health check failed: {e!s}")
			return {"status": "unhealthy", "error": str(e)}

	def clear_all_caches(self) -> None:
		"""Clear caches in all services."""
		try:
			self.query.clear_cache()
			logger.info("All analytics caches cleared")
		except Exception as e:
			logger.error(f"Failed to clear caches: {e!s}")

	def get_collection_stats(self) -> Dict[str, Any]:
		"""Get statistics from collection service."""
		return self.analytics_service.get_stats() # Changed to analytics_service
