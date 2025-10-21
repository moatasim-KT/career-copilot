"""
Career Copilot - Comprehensive Job Tracking Application
Production-ready FastAPI application for job application tracking and career management
"""

import asyncio
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from .core.config import get_settings
from .core.logging import get_logger, setup_logging
from .core.exceptions import SecurityError
from .models.api_models import ErrorResponse
from .middleware.comprehensive_security import ComprehensiveSecurityMiddleware
from .middleware.resource_middleware import ResourceManagementMiddleware
from .middleware.jwt_auth_middleware import JWTAuthenticationMiddleware, SessionManagementMiddleware
from .middleware.logging_middleware import LoggingMiddleware
from .middleware.global_error_handler import GlobalErrorHandlerMiddleware
from .middleware.request_validation import RequestValidationMiddleware, ContentValidationMiddleware

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the Career Copilot application."""
    
    setup_logging()
    settings = get_settings()
    
    app = FastAPI(
        title="Career Copilot API",
        description="Comprehensive AI-powered job application tracking and career management system",
        version="2.0.0",
        docs_url="/docs" if settings.api_debug else None,
        redoc_url="/redoc" if settings.api_debug else None,
    )
    
    # ============================================================================
    # MIDDLEWARE STACK (Order matters!)
    # ============================================================================
    
    app.add_middleware(GlobalErrorHandlerMiddleware)
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(ContentValidationMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ResourceManagementMiddleware, enable_throttling=True)
    app.add_middleware(JWTAuthenticationMiddleware)
    app.add_middleware(SessionManagementMiddleware)
    app.add_middleware(ComprehensiveSecurityMiddleware)
    
    # CORS Configuration
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining"],
    )
    
    # ============================================================================
    # EXCEPTION HANDLERS
    # ============================================================================
    
    @app.exception_handler(SecurityError)
    async def security_exception_handler(request: Request, exc: SecurityError):
        logger.warning(f"Security error: {exc.message}")
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                error="Security Error",
                message="Access denied due to security policy",
                suggestions=["Please ensure your request complies with security requirements"],
            ).model_dump(),
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": "Validation Error", "details": exc.errors()},
        )
    
    # ============================================================================
    # CORE ROUTES
    # ============================================================================
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Career Copilot API",
            "version": "2.0.0",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "docs": "/docs",
            "endpoints": {
                "health": "/api/v1/health",
                "jobs": "/api/v1/jobs",
                "applications": "/api/v1/applications",
                "analytics": "/api/v1/analytics",
                "profile": "/api/v1/profile",
                "documents": "/api/v1/documents",
            }
        }
    
    @app.get("/api/v1/health")
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Career Copilot API",
            "version": "2.0.0"
        }
    
    # ============================================================================
    # API ROUTERS - JOB TRACKING FOCUSED
    # ============================================================================
    
    # Core Job Tracking
    from .api.v1 import jobs, applications, auth, users, profile
    from .api.v1 import analytics, recommendations, skill_matching
    from .api.v1 import documents, templates, goals
    from .api.v1 import notifications, briefings, feedback
    from .api.v1 import job_ingestion, saved_searches, dashboard_layouts
    
    # Job Management
    app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
    app.include_router(applications.router, prefix="/api/v1", tags=["Applications"])
    
    # User & Profile
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users.router, prefix="/api/v1", tags=["Users"])
    app.include_router(profile.router, prefix="/api/v1", tags=["Profile"])
    
    # Analytics & Insights
    app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
    app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])
    app.include_router(skill_matching.router, prefix="/api/v1", tags=["Skills"])
    
    # Reporting & Insights
    try:
        from .api.v1.reporting_insights import router as reporting_insights_router
        app.include_router(reporting_insights_router, prefix="/api/v1/reports", tags=["Reports"])
        logger.info("Reporting insights router loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load reporting insights router: {e}")
    
    # Documents & Templates
    app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
    app.include_router(templates.router, prefix="/api/v1", tags=["Templates"])
    
    # Goals & Progress
    app.include_router(goals.router, prefix="/api/v1", tags=["Goals"])
    
    # Notifications & Communication
    app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
    app.include_router(briefings.router, prefix="/api/v1", tags=["Briefings"])
    
    # Feedback & Improvement
    app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
    
    # Job Discovery
    app.include_router(job_ingestion.router, prefix="/api/v1", tags=["Job Discovery"])
    app.include_router(saved_searches.router, prefix="/api/v1", tags=["Saved Searches"])
    
    # Customization
    app.include_router(dashboard_layouts.router, prefix="/api/v1", tags=["Dashboard"])
    
    # Optional: Advanced Features
    try:
        from .api.v1 import slack, email, export, offline
        app.include_router(slack.router, prefix="/api/v1", tags=["Integrations"])
        app.include_router(email.router, prefix="/api/v1", tags=["Email"])
        app.include_router(export.router, prefix="/api/v1", tags=["Export"])
        app.include_router(offline.router, prefix="/api/v1", tags=["Offline"])
    except ImportError as e:
        logger.warning(f"Optional features not loaded: {e}")
    
    # Monitoring & Health (if enabled)
    if settings.enable_monitoring:
        from .api.v1 import health_comprehensive, monitoring, performance
        app.include_router(health_comprehensive.router, prefix="/api/v1", tags=["Health"])
        app.include_router(monitoring.router, prefix="/api/v1", tags=["Monitoring"])
        app.include_router(performance.router, prefix="/api/v1", tags=["Performance"])
    
    # ============================================================================
    # STARTUP & SHUTDOWN EVENTS
    # ============================================================================
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 Career Copilot API starting up...")
        logger.info(f"🌐 API running on {settings.api_host}:{settings.api_port}")
        
        # Initialize database
        from .core.database import init_db
        try:
            await init_db()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            logger.warning("⚠️  Continuing with limited functionality")
        
        # Initialize services
        try:
            from .services.job_service import JobService
            from .services.application_service import ApplicationService
            from .services.analytics_service import AnalyticsService
            from .services.recommendation_service import RecommendationService
            from .services.skill_matching_service import SkillMatchingService
            
            logger.info("✅ Core services initialized")
        except Exception as e:
            logger.warning(f"⚠️  Some services failed to initialize: {e}")
        
        # Initialize background tasks
        if settings.enable_monitoring:
            try:
                from .tasks import job_ingestion_tasks, analytics_tasks, notification_tasks
                asyncio.create_task(job_ingestion_tasks.start_periodic_ingestion())
                asyncio.create_task(analytics_tasks.start_periodic_analytics())
                asyncio.create_task(notification_tasks.start_notification_processor())
                logger.info("✅ Background tasks started")
            except Exception as e:
                logger.warning(f"⚠️  Background tasks not started: {e}")
        
        logger.info("🎯 Career Copilot API ready!")
        logger.info("📚 API Documentation: /docs")
        logger.info("🔍 Health Check: /api/v1/health")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🛑 Career Copilot API shutting down...")
        
        # Cleanup resources
        try:
            from .core.database import close_db
            await close_db()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing database: {e}")
        
        logger.info("👋 Career Copilot API shutdown complete")
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.app.main_job_tracker:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level="info"
    )
