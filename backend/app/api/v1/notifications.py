"""
Consolidated Notification Management API

This module provides comprehensive notification functionality including:
- CRUD operations for notifications
- Bulk operations (mark read, delete)
- Notification preferences management
- Opt-in/opt-out controls
- Scheduled notification testing
- Statistics (user-specific and admin)

Consolidated from notifications.py and notifications_v2.py to eliminate duplication.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...dependencies import get_current_user
from ...models.notification import (
	Notification,
	NotificationPriority,
	NotificationType,
)
from ...models.notification import (
	NotificationPreferences as NotificationPreferencesModel,
)
from ...models.user import User
from ...schemas.notification import (
	NotificationBulkDeleteRequest,
	NotificationListResponse,
	NotificationMarkReadRequest,
	NotificationPreferencesResponse,
	NotificationPreferencesUpdate,
	NotificationResponse,
	NotificationStatistics,
)
from ...services.notification_service import notification_service as scheduled_notification_service
from ...utils.datetime import utc_now

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ============================================================================
# SECTION 1: NOTIFICATION CRUD OPERATIONS
# ============================================================================


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
	skip: int = Query(0, ge=0, description="Number of notifications to skip"),
	limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
	unread_only: bool = Query(False, description="Return only unread notifications"),
	notification_type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
	priority: Optional[NotificationPriority] = Query(None, description="Filter by priority"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
	"""
	Get paginated list of notifications for the current user.

	Supports filtering by:
	- Read/unread status
	- Notification type
	- Priority level
	"""
	# Build query with filters
	query = select(Notification).where(Notification.user_id == current_user.id)

	if unread_only:
		query = query.where(Notification.is_read == False)

	if notification_type:
		query = query.where(Notification.type == notification_type)

	if priority:
		query = query.where(Notification.priority == priority)

	# Order by created_at descending (newest first)
	query = query.order_by(desc(Notification.created_at))

	# Get total count
	count_query = select(func.count()).select_from(Notification).where(Notification.user_id == current_user.id)
	if unread_only:
		count_query = count_query.where(Notification.is_read == False)
	if notification_type:
		count_query = count_query.where(Notification.type == notification_type)
	if priority:
		count_query = count_query.where(Notification.priority == priority)

	total_result = await db.execute(count_query)
	total = total_result.scalar() or 0

	# Get unread count
	unread_query = select(func.count()).select_from(Notification).where(and_(Notification.user_id == current_user.id, Notification.is_read == False))
	unread_result = await db.execute(unread_query)
	unread_count = unread_result.scalar() or 0

	# Apply pagination
	query = query.offset(skip).limit(limit)

	# Execute query
	result = await db.execute(query)
	notifications = result.scalars().all()

	return NotificationListResponse(
		notifications=[NotificationResponse.from_orm(n) for n in notifications],
		total=total,
		unread_count=unread_count,
		page=skip // limit + 1,
		page_size=limit,
	)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
	notification_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
	"""Get a specific notification by ID"""
	query = select(Notification).where(and_(Notification.id == notification_id, Notification.user_id == current_user.id))
	result = await db.execute(query)
	notification = result.scalar_one_or_none()

	if not notification:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Notification with id {notification_id} not found",
		)

	return NotificationResponse.from_orm(notification)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
	notification_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
	"""Mark a notification as read"""
	query = select(Notification).where(and_(Notification.id == notification_id, Notification.user_id == current_user.id))
	result = await db.execute(query)
	notification = result.scalar_one_or_none()

	if not notification:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Notification with id {notification_id} not found",
		)

	if not notification.is_read:
		notification.is_read = True
		notification.read_at = utc_now()
		await db.commit()
		await db.refresh(notification)

	return NotificationResponse.from_orm(notification)


@router.put("/{notification_id}/unread", response_model=NotificationResponse)
async def mark_notification_unread(
	notification_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
	"""Mark a notification as unread"""
	query = select(Notification).where(and_(Notification.id == notification_id, Notification.user_id == current_user.id))
	result = await db.execute(query)
	notification = result.scalar_one_or_none()

	if not notification:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Notification with id {notification_id} not found",
		)

	if notification.is_read:
		notification.is_read = False
		notification.read_at = None
		await db.commit()
		await db.refresh(notification)

	return NotificationResponse.from_orm(notification)


@router.delete("/{notification_id}")
async def delete_notification(
	notification_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	"""Delete a specific notification"""
	query = select(Notification).where(and_(Notification.id == notification_id, Notification.user_id == current_user.id))
	result = await db.execute(query)
	notification = result.scalar_one_or_none()

	if not notification:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Notification with id {notification_id} not found",
		)

	await db.delete(notification)
	await db.commit()

	return {
		"success": True,
		"message": f"Notification {notification_id} deleted successfully",
		"notification_id": notification_id,
	}


# ============================================================================
# SECTION 2: BULK OPERATIONS
# ============================================================================


@router.put("/read-all")
async def mark_all_notifications_read(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	"""Mark all notifications as read for the current user"""
	query = select(Notification).where(and_(Notification.user_id == current_user.id, Notification.is_read == False))
	result = await db.execute(query)
	notifications = result.scalars().all()

	count = 0
	for notification in notifications:
		notification.is_read = True
		notification.read_at = utc_now()
		count += 1

	await db.commit()

	return {
		"success": True,
		"message": f"Marked {count} notifications as read",
		"count": count,
	}


@router.post("/mark-read", response_model=dict)
async def mark_notifications_read(
	request: NotificationMarkReadRequest,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	"""Mark multiple notifications as read"""
	query = select(Notification).where(
		and_(
			Notification.id.in_(request.notification_ids),
			Notification.user_id == current_user.id,
			Notification.is_read == False,
		)
	)
	result = await db.execute(query)
	notifications = result.scalars().all()

	count = 0
	for notification in notifications:
		notification.is_read = True
		notification.read_at = utc_now()
		count += 1

	await db.commit()

	return {
		"success": True,
		"message": f"Marked {count} notifications as read",
		"count": count,
		"notification_ids": [n.id for n in notifications],
	}


@router.post("/bulk-delete")
async def bulk_delete_notifications(
	request: NotificationBulkDeleteRequest,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	"""Delete multiple notifications"""
	query = select(Notification).where(
		and_(
			Notification.id.in_(request.notification_ids),
			Notification.user_id == current_user.id,
		)
	)
	result = await db.execute(query)
	notifications = result.scalars().all()

	count = 0
	deleted_ids = []
	for notification in notifications:
		deleted_ids.append(notification.id)
		await db.delete(notification)
		count += 1

	await db.commit()

	return {
		"success": True,
		"message": f"Deleted {count} notifications",
		"count": count,
		"deleted_ids": deleted_ids,
	}


@router.delete("/all")
async def delete_all_notifications(
	read_only: bool = Query(False, description="Delete only read notifications"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	"""Delete all notifications for the current user"""
	query = select(Notification).where(Notification.user_id == current_user.id)

	if read_only:
		query = query.where(Notification.is_read == True)

	result = await db.execute(query)
	notifications = result.scalars().all()

	count = 0
	for notification in notifications:
		await db.delete(notification)
		count += 1

	await db.commit()

	return {
		"success": True,
		"message": f"Deleted {count} notifications",
		"count": count,
	}


# ============================================================================
# SECTION 3: NOTIFICATION PREFERENCES
# ============================================================================


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> NotificationPreferencesResponse:
	"""Get notification preferences for the current user"""
	query = select(NotificationPreferencesModel).where(NotificationPreferencesModel.user_id == current_user.id)
	result = await db.execute(query)
	preferences = result.scalar_one_or_none()

	# Create default preferences if they don't exist
	if not preferences:
		preferences = NotificationPreferencesModel(user_id=current_user.id)
		db.add(preferences)
		await db.commit()
		await db.refresh(preferences)

	return NotificationPreferencesResponse.from_orm(preferences)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
	preferences_update: NotificationPreferencesUpdate,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> NotificationPreferencesResponse:
	"""Update notification preferences for the current user"""
	query = select(NotificationPreferencesModel).where(NotificationPreferencesModel.user_id == current_user.id)
	result = await db.execute(query)
	preferences = result.scalar_one_or_none()

	# Create preferences if they don't exist
	if not preferences:
		preferences = NotificationPreferencesModel(user_id=current_user.id)
		db.add(preferences)

	# Update preferences
	update_data = preferences_update.dict(exclude_unset=True)
	for field, value in update_data.items():
		setattr(preferences, field, value)

	preferences.updated_at = utc_now()

	await db.commit()
	await db.refresh(preferences)

	return NotificationPreferencesResponse.from_orm(preferences)


@router.post("/preferences/reset")
async def reset_notification_preferences(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> dict:
	"""Reset notification preferences to default values"""
	query = select(NotificationPreferencesModel).where(NotificationPreferencesModel.user_id == current_user.id)
	result = await db.execute(query)
	preferences = result.scalar_one_or_none()

	if preferences:
		await db.delete(preferences)

	# Create new preferences with default values
	new_preferences = NotificationPreferencesModel(user_id=current_user.id)
	db.add(new_preferences)
	await db.commit()

	return {
		"success": True,
		"message": "Notification preferences reset to default values",
	}


# ============================================================================
# SECTION 4: OPT-IN/OPT-OUT CONTROLS
# ============================================================================


class OptOutRequest(BaseModel):
	"""Model for opt-out requests"""

	notification_types: List[str] = Field(..., description="List of notification types to opt out of")


class OptInRequest(BaseModel):
	"""Model for opt-in requests"""

	notification_types: List[str] = Field(..., description="List of notification types to opt into")


@router.post("/opt-out")
async def opt_out_notifications(
	request: OptOutRequest,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Opt user out of specific notification types"""
	result = await scheduled_notification_service.opt_out_user(user_id=current_user.id, notification_types=request.notification_types, db=db)

	if not result["success"]:
		if result.get("error") == "invalid_notification_types":
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid notification types: {result.get('invalid_types')}")
		else:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Failed to opt out of notifications"))

	return {
		"success": True,
		"message": f"Successfully opted out of: {', '.join(result['opted_out_types'])}",
		"opted_out_types": result["opted_out_types"],
	}


