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
from app.schemas.api_models import ErrorResponse
from app.services.resume_parser_service import ResumeParserService

logger = get_logger(__name__)


import os
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
	logger.info("🚀 Career Copilot API starting...")
	logger.info(f"🌐 Running on {get_settings().api_host}:{get_settings().api_port}")

	# Initialize database
	from .core.database import _setup_legacy_compatibility, get_db_manager

	# Initialize database engines on the active event loop to avoid
	# asyncpg "Future attached to a different loop" errors.
	# Prefer eager init during application lifespan so the async engine is
	# available for all request handlers. You can explicitly disable eager
	# initialization by setting DB_EAGER_INIT=0 or FALSE in the environment.
	# This keeps backwards compatibility while making the test runner and
	# production server more deterministic.
	eager_flag = os.getenv("DB_EAGER_INIT", os.getenv("FORCE_DB_INIT", "1")).lower()
	if eager_flag in {"1", "true", "yes"}:
		logger.info("DB_EAGER_INIT enabled (default): performing eager DB engine initialization in lifespan")
		db_manager = get_db_manager()
		# Initialize engines (creates async and sync engines) on this loop.
		# Wrap in try/except so the app can still start in degraded mode
		# if an async driver is missing (useful for environments without asyncpg).
		try:
			# Create both sync and async engines on the active event loop
			db_manager._initialize_engines()
			# Ensure schema exists using the async initialization path if async engine created,
			# otherwise fall back to sync schema creation via init_db() called below.
			if db_manager.async_engine is not None:
				try:
					await db_manager.init_database()

					# Initialize default user for single-user mode
					from app.core.init_db import initialize_database

					async with db_manager.async_session() as session:
						await initialize_database(session)

				except Exception:
					logger.exception("Failed to perform async database init during lifespan; will fall back to sync init if possible")
			# Update legacy compatibility globals now that engines may be ready
			_setup_legacy_compatibility()
			logger.info("✅ Database engines initialized and schema ensured (eager)")
		except Exception as exc:
			logger.exception("Eager DB engine initialization failed: %s", exc)
			logger.warning("Proceeding without eager async engine; engines will be created lazily on first use")
	else:
		logger.info("DB_EAGER_INIT explicitly disabled: skipping eager DB initialization. Engines will be created lazily on first use.")

	# Initialize cache service
	from .services.cache_service import cache_service

	if cache_service.enabled:
		logger.info("✅ Redis cache service initialized")
	else:
		logger.warning("⚠️ Redis cache service disabled")

	# Start scheduler
	if get_settings().enable_scheduler and os.getenv("DISABLE_SCHEDULER_IN_TESTS") != "True":
		from .tasks.scheduled_tasks import start_scheduler

		start_scheduler()
		logger.info("✅ Scheduler started")
	elif os.getenv("DISABLE_SCHEDULER_IN_TESTS") == "True":
		logger.info("Info: scheduler disabled for testing environment.")
	else:
		logger.info("Info: scheduler disabled by configuration.")

	# Initialize Celery (workers should be started separately)
	logger.info("✅ Celery application configured")

	yield

	logger.info("🛑 Career Copilot API shutting down...")
	# Shutdown scheduler
	if get_settings().enable_scheduler and os.getenv("DISABLE_SCHEDULER_IN_TESTS") != "True":
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

	# ⚠️ SECURITY WARNING: Check if authentication is disabled
	if getattr(settings, "disable_auth", False):
		logger.warning("=" * 80)
		logger.warning("⚠️  SECURITY WARNING: AUTHENTICATION IS DISABLED!")
		logger.warning("⚠️  This is ONLY acceptable in development environments.")
		logger.warning("⚠️  ")
		logger.warning(f"⚠️  Current environment: {settings.environment}")
		if settings.environment.lower() == "production":
			logger.error("❌ CRITICAL: Authentication is disabled in PRODUCTION!")
			logger.error("❌ This is a severe security risk!")
			logger.error("❌ Set DISABLE_AUTH=false or remove it from environment")
			logger.error("=" * 80)
			# In production, we could raise an exception here to prevent startup
			# raise RuntimeError("Cannot start in production with authentication disabled")
		else:
			logger.warning("⚠️  To enable authentication, set DISABLE_AUTH=false")
		logger.warning("=" * 80)

	logger.info("-----------------------------")

	# Create FastAPI application
	app = FastAPI(
		title="Career Copilot API", description="AI-powered job application tracking and career management system", version="1.0.0", lifespan=lifespan
	)

	# Normalize module aliases to avoid duplicate imports under both
	# "app.*" and "backend.app.*" module paths which can cause SQLAlchemy
	# to register the same ORM class twice under different module names.
	# This can happen in some test or import contexts where the package is
	# referenced by both top-level names. We scan sys.modules for pairs of
	# modules that point to the same file and alias the backend.* name to the
	# canonical app.* module object so SQLAlchemy sees only one class.
	def _normalize_module_aliases():
		import sys
		from importlib import import_module

		# Only proceed when both naming schemes might be present
		if not any(name.startswith("backend.app") for name in sys.modules):
			return

		for name, mod in list(sys.modules.items()):
			# look for loaded app.* modules and their backend.app.* counterparts
			if not name.startswith("app."):
				continue
			backend_name = "backend." + name
			if backend_name in sys.modules:
				# If both are present and point to the same file, alias them to
				# the same module object to avoid duplicate class registration
				mod_b = sys.modules[backend_name]
				try:
					file_a = getattr(mod, "__file__", None)
					file_b = getattr(mod_b, "__file__", None)
				except Exception:
					file_a = file_b = None
				if file_a and file_b and file_a == file_b:
					sys.modules[backend_name] = mod

	# Run normalization early, before routers and models are imported
	_normalize_module_aliases()

	# Proactively import the canonical `app` model modules and alias them
	# to the `backend.app.*` names so that any later import using the
	# alternate package path does not create duplicate module objects
	# (which would register ORM classes twice).
	def _import_and_alias_app_packages():
		import importlib
		import pkgutil
		import sys

		try:
			app_models = importlib.import_module("app.models")
		except Exception:
			# If app.models cannot be imported yet, skip this step.
			return

		# Walk all submodules under app.models and import them to ensure
		# they are loaded under the canonical 'app.' package name.
		for finder, modname, ispkg in pkgutil.walk_packages(app_models.__path__, prefix=app_models.__name__ + "."):
			try:
				importlib.import_module(modname)
			except Exception:
				# Ignore import errors here; modules may have heavy deps.
				continue

		# Create aliases for backend.* -> app.* so later imports reuse same modules
		for name in list(sys.modules.keys()):
			if name.startswith("app."):
				backend_name = "backend." + name
				if backend_name not in sys.modules:
					sys.modules[backend_name] = sys.modules[name]

	_import_and_alias_app_packages()

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
		payload = ErrorResponse(
			request_id=get_correlation_id(),
			timestamp=datetime.now().isoformat(),
			error_code="VALIDATION_ERROR",
			detail="Validation error in request data",
			field_errors={"validation_errors": exc.errors()},
			suggestions=["Please check the request format and required fields", "Ensure all data types match the expected format"],
		)
		return JSONResponse(status_code=400, content=payload.model_dump())

	@app.exception_handler(HTTPException)
	async def http_exception_handler(request: Request, exc: HTTPException):
		"""Handle HTTP exceptions (404, etc.)"""
		logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
		payload = ErrorResponse(
			request_id=get_correlation_id(),
			timestamp=datetime.now().isoformat(),
			error_code=f"HTTP_{exc.status_code}",
			detail=exc.detail,
		)
		return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

	@app.exception_handler(Exception)
	async def general_exception_handler(request: Request, exc: Exception):
		"""Handle all other exceptions (500)"""
		logger.error(f"Unhandled exception: {exc!s}", exc_info=True)
		logger.error(f"Stack trace: {traceback.format_exc()}")
		payload = ErrorResponse(
			request_id=get_correlation_id(),
			timestamp=datetime.now().isoformat(),
			error_code="INTERNAL_SERVER_ERROR",
			detail="An internal server error occurred. Please try again later.",
		)
		return JSONResponse(status_code=500, content=payload.model_dump())

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

		# Authenticate connection (handles both JWT tokens and guest access in dev mode)
		token = websocket.query_params.get("token")
		user_id = await websocket_service.authenticate_websocket(websocket, token, db)

		if user_id:
			logger.info(f"WebSocket connection accepted for user: {user_id}")
			await websocket_service.handle_websocket_connection(websocket, user_id)
		else:
			logger.warning("WebSocket authentication failed")
			await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

	# Include routers - Comprehensive registration of ALL API endpoints
	from .api.v1 import (
		analytics,
		applications,
		auth,
		bulk_operations,
		cache_admin,
		content,
		dashboard,
		database_admin,
		database_performance,
		email_admin,
		export,
		feedback,
		feedback_analysis,
		# groq,  # Commented out - missing dependencies (groq_service, groq_optimizer, groq_router, groq_monitor)
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
		notifications,
		personalization,
		progress_admin,
		recommendations,
		resources,
		resume,
		scheduled_reports,
		services_admin,
		skill_gap_analysis,
		slack,
		slack_integration,
		social,
		status_admin,
		storage_admin,
		tasks,
		vector_store_admin,
		websocket_notifications,
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

	# Bulk Operations
	app.include_router(bulk_operations.router)

	# Analytics & Reporting (unified)
	# Use unified analytics router which consolidates legacy and v1 analytics endpoints
	from .api.v1 import analytics as analytics_module

	app.include_router(analytics_module.router, prefix="/api/v1", tags=["analytics"])
	app.include_router(dashboard.router)
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
	app.include_router(notifications.router, prefix="/api/v1")
	app.include_router(websocket_notifications.router, prefix="/api/v1")
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
	app.include_router(slack.router, prefix="/api/v1")
	app.include_router(slack_integration.router, prefix="/api/v1")
	app.include_router(services_admin.router)
	app.include_router(integrations_admin.router, prefix="/api/v1/integrations", tags=["integrations"])
	# app.include_router(groq.router, prefix="/api/v1")  # Commented out - missing service dependencies

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
