"""
FastAPI application factory and configuration with comprehensive security.
"""

import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1 import contracts_router, contract_results_router, health_router, monitoring_router, security_router, email_router, performance_router, precedents_router, users, docusign, slack, cloud_storage, progress, cache, load_balancer, database_performance, auth, service_management as services_router, groq, production_orchestration, health_analytics, external_services_router, agent_cache, cost_management, file_storage, configuration, production_optimization, firebase_auth
from .api.v1.performance_metrics import router as performance_metrics_router
# health_enhanced router not available
from .api.v1.health_comprehensive import router as health_comprehensive_router
from .api.v1.monitoring import router as monitoring_api_router
from .api.v1.production_health import router as production_health_router
from .api.v1.chroma_health import router as chroma_health_router
from .api import analytics, workflows, websockets
from .api.workflow_progress import router as workflow_progress_router
from .core.audit import AuditEventType, AuditSeverity, audit_logger
from .core.config import get_settings, setup_langsmith, validate_required_settings
from .core.exceptions import DocumentProcessingError, SecurityError, ValidationError
from .core.validation_handler import ValidationExceptionHandler
from .models.validation_models import ValidationError as CustomValidationError
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from .core.langsmith_integration import initialize_langsmith
from .core.logging import get_logger, setup_logging
from .core.monitoring import initialize_monitoring, monitoring_system
from .core.openapi_config import setup_api_documentation, customize_openapi_schema
from .core.api_playground import setup_api_playground, APIPlaygroundConfig
from .middleware.comprehensive_security import ComprehensiveSecurityMiddleware
from .middleware.resource_middleware import ResourceManagementMiddleware
from .middleware.jwt_auth_middleware import JWTAuthenticationMiddleware, SessionManagementMiddleware
from .middleware.logging_middleware import LoggingMiddleware
from .middleware.global_error_handler import GlobalErrorHandlerMiddleware
from .middleware.request_validation import RequestValidationMiddleware, ContentValidationMiddleware
from .middleware.firebase_auth_middleware import FirebaseAuthMiddleware
from .middleware.input_validation_middleware import InputValidationMiddleware
from .middleware.rate_limiting_middleware import RateLimitingMiddleware, set_rate_limiter
from .middleware.csp_middleware import CSPMiddleware, SecurityHeadersMiddleware, set_csp_middleware
from .dependencies import get_service_registry

from .middleware.monitoring_middleware import (
	create_health_check_middleware,
	create_metrics_collection_middleware,
	create_monitoring_middleware,
)
from .models.api_models import ErrorResponse

logger = get_logger(__name__)


