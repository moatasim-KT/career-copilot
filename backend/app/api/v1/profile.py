"""
Profile API endpoints for Career Co-Pilot system
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.dependencies import get_current_active_user, get_profile_service
from app.models.user import User
from app.schemas.profile import (
    UserProfileUpdate, UserSettingsUpdate, UserProfileResponse,
    ApplicationHistoryResponse, ProgressTrackingStats, DocumentManagementResponse
)
from app.services.profile_service import ProfileService

router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get current user's profile information
    
    Args:
        current_user: Current authenticated user
        profile_service: Profile service instance
        
    Returns:
        User profile with completion percentage
        
    Raises:
        HTTPException: If profile not found
    """
    profile = profile_service.get_user_profile(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Update current user's profile information
    
    Args:
        profile_update: Profile update data
        current_user: Current authenticated user
        profile_service: Profile service instance
        
    Returns:
        Updated user profile
        
    Raises:
        HTTPException: If update fails
    """
    try:
        updated_profile = profile_service.update_user_profile(
            current_user.id, 
            profile_update
        )
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return updated_profile
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.put("/settings", status_code=status.HTTP_200_OK)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Update current user's settings
    
    Args:
        settings_update: Settings update data
        current_user: Current authenticated user
        profile_service: Profile service instance
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If update fails
    """
    try:
        success = profile_service.update_user_settings(
            current_user.id, 
            settings_update
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "Settings updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )


@router.get("/application-history", response_model=ApplicationHistoryResponse)
async def get_application_history(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by application status"),
    date_from: Optional[datetime] = Query(None, description="Filter applications from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter applications to this date"),
    current_user: User = Depends(get_current_active_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get user's application history with filtering and pagination
    
    Args:
        page: Page number for pagination
        per_page: Number of items per page
        status_filter: Optional status filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        current_user: Current authenticated user
        profile_service: Profile service instance
        
    Returns:
        Paginated application history with statistics
    """
    try:
        history = profile_service.get_application_history(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            status_filter=status_filter,
            date_from=date_from,
            date_to=date_to
        )
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application history"
        )


@router.get("/progress-stats", response_model=ProgressTrackingStats)
async def get_progress_tracking_stats(
    current_user: User = Depends(get_current_active_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get comprehensive progress tracking statistics
    
    Args:
        current_user: Current authenticated user
        profile_service: Profile service instance
        
    Returns:
        Progress tracking statistics and trends
    """
    try:
        stats = profile_service.get_progress_tracking_stats(current_user.id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve progress statistics"
        )


@router.get("/documents", response_model=DocumentManagementResponse)
async def get_document_management_summary(
    current_user: User = Depends(get_current_active_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get document management summary and statistics
    
    Args:
        current_user: Current authenticated user
        profile_service: Profile service instance
        
    Returns:
        Document management summary with statistics
    """
    try:
        summary = profile_service.get_document_management_summary(current_user.id)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document summary"
        )


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get comprehensive dashboard statistics
    
    Args:
        current_user: Current authenticated user
        profile_service: Profile service instance
        
    Returns:
        Combined dashboard statistics
    """
    try:
        # Get all dashboard data in one call for efficiency
        progress_stats = profile_service.get_progress_tracking_stats(current_user.id)
        document_summary = profile_service.get_document_management_summary(current_user.id)
        profile = profile_service.get_user_profile(current_user.id)
        
        return {
            "profile_completion": profile.profile_completion if profile else 0,
            "total_applications": progress_stats.total_applications,
            "applications_this_week": progress_stats.applications_this_week,
            "applications_this_month": progress_stats.applications_this_month,
            "interview_rate": progress_stats.interview_rate,
            "offer_rate": progress_stats.offer_rate,
            "response_rate": progress_stats.response_rate,
            "total_documents": document_summary.total_documents,
            "documents_by_type": document_summary.documents_by_type,
            "weekly_goal_progress": progress_stats.goal_completion_rate,
            "status_distribution": progress_stats.status_distribution,
            "weekly_trend": progress_stats.weekly_application_trend[-4:]  # Last 4 weeks
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )