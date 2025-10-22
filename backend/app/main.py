"""
Career Copilot - Job Application Tracking System
FastAPI application entry point
"""

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import traceback
import os

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging, set_correlation_id, get_correlation_id
from app.core.database import get_db
from app.core.exceptions import ContractAnalysisError, AuthenticationError, AuthorizationError
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.auth_middleware import AuthMiddleware
from app.scheduler import scheduler
from app.middleware.error_handling import add_error_handlers

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    setup_logging()
    settings = get_settings()

    logger.info("--- Configuration Summary ---")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"API Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"JWT Expiration: {settings.jwt_expiration_hours} hours")
    logger.info(f"SMTP Enabled: {settings.smtp_enabled}")
    logger.info(f"Scheduler Enabled: {settings.enable_scheduler}")
    logger.info(f"Job Scraping Enabled: {settings.enable_job_scraping}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info("-----------------------------")
    
    # Create FastAPI application
    app = FastAPI(
        title="Career Copilot API",
        description="AI-powered job application tracking and career management system",
        version="1.0.0"
    )
    
    # CORS configuration
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    
    # Essential middleware
    add_error_handlers(app)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware)
    
    # Exception handlers for structured error responses
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors (400)"""
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Validation error in request data",
                "error_code": "VALIDATION_ERROR",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": get_correlation_id(),
                "errors": exc.errors()
            }
        )
    
    @app.exception_handler(AuthenticationError)
    async def authentication_exception_handler(request: Request, exc: AuthenticationError):
        """Handle authentication errors (401)"""
        logger.warning(f"Authentication error: {exc.message}")
        return JSONResponse(
            status_code=401,
            content={
                "detail": exc.user_message,
                "error_code": exc.error_code,
                "timestamp": datetime.now().isoformat(),
                "correlation_id": get_correlation_id()
            }
        )
    
    @app.exception_handler(AuthorizationError)
    async def authorization_exception_handler(request: Request, exc: AuthorizationError):
        """Handle authorization errors (403)"""
        logger.warning(f"Authorization error: {exc.message}")
        return JSONResponse(
            status_code=403,
            content={
                "detail": exc.user_message,
                "error_code": exc.error_code,
                "timestamp": datetime.now().isoformat(),
                "correlation_id": get_correlation_id()
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions (404, etc.)"""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": get_correlation_id()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions (500)"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred. Please try again later.",
                "error_code": "INTERNAL_SERVER_ERROR",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": get_correlation_id()
            }
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
    
    # Include routers
    from .api.v1 import health, auth, jobs, applications, analytics, recommendations, skill_gap, profile
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(jobs.router)
    app.include_router(analytics.router)
    app.include_router(recommendations.router)
    app.include_router(skill_gap.router)
    app.include_router(applications.router)
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("🚀 Career Copilot API starting...")
        logger.info(f"🌐 Running on {settings.api_host}:{settings.api_port}")
        
        # Initialize database
        from .core.database import init_db
        init_db()
        logger.info("✅ Database initialized")
        
        # Start scheduler
        if settings.enable_scheduler:
            from .scheduler import start_scheduler
            start_scheduler()
            logger.info("✅ Scheduler started")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🛑 Career Copilot API shutting down...")
        
        # Shutdown scheduler
        if settings.enable_scheduler:
            from .scheduler import shutdown_scheduler
            shutdown_scheduler()
            logger.info("✅ Scheduler shut down")
    
    return app


app = create_app()
