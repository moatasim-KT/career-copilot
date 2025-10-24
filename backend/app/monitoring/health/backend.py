"""
Backend service health checker implementation.
"""

import time
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from celery.app.control import Inspect
from fastapi import HTTPException
from sqlalchemy import text

from .base import BaseHealthChecker, HealthCheckResult, HealthStatus
from ...core.config import get_settings
from ...core.database import get_db
from ...core.logging import get_logger
from ...celery import celery_app

logger = get_logger(__name__)
settings = get_settings()


class BackendHealthChecker(BaseHealthChecker):
    """Backend service health checker."""

    def __init__(self, startup_timeout: float = 30.0):
        """Initialize backend health checker."""
        self.startup_timeout = startup_timeout
        self._startup_time = datetime.utcnow()

    async def check_health(self) -> HealthCheckResult:
        """Perform comprehensive backend health check."""
        start_time = time.time()
        
        try:
            # Check FastAPI endpoint
            api_status = await self._check_api()
            if not api_status["healthy"]:
                return self._create_unhealthy_result(
                    message="API endpoint check failed",
                    response_time_ms=(time.time() - start_time) * 1000,
                    error=api_status.get("error")
                )

            # Check Celery workers
            celery_status = await self._check_celery()
            if not celery_status["healthy"]:
                return self._create_unhealthy_result(
                    message="Celery worker check failed",
                    response_time_ms=(time.time() - start_time) * 1000,
                    error=celery_status.get("error")
                )

            # Check service startup
            startup_status = self._check_startup()
            if not startup_status["healthy"]:
                return self._create_unhealthy_result(
                    message="Service startup check failed",
                    response_time_ms=(time.time() - start_time) * 1000,
                    error=startup_status.get("error")
                )

            return self._create_healthy_result(
                message="Backend service is healthy",
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    "api": api_status,
                    "celery": celery_status,
                    "startup": startup_status
                }
            )

        except Exception as e:
            logger.error(f"Backend health check failed: {e}")
            return self._create_unhealthy_result(
                message="Backend health check failed",
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )

    async def _check_api(self) -> Dict[str, Any]:
        """Check FastAPI endpoint health."""
        try:
            # Verify database connection through FastAPI endpoint
            async for db in get_db():
                try:
                    # Execute simple query to check database connection
                    await db.execute(text("SELECT 1"))
                    return {
                        "healthy": True,
                        "message": "API endpoint is responding"
                    }
                except Exception as e:
                    return {
                        "healthy": False,
                        "error": f"Database connection failed: {e!s}"
                    }
        except Exception as e:
            return {
                "healthy": False,
                "error": f"API endpoint check failed: {e!s}"
            }

    async def _check_celery(self) -> Dict[str, Any]:
        """Check Celery worker status."""
        try:
            inspect = Inspect(app=celery_app)
            active_workers = inspect.active()
            
            if not active_workers:
                return {
                    "healthy": False,
                    "error": "No Celery workers are active"
                }

            workers_info = {
                "active_workers": len(active_workers),
                "worker_stats": {}
            }

            # Get detailed worker stats
            for worker, tasks in active_workers.items():
                workers_info["worker_stats"][worker] = {
                    "active_tasks": len(tasks),
                    "status": "running"
                }

            return {
                "healthy": True,
                "message": "Celery workers are running",
                "details": workers_info
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": f"Celery worker check failed: {e!s}"
            }

    def _check_startup(self) -> Dict[str, Any]:
        """Check service startup status."""
        current_time = datetime.utcnow()
        startup_duration = (current_time - self._startup_time).total_seconds()

        if startup_duration > self.startup_timeout:
            return {
                "healthy": True,
                "message": "Service startup completed",
                "startup_duration": startup_duration
            }
        else:
            return {
                "healthy": False,
                "error": f"Service still starting up (elapsed: {startup_duration:.1f}s)",
                "startup_duration": startup_duration
            }