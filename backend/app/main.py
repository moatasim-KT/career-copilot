"""
Career Copilot - Job Application Tracking System
FastAPI application entry point
"""

import traceback
from datetime import datetime

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.logging import get_correlation_id, get_logger, setup_logging
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.error_handling import add_error_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

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
	app = FastAPI(title="Career Copilot API", description="AI-powered job application tracking and career management system", version="1.0.0")

	# CORS configuration
	if isinstance(settings.cors_origins, str):
		cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
	else:
		cors_origins = settings.cors_origins
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

	# Security headers
	from app.middleware.security_headers import SecurityHeadersMiddleware

	app.add_middleware(SecurityHeadersMiddleware)

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
				"correlation_id": get_correlation_id(),
			},
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
				"correlation_id": get_correlation_id(),
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
		token = websocket.headers.get("authorization")
		if token and token.startswith("Bearer "):
			token = token.split(" ")[1]

		user_id = await websocket_service.authenticate_websocket(websocket, token, db)

		if user_id:
			await websocket_service.handle_websocket_connection(websocket, user_id)
		else:
			await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")

	# Include routers
	from .api.v1 import (advanced_user_analytics, analytics, applications, auth,
	                     database_performance, feedback_analysis, groq, health,
	                     job_recommendation_feedback, job_sources, jobs,
	                     linkedin_jobs, market_analysis, profile, recommendations,
	                     scheduled_reports, skill_gap_analysis, tasks)

	app.include_router(health.router)
	app.include_router(auth.router)
	app.include_router(profile.router)
	app.include_router(jobs.router)
	app.include_router(job_sources.router)
	app.include_router(analytics.router)
	app.include_router(recommendations.router)
	app.include_router(skill_gap_analysis.router)
	app.include_router(applications.router)
	app.include_router(job_recommendation_feedback.router, prefix="/api/v1", tags=["job-recommendation-feedback"])
	app.include_router(feedback_analysis.router, prefix="/api/v1", tags=["feedback-analysis"])
	app.include_router(market_analysis.router)
	app.include_router(advanced_user_analytics.router)
	app.include_router(scheduled_reports.router)
	app.include_router(tasks.router)
	app.include_router(database_performance.router)

	app.include_router(linkedin_jobs.router)
	app.include_router(groq.router, prefix="/api/v1")

	from .api.v1 import interview

	app.include_router(interview.router)

	@app.on_event("startup")
	async def startup_event():
		logger.info("🚀 Career Copilot API starting...")
		logger.info(f"🌐 Running on {settings.api_host}:{settings.api_port}")

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
		if settings.enable_scheduler:
			from .tasks.scheduled_tasks import start_scheduler

			start_scheduler()
			logger.info("✅ Scheduler started")

		# Initialize Celery (workers should be started separately)

		logger.info("✅ Celery application configured")

	@app.on_event("shutdown")
	async def shutdown_event():
		logger.info("🛑 Career Copilot API shutting down...")

		# Shutdown scheduler
		if settings.enable_scheduler:
			from .tasks.scheduled_tasks import shutdown_scheduler

			shutdown_scheduler()
			logger.info("✅ Scheduler shut down")

	return app


app = create_app()
