"""
Analytics Specialized Service - Backward Compatibility Layer.

This service provides backward compatibility for existing endpoints
while using the new production-grade analytics services under the hood.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from .analytics_processing_service import AnalyticsProcessingService
from .analytics_query_service import AnalyticsQueryService
from .analytics_reporting_service import AnalyticsReportingService

logger = logging.getLogger(__name__)


class SlackEventType(str, Enum):
	"""Slack event types for tracking."""

	MESSAGE = "message"
	REACTION = "reaction"
	FILE_UPLOAD = "file_upload"
	CHANNEL_JOIN = "channel_join"
	CHANNEL_LEAVE = "channel_leave"


class SlackEvent(BaseModel):
	"""Slack event model."""

	event_type: SlackEventType
	user_id: str
	channel_id: str
	timestamp: datetime
	metadata: Dict[str, Any] = {}


class AnalyticsSpecializedService:
	"""
	Specialized analytics service for backward compatibility.

	Wraps new production-grade analytics services to maintain
	existing API contracts.
	"""

	def __init__(self) -> None:
		"""Initialize analytics specialized service."""
		logger.info("AnalyticsSpecializedService initialized (backward compatibility layer)")

	def calculate_detailed_success_rates(self, db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
		"""
		Calculate detailed success rates for user applications.

		Args:
		    db: Database session
		    user_id: User identifier
		    days: Number of days to analyze

		Returns:
		    Dict with success rate analysis
		"""
		try:
			# Use new analytics processing service
			processing = AnalyticsProcessingService(db=db)

			# Get user analytics
			analytics = processing.get_user_analytics(user_id=user_id)

			# Calculate rates
			total_apps = analytics.get("applications_submitted", 0)
			interviews = analytics.get("interviews_scheduled", 0)
			offers = analytics.get("offers_received", 0)

			interview_rate = (interviews / total_apps * 100) if total_apps > 0 else 0
			offer_rate = (offers / total_apps * 100) if total_apps > 0 else 0

			return {
				"user_id": user_id,
				"period_days": days,
				"total_applications": total_apps,
				"total_interviews": interviews,
				"total_offers": offers,
				"interview_rate": round(interview_rate, 2),
				"offer_rate": round(offer_rate, 2),
				"success_rate": round(offer_rate, 2),  # Alias for compatibility
			}

		except Exception as e:
			logger.error(f"Failed to calculate success rates: {e!s}")
			return {"error": str(e), "user_id": user_id}

	def calculate_conversion_rates(self, db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
		"""
		Calculate conversion funnel rates.

		Args:
		    db: Database session
		    user_id: User identifier
		    days: Number of days to analyze

		Returns:
		    Dict with conversion funnel analysis
		"""
		try:
			# Use new analytics processing service
			processing = AnalyticsProcessingService(db=db)

			# Get funnel data
			start_date = datetime.now(timezone.utc) - timedelta(days=days)
			funnel = processing.process_user_funnel(user_id=user_id, start_date=start_date)

			return {
				"user_id": user_id,
				"period_days": days,
				"funnel": funnel,
				"overall_conversion": funnel.get("offered", {}).get("conversion", 0),
			}

		except Exception as e:
			logger.error(f"Failed to calculate conversion rates: {e!s}")
			return {"error": str(e), "user_id": user_id}

	def generate_performance_benchmarks(self, db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
		"""
		Generate performance benchmarks comparing user to averages.

		Args:
		    db: Database session
		    user_id: User identifier
		    days: Number of days to analyze

		Returns:
		    Dict with benchmark comparison
		"""
		try:
			# Use new analytics reporting service
			reporting = AnalyticsReportingService(db=db)

			# Get user insights
			insights = reporting.generate_user_insights(user_id=user_id, days=days)

			# Get market trends for comparison
			trends = reporting.analyze_market_trends(user_id=user_id, days=days)

			metrics = insights.get("metrics", {})

			return {
				"user_id": user_id,
				"period_days": days,
				"user_metrics": metrics,
				"market_overview": trends.get("market_overview", {}),
				"insights": insights.get("insights", []),
				"performance_summary": {
					"applications": metrics.get("applications", 0),
					"interviews": metrics.get("interviews", 0),
					"offers": metrics.get("offers", 0),
					"interview_rate": metrics.get("interview_rate", 0),
				},
			}

		except Exception as e:
			logger.error(f"Failed to generate benchmarks: {e!s}")
			return {"error": str(e), "user_id": user_id}

	def track_slack_event(self, event: SlackEvent) -> bool:
		"""
		Track Slack integration event.

		Args:
		    event: Slack event to track

		Returns:
		    Success status
		"""
		try:
			logger.info(f"Slack event tracked: {event.event_type} from user {event.user_id}")
			# Could integrate with analytics collection service if needed
			return True

		except Exception as e:
			logger.error(f"Failed to track Slack event: {e!s}")
			return False


# Singleton instance for backward compatibility
analytics_specialized_service = AnalyticsSpecializedService()
