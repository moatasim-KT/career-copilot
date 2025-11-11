"""
Notification CRUD API endpoints
Implements comprehensive notification management system
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...dependencies import get_current_user
from ...models.notification import Notification, NotificationPriority, NotificationType
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

router = APIRouter(prefix="/notifications", tags=["notifications"])


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
    unread_query = select(func.count()).select_from(Notification).where(
        and_(Notification.user_id == current_user.id, Notification.is_read == False)
    )
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
    query = select(Notification).where(
        and_(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
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
    query = select(Notification).where(
        and_(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with id {notification_id} not found",
        )
    
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
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
    query = select(Notification).where(
        and_(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
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


@router.put("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark all notifications as read for the current user"""
    query = select(Notification).where(
        and_(Notification.user_id == current_user.id, Notification.is_read == False)
    )
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    count = 0
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
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
        notification.read_at = datetime.utcnow()
        count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Marked {count} notifications as read",
        "count": count,
        "notification_ids": [n.id for n in notifications],
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a specific notification"""
    query = select(Notification).where(
        and_(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
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


@router.get("/statistics", response_model=NotificationStatistics)
async def get_notification_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationStatistics:
    """Get notification statistics for the current user"""
    # Total notifications
    total_query = select(func.count()).select_from(Notification).where(
        Notification.user_id == current_user.id
    )
    total_result = await db.execute(total_query)
    total_notifications = total_result.scalar() or 0
    
    # Unread notifications
    unread_query = select(func.count()).select_from(Notification).where(
        and_(Notification.user_id == current_user.id, Notification.is_read == False)
    )
    unread_result = await db.execute(unread_query)
    unread_notifications = unread_result.scalar() or 0
    
    # Notifications by type
    type_query = select(
        Notification.type,
        func.count(Notification.id).label("count")
    ).where(
        Notification.user_id == current_user.id
    ).group_by(Notification.type)
    type_result = await db.execute(type_query)
    notifications_by_type = {row[0].value: row[1] for row in type_result.all()}
    
    # Notifications by priority
    priority_query = select(
        Notification.priority,
        func.count(Notification.id).label("count")
    ).where(
        Notification.user_id == current_user.id
    ).group_by(Notification.priority)
    priority_result = await db.execute(priority_query)
    notifications_by_priority = {row[0].value: row[1] for row in priority_result.all()}
    
    # Notifications today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_query = select(func.count()).select_from(Notification).where(
        and_(
            Notification.user_id == current_user.id,
            Notification.created_at >= today_start
        )
    )
    today_result = await db.execute(today_query)
    notifications_today = today_result.scalar() or 0
    
    # Notifications this week
    week_start = today_start - timedelta(days=today_start.weekday())
    week_query = select(func.count()).select_from(Notification).where(
        and_(
            Notification.user_id == current_user.id,
            Notification.created_at >= week_start
        )
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



# Notification Preferences Endpoints
@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationPreferencesResponse:
    """Get notification preferences for the current user"""
    from ...models.notification import NotificationPreferences as NotificationPreferencesModel
    from ...schemas.notification import NotificationPreferencesResponse
    
    query = select(NotificationPreferencesModel).where(
        NotificationPreferencesModel.user_id == current_user.id
    )
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
    from ...models.notification import NotificationPreferences as NotificationPreferencesModel
    from ...schemas.notification import NotificationPreferencesResponse, NotificationPreferencesUpdate
    
    query = select(NotificationPreferencesModel).where(
        NotificationPreferencesModel.user_id == current_user.id
    )
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
    
    preferences.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(preferences)
    
    return NotificationPreferencesResponse.from_orm(preferences)


@router.post("/preferences/reset")
async def reset_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset notification preferences to default values"""
    from ...models.notification import NotificationPreferences as NotificationPreferencesModel
    
    query = select(NotificationPreferencesModel).where(
        NotificationPreferencesModel.user_id == current_user.id
    )
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
