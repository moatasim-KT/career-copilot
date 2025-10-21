"""
API endpoints for notification management
"""

from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...core.auth import get_current_user
from ...models.user import User
from ...services.scheduled_notification_service import scheduled_notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationPreferences(BaseModel):
    """Model for notification preferences"""
    morning_briefing: bool = Field(True, description="Enable morning briefings")
    evening_update: bool = Field(True, description="Enable evening updates")
    morning_time: str = Field("08:00", description="Preferred morning notification time (HH:MM)")
    evening_time: str = Field("18:00", description="Preferred evening notification time (HH:MM)")
    frequency: str = Field("daily", description="Notification frequency (daily, weekly, never)")
    job_alerts: bool = Field(True, description="Enable job alert notifications")
    application_reminders: bool = Field(True, description="Enable application reminder notifications")
    skill_gap_reports: bool = Field(True, description="Enable skill gap report notifications")


class OptOutRequest(BaseModel):
    """Model for opt-out requests"""
    notification_types: List[str] = Field(..., description="List of notification types to opt out of")


class OptInRequest(BaseModel):
    """Model for opt-in requests"""
    notification_types: List[str] = Field(..., description="List of notification types to opt into")


@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current user's notification preferences"""
    
    result = await scheduled_notification_service.get_user_notification_preferences(
        user_id=current_user.id,
        db=db
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Failed to get notification preferences")
        )
    
    return {
        "success": True,
        "preferences": result["preferences"]
    }


@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update user's notification preferences"""
    
    result = await scheduled_notification_service.update_user_notification_preferences(
        user_id=current_user.id,
        preferences=preferences.dict(),
        db=db
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to update notification preferences")
        )
    
    return {
        "success": True,
        "message": "Notification preferences updated successfully",
        "preferences": result["preferences"]
    }


@router.post("/opt-out")
async def opt_out_notifications(
    request: OptOutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Opt user out of specific notification types"""
    
    result = await scheduled_notification_service.opt_out_user(
        user_id=current_user.id,
        notification_types=request.notification_types,
        db=db
    )
    
    if not result["success"]:
        if result.get("error") == "invalid_notification_types":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification types: {result.get('invalid_types')}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to opt out of notifications")
            )
    
    return {
        "success": True,
        "message": f"Successfully opted out of: {', '.join(result['opted_out_types'])}",
        "opted_out_types": result["opted_out_types"]
    }


@router.post("/opt-in")
async def opt_in_notifications(
    request: OptInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Opt user back into specific notification types"""
    
    result = await scheduled_notification_service.opt_in_user(
        user_id=current_user.id,
        notification_types=request.notification_types,
        db=db
    )
    
    if not result["success"]:
        if result.get("error") == "invalid_notification_types":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification types: {result.get('invalid_types')}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to opt into notifications")
            )
    
    return {
        "success": True,
        "message": f"Successfully opted into: {', '.join(result['opted_in_types'])}",
        "opted_in_types": result["opted_in_types"]
    }


@router.post("/test/morning-briefing")
async def test_morning_briefing(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Send a test morning briefing to the current user"""
    
    result = await scheduled_notification_service.send_morning_briefing(
        user_id=current_user.id,
        db=db,
        force_send=True  # Override user preferences for testing
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to send test morning briefing")
        )
    
    return {
        "success": True,
        "message": "Test morning briefing sent successfully",
        "tracking_id": result.get("tracking_id"),
        "recommendations_count": result.get("recommendations_count", 0)
    }


@router.post("/test/evening-update")
async def test_evening_update(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Send a test evening update to the current user"""
    
    result = await scheduled_notification_service.send_evening_update(
        user_id=current_user.id,
        db=db,
        force_send=True  # Override user preferences for testing
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to send test evening update")
        )
    
    return {
        "success": True,
        "message": "Test evening update sent successfully",
        "tracking_id": result.get("tracking_id"),
        "activity_summary": result.get("activity_summary", {})
    }


@router.get("/statistics")
async def get_notification_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get notification statistics (admin only)"""
    
    # Check if user is admin (simplified check)
    if not current_user.profile.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    result = await scheduled_notification_service.get_notification_statistics(db)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Failed to get notification statistics")
        )
    
    return {
        "success": True,
        "statistics": result["statistics"]
    }


@router.get("/valid-types")
async def get_valid_notification_types() -> Dict[str, Any]:
    """Get list of valid notification types for opt-in/opt-out"""
    
    return {
        "success": True,
        "notification_types": [
            {
                "type": "morning_briefing",
                "name": "Morning Briefing",
                "description": "Daily morning briefing with job recommendations and progress"
            },
            {
                "type": "evening_update", 
                "name": "Evening Update",
                "description": "Daily evening summary with progress tracking and tomorrow's plan"
            },
            {
                "type": "job_alerts",
                "name": "Job Alerts",
                "description": "Notifications when new matching jobs are found"
            },
            {
                "type": "application_reminders",
                "name": "Application Reminders",
                "description": "Reminders to follow up on applications"
            },
            {
                "type": "skill_gap_reports",
                "name": "Skill Gap Reports",
                "description": "Weekly reports on skill gaps and learning recommendations"
            },
            {
                "type": "all",
                "name": "All Notifications",
                "description": "All notification types"
            }
        ],
        "frequency_options": [
            {
                "value": "daily",
                "name": "Daily",
                "description": "Receive notifications every day"
            },
            {
                "value": "weekly",
                "name": "Weekly", 
                "description": "Receive notifications once per week"
            },
            {
                "value": "never",
                "name": "Never",
                "description": "Disable all notifications"
            }
        ]
    }