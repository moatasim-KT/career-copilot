"""Simplified FastAPI application for job tracking."""
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create simplified FastAPI application."""
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title="Career Copilot API",
        description="AI-powered job application tracking system",
        version="1.0.0",
    )

    # CORS
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Career Copilot API",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        }

    # Health check
    @app.get("/api/v1/health")
    async def health():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    # Include job router
    try:
        from app.api.v1.jobs import router as jobs_router
        app.include_router(jobs_router, prefix="/api/v1")
        logger.info("Job tracking routes loaded")
    except Exception as e:
        logger.error(f"Failed to load job routes: {e}")

    # Include auth router
    try:
        from app.api.v1.auth import router as auth_router
        app.include_router(auth_router, prefix="/api/v1/auth")
        logger.info("Auth routes loaded")
    except Exception as e:
        logger.warning(f"Auth routes not available: {e}")

    @app.on_event("startup")
    async def startup():
        logger.info("🚀 Career Copilot API starting...")
        logger.info(f"📍 Running on {settings.api_host}:{settings.api_port}")
        logger.info("📋 Endpoints:")
        logger.info("  - GET  /api/v1/health")
        logger.info("  - GET  /api/v1/jobs/applications")
        logger.info("  - POST /api/v1/jobs/applications")
        logger.info("  - GET  /api/v1/jobs/statistics")

    return app


app = create_app()
