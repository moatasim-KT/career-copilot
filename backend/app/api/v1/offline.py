"""
Offline functionality API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.offline_service import offline_service

router = APIRouter()


@router.get("/manifest")
async def get_offline_manifest(
    current_user: User = Depends(get_current_user)
):
    """Get offline capability manifest"""
    return offline_service.get_offline_manifest()


@router.post("/prepare")
async def prepare_offline_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Prepare data for offline use"""
    return offline_service.prepare_offline_data(current_user.id, db)


@router.get("/data")
async def get_offline_data(
    current_user: User = Depends(get_current_user)
):
    """Get cached offline data"""
    data = offline_service.get_offline_data(current_user.id)
    
    if not data:
        return {
            "success": False,
            "message": "No offline data available. Please prepare offline data first."
        }
    
    return {
        "success": True,
        "data": data
    }


@router.get("/status")
async def get_offline_status(
    current_user: User = Depends(get_current_user)
):
    """Get offline capability status"""
    data = offline_service.get_offline_data(current_user.id)
    
    return {
        "offline_ready": data is not None,
        "has_cached_data": data is not None,
        "manifest": offline_service.get_offline_manifest()
    }


@router.get("/degradation-status")
async def get_degradation_status():
    """Get system degradation status and available fallbacks"""
    from app.services.graceful_degradation_service import graceful_degradation_service
    return graceful_degradation_service.get_degradation_status()


@router.post("/complete-offline")
async def enable_complete_offline_mode(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable complete offline mode with all fallbacks"""
    from app.services.graceful_degradation_service import graceful_degradation_service
    result = graceful_degradation_service.handle_complete_offline_mode(db, current_user.id)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to enable offline mode'))
    
    return result


@router.get("/capabilities")
async def get_offline_capabilities():
    """Get detailed offline capabilities information"""
    return {
        "service_worker": {
            "supported": True,
            "cache_strategies": ["network-first", "cache-first", "stale-while-revalidate"],
            "background_sync": True,
            "push_notifications": False
        },
        "storage": {
            "indexeddb": True,
            "local_storage": True,
            "cache_api": True,
            "estimated_quota_mb": 50
        },
        "offline_features": {
            "job_browsing": True,
            "profile_editing": True,
            "application_tracking": True,
            "data_export": True,
            "local_search": True,
            "basic_analytics": True
        },
        "sync_capabilities": {
            "background_sync": True,
            "conflict_resolution": "last-write-wins",
            "retry_strategy": "exponential-backoff"
        }
    }