@router.post("/opt-in")
async def opt_in_notifications(
	request: OptInRequest,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Opt user back into specific notification types"""
	result = await scheduled_notification_service.opt_in_user(user_id=current_user.id, notification_types=request.notification_types, db=db)

	if not result["success"]:
		if result.get("error") == "invalid_notification_types":
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid notification types: {result.get('invalid_types')}")
		else:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Failed to opt into notifications"))

	return {
		"success": True,
		"message": f"Successfully opted into: {', '.join(result['opted_in_types'])}",
		"opted_in_types": result["opted_in_types"],
	}


@router.get("/valid-types")
async def get_valid_notification_types() -> Dict[str, Any]:
	"""Get list of valid notification types for opt-in/opt-out"""
	return {
		"success": True,
		"notification_types": [
			{"type": "morning_briefing", "name": "Morning Briefing", "description": "Daily morning briefing with job recommendations and progress"},
			{"type": "evening_update", "name": "Evening Update", "description": "Daily evening summary with progress tracking and tomorrow's plan"},
			{"type": "job_alerts", "name": "Job Alerts", "description": "Notifications when new matching jobs are found"},
			{"type": "application_reminders", "name": "Application Reminders", "description": "Reminders to follow up on applications"},
			{"type": "skill_gap_reports", "name": "Skill Gap Reports", "description": "Weekly reports on skill gaps and learning recommendations"},
			{"type": "all", "name": "All Notifications", "description": "All notification types"},
		],
		"frequency_options": [
			{"value": "daily", "name": "Daily", "description": "Receive notifications every day"},
			{"value": "weekly", "name": "Weekly", "description": "Receive notifications once per week"},
			{"value": "never", "name": "Never", "description": "Disable all notifications"},
		],
	}


# ============================================================================
# SECTION 5: SCHEDULED NOTIFICATION TESTING
# ============================================================================


@router.post("/test/morning-briefing")
async def test_morning_briefing(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Send a test morning briefing to the current user"""
	result = await scheduled_notification_service.send_morning_briefing(
		user_id=current_user.id,
		db=db,
		force_send=True,  # Override user preferences for testing
	)

	if not result["success"]:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Failed to send test morning briefing"))

	return {
		"success": True,
		"message": "Test morning briefing sent successfully",
		"tracking_id": result.get("tracking_id"),
		"recommendations_count": result.get("recommendations_count", 0),
	}


@router.post("/test/evening-update")
async def test_evening_update(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Send a test evening update to the current user"""
	result = await scheduled_notification_service.send_evening_update(
		user_id=current_user.id,
		db=db,
		force_send=True,  # Override user preferences for testing
	)

	if not result["success"]:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Failed to send test evening update"))

	return {
		"success": True,
		"message": "Test evening update sent successfully",
		"tracking_id": result.get("tracking_id"),
		"activity_summary": result.get("activity_summary", {}),
	}


# ============================================================================
# SECTION 6: STATISTICS
# ============================================================================


@router.get("/statistics", response_model=NotificationStatistics)
async def get_notification_statistics(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> NotificationStatistics:
	"""Get notification statistics for the current user"""
	# Total notifications
	total_query = select(func.count()).select_from(Notification).where(Notification.user_id == current_user.id)
	total_result = await db.execute(total_query)
	total_notifications = total_result.scalar() or 0

	# Unread notifications
	unread_query = select(func.count()).select_from(Notification).where(and_(Notification.user_id == current_user.id, Notification.is_read == False))
	unread_result = await db.execute(unread_query)
	unread_notifications = unread_result.scalar() or 0

	# Notifications by type
	type_query = (
		select(Notification.type, func.count(Notification.id).label("count"))
		.where(Notification.user_id == current_user.id)
		.group_by(Notification.type)
	)
	type_result = await db.execute(type_query)
	notifications_by_type = {row[0].value: row[1] for row in type_result.all()}

	# Notifications by priority
	priority_query = (
		select(Notification.priority, func.count(Notification.id).label("count"))
		.where(Notification.user_id == current_user.id)
		.group_by(Notification.priority)
	)
	priority_result = await db.execute(priority_query)
	notifications_by_priority = {row[0].value: row[1] for row in priority_result.all()}

	# Notifications today
	today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
	today_query = (
		select(func.count()).select_from(Notification).where(and_(Notification.user_id == current_user.id, Notification.created_at >= today_start))
	)
	today_result = await db.execute(today_query)
	notifications_today = today_result.scalar() or 0

	# Notifications this week
	week_start = today_start - timedelta(days=today_start.weekday())
	week_query = (
		select(func.count()).select_from(Notification).where(and_(Notification.user_id == current_user.id, Notification.created_at >= week_start))
	)
	week_result = await db.execute(week_query)
	notifications_this_week = week_result.scalar() or 0

	return NotificationStatistics(
		total_notifications=total_notifications,
		unread_notifications=unread_notifications,
		notifications_by_type=notifications_by_type,
		notifications_by_priority=notifications_by_priority,
		notifications_today=notifications_today,
		notifications_this_week=notifications_this_week,
	)


@router.get("/statistics/admin")
async def get_admin_notification_statistics(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
	"""Get system-wide notification statistics (admin only)"""
	# Check if user is admin
	if not current_user.profile.get("is_admin", False):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

	result = await scheduled_notification_service.get_notification_statistics(db)

	if not result["success"]:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Failed to get notification statistics"))

	return {"success": True, "statistics": result["statistics"]}


# ============================================================================
# SECTION 7: LEGACY ENDPOINTS (DEPRECATED)
# ============================================================================


@router.get("/api/v1/notifications")
async def list_notifications_legacy(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	DEPRECATED: Use GET /notifications instead.

	List all notifications for the current user.
	Maintained for backward compatibility.
	"""
	# Redirect to new endpoint logic
	stored = getattr(current_user, "settings", {}) or {}
	notifications = stored.get("notifications_list", [])
	unread_count = sum(1 for n in notifications if not n.get("is_read")) if isinstance(notifications, list) else 0
	return {
		"notifications": notifications,
		"total": len(notifications) if isinstance(notifications, list) else 0,
		"unread": unread_count,
		"_deprecated": True,
		"_message": "This endpoint is deprecated. Use GET /notifications instead.",
	}


@router.put("/api/v1/notifications/preferences")
async def update_notification_preferences_legacy(
	preferences: dict,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	DEPRECATED: Use PUT /preferences instead.

	Update the current user's notification preferences.
	Maintained for backward compatibility.
	"""
	from ...schemas.api_models import NotificationPreferences

	query = select(NotificationPreferencesModel).where(NotificationPreferencesModel.user_id == current_user.id)
	result = await db.execute(query)
	prefs = result.scalar_one_or_none()

	if prefs is None:
		prefs = NotificationPreferencesModel(user_id=current_user.id)

	# Map API model fields to DB columns
	prefs.email_enabled = bool(preferences.get("email", True))
	prefs.push_enabled = bool(preferences.get("push", False))

	db.add(prefs)
	await db.commit()
	await db.refresh(prefs)

	return {
		**NotificationPreferences(email=prefs.email_enabled, push=prefs.push_enabled, sms=False).dict(),
		"_deprecated": True,
		"_message": "This endpoint is deprecated. Use PUT /preferences instead.",
	}


@router.get("/api/v1/notifications/unread")
async def get_unread_notifications_legacy(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	DEPRECATED: Use GET /notifications?unread_only=true instead.

	Get a list of unread notifications for the current user.
	Maintained for backward compatibility.
	"""
	stored = getattr(current_user, "settings", {}) or {}
	notifications = stored.get("notifications_list", [])
	unread = [n for n in notifications if not n.get("is_read")] if isinstance(notifications, list) else []
	return {
		"unread": unread,
		"count": len(unread),
		"_deprecated": True,
		"_message": "This endpoint is deprecated. Use GET /notifications?unread_only=true instead.",
	}
