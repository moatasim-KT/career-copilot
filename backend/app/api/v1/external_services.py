"""
External Services API endpoints
Provides endpoints for managing and validating external service integrations.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from ...core.logging import get_logger
from ...services.external_service_manager import get_external_service_manager
from ...services.external_service_validator import get_external_service_validator
from ...core.auth import get_current_user_optional

logger = get_logger(__name__)

router = APIRouter(prefix="/external-services", tags=["external-services"])


class ServiceHealthResponse(BaseModel):
	"""Response model for service health"""

	service_name: str
	status: str
	last_check: str
	response_time_ms: Optional[float] = None
	error_count: int = 0
	success_count: int = 0
	uptime_percentage: float = 100.0
	circuit_state: str = "closed"


class ValidationRequest(BaseModel):
	"""Request model for service validation"""

	services: Optional[list[str]] = None  # If None, validate all services
	include_functionality_tests: bool = True
	timeout_seconds: int = 30


@router.get("/health", summary="Get health status of all external services")
async def get_services_health(current_user: Optional[Dict] = Depends(get_current_user_optional)) -> Dict[str, Any]:
	"""
	Get health status of all external services including circuit breaker states,
	response times, and error rates.
	"""
	try:
		service_manager = get_external_service_manager()

		# Get health information for all services
		health_data = service_manager.get_all_service_health()

		# Get service statistics
		stats = service_manager.get_service_statistics()

		# Format response
		services_health = {}
		for service_name, health in health_data.items():
			services_health[service_name] = {
				"service_name": health.service_name,
				"status": health.status.value,
				"last_check": health.last_check.isoformat(),
				"response_time_ms": health.response_time_ms,
				"error_count": health.error_count,
				"success_count": health.success_count,
				"uptime_percentage": health.uptime_percentage,
				"circuit_state": health.circuit_state.value,
				"last_error": health.last_error,
			}

		return {
			"services": services_health,
			"summary": stats,
			"timestamp": health_data[list(health_data.keys())[0]].last_check.isoformat() if health_data else None,
		}

	except Exception as e:
		logger.error(f"Failed to get services health: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get services health: {e!s}")


@router.get("/health/{service_name}", summary="Get health status of a specific service")
async def get_service_health(service_name: str, current_user: Optional[Dict] = Depends(get_current_user_optional)) -> ServiceHealthResponse:
	"""
	Get detailed health status of a specific external service.
	"""
	try:
		service_manager = get_external_service_manager()

		health = service_manager.get_service_health(service_name)
		if not health:
			raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

		return ServiceHealthResponse(
			service_name=health.service_name,
			status=health.status.value,
			last_check=health.last_check.isoformat(),
			response_time_ms=health.response_time_ms,
			error_count=health.error_count,
			success_count=health.success_count,
			uptime_percentage=health.uptime_percentage,
			circuit_state=health.circuit_state.value,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get health for service {service_name}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get service health: {e!s}")


@router.post("/health-check", summary="Perform health check on all services")
async def perform_health_check(
	background_tasks: BackgroundTasks, current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
	"""
	Trigger a health check on all external services. This will update the health
	status and circuit breaker states.
	"""
	try:
		service_manager = get_external_service_manager()

		# Perform health check in background
		background_tasks.add_task(service_manager.health_check_all_services)

		return {"message": "Health check initiated for all services", "status": "in_progress"}

	except Exception as e:
		logger.error(f"Failed to initiate health check: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to initiate health check: {e!s}")


@router.post("/validate", summary="Validate external service integrations")
async def validate_services(
	request: ValidationRequest, background_tasks: BackgroundTasks, current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
	"""
	Perform comprehensive validation of external service integrations including
	configuration, connectivity, authentication, and functionality tests.
	"""
	try:
		validator = get_external_service_validator()

		# Start validation in background
		background_tasks.add_task(validator.validate_all_services)

		return {
			"message": "External service validation initiated",
			"status": "in_progress",
			"services": request.services or ["docusign", "slack", "gmail", "google_drive", "vector_store"],
		}

	except Exception as e:
		logger.error(f"Failed to initiate service validation: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to initiate validation: {e!s}")


@router.get("/validation-results", summary="Get external service validation results")
async def get_validation_results(current_user: Optional[Dict] = Depends(get_current_user_optional)) -> Dict[str, Any]:
	"""
	Get the results of the most recent external service validation.
	"""
	try:
		validator = get_external_service_validator()

		if not validator.validation_results:
			return {
				"message": "No validation results available",
				"status": "no_results",
				"suggestion": "Run validation first using POST /external-services/validate",
			}

		# Get validation summary
		summary = validator.get_validation_summary()

		# Get detailed results
		detailed_results = {}
		for service_name, report in validator.validation_results.items():
			detailed_results[service_name] = {
				"service_name": report.service_name,
				"overall_status": report.overall_status.value,
				"configuration_status": report.configuration_status.value,
				"connectivity_status": report.connectivity_status.value,
				"authentication_status": report.authentication_status.value,
				"functionality_status": report.functionality_status.value,
				"total_tests": report.total_tests,
				"passed_tests": report.passed_tests,
				"failed_tests": report.failed_tests,
				"warning_tests": report.warning_tests,
				"skipped_tests": report.skipped_tests,
				"total_response_time_ms": report.total_response_time_ms,
				"recommendations": report.recommendations,
				"test_results": [
					{
						"test_name": result.test_name,
						"status": result.status.value,
						"message": result.message,
						"response_time_ms": result.response_time_ms,
						"error": result.error,
						"suggestions": result.suggestions,
						"details": result.details,
					}
					for result in report.results
				],
			}

		return {"summary": summary, "detailed_results": detailed_results, "status": "completed"}

	except Exception as e:
		logger.error(f"Failed to get validation results: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get validation results: {e!s}")


@router.post("/circuit-breaker/{service_name}/reset", summary="Reset circuit breaker for a service")
async def reset_circuit_breaker(service_name: str, current_user: Optional[Dict] = Depends(get_current_user_optional)) -> Dict[str, Any]:
	"""
	Manually reset the circuit breaker for a specific service. This can be useful
	when a service has recovered but the circuit breaker is still open.
	"""
	try:
		service_manager = get_external_service_manager()

		# Reset circuit breaker
		service_manager.reset_circuit_breaker(service_name)

		return {"message": f"Circuit breaker reset for service '{service_name}'", "service_name": service_name, "status": "reset"}

	except Exception as e:
		logger.error(f"Failed to reset circuit breaker for {service_name}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to reset circuit breaker: {e!s}")


@router.get("/statistics", summary="Get external service statistics")
async def get_service_statistics(current_user: Optional[Dict] = Depends(get_current_user_optional)) -> Dict[str, Any]:
	"""
	Get comprehensive statistics for all external services including success rates,
	response times, and circuit breaker states.
	"""
	try:
		service_manager = get_external_service_manager()

		stats = service_manager.get_service_statistics()

		return {"statistics": stats, "timestamp": stats.get("timestamp", "unknown")}

	except Exception as e:
		logger.error(f"Failed to get service statistics: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get service statistics: {e!s}")


@router.get("/configuration", summary="Get external service configuration status")
async def get_configuration_status(current_user: Optional[Dict] = Depends(get_current_user_optional)) -> Dict[str, Any]:
	"""
	Get configuration status for all external services without performing
	connectivity or functionality tests.
	"""
	try:
		from ...core.config import get_settings

		settings = get_settings()

		services_config = {
			"docusign": {
				"enabled": getattr(settings, "docusign_enabled", False) or getattr(settings, "docusign_sandbox_enabled", False),
				"environment": "sandbox" if getattr(settings, "docusign_sandbox_enabled", False) else "production",
				"configured": bool(getattr(settings, "docusign_client_id", "") or getattr(settings, "docusign_sandbox_client_id", "")),
			},
			"slack": {
				"enabled": getattr(settings, "slack_enabled", False),
				"webhook_configured": bool(getattr(settings, "slack_webhook_url", "")),
				"bot_configured": bool(getattr(settings, "slack_bot_token", "")),
				"configured": bool(getattr(settings, "slack_webhook_url", "") or getattr(settings, "slack_bot_token", "")),
			},
			"gmail": {"enabled": getattr(settings, "gmail_enabled", False), "configured": bool(getattr(settings, "gmail_client_id", ""))},
			"google_drive": {
				"enabled": getattr(settings, "google_drive_enabled", False),
				"configured": bool(getattr(settings, "google_drive_client_id", "")),
			},
			"vector_store": {
				"enabled": True,  # Always enabled as internal service
				"configured": True,
			},
		}

		# Count configured services
		total_services = len(services_config)
		enabled_services = sum(1 for config in services_config.values() if config["enabled"])
		configured_services = sum(1 for config in services_config.values() if config["configured"])

		return {
			"services": services_config,
			"summary": {
				"total_services": total_services,
				"enabled_services": enabled_services,
				"configured_services": configured_services,
				"configuration_complete": configured_services == total_services,
			},
		}

	except Exception as e:
		logger.error(f"Failed to get configuration status: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get configuration status: {e!s}")


@router.get("/test/{service_name}", summary="Test a specific external service")
async def test_service(service_name: str, current_user: Optional[Dict] = Depends(get_current_user_optional)) -> Dict[str, Any]:
	"""
	Test a specific external service with basic connectivity and functionality checks.
	"""
	try:
		# Map service names to test functions
		test_functions = {
			"docusign": _test_docusign,
			"slack": _test_slack,
			"gmail": _test_gmail,
			"google_drive": _test_google_drive,
			"vector_store": _test_vector_store,
		}

		if service_name not in test_functions:
			raise HTTPException(status_code=400, detail=f"Unknown service '{service_name}'. Available services: {list(test_functions.keys())}")

		# Run the test
		result = await test_functions[service_name]()

		return {"service_name": service_name, "test_result": result, "timestamp": result.get("timestamp", "unknown")}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to test service {service_name}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to test service: {e!s}")


# Test functions for individual services
async def _test_docusign() -> Dict[str, Any]:
	"""Test DocuSign service"""
	try:
		from ...services.docusign_service import DocuSignService

		service = DocuSignService()

		if not service.enabled:
			return {"status": "not_configured", "message": "DocuSign is not enabled", "timestamp": "2024-01-01T00:00:00Z"}

		# Test authorization URL generation
		auth_url = service.get_authorization_url()

		return {
			"status": "success" if auth_url else "failed",
			"message": "DocuSign authorization URL generated" if auth_url else "Failed to generate authorization URL",
			"has_auth_url": bool(auth_url),
			"environment": service.environment,
			"timestamp": "2024-01-01T00:00:00Z",
		}

	except Exception as e:
		return {"status": "error", "message": f"DocuSign test failed: {e!s}", "timestamp": "2024-01-01T00:00:00Z"}


async def _test_slack() -> Dict[str, Any]:
	"""Test Slack service"""
	try:
		from ...services.slack_service import SlackService, SlackMessage

		service = SlackService()

		if not service.enabled:
			return {"status": "not_configured", "message": "Slack is not enabled", "timestamp": "2024-01-01T00:00:00Z"}

		# Test message sending
		test_message = SlackMessage(text="🧪 Test message from Career Copilot API")
		result = await service.send_message(test_message, user_id="api_test")

		return {
			"status": "success" if result.get("success") else "failed",
			"message": result.get("message", "Unknown result"),
			"method": result.get("method"),
			"mock": result.get("mock", False),
			"timestamp": "2024-01-01T00:00:00Z",
		}

	except Exception as e:
		return {"status": "error", "message": f"Slack test failed: {e!s}", "timestamp": "2024-01-01T00:00:00Z"}


async def _test_gmail() -> Dict[str, Any]:
	"""Test Gmail service"""
	try:
		from ...services.email_service import EmailService

		service = EmailService()

		if not service.enabled:
			return {"status": "not_configured", "message": "Gmail is not enabled", "timestamp": "2024-01-01T00:00:00Z"}

		# Test authentication
		auth_result = await service.authenticate()

		return {
			"status": "success" if auth_result else "warning",
			"message": "Gmail authentication successful" if auth_result else "Gmail authentication requires OAuth flow",
			"authenticated": bool(auth_result),
			"template_engine_available": service.template_env is not None,
			"timestamp": "2024-01-01T00:00:00Z",
		}

	except Exception as e:
		return {"status": "error", "message": f"Gmail test failed: {e!s}", "timestamp": "2024-01-01T00:00:00Z"}


async def _test_google_drive() -> Dict[str, Any]:
	"""Test Google Drive service"""
	try:
		from ...services.google_drive_service import GoogleDriveService

		service = GoogleDriveService()

		if not service.enabled:
			return {"status": "not_configured", "message": "Google Drive is not enabled", "timestamp": "2024-01-01T00:00:00Z"}

		# Test authentication URL generation
		auth_url = await service.authenticate()

		return {
			"status": "success" if auth_url else "warning",
			"message": "Google Drive authentication URL generated" if auth_url else "Google Drive authentication requires OAuth flow",
			"has_auth_url": bool(auth_url),
			"timestamp": "2024-01-01T00:00:00Z",
		}

	except Exception as e:
		return {"status": "error", "message": f"Google Drive test failed: {e!s}", "timestamp": "2024-01-01T00:00:00Z"}


async def _test_vector_store() -> Dict[str, Any]:
	"""Test Vector Store service"""
	try:
		from ...services.vector_store_service import get_vector_store_service

		service = get_vector_store_service()

		# Test health check
		health_status = service.health_check()

		# Test basic functionality
		stats = service.get_collection_stats()

		return {
			"status": "success" if health_status.get("status") == "healthy" else "failed",
			"message": "Vector Store is healthy" if health_status.get("status") == "healthy" else "Vector Store health check failed",
			"health_status": health_status,
			"collection_stats": stats,
			"timestamp": "2024-01-01T00:00:00Z",
		}

	except Exception as e:
		return {"status": "error", "message": f"Vector Store test failed: {e!s}", "timestamp": "2024-01-01T00:00:00Z"}
