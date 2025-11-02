"""
API endpoints for briefing management and engagement tracking
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.briefing_service import briefing_service
from ...tasks.email_tasks import send_morning_briefing_task, send_evening_summary_task, track_email_engagement

logger = logging.getLogger(__name__)

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(prefix="/briefings", tags=["briefings"])


class BriefingPreferences(BaseModel):
	"""Briefing preferences model"""

	morning_briefing_enabled: bool = Field(default=True, description="Enable morning briefings")
	evening_summary_enabled: bool = Field(default=True, description="Enable evening summaries")
	preferred_morning_time: Optional[str] = Field(default=None, description="Preferred morning time (HH:MM format)")
	preferred_evening_time: Optional[str] = Field(default=None, description="Preferred evening time (HH:MM format)")
	timezone: Optional[str] = Field(default="UTC", description="User timezone")


class EmailEngagement(BaseModel):
	"""Email engagement tracking model"""

	email_type: str = Field(..., description="Type of email (morning_briefing, evening_summary)")
	action: str = Field(..., description="Action taken (opened, clicked, applied)")


@router.get("/preferences")
async def get_briefing_preferences(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
	"""
	Get user's briefing preferences and optimal timing
	"""
	try:
		# Get current preferences
		email_settings = current_user.settings.get("email_notifications", {})

		# Get optimal timing based on engagement patterns
		optimal_morning, optimal_evening = briefing_service.get_optimal_briefing_times(db, current_user.id)

		return {
			"preferences": {
				"morning_briefing_enabled": email_settings.get("morning_briefing", True),
				"evening_summary_enabled": email_settings.get("evening_summary", True),
				"preferred_morning_time": email_settings.get("preferred_morning_time"),
				"preferred_evening_time": email_settings.get("preferred_evening_time"),
				"timezone": email_settings.get("timezone", "UTC"),
			},
			"optimal_timing": {"morning": optimal_morning.strftime("%H:%M"), "evening": optimal_evening.strftime("%H:%M")},
			"engagement_stats": await _get_engagement_stats(db, current_user.id),
		}

	except Exception as e:
		logger.error(f"Error getting briefing preferences for user {current_user.id}: {e}")
		raise HTTPException(status_code=500, detail="Failed to get briefing preferences")


@router.put("/preferences")
async def update_briefing_preferences(
	preferences: BriefingPreferences, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
	"""
	Update user's briefing preferences
	"""
	try:
		# Initialize email_notifications if not exists
		if "email_notifications" not in current_user.settings:
			current_user.settings["email_notifications"] = {}

		# Update preferences
		current_user.settings["email_notifications"].update(
			{
				"morning_briefing": preferences.morning_briefing_enabled,
				"evening_summary": preferences.evening_summary_enabled,
				"timezone": preferences.timezone,
			}
		)

		# Update preferred times if provided
		if preferences.preferred_morning_time:
			try:
				# Validate time format
				time.fromisoformat(preferences.preferred_morning_time)
				current_user.settings["email_notifications"]["preferred_morning_time"] = preferences.preferred_morning_time
			except ValueError:
				raise HTTPException(status_code=400, detail="Invalid morning time format. Use HH:MM")

		if preferences.preferred_evening_time:
			try:
				# Validate time format
				time.fromisoformat(preferences.preferred_evening_time)
				current_user.settings["email_notifications"]["preferred_evening_time"] = preferences.preferred_evening_time
			except ValueError:
				raise HTTPException(status_code=400, detail="Invalid evening time format. Use HH:MM")

		# Mark settings as modified for SQLAlchemy
		current_user.settings = current_user.settings.copy()

		await db.commit()

		logger.info(f"Updated briefing preferences for user {current_user.id}")

		return {
			"status": "success",
			"message": "Briefing preferences updated successfully",
			"preferences": current_user.settings["email_notifications"],
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error updating briefing preferences for user {current_user.id}: {e}")
		db.rollback()
		raise HTTPException(status_code=500, detail="Failed to update briefing preferences")


@router.post("/send-morning-briefing")
async def send_morning_briefing_now(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
	"""
	Send morning briefing immediately (for testing or manual trigger)
	"""
	try:
		# Schedule the task
		task = send_morning_briefing_task.delay(current_user.id)

		logger.info(f"Manual morning briefing triggered for user {current_user.id}")

		return {"status": "success", "message": "Morning briefing scheduled", "task_id": task.id}

	except Exception as e:
		logger.error(f"Error sending morning briefing for user {current_user.id}: {e}")
		raise HTTPException(status_code=500, detail="Failed to send morning briefing")


@router.post("/send-evening-summary")
async def send_evening_summary_now(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
	"""
	Send evening summary immediately (for testing or manual trigger)
	"""
	try:
		# Schedule the task
		task = send_evening_summary_task.delay(current_user.id)

		logger.info(f"Manual evening summary triggered for user {current_user.id}")

		return {"status": "success", "message": "Evening summary scheduled", "task_id": task.id}

	except Exception as e:
		logger.error(f"Error sending evening summary for user {current_user.id}: {e}")
		raise HTTPException(status_code=500, detail="Failed to send evening summary")


@router.post("/track-engagement")
async def track_engagement(engagement: EmailEngagement, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
	"""
	Track email engagement for adaptive timing
	"""
	try:
		# Validate email type
		valid_email_types = ["morning_briefing", "evening_summary"]
		if engagement.email_type not in valid_email_types:
			raise HTTPException(status_code=400, detail=f"Invalid email type. Must be one of: {valid_email_types}")

		# Validate action
		valid_actions = ["opened", "clicked", "applied"]
		if engagement.action not in valid_actions:
			raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")

		# Schedule engagement tracking task
		track_email_engagement.delay(current_user.id, engagement.email_type, engagement.action)

		logger.info(f"Engagement tracked for user {current_user.id}: {engagement.email_type} {engagement.action}")

		return {"status": "success", "message": "Engagement tracked successfully"}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error tracking engagement for user {current_user.id}: {e}")
		raise HTTPException(status_code=500, detail="Failed to track engagement")


@router.get("/preview/morning-briefing")
async def preview_morning_briefing(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
	"""
	Preview morning briefing content without sending email
	"""
	try:
		# Generate briefing data
		briefing_data = briefing_service.generate_morning_briefing_data(db, current_user.id)

		return {"status": "success", "preview": briefing_data, "message": "Morning briefing preview generated"}

	except Exception as e:
		logger.error(f"Error generating morning briefing preview for user {current_user.id}: {e}")
		raise HTTPException(status_code=500, detail="Failed to generate morning briefing preview")


@router.get("/preview/evening-summary")
async def preview_evening_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
	"""
	Preview evening summary content without sending email
	"""
	try:
		# Generate summary data
		summary_data = briefing_service.generate_evening_summary_data(db, current_user.id)

		return {"status": "success", "preview": summary_data, "message": "Evening summary preview generated"}

	except Exception as e:
		logger.error(f"Error generating evening summary preview for user {current_user.id}: {e}")
		raise HTTPException(status_code=500, detail="Failed to generate evening summary preview")


@router.get("/analytics")
async def get_briefing_analytics(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
	days: int = Query(default=30, ge=1, le=90, description="Number of days to analyze"),
) -> Dict[str, Any]:
	"""
	Get briefing analytics and engagement patterns
	"""
	try:
		# Get engagement analytics
		engagement_stats = await _get_engagement_stats(db, current_user.id, days)

		# Get optimal timing
		optimal_morning, optimal_evening = briefing_service.get_optimal_briefing_times(db, current_user.id)

		return {
			"status": "success",
			"analytics": {
				"engagement_stats": engagement_stats,
				"optimal_timing": {"morning": optimal_morning.strftime("%H:%M"), "evening": optimal_evening.strftime("%H:%M")},
				"period_days": days,
			},
		}

	except Exception as e:
		logger.error(f"Error getting briefing analytics for user {current_user.id}: {e}")
		raise HTTPException(status_code=500, detail="Failed to get briefing analytics")


# Helper functions


async def _get_engagement_stats(db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
	"""Get engagement statistics for the user"""
	try:
		from ...models.analytics import Analytics
		from datetime import timedelta

		cutoff_date = datetime.now() - timedelta(days=days)

		# Get engagement data
		result = await db.execute(
			select(Analytics).where(
				Analytics.user_id == user_id,
				Analytics.type == "email_engagement",
				Analytics.generated_at >= cutoff_date
			)
		)
		engagement_data = result.scalars().all()

		if not engagement_data:
			return {
				"total_emails_sent": 0,
				"total_opens": 0,
				"total_clicks": 0,
				"total_applications": 0,
				"open_rate": 0,
				"click_rate": 0,
				"application_rate": 0,
			}

		# Calculate stats
		total_sent = len([e for e in engagement_data if e.data.get("action") == "sent"])
		total_opens = len([e for e in engagement_data if e.data.get("action") == "opened"])
		total_clicks = len([e for e in engagement_data if e.data.get("action") == "clicked"])
		total_applications = len([e for e in engagement_data if e.data.get("action") == "applied"])

		return {
			"total_emails_sent": total_sent,
			"total_opens": total_opens,
			"total_clicks": total_clicks,
			"total_applications": total_applications,
			"open_rate": (total_opens / total_sent * 100) if total_sent > 0 else 0,
			"click_rate": (total_clicks / total_sent * 100) if total_sent > 0 else 0,
			"application_rate": (total_applications / total_sent * 100) if total_sent > 0 else 0,
		}

	except Exception as e:
		logger.error(f"Error getting engagement stats for user {user_id}: {e}")
		return {}