def create_app() -> FastAPI:
	"""Create and configure the FastAPI application with comprehensive security measures."""

	# Setup logging first
	setup_logging()

	# Initialize enhanced configuration system
	try:
		from .core.config_init import initialize_configuration_system, get_configuration_status, is_configuration_ready
		
		config_status = initialize_configuration_system(
			enable_hot_reload=True,
			enable_validation=True
		)
		logger.info(f"Configuration system initialized: {config_status.environment} environment")
		
		if not config_status.validation_passed:
			logger.error(f"Configuration validation failed with {config_status.errors} errors")
			if config_status.environment == "production":
				raise RuntimeError("Configuration validation failed in production")
		
		if config_status.warnings > 0:
			logger.warning(f"Configuration has {config_status.warnings} warnings")
			
	except Exception as e:
		logger.error(f"Failed to initialize enhanced configuration system: {e}")
		logger.warning("Falling back to legacy configuration system")
		
		# Fallback to legacy system
		validate_required_settings()
		setup_langsmith()

	settings = get_settings()

	app = FastAPI(
		title="Career Copilot API",
		description="AI-powered job application tracking and career management system",
		version="1.0.0",
		docs_url="/docs" if settings.api_debug else None,
		redoc_url="/redoc" if settings.api_debug else None,
		openapi_tags=None,  # Will be set by setup_api_documentation
	)

	# Set up enhanced API documentation
	setup_api_documentation(app)
	
	# Set up interactive API playground
	playground_config = APIPlaygroundConfig(
		title="Career Copilot API Playground",
		description="Interactive API testing and documentation environment",
		version="1.0.0",
		enable_auth_helper=True,
		enable_examples=True,
		enable_code_generation=True
	)
	setup_api_playground(app, playground_config)

	# Add global error handler first to catch all exceptions
	app.add_middleware(GlobalErrorHandlerMiddleware)
	
	# Add enhanced input validation middleware (first line of defense)
	from .middleware.enhanced_input_validation import EnhancedInputValidationMiddleware
	app.add_middleware(EnhancedInputValidationMiddleware)
	
	# Add original input validation middleware as backup
	app.add_middleware(InputValidationMiddleware)
	
	# Add request validation middleware (before other processing)
	app.add_middleware(RequestValidationMiddleware)
	app.add_middleware(ContentValidationMiddleware)
	
	# Add rate limiting middleware
	rate_limiter = RateLimitingMiddleware(app)
	set_rate_limiter(rate_limiter)
	app.add_middleware(RateLimitingMiddleware)
	
	# Add logging middleware for request tracking
	app.add_middleware(LoggingMiddleware)
	
	# Add monitoring middleware (for comprehensive tracking)
	if settings.enable_monitoring:
		app.add_middleware(create_monitoring_middleware())
		app.add_middleware(create_health_check_middleware())
		app.add_middleware(create_metrics_collection_middleware())

	# Add resource management middleware for throttling and resource monitoring
	app.add_middleware(ResourceManagementMiddleware, enable_throttling=True)

	# Enhanced rate limiting removed during cleanup

	# Add Firebase authentication middleware
	app.add_middleware(FirebaseAuthMiddleware)
	
	# Add JWT authentication middleware
	app.add_middleware(JWTAuthenticationMiddleware)
	
	# Add session management middleware
	app.add_middleware(SessionManagementMiddleware)

	# Add enhanced security headers middleware
	from .middleware.enhanced_security_headers import EnhancedSecurityHeadersMiddleware, set_enhanced_security_headers_middleware
	enhanced_security_headers = EnhancedSecurityHeadersMiddleware(app)
	set_enhanced_security_headers_middleware(enhanced_security_headers)
	app.add_middleware(EnhancedSecurityHeadersMiddleware)
	
	# Add original CSP and security headers middleware as backup
	csp_middleware = CSPMiddleware(app)
	set_csp_middleware(csp_middleware)
	app.add_middleware(CSPMiddleware)
	app.add_middleware(SecurityHeadersMiddleware)
	
	# Add comprehensive security middleware (order matters!)
	app.add_middleware(ComprehensiveSecurityMiddleware)

	# Add enhanced CORS middleware with security hardening
	from .middleware.enhanced_cors_middleware import EnhancedCORSMiddleware, set_enhanced_cors_middleware
	enhanced_cors = EnhancedCORSMiddleware(app)
	set_enhanced_cors_middleware(enhanced_cors)
	app.add_middleware(EnhancedCORSMiddleware)
	
	# Add original CORS middleware as fallback
	cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
	logger.info(f"CORS origins configured: {cors_origins}")
	
	app.add_middleware(
		CORSMiddleware,
		allow_origins=cors_origins,
		allow_credentials=True,
		allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Allow necessary methods
		allow_headers=[
			"Authorization", 
			"Content-Type", 
			"X-API-Key", 
			"X-Request-ID", 
			"X-Correlation-ID",
			"Accept",
			"Origin",
			"User-Agent"
		],
		expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining", "X-Correlation-ID"],
	)

	# Add validation exception handlers
	@app.exception_handler(CustomValidationError)
	async def validation_exception_handler(request: Request, exc: CustomValidationError) -> JSONResponse:
		"""Handle custom validation errors."""
		return await ValidationExceptionHandler.validation_exception_handler(request, exc)
	
	@app.exception_handler(RequestValidationError)
	async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
		"""Handle FastAPI request validation errors."""
		return await ValidationExceptionHandler.request_validation_exception_handler(request, exc)
	
	@app.exception_handler(PydanticValidationError)
	async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
		"""Handle Pydantic validation errors."""
		return await ValidationExceptionHandler.pydantic_validation_exception_handler(request, exc)

	# Add security exception handlers
	@app.exception_handler(SecurityError)
	async def security_exception_handler(request: Request, exc: SecurityError) -> JSONResponse:
		"""Handle security errors."""
		logger.warning(f"Security error: {exc.message}")

		# Log security violation
		from .core.audit import audit_logger

		audit_logger.log_security_violation(violation_type="security_error", description=exc.message, request=request, severity="high")

		return JSONResponse(
			status_code=403,
			content=ErrorResponse(
				error="Security Error",
				message="Access denied due to security policy",
				suggestions=["Please ensure your request complies with security requirements"],
			).model_dump(),
		)

	@app.exception_handler(HTTPException)
	async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
		"""Handle HTTP exceptions with security logging."""
		# Log unauthorized access attempts
		if exc.status_code == 401:
			from .core.audit import audit_logger

			audit_logger.log_unauthorized_access(attempted_resource=str(request.url.path), reason="Invalid authentication", request=request)
		elif exc.status_code == 403:
			from .core.audit import audit_logger

			audit_logger.log_unauthorized_access(attempted_resource=str(request.url.path), reason="Insufficient permissions", request=request)
		elif exc.status_code == 429:
			from .core.audit import audit_logger

			audit_logger.log_rate_limit_exceeded(limit_type="http_rate_limit", request=request)

		return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

	# Add root route
	@app.get("/")
	async def root():
		"""Root endpoint with API information."""
		return {
			"message": "Career Copilot API",
			"version": "1.0.0",
			"status": "running",
			"timestamp": datetime.now().isoformat(),
			"docs": "/docs",
			"health": "/api/v1/health",
			"endpoints": {
				"health": "/api/v1/health",
				"contracts": "/api/v1/contracts",
				"auth": "/api/v1/auth",
				"monitoring": "/monitoring"
			}
		}

	# Add connection test endpoint
	@app.get("/api/v1/connection-test")
	async def connection_test():
		"""Simple endpoint to test frontend-backend connectivity."""
		return {
			"status": "connected",
			"message": "Frontend-backend connection successful",
			"timestamp": datetime.now().isoformat(),
			"server_info": {
				"host": settings.api_host,
				"port": settings.api_port,
				"cors_origins": settings.cors_origins.split(",")
			}
		}

	@app.get("/favicon.ico")
	async def favicon():
		"""Favicon endpoint to prevent 404 errors."""
		from fastapi.responses import Response
		return Response(status_code=204)  # No Content

	# Include API routers
	# API v1 routes
	app.include_router(health_router, prefix="/api/v1")
	# health_enhanced router not available
	app.include_router(health_comprehensive_router, prefix="/api/v1")
	app.include_router(monitoring_api_router, prefix="/api/v1")
	app.include_router(contracts_router, prefix="/api/v1")
	app.include_router(contract_results_router, prefix="/api/v1")
	app.include_router(precedents_router, prefix="/api/v1")
	app.include_router(auth.router, prefix="/api/v1/auth")
	app.include_router(firebase_auth.router, prefix="/api/v1/auth")
	app.include_router(security_router, prefix="/api/v1/security")
	
	# Import and include security validation router
	try:
		from .api.v1.security_validation import router as security_validation_router
		app.include_router(security_validation_router, prefix="/api/v1")
		logger.info("Security validation router loaded successfully")
	except Exception as e:
		logger.warning(f"Failed to import security validation router: {e}")
	app.include_router(monitoring_router)  # No prefix, already has /monitoring
	app.include_router(performance_router, prefix="/api/v1")  # Performance monitoring
	app.include_router(email_router, prefix="/api/v1")
	app.include_router(docusign.router, prefix="/api/v1")
	app.include_router(users.router, prefix="/api/v1")
	app.include_router(slack.router, prefix="/api/v1")
	app.include_router(cloud_storage.router, prefix="/api/v1")
	app.include_router(progress.router, prefix="/api/v1")
	app.include_router(cache.router, prefix="/api/v1")
	app.include_router(load_balancer.router, prefix="/api/v1")
	app.include_router(database_performance.router, prefix="/api/v1")
	app.include_router(analytics.router, prefix="/api/v1")
	app.include_router(workflows.router, prefix="/api/v1")
	app.include_router(workflow_progress_router)
	app.include_router(websockets.router)
	app.include_router(services_router.router, prefix="/api/v1/services")
	app.include_router(groq.router, prefix="/api/v1")
	app.include_router(production_orchestration.router, prefix="/api/v1")
	app.include_router(file_storage.router, prefix="/api/v1")
	app.include_router(production_health_router, prefix="/api/v1")
	app.include_router(health_analytics, prefix="/api/v1")
	app.include_router(external_services_router, prefix="/api/v1")
	app.include_router(agent_cache.router, prefix="/api/v1")
	app.include_router(cost_management.router, prefix="/api/v1")
	app.include_router(performance_metrics_router, prefix="/api/v1")
	app.include_router(chroma_health_router, prefix="/api/v1")
	app.include_router(configuration.router, prefix="/api/v1")
	app.include_router(production_optimization.router, prefix="/api/v1/production")
	
	# Import vector store router separately to avoid circular imports
	try:
		from .api.v1.vector_store import router as vector_store_router
		app.include_router(vector_store_router, prefix="/api/v1")
	except Exception as e:
		logger.warning(f"Failed to import vector store router: {e}")
	
	# Import enhanced upload router
	try:
		from .api.v1.upload import router as upload_router
		app.include_router(upload_router, prefix="/api/v1")
		logger.info("Enhanced upload router loaded successfully")
	except Exception as e:
		logger.warning(f"Failed to import enhanced upload router: {e}")
	
	# Import real-time analysis status router
	try:
		from .api.v1.analysis_status import router as analysis_status_router
		app.include_router(analysis_status_router, prefix="/api/v1")
		logger.info("Real-time analysis status router loaded successfully")
	except Exception as e:
		logger.warning(f"Failed to import analysis status router: {e}")
	
	# Import analysis history router
	try:
		from .api.v1.analysis_history import router as analysis_history_router
		app.include_router(analysis_history_router, prefix="/api/v1")
		logger.info("Analysis history router loaded successfully")
	except Exception as e:
		logger.warning(f"Failed to import analysis history router: {e}")
	
	# Import migration management router
	try:
		from .api.v1.migrations import router as migrations_router
		app.include_router(migrations_router, prefix="/api/v1")
		logger.info("Migration management router loaded successfully")
	except Exception as e:
		logger.warning(f"Failed to import migration management router: {e}")
	
	# Import background tasks router
	try:
		from .api.v1.background_tasks import router as background_tasks_router
		app.include_router(background_tasks_router, prefix="/api/v1/tasks")
		logger.info("Background tasks router loaded successfully")
	except Exception as e:
		logger.warning(f"Failed to import background tasks router: {e}")
	
	# Import email templates router
	try:
		from .api.v1.email_templates import router as email_templates_router
		app.include_router(email_templates_router, prefix="/api/v1")
		logger.info("Email templates router loaded successfully")
	except Exception as e:
		logger.warning(f"Failed to import email templates router: {e}")

	# Add startup event
	@app.on_event("startup")
	async def startup_event():
		logger.info("🚀 Career Copilot API starting up...")
		logger.info(f"🌐 API will run on {settings.api_host}:{settings.api_port}")

		# Initialize environment configuration first
		from .core.environment_config import setup_environment
		setup_environment()

		# Initialize service dependency manager
		from .core.service_dependency_manager import get_service_dependency_manager, setup_default_services
		
		service_manager = get_service_dependency_manager()
		setup_default_services()
		
		# Mark backend as starting
		service_manager.mark_service_starting("backend")
		
		# Run comprehensive startup checks and auto-initialize database if needed
		from .core.startup_checks import startup_check_and_init
		
		logger.info("🔍 Running comprehensive startup validation...")
		try:
			startup_success = await startup_check_and_init()
			
			if not startup_success:
				logger.error("❌ Startup validation failed. Please check the logs and fix the issues.")
				service_manager.mark_service_failed("backend", "Startup validation failed")
				
				# Continue in production mode but with warnings
				logger.warning("⚠️  Continuing despite validation failures - some features may be limited")
			else:
				logger.info("✅ Startup validation completed successfully")
				service_manager.mark_service_running("backend")
		except Exception as e:
			logger.error(f"❌ Startup validation error: {e}")
			service_manager.mark_service_failed("backend", f"Startup error: {e}")
			logger.warning("⚠️  Continuing with basic startup - some features may be limited")

		# Initialize security components (simplified for production readiness)
		try:
			from .core.environment_config import get_environment_config_manager
			env_manager = get_environment_config_manager()
			
			if env_manager.is_production():
				logger.info("🔒 Production security mode enabled")
			else:
				logger.info("🔓 Development mode - security features simplified")
		except Exception as e:
			logger.warning(f"Security validation error: {e}")

		# Initialize load balancer and resource manager (simplified for production readiness)
		from .core.environment_config import get_environment_config_manager
		env_manager = get_environment_config_manager()
		
		if env_manager.is_production() and settings.enable_monitoring:
			try:
				from .core.load_balancer import get_load_balancer
				from .core.resource_manager import get_resource_manager
				
				# Start load balancer
				load_balancer = await get_load_balancer()
				await load_balancer.start()
				logger.info("Load balancer initialized and started")
				
				# Start resource manager
				resource_manager = await get_resource_manager()
				await resource_manager.start()
				logger.info("Resource manager initialized and started")
				
			except ImportError:
				logger.info("Load balancer and resource manager modules not available, using simplified mode")
			except Exception as e:
				logger.warning(f"Failed to initialize load balancer or resource manager: {e}")
		else:
			logger.info("Load balancer and resource manager disabled (development/simplified mode)")

		# Initialize Service Registry and Manager
		from .core.service_manager import get_service_manager
		service_manager = await get_service_manager()
		app.state.service_manager = service_manager
		
		# Register default services (example) - skip for now to avoid errors
		# TODO: Implement proper service registration when needed
		logger.info("Service registry initialized (service registration skipped)")

		service_manager.start()
		
		# Start service monitoring (environment-aware)
		if env_manager.is_production() and settings.enable_monitoring:
			try:
				from .services.monitoring_service import get_monitoring_service
				monitoring_service = get_monitoring_service()
				asyncio.create_task(monitoring_service.start_monitoring())
				logger.info("Service monitoring started")
			except Exception as e:
				logger.warning(f"Service monitoring initialization failed: {e}")
		else:
			logger.info("Service monitoring disabled (development/simplified mode)")

		# Initialize logging health service and create missing directories
		from .services.logging_health_service import get_logging_health_service
		logging_health = get_logging_health_service()
		creation_results = logging_health.create_missing_directories()
		if creation_results:
			logger.info("Created missing log directories", directories=list(creation_results.keys()))

		# Initialize and start comprehensive monitoring system
		try:
			from .core.comprehensive_monitoring import get_comprehensive_monitoring
			comprehensive_monitoring = get_comprehensive_monitoring()
			await comprehensive_monitoring.start()
			logger.info("Comprehensive monitoring system started")
		except Exception as e:
			logger.warning(f"Comprehensive monitoring system initialization failed: {e}")

		# Initialize and start health automation service (environment-aware)
		if env_manager.is_production() and settings.enable_monitoring:
			try:
				from .services.health_automation_service import get_health_automation_service
				health_automation = get_health_automation_service()
				await health_automation.start()
				logger.info("Health automation service started")
			except Exception as e:
				logger.warning(f"Health automation service initialization failed: {e}")
		else:
			logger.info("Health automation service disabled (development/simplified mode)")

		# Log startup event (simplified)
		try:
			audit_logger.log_event(
				event_type=AuditEventType.SYSTEM_START,
				action="Application startup",
				result="success",
				severity=AuditSeverity.MEDIUM,
				details={
					"version": "1.0.0",
					"environment": env_manager.get_environment().value,
					"security_enabled": env_manager.get_config().enable_security,
					"monitoring_enabled": settings.enable_monitoring,
				},
			)
		except Exception as e:
			logger.warning(f"Audit logging failed: {e}")

		# Start agent health monitoring if available
		try:
			from .agents.orchestration_service import get_orchestration_service
			orchestration_service = get_orchestration_service()
			await orchestration_service.start_health_monitoring_if_enabled()
		except Exception as e:
			logger.warning(f"Agent health monitoring initialization failed: {e}")
		
		# Initialize ChromaDB client and health monitoring
		try:
			from .services.chroma_client import get_chroma_client
			from .services.chroma_health_monitor import start_health_monitoring
			
			logger.info("🔍 Initializing ChromaDB client with connection pooling...")
			chroma_client = await get_chroma_client()
			
			# Perform initial health check
			health_info = await chroma_client.health_check()
			if health_info["status"] == "healthy":
				logger.info("✅ ChromaDB client initialized successfully")
				
				# Start health monitoring
				await start_health_monitoring()
				logger.info("✅ ChromaDB health monitoring started")
			else:
				logger.warning(f"⚠️  ChromaDB client initialized with warnings: {health_info}")
				
		except Exception as e:
			logger.error(f"❌ ChromaDB initialization failed: {e}")
			logger.warning("⚠️  Continuing without ChromaDB - vector search features will be limited")
		
		# Initialize background task queue system
		try:
			from .services.task_queue_manager import initialize_task_queue_manager
			
			logger.info("🔄 Initializing background task queue system...")
			await initialize_task_queue_manager()
			logger.info("✅ Background task queue system initialized successfully")
			
		except Exception as e:
			logger.error(f"❌ Background task queue initialization failed: {e}")
			logger.warning("⚠️  Continuing without background tasks - some features will be limited")
		
		logger.info("🌐 Available endpoints:")
		logger.info("  - GET /api/v1/health - Basic health check")
		logger.info("  - GET /api/v1/health/detailed - Comprehensive health check")
		logger.info("  - GET /api/v1/health/readiness - Kubernetes readiness probe")
		logger.info("  - GET /api/v1/health/liveness - Kubernetes liveness probe")
		logger.info("  - GET /api/v1/health/environment - Environment info")
		logger.info("  - GET /api/v1/connection-test - Connection test")
		logger.info("  - POST /api/v1/applications - Create job application")

		# Enhanced monitoring endpoints (environment-aware)
		if env_manager.is_production() and settings.enable_monitoring:
			logger.info("Enhanced monitoring endpoints:")
			logger.info("  - GET /monitoring/health - Basic health check")
			logger.info("  - GET /monitoring/health/detailed - Comprehensive health check")
			logger.info("  - GET /monitoring/health/live - Kubernetes liveness probe")
			logger.info("  - GET /monitoring/health/ready - Kubernetes readiness probe")
			logger.info("  - GET /monitoring/status - System status")
			logger.info("  - GET /monitoring/metrics - Application metrics")
			logger.info("  - GET /monitoring/alerts - Alert management")
		else:
			logger.info("Basic monitoring endpoints:")
			logger.info("  - GET /api/v1/health - Basic health check")
			logger.info("  - GET /api/v1/health/detailed - Comprehensive health check")
			logger.info("  - GET /api/v1/health/readiness - Readiness probe")
			logger.info("  - GET /api/v1/health/liveness - Liveness probe")

		if settings.api_debug:
			logger.info("  - GET /docs - API documentation")
			logger.info("  - GET /redoc - Alternative API documentation")

		# Initialize enhanced monitoring system (environment-aware)
		if env_manager.is_production() and settings.enable_monitoring:
			try:
				initialize_monitoring()
				
				# Initialize default alert rules
				from .core.alerting import initialize_default_alert_rules
				initialize_default_alert_rules()
				
				logger.info("Enhanced monitoring and observability initialized")
				logger.info(f"  - Prometheus metrics: {settings.enable_prometheus}")
				logger.info(f"  - OpenTelemetry tracing: {settings.enable_opentelemetry}")
				logger.info(f"  - LangSmith tracing: {settings.langsmith_tracing}")
				if settings.langsmith_tracing:
					logger.info(f"  - LangSmith project: {settings.langsmith_project}")
				logger.info(f"  - Structured logging: enabled")
				
				# Get alert rules count safely
				try:
					if hasattr(monitoring_system, 'alert_manager') and hasattr(monitoring_system.alert_manager, 'alert_rules'):
						alert_count = len(monitoring_system.alert_manager.alert_rules)
					else:
						alert_count = 0
					logger.info(f"  - Alert thresholds configured: {alert_count} rules")
				except Exception as e:
					logger.warning(f"Could not get alert rules count: {e}")
					logger.info("  - Alert thresholds configured: 0 rules")
			except Exception as e:
				logger.warning(f"Enhanced monitoring initialization failed: {e}")
		else:
			logger.info("Basic monitoring initialized (development/simplified mode)")

		# Initialize LangSmith integration
		if settings.langsmith_tracing:
			langsmith_success = initialize_langsmith()
			if langsmith_success:
				logger.info("LangSmith integration initialized successfully")
			else:
				logger.warning("LangSmith initialization failed - tracing will be disabled")

		# WebSocket monitoring removed during cleanup

		# Start enhanced monitoring background task
		from .core.monitoring import monitoring_background_task

		asyncio.create_task(monitoring_background_task())

		# Initialize secure file handler
		from .core.file_handler import temp_file_handler

		logger.info("Secure file handler initialized")

		logger.info("Comprehensive security measures enabled:")
		logger.info("  - Advanced threat detection and analysis")
		logger.info("  - File upload validation and malware scanning")
		logger.info("  - Input sanitization and injection protection")
		logger.info("  - Rate limiting and IP blocking with honeypots")
		logger.info("  - Comprehensive audit logging and monitoring")
		logger.info("  - Secure temporary file management with encryption")
		logger.info("  - Content Security Policy and security headers")
		logger.info("  - API key management and authentication")
		logger.info("  - Memory management and cleanup")
		logger.info("  - Real-time security monitoring dashboard")

	# Add shutdown event
	@app.on_event("shutdown")
	async def shutdown_event():
		logger.info("🛑 Career Copilot API shutting down...")

		# Shutdown service dependency manager
		from .core.service_dependency_manager import get_service_dependency_manager
		service_manager = get_service_dependency_manager()
		await service_manager.shutdown()

		# Gracefully shutdown load balancer and resource manager
		from .core.load_balancer import get_load_balancer
		from .core.resource_manager import get_resource_manager
		
		try:
			# Stop load balancer gracefully
			load_balancer = await get_load_balancer()
			await load_balancer.stop()
			logger.info("Load balancer stopped gracefully")
			
			# Stop resource manager
			resource_manager = await get_resource_manager()
			await resource_manager.stop()
			logger.info("Resource manager stopped")
			
		except Exception as e:
			logger.error(f"Error during graceful shutdown: {e}")

		# Shutdown Service Manager and Registry
		if hasattr(app.state, 'service_manager'):
			app.state.service_manager.stop()
		service_registry = get_service_registry()
		await service_registry.shutdown()

		# Stop comprehensive monitoring system
		try:
			from .core.comprehensive_monitoring import get_comprehensive_monitoring
			comprehensive_monitoring = get_comprehensive_monitoring()
			await comprehensive_monitoring.stop()
			logger.info("Comprehensive monitoring system stopped")
		except Exception as e:
			logger.warning(f"Error stopping comprehensive monitoring: {e}")

		# Stop health automation service
		from .services.health_automation_service import get_health_automation_service
		health_automation = get_health_automation_service()
		await health_automation.stop()
		logger.info("Health automation service stopped")
		
		# Stop service monitoring
		from .services.monitoring_service import get_monitoring_service
		monitoring_service = get_monitoring_service()
		monitoring_service.stop_monitoring()
		logger.info("Service monitoring stopped")

		# Stop ChromaDB health monitoring and close client
		try:
			from .services.chroma_health_monitor import stop_health_monitoring
			from .services.chroma_client import close_chroma_client
			
			await stop_health_monitoring()
			logger.info("ChromaDB health monitoring stopped")
			
			await close_chroma_client()
			logger.info("ChromaDB client closed")
		except Exception as e:
			logger.warning(f"Error stopping ChromaDB services: {e}")
		
		# Stop background task queue system
		try:
			from .services.task_queue_manager import shutdown_task_queue_manager
			
			await shutdown_task_queue_manager()
			logger.info("Background task queue system stopped")
		except Exception as e:
			logger.warning(f"Error stopping background task queue: {e}")

		# WebSocket monitoring removed during cleanup

		# Clean up temporary files
		from .core.file_handler import temp_file_handler

		cleaned_files = temp_file_handler.cleanup_all()
		logger.info(f"Cleaned up {cleaned_files} temporary files")

		# Log shutdown
		audit_logger.log_event(
			event_type=AuditEventType.SYSTEM_SHUTDOWN,
			action="Application shutdown",
			result="success",
			severity=AuditSeverity.MEDIUM,
			details={"cleaned_files": cleaned_files},
		)

	return app


# Create the application instance
app = create_app()
