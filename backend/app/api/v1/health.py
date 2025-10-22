"""Health check endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from ...core.database import get_db
from ...core.logging import get_logger
from ...scheduler import scheduler

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint that verifies system component status.
    
    Checks:
    - Database connectivity
    - Scheduler status
    
    Returns overall status and individual component health.
    """
    db_status = "unhealthy"
    scheduler_status = "unhealthy"
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check scheduler status
    try:
        if scheduler.running:
            scheduler_status = "healthy"
        else:
            scheduler_status = "unhealthy"
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        scheduler_status = "unhealthy"
    
    # Determine overall status
    overall_status = "healthy" if db_status == "healthy" and scheduler_status == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": db_status,
            "scheduler": scheduler_status
        }
    }


@router.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
