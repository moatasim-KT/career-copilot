"""
Career Copilot - Job Application Tracking System
FastAPI application entry point
"""

import traceback
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_correlation_id, get_logger, setup_logging
from app.middleware.error_handling import add_error_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from app.services.resume_parser_service import ResumeParserService

logger = get_logger(__name__)


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
	logger.info("🚀 Career Copilot API starting...")
	logger.info(f"🌐 Running on {get_settings().api_host}:{get_settings().api_port}")

	# Initialize database
	from .core.database import init_db

	init_db()
	logger.info("✅ Database initialized")

	# Initialize cache service
	from .services.cache_service import cache_service

	if cache_service.enabled:
		logger.info("✅ Redis cache service initialized")
	else:
		logger.warning("⚠️ Redis cache service disabled")

	# Start scheduler
	if get_settings().enable_scheduler:
		from .tasks.scheduled_tasks import start_scheduler

		start_scheduler()
		logger.info("✅ Scheduler started")

	# Initialize Celery (workers should be started separately)
	logger.info("✅ Celery application configured")

	yield

	logger.info("🛑 Career Copilot API shutting down...")
	# Shutdown scheduler
	if get_settings().enable_scheduler:
		from .tasks.scheduled_tasks import shutdown_scheduler

		shutdown_scheduler()
		logger.info("✅ Scheduler shut down")


def create_app() -> FastAPI:
	"""Create and configure the FastAPI application."""

	setup_logging()
	settings = get_settings()

	logger.info("--- Configuration Summary ---")
	logger.info(f"Environment: {settings.environment}")
	logger.info(f"Debug Mode: {settings.debug}")
	logger.info(f"API Host: {settings.api_host}:{settings.api_port}")
	logger.info(f"Database URL: {settings.database_url}")
	logger.info(f"SMTP Enabled: {settings.smtp_enabled}")
	logger.info(f"Scheduler Enabled: {settings.enable_scheduler}")
	logger.info(f"Job Scraping Enabled: {settings.enable_job_scraping}")
	logger.info(f"CORS Origins: {settings.cors_origins}")
	logger.info(f"ResumeParserService Version: {ResumeParserService.__version__}")
	logger.info("-----------------------------")

	# Create FastAPI application
	app = FastAPI(
		title="Career Copilot API", description="AI-powered job application tracking and career management system", version="1.0.0", lifespan=lifespan
	)

	# CORS configuration
	if isinstance(settings.cors_origins, str):
		cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
	else:
		cors_origins = settings.cors_origins
	app.add_middleware(
		CORSMiddleware,
		allow_origins=cors_origins,
		allow_credentials=True,
		allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
		allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
		expose_headers=["Content-Type", "Authorization"],
		max_age=600,  # Cache preflight for 10 minutes
	)

	# Essential middleware
	add_error_handlers(app)
	app.add_middleware(LoggingMiddleware)

	# Security headers
	from app.middleware.security_headers import SecurityHeadersMiddleware

	app.add_middleware(SecurityHeadersMiddleware)

	# Metrics middleware (Prometheus)
	from app.middleware.metrics_middleware import MetricsMiddleware

	app.add_middleware(MetricsMiddleware)
	logger.info("✅ Prometheus metrics middleware enabled")

	# OpenTelemetry tracing (optional)
	if settings.enable_opentelemetry:
		from app.core.telemetry import configure_opentelemetry

		configure_opentelemetry(app)

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
				"errors": exc.errors(),
			},
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
				"correlation_id": get_correlation_id(),
			},
		)

	@app.exception_handler(Exception)
	async def general_exception_handler(request: Request, exc: Exception):
		"""Handle all other exceptions (500)"""
		logger.error(f"Unhandled exception: {exc!s}", exc_info=True)
		logger.error(f"Stack trace: {traceback.format_exc()}")
		return JSONResponse(
			status_code=500,
			content={
				"detail": "An internal server error occurred. Please try again later.",
				"error_code": "INTERNAL_SERVER_ERROR",
				"timestamp": datetime.now().isoformat(),
				"correlation_id": get_correlation_id(),
			},
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

	from app.services.websocket_service import websocket_service

	@app.websocket("/ws")
	async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
		await websocket.accept()
		await websocket_service.handle_websocket_connection(websocket, None)

	# Include routers - Comprehensive registration of ALL API endpoints
	from .api.v1 import (
		advanced_user_analytics,
		analytics,
		analytics_extended,
		applications,
		auth,
		cache_admin,
		content,
		dashboard,
		database_admin,
		database_performance,
		email_admin,
		export,
		feedback,
		feedback_analysis,
		groq,
		health,
		import_data,
		integrations_admin,
		interview,
		job_recommendation_feedback,
		job_sources,
		jobs,
		learning,
		linkedin_jobs,
		llm_admin,
		market,
		notifications_new,
		personalization,
		progress_admin,
		recommendations,
		resources,
		resume,
		scheduled_reports,
		services_admin,
		skill_gap_analysis,
		slack_admin,
		social,
		status_admin,
		storage_admin,
		tasks,
		vector_store_admin,
		workflows,
	)

	# Core system routes
	app.include_router(health.router)

	# Authentication & User Management
	app.include_router(auth.router)

	# Include personalization and social routers FIRST (before jobs router)
	# This prevents /jobs/available from conflicting with /jobs/{job_id}
	app.include_router(personalization.router, prefix="/api/v1", tags=["personalization"])
	app.include_router(social.router, prefix="/api/v1", tags=["social"])

	# Core Business Logic
	app.include_router(jobs.router)
	app.include_router(job_sources.router)
	app.include_router(applications.router)
	app.include_router(resume.router, prefix="/api/v1/resume", tags=["resume", "parsing"])
	
	# Data Export & Import
	app.include_router(export.router)
	app.include_router(import_data.router)

	# Analytics & Reporting
	app.include_router(analytics.router)
	app.include_router(analytics_extended.router)
	app.include_router(dashboard.router)
	app.include_router(advanced_user_analytics.router)
	app.include_router(market.router, prefix="/api/v1", tags=["Market Intelligence"])

	# Recommendations & Matching
	app.include_router(recommendations.router)
	app.include_router(skill_gap_analysis.router)
	app.include_router(job_recommendation_feedback.router, prefix="/api/v1", tags=["job-recommendation-feedback"])

	# User Engagement
	app.include_router(workflows.router)
	app.include_router(content.router)
	app.include_router(resources.router)
	app.include_router(learning.router)
	app.include_router(notifications_new.router)
	app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
	app.include_router(feedback_analysis.router, prefix="/api/v1", tags=["feedback-analysis"])
	app.include_router(interview.router)  # Already has prefix="/api/v1/interview"

	# Reporting & Insights
	app.include_router(scheduled_reports.router)
	app.include_router(progress_admin.router)
	app.include_router(status_admin.router)

	# Integration & External Services
	app.include_router(linkedin_jobs.router)
	app.include_router(email_admin.router)
	app.include_router(slack_admin.router)
	app.include_router(services_admin.router)
	app.include_router(integrations_admin.router, prefix="/api/v1/integrations", tags=["integrations"])
	app.include_router(groq.router, prefix="/api/v1")

	# System Administration
	app.include_router(database_admin.router)
	app.include_router(database_performance.router)
	app.include_router(cache_admin.router)
	app.include_router(storage_admin.router)
	app.include_router(vector_store_admin.router)
	app.include_router(llm_admin.router)

	# Background Tasks
	app.include_router(tasks.router)

	# Metrics endpoint for Prometheus scraping
	from .api.v1 import metrics as metrics_api

	app.include_router(metrics_api.router)

	return app


app = create_app()
