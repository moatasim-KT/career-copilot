"""
Comprehensive health check endpoints for both development and production environments.

This module provides environment-aware health checks that adapt their behavior
based on the current environment (development, production, testing).
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...core.environment_config import get_environment_config_manager, get_current_environment, Environment
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    """Health status response model."""
    status: str
    timestamp: datetime
    environment: str
    uptime_seconds: float
    version: str = "1.0.0"


class DetailedHealthStatus(BaseModel):
    """Detailed health status response model."""
    status: str
    timestamp: datetime
    environment: str
    uptime_seconds: float
    version: str = "1.0.0"
    services: Dict[str, Any]
    system: Dict[str, Any]
    configuration: Dict[str, Any]


class ServiceHealth(BaseModel):
    """Individual service health status."""
    name: str
    status: str
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# Application start time for uptime calculation
_app_start_time = time.time()


def get_uptime() -> float:
    """Get application uptime in seconds."""
    return time.time() - _app_start_time


async def check_database_health() -> ServiceHealth:
    """Check database health."""
    start_time = time.time()
    
    try:
        # Try to import and check database
        from ...core.database import get_database_manager
        
        db_manager = await get_database_manager()
        health_status = await db_manager.health_check()
        
        response_time = (time.time() - start_time) * 1000
        
        if health_status.get("database", False):
            return ServiceHealth(
                name="database",
                status="healthy",
                last_check=datetime.now(),
                response_time_ms=response_time,
                details=health_status
            )
        else:
            return ServiceHealth(
                name="database",
                status="unhealthy",
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message="Database health check failed",
                details=health_status
            )
    
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            name="database",
            status="unhealthy",
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_message=str(e)
        )


async def check_vector_store_health() -> ServiceHealth:
    """Check vector store (ChromaDB) health."""
    start_time = time.time()
    
    try:
        import chromadb
        from chromadb.config import Settings
        from pathlib import Path
        
        chroma_dir = Path("data/chroma")
        if not chroma_dir.exists():
            chroma_dir.mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Test basic operations
        collections = client.list_collections()
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealth(
            name="vector_store",
            status="healthy",
            last_check=datetime.now(),
            response_time_ms=response_time,
            details={"collections_count": len(collections)}
        )
    
    except ImportError:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            name="vector_store",
            status="degraded",
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_message="ChromaDB not installed"
        )
    
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            name="vector_store",
            status="unhealthy",
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_message=str(e)
        )


async def check_ai_services_health() -> ServiceHealth:
    """Check AI services health."""
    start_time = time.time()
    
    try:
        details = {}
        
        # Check OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            details["openai"] = {
                "configured": True,
                "key_format_valid": openai_key.startswith("sk-")
            }
        else:
            details["openai"] = {"configured": False}
        
        # Check Groq
        groq_key = os.getenv("GROQ_API_KEY")
        details["groq"] = {"configured": bool(groq_key)}
        
        # Check Ollama
        ollama_enabled = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
        details["ollama"] = {"enabled": ollama_enabled}
        
        response_time = (time.time() - start_time) * 1000
        
        # At least OpenAI should be configured
        if details["openai"]["configured"]:
            status = "healthy"
            error_message = None
        else:
            status = "unhealthy"
            error_message = "OpenAI API key not configured"
        
        return ServiceHealth(
            name="ai_services",
            status=status,
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_message=error_message,
            details=details
        )
    
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            name="ai_services",
            status="unhealthy",
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_message=str(e)
        )


async def check_external_services_health() -> ServiceHealth:
    """Check external services health."""
    start_time = time.time()
    
    try:
        details = {}
        
        # Check email services
        smtp_enabled = os.getenv("SMTP_ENABLED", "false").lower() == "true"
        gmail_enabled = os.getenv("GMAIL_ENABLED", "false").lower() == "true"
        details["email"] = {
            "smtp_enabled": smtp_enabled,
            "gmail_enabled": gmail_enabled
        }
        
        # Check Slack
        slack_enabled = os.getenv("SLACK_ENABLED", "false").lower() == "true"
        details["slack"] = {"enabled": slack_enabled}
        
        # Check DocuSign
        docusign_enabled = os.getenv("DOCUSIGN_ENABLED", "false").lower() == "true"
        docusign_sandbox_enabled = os.getenv("DOCUSIGN_SANDBOX_ENABLED", "false").lower() == "true"
        details["docusign"] = {
            "enabled": docusign_enabled,
            "sandbox_enabled": docusign_sandbox_enabled
        }
        
        # Check Google Drive
        google_drive_enabled = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
        details["google_drive"] = {"enabled": google_drive_enabled}
        
        response_time = (time.time() - start_time) * 1000
        
        # External services are optional, so always healthy
        return ServiceHealth(
            name="external_services",
            status="healthy",
            last_check=datetime.now(),
            response_time_ms=response_time,
            details=details
        )
    
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealth(
            name="external_services",
            status="degraded",
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_message=str(e)
        )


async def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    import psutil
    import platform
    
    try:
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent if os.path.exists('/') else None
        }
    except ImportError:
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "psutil_available": False
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/health", response_model=HealthStatus)
async def basic_health_check():
    """Basic health check endpoint."""
    env_manager = get_environment_config_manager()
    current_env = get_current_environment()
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(),
        environment=current_env.value,
        uptime_seconds=get_uptime()
    )


@router.get("/health/detailed", response_model=DetailedHealthStatus)
async def detailed_health_check():
    """Detailed health check with service status."""
    env_manager = get_environment_config_manager()
    current_env = get_current_environment()
    env_config = env_manager.get_config()
    
    # Check all services
    service_checks = await asyncio.gather(
        check_database_health(),
        check_vector_store_health(),
        check_ai_services_health(),
        check_external_services_health(),
        return_exceptions=True
    )
    
    services = {}
    overall_status = "healthy"
    
    for check in service_checks:
        if isinstance(check, ServiceHealth):
            services[check.name] = check.dict()
            if check.status == "unhealthy":
                overall_status = "unhealthy"
            elif check.status == "degraded" and overall_status == "healthy":
                overall_status = "degraded"
        else:
            # Exception occurred
            services["unknown"] = {
                "status": "unhealthy",
                "error": str(check)
            }
            overall_status = "unhealthy"
    
    # Get system information
    system_info = await get_system_info()
    
    # Configuration information (environment-aware)
    config_info = {
        "environment": current_env.value,
        "debug": env_config.debug,
        "monitoring_enabled": env_config.enable_monitoring,
        "security_enabled": env_config.enable_security,
        "auth_enabled": env_config.enable_auth,
        "worker_count": env_config.worker_count,
        "database_pool_size": env_config.database_pool_size
    }
    
    return DetailedHealthStatus(
        status=overall_status,
        timestamp=datetime.now(),
        environment=current_env.value,
        uptime_seconds=get_uptime(),
        services=services,
        system=system_info,
        configuration=config_info
    )


@router.get("/health/readiness")
async def readiness_probe():
    """Kubernetes readiness probe."""
    try:
        # Check critical services for readiness
        db_health = await check_database_health()
        ai_health = await check_ai_services_health()
        
        if db_health.status == "healthy" and ai_health.status == "healthy":
            return {"status": "ready", "timestamp": datetime.now()}
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "timestamp": datetime.now(),
                    "issues": {
                        "database": db_health.status,
                        "ai_services": ai_health.status
                    }
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.now(),
                "error": str(e)
            }
        )


@router.get("/health/liveness")
async def liveness_probe():
    """Kubernetes liveness probe."""
    # Simple liveness check - just verify the application is running
    return {
        "status": "alive",
        "timestamp": datetime.now(),
        "uptime_seconds": get_uptime()
    }


@router.get("/health/startup")
async def startup_probe():
    """Kubernetes startup probe."""
    try:
        # Check if application has completed startup
        uptime = get_uptime()
        
        # Consider startup complete after 30 seconds or when critical services are healthy
        if uptime > 30:
            return {"status": "started", "timestamp": datetime.now(), "uptime_seconds": uptime}
        
        # Check critical services
        db_health = await check_database_health()
        ai_health = await check_ai_services_health()
        
        if db_health.status in ["healthy", "degraded"] and ai_health.status in ["healthy", "degraded"]:
            return {"status": "started", "timestamp": datetime.now(), "uptime_seconds": uptime}
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "starting",
                    "timestamp": datetime.now(),
                    "uptime_seconds": uptime,
                    "services": {
                        "database": db_health.status,
                        "ai_services": ai_health.status
                    }
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "starting",
                "timestamp": datetime.now(),
                "error": str(e)
            }
        )


@router.get("/health/environment")
async def environment_info():
    """Get environment-specific information."""
    env_manager = get_environment_config_manager()
    current_env = get_current_environment()
    env_config = env_manager.get_config()
    
    # Validate environment consistency
    consistency_issues = env_manager.validate_environment_consistency()
    
    return {
        "environment": current_env.value,
        "configuration": {
            "debug": env_config.debug,
            "log_level": env_config.log_level,
            "monitoring_enabled": env_config.enable_monitoring,
            "security_enabled": env_config.enable_security,
            "auth_enabled": env_config.enable_auth,
            "rate_limit_enabled": env_config.rate_limit_enabled,
            "worker_count": env_config.worker_count,
            "database_pool_size": env_config.database_pool_size,
            "cors_origins": env_config.cors_origins,
            "file_upload_max_size": env_config.file_upload_max_size,
            "session_timeout": env_config.session_timeout
        },
        "consistency_check": {
            "issues": consistency_issues,
            "valid": len(consistency_issues) == 0
        },
        "timestamp": datetime.now()
    }