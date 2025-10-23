"""Health check endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from ...core.database import get_db
from ...core.logging import get_logger
from ...scheduler import scheduler
from ...core.optimized_database import check_database_health
from ...services.cache_service import cache_service

from ...schemas.health import HealthResponse

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint that verifies system component status.
    
    Checks:
    - Database connectivity and performance
    - Scheduler status
    - Cache service status
    
    Returns overall status and individual component health.
    """
    components = {}
    
    # Check database connectivity and performance
    try:
        from ...core.database import engine
        db_health = check_database_health(engine)
        components["database"] = db_health
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        components["database"] = {"status": "unhealthy", "error": str(e)}
    
    # Check scheduler status
    try:
        if scheduler.running:
            components["scheduler"] = {"status": "healthy"}
        else:
            components["scheduler"] = {"status": "unhealthy", "message": "Scheduler not running"}
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        components["scheduler"] = {"status": "unhealthy", "error": str(e)}
    
    # Check cache service status
    try:
        if cache_service.enabled:
            cache_stats = cache_service.get_cache_stats()
            components["cache"] = {
                "status": "healthy" if cache_stats.get("enabled") else "unhealthy",
                "stats": cache_stats
            }
        else:
            components["cache"] = {"status": "disabled", "message": "Cache service disabled"}
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        components["cache"] = {"status": "unhealthy", "error": str(e)}
    
    # Determine overall status
    healthy_components = [comp for comp in components.values() if comp.get("status") == "healthy"]
    overall_status = "healthy" if len(healthy_components) >= 2 else "unhealthy"  # At least DB and one other
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": components
    }


@router.get("/api/v1/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
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