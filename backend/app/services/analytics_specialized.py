"""
Analytics Specialized Service - Backward Compatibility Layer.

This service provides backward compatibility for existing endpoints
while using the consolidated analytics service under the hood.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from .analytics_service import AnalyticsService

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

	Wraps consolidated analytics service to maintain existing API contracts.
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
			# Use consolidated analytics service
			analytics_service = AnalyticsService(db=db)
			return analytics_service.calculate_detailed_success_rates(user_id=user_id, days=days)

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
			# Use consolidated analytics service
			analytics_service = AnalyticsService(db=db)
			return analytics_service.calculate_conversion_rates(user_id=user_id, days=days)

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
			# Use consolidated analytics service
			analytics_service = AnalyticsService(db=db)
			return analytics_service.generate_performance_benchmarks(user_id=user_id, days=days)

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
			# Use consolidated analytics service
			analytics_service = AnalyticsService()
			return analytics_service.track_slack_event(event)

		except Exception as e:
			logger.error(f"Failed to track Slack event: {e!s}")
			return False


# Singleton instance for backward compatibility
analytics_specialized_service = AnalyticsSpecializedService()
