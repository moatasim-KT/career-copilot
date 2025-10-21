"""
Health check and monitoring endpoints.
"""

from fastapi import APIRouter, status
from datetime import datetime
from typing import Dict, Any

from ...core.health_checker import get_health_checker
from ...core.production_monitoring import get_production_monitor

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "career-copilot"
    }


@router.get("/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with all system components."""
    health_checker = get_health_checker()
    return health_checker.run_all_checks()


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_metrics() -> Dict[str, Any]:
    """Get system metrics."""
    monitor = get_production_monitor()
    return monitor.get_metrics()


@router.get("/errors", status_code=status.HTTP_200_OK)
async def get_errors(limit: int = 100) -> Dict[str, Any]:
    """Get recent errors."""
    monitor = get_production_monitor()
    return {"errors": monitor.get_errors(limit)}


@router.get("/alerts", status_code=status.HTTP_200_OK)
async def get_alerts(limit: int = 50) -> Dict[str, Any]:
    """Get recent alerts."""
    monitor = get_production_monitor()
    return {"alerts": monitor.get_alerts(limit)}
