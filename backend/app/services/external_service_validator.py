"""
External Service Validator
Validates and tests all external service connections with comprehensive reporting.
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from ..core.config import get_settings
from ..core.logging import get_logger

# Optional imports for external services
try:
	from .docusign_service import DocuSignService

	DOCUSIGN_AVAILABLE = True
except ImportError:
	DocuSignService = None
	DOCUSIGN_AVAILABLE = False

try:
	from .google_drive_service import GoogleDriveService

	GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
	GoogleDriveService = None
	GOOGLE_DRIVE_AVAILABLE = False

from .email_service import EmailService
from .external_service_manager import get_external_service_manager
from .slack_service import EnhancedSlackService as SlackService
from .slack_service import SlackMessage
from .vector_store_service import get_vector_store_service

logger = get_logger(__name__)


class ValidationStatus(str, Enum):
	PASSED = "passed"
	FAILED = "failed"
	WARNING = "warning"
	SKIPPED = "skipped"
	NOT_CONFIGURED = "not_configured"


@dataclass
class ValidationResult:
	service_name: str
	test_name: str
	status: ValidationStatus
	message: str
	details: Optional[Dict[str, Any]] = None
	response_time_ms: Optional[float] = None
	error: Optional[str] = None
	suggestions: Optional[List[str]] = None


@dataclass
class ServiceValidationReport:
	service_name: str
	overall_status: ValidationStatus
	configuration_status: ValidationStatus
	connectivity_status: ValidationStatus
	authentication_status: ValidationStatus
	functionality_status: ValidationStatus
	results: List[ValidationResult]
	total_tests: int
	passed_tests: int
	failed_tests: int
	warning_tests: int
	skipped_tests: int
	total_response_time_ms: float
	recommendations: List[str]


class ExternalServiceValidator:
	"""Comprehensive external service validator."""

	def __init__(self) -> None:
		self.settings = get_settings()
		self.service_manager = get_external_service_manager()
		self.validation_results: Dict[str, ServiceValidationReport] = {}

	async def validate_all_services(self) -> Dict[str, ServiceValidationReport]:
		"""Validate all external services and return comprehensive report."""
		logger.info("Starting comprehensive external service validation...")

		services = {
			"docusign": self._validate_docusign_service,
			"slack": self._validate_slack_service,
			"gmail": self._validate_gmail_service,
			"google_drive": self._validate_google_drive_service,
			"vector_store": self._validate_vector_store_service,
		}

		tasks = [self._run_service_validation(name, func) for name, func in services.items()]
		await asyncio.gather(*tasks, return_exceptions=True)

		self._generate_validation_summary()
		logger.info("External service validation completed")
		return self.validation_results

	async def _run_service_validation(self, service_name: str, validator_func):
		try:
			report = await validator_func()
			self.validation_results[service_name] = report
		except Exception as e:  # pragma: no cover - defensive
			logger.error(f"Validation failed for {service_name}: {e}")
			self.validation_results[service_name] = ServiceValidationReport(
				service_name=service_name,
				overall_status=ValidationStatus.FAILED,
				configuration_status=ValidationStatus.FAILED,
				connectivity_status=ValidationStatus.FAILED,
				authentication_status=ValidationStatus.FAILED,
				functionality_status=ValidationStatus.FAILED,
				results=[
					ValidationResult(
						service_name=service_name,
						test_name="validation_error",
						status=ValidationStatus.FAILED,
						message=f"Validation error: {e!r}",
						error=str(e),
					)
				],
				total_tests=1,
				passed_tests=0,
				failed_tests=1,
				warning_tests=0,
				skipped_tests=0,
				total_response_time_ms=0.0,
				recommendations=[f"Fix validation error for {service_name}"],
			)

	async def _validate_docusign_service(self) -> ServiceValidationReport:
		service_name = "docusign"
		results: List[ValidationResult] = []

		config_result = self._validate_docusign_configuration()
		results.append(config_result)
		if config_result.status == ValidationStatus.NOT_CONFIGURED:
			return self._create_service_report(service_name, results)

		if not DOCUSIGN_AVAILABLE:
			results.append(
				ValidationResult(
					service_name=service_name,
					test_name="service_availability",
					status=ValidationStatus.SKIPPED,
					message="DocuSign service not available",
				)
			)
			return self._create_service_report(service_name, results)

		try:
			docusign_service = DocuSignService()
		except Exception as e:
			results.append(
				ValidationResult(
					service_name=service_name,
					test_name="service_initialization",
					status=ValidationStatus.FAILED,
					message=f"Failed to initialize DocuSign service: {e!r}",
					error=str(e),
				)
			)
			return self._create_service_report(service_name, results)

		results.append(await self._test_docusign_connectivity(docusign_service))
		auth_result = await self._test_docusign_authentication(docusign_service)
		results.append(auth_result)
		if auth_result.status == ValidationStatus.PASSED:
			results.extend(await self._test_docusign_functionality(docusign_service))

		return self._create_service_report(service_name, results)

	def _validate_docusign_configuration(self) -> ValidationResult:
		sandbox_enabled = getattr(self.settings, "docusign_sandbox_enabled", False)
		production_enabled = getattr(self.settings, "docusign_enabled", False)

		if not sandbox_enabled and not production_enabled:
			return ValidationResult(
				service_name="docusign",
				test_name="configuration_check",
				status=ValidationStatus.NOT_CONFIGURED,
				message="DocuSign is not enabled (neither sandbox nor production)",
				suggestions=[
					"Set DOCUSIGN_ENABLED=true for production or DOCUSIGN_SANDBOX_ENABLED=true for sandbox",
					"Configure DocuSign client credentials",
				],
			)

		required_settings: List[tuple] = []
		if sandbox_enabled:
			required_settings = [
				("docusign_sandbox_client_id", "DOCUSIGN_SANDBOX_CLIENT_ID"),
				("docusign_sandbox_client_secret", "DOCUSIGN_SANDBOX_CLIENT_SECRET"),
				("docusign_sandbox_redirect_uri", "DOCUSIGN_SANDBOX_REDIRECT_URI"),
			]
		elif production_enabled:
			required_settings = [
				("docusign_client_id", "DOCUSIGN_CLIENT_ID"),
				("docusign_client_secret", "DOCUSIGN_CLIENT_SECRET"),
				("docusign_redirect_uri", "DOCUSIGN_REDIRECT_URI"),
			]

		missing = [env for attr, env in required_settings if not getattr(self.settings, attr, "")]
		if missing:
			return ValidationResult(
				service_name="docusign",
				test_name="configuration_check",
				status=ValidationStatus.FAILED,
				message=f"Missing required DocuSign configuration: {', '.join(missing)}",
				suggestions=[f"Set environment variable: {var}" for var in missing],
			)

		return ValidationResult(
			service_name="docusign",
			test_name="configuration_check",
			status=ValidationStatus.PASSED,
			message="DocuSign configuration is valid",
		)

	async def _test_docusign_connectivity(self, service: DocuSignService) -> ValidationResult:
		start = time.time()
		try:
			auth_url = service.get_authorization_url()
			rt = (time.time() - start) * 1000
			if auth_url:
				return ValidationResult(
					service_name="docusign",
					test_name="connectivity_check",
					status=ValidationStatus.PASSED,
					message="DocuSign connectivity test passed",
					response_time_ms=rt,
					details={"auth_url_generated": True},
				)
			return ValidationResult(
				service_name="docusign",
				test_name="connectivity_check",
				status=ValidationStatus.FAILED,
				message="Failed to generate DocuSign authorization URL",
				response_time_ms=rt,
			)
		except Exception as e:
			rt = (time.time() - start) * 1000
			return ValidationResult(
				service_name="docusign",
				test_name="connectivity_check",
				status=ValidationStatus.FAILED,
				message=f"DocuSign connectivity test failed: {e!r}",
				response_time_ms=rt,
				error=str(e),
			)

	async def _test_docusign_authentication(self, service: DocuSignService) -> ValidationResult:
		if not service.enabled:
			return ValidationResult(
				service_name="docusign",
				test_name="authentication_check",
				status=ValidationStatus.SKIPPED,
				message="DocuSign authentication test skipped - service not enabled",
			)
		if getattr(service, "access_token", None) and getattr(service, "refresh_token", None):
			return ValidationResult(
				service_name="docusign",
				test_name="authentication_check",
				status=ValidationStatus.PASSED,
				message="DocuSign has valid authentication tokens",
			)
		return ValidationResult(
			service_name="docusign",
			test_name="authentication_check",
			status=ValidationStatus.WARNING,
			message="DocuSign authentication not completed - requires OAuth flow",
			suggestions=["Complete OAuth authentication flow", "Visit the authorization URL to authenticate"],
		)

	async def _test_docusign_functionality(self, service: DocuSignService) -> List[ValidationResult]:
		results: List[ValidationResult] = []
		if getattr(service, "access_token", None):
			start = time.time()
			try:
				account_info = await service.get_account_info()
				rt = (time.time() - start) * 1000
				status = ValidationStatus.PASSED if account_info else ValidationStatus.FAILED
				msg = "DocuSign account info retrieval successful" if account_info else "Failed to retrieve DocuSign account info"
				results.append(
					ValidationResult(
						service_name="docusign",
						test_name="account_info_test",
						status=status,
						message=msg,
						response_time_ms=rt,
					)
				)
			except Exception as e:
				rt = (time.time() - start) * 1000
				results.append(
					ValidationResult(
						service_name="docusign",
						test_name="account_info_test",
						status=ValidationStatus.FAILED,
						message=f"DocuSign account info test failed: {e!r}",
						response_time_ms=rt,
						error=str(e),
					)
				)
		return results

	async def _validate_slack_service(self) -> ServiceValidationReport:
		service_name = "slack"
		results: List[ValidationResult] = []

		config_result = self._validate_slack_configuration()
		results.append(config_result)
		if config_result.status == ValidationStatus.NOT_CONFIGURED:
			return self._create_service_report(service_name, results)

		try:
			slack_service = SlackService()
		except Exception as e:
			results.append(
				ValidationResult(
					service_name=service_name,
					test_name="service_initialization",
					status=ValidationStatus.FAILED,
					message=f"Failed to initialize Slack service: {e!r}",
					error=str(e),
				)
			)
			return self._create_service_report(service_name, results)

		results.append(await self._test_slack_connectivity(slack_service))
		results.append(await self._test_slack_message_sending(slack_service))
		return self._create_service_report(service_name, results)

	def _validate_slack_configuration(self) -> ValidationResult:
		slack_enabled = getattr(self.settings, "slack_enabled", False)
		if not slack_enabled:
			return ValidationResult(
				service_name="slack",
				test_name="configuration_check",
				status=ValidationStatus.NOT_CONFIGURED,
				message="Slack is not enabled",
				suggestions=["Set SLACK_ENABLED=true to enable Slack integration"],
			)
		webhook_url = getattr(self.settings, "slack_webhook_url", "")
		bot_token = getattr(self.settings, "slack_bot_token", "")
		if not webhook_url and not bot_token:
			return ValidationResult(
				service_name="slack",
				test_name="configuration_check",
				status=ValidationStatus.FAILED,
				message="Neither Slack webhook URL nor bot token is configured",
				suggestions=[
					"Set SLACK_WEBHOOK_URL for webhook integration",
					"Or set SLACK_BOT_TOKEN for bot integration",
				],
			)
		return ValidationResult(
			service_name="slack",
			test_name="configuration_check",
			status=ValidationStatus.PASSED,
			message="Slack configuration is valid",
			details={"webhook_configured": bool(webhook_url), "bot_token_configured": bool(bot_token)},
		)

	async def _test_slack_connectivity(self, service: SlackService) -> ValidationResult:
		start = time.time()
		try:
			if service.bot_token and not ("test" in service.bot_token.lower()):
				response = await self.service_manager.make_request(
					service_name="slack", method="GET", url=f"{service.base_url}/api.test", require_auth=True, timeout=10.0
				)
				rt = (time.time() - start) * 1000
				if response.status_code == 200:
					result = response.json()
					if result.get("ok"):
						return ValidationResult(
							service_name="slack",
							test_name="connectivity_check",
							status=ValidationStatus.PASSED,
							message="Slack API connectivity test passed",
							response_time_ms=rt,
						)
					return ValidationResult(
						service_name="slack",
						test_name="connectivity_check",
						status=ValidationStatus.FAILED,
						message=f"Slack API test failed: {result.get('error', 'Unknown error')}",
						response_time_ms=rt,
					)
				return ValidationResult(
					service_name="slack",
					test_name="connectivity_check",
					status=ValidationStatus.FAILED,
					message=f"Slack API connectivity failed: HTTP {response.status_code}",
					response_time_ms=rt,
				)
			# webhook or test tokens
			return ValidationResult(
				service_name="slack",
				test_name="connectivity_check",
				status=ValidationStatus.PASSED,
				message="Slack connectivity assumed valid (webhook or test configuration)",
				response_time_ms=(time.time() - start) * 1000,
			)
		except Exception as e:
			rt = (time.time() - start) * 1000
			return ValidationResult(
				service_name="slack",
				test_name="connectivity_check",
				status=ValidationStatus.FAILED,
				message=f"Slack connectivity test failed: {e!r}",
				response_time_ms=rt,
				error=str(e),
			)

	async def _test_slack_message_sending(self, service: SlackService) -> ValidationResult:
		start = time.time()
		try:
			test_message = SlackMessage(text="🧪 Test message from Career Copilot - External Service Validation", channel="#general")
			result = await service.send_message(test_message, user_id="validation_test")
			rt = (time.time() - start) * 1000
			if result.get("success"):
				return ValidationResult(
					service_name="slack",
					test_name="message_sending_test",
					status=ValidationStatus.PASSED,
					message="Slack message sending test passed",
					response_time_ms=rt,
					details={"method": result.get("method"), "mock": result.get("mock", False)},
				)
			return ValidationResult(
				service_name="slack",
				test_name="message_sending_test",
				status=ValidationStatus.FAILED,
				message=f"Slack message sending failed: {result.get('message', 'Unknown error')}",
				response_time_ms=rt,
				error=result.get("error"),
			)
		except Exception as e:
			rt = (time.time() - start) * 1000
			return ValidationResult(
				service_name="slack",
				test_name="message_sending_test",
				status=ValidationStatus.FAILED,
				message=f"Slack message sending test failed: {e!r}",
				response_time_ms=rt,
				error=str(e),
			)

	async def _validate_gmail_service(self) -> ServiceValidationReport:
		service_name = "gmail"
		results: List[ValidationResult] = []

		config_result = self._validate_gmail_configuration()
		results.append(config_result)
		if config_result.status == ValidationStatus.NOT_CONFIGURED:
			return self._create_service_report(service_name, results)

		try:
			email_service = EmailService()
		except Exception as e:
			results.append(
				ValidationResult(
					service_name=service_name,
					test_name="service_initialization",
					status=ValidationStatus.FAILED,
					message=f"Failed to initialize Email service: {e!r}",
					error=str(e),
				)
			)
			return self._create_service_report(service_name, results)

		results.append(await self._test_gmail_authentication(email_service))
		results.append(self._test_gmail_template_engine(email_service))
		return self._create_service_report(service_name, results)

	def _validate_gmail_configuration(self) -> ValidationResult:
		gmail_enabled = getattr(self.settings, "gmail_enabled", False)
		if not gmail_enabled:
			return ValidationResult(
				service_name="gmail",
				test_name="configuration_check",
				status=ValidationStatus.NOT_CONFIGURED,
				message="Gmail is not enabled",
				suggestions=["Set GMAIL_ENABLED=true to enable Gmail integration"],
			)

		required_settings = [
			("gmail_client_id", "GMAIL_CLIENT_ID"),
			("gmail_client_secret", "GMAIL_CLIENT_SECRET"),
			("gmail_redirect_uri", "GMAIL_REDIRECT_URI"),
		]

		missing = [env for attr, env in required_settings if not getattr(self.settings, attr, "")]
		if missing:
			return ValidationResult(
				service_name="gmail",
				test_name="configuration_check",
				status=ValidationStatus.FAILED,
				message=f"Missing required Gmail configuration: {', '.join(missing)}",
				suggestions=[f"Set environment variable: {var}" for var in missing],
			)

		return ValidationResult(
			service_name="gmail",
			test_name="configuration_check",
			status=ValidationStatus.PASSED,
			message="Gmail configuration is valid",
		)

	async def _test_gmail_authentication(self, service: EmailService) -> ValidationResult:
		start = time.time()
		try:
			auth_result = await service.test_authentication()  # type: ignore[attr-defined]
			rt = (time.time() - start) * 1000
			if auth_result:
				return ValidationResult(
					service_name="gmail",
					test_name="authentication_test",
					status=ValidationStatus.PASSED,
					message="Gmail authentication test passed",
					response_time_ms=rt,
				)
			return ValidationResult(
				service_name="gmail",
				test_name="authentication_test",
				status=ValidationStatus.WARNING,
				message="Gmail authentication not completed - requires OAuth flow",
				response_time_ms=rt,
				suggestions=["Complete OAuth authentication flow for Gmail"],
			)
		except Exception as e:
			rt = (time.time() - start) * 1000
			return ValidationResult(
				service_name="gmail",
				test_name="authentication_test",
				status=ValidationStatus.FAILED,
				message=f"Gmail authentication test failed: {e!r}",
				response_time_ms=rt,
				error=str(e),
			)

	def _test_gmail_template_engine(self, service: EmailService) -> ValidationResult:
		try:
			if getattr(service, "jinja_env", None):
				return ValidationResult(
					service_name="gmail",
					test_name="template_engine_test",
					status=ValidationStatus.PASSED,
					message="Gmail template engine initialized successfully",
				)
			return ValidationResult(
				service_name="gmail",
				test_name="template_engine_test",
				status=ValidationStatus.WARNING,
				message="Gmail template engine not initialized",
				suggestions=["Check email template directory and Jinja2 installation"],
			)
		except Exception as e:
			return ValidationResult(
				service_name="gmail",
				test_name="template_engine_test",
				status=ValidationStatus.FAILED,
				message=f"Gmail template engine test failed: {e!r}",
				error=str(e),
			)

	async def _validate_google_drive_service(self) -> ServiceValidationReport:
		service_name = "google_drive"
		results: List[ValidationResult] = []

		config_result = self._validate_google_drive_configuration()
		results.append(config_result)
		if config_result.status == ValidationStatus.NOT_CONFIGURED:
			return self._create_service_report(service_name, results)

		if not GOOGLE_DRIVE_AVAILABLE:
			results.append(
				ValidationResult(
					service_name=service_name,
					test_name="service_availability",
					status=ValidationStatus.SKIPPED,
					message="Google Drive service not available",
				)
			)
			return self._create_service_report(service_name, results)

		try:
			drive_service = GoogleDriveService()
		except Exception as e:
			results.append(
				ValidationResult(
					service_name=service_name,
					test_name="service_initialization",
					status=ValidationStatus.FAILED,
					message=f"Failed to initialize Google Drive service: {e!r}",
					error=str(e),
				)
			)
			return self._create_service_report(service_name, results)

		results.append(await self._test_google_drive_authentication(drive_service))
		return self._create_service_report(service_name, results)

	def _validate_google_drive_configuration(self) -> ValidationResult:
		drive_enabled = getattr(self.settings, "google_drive_enabled", False)
		if not drive_enabled:
			return ValidationResult(
				service_name="google_drive",
				test_name="configuration_check",
				status=ValidationStatus.NOT_CONFIGURED,
				message="Google Drive is not enabled",
				suggestions=["Set GOOGLE_DRIVE_ENABLED=true to enable Google Drive integration"],
			)

		required_settings = [
			("google_drive_client_id", "GOOGLE_DRIVE_CLIENT_ID"),
			("google_drive_client_secret", "GOOGLE_DRIVE_CLIENT_SECRET"),
			("google_drive_redirect_uri", "GOOGLE_DRIVE_REDIRECT_URI"),
		]
		missing = [env for attr, env in required_settings if not getattr(self.settings, attr, "")]
		if missing:
			return ValidationResult(
				service_name="google_drive",
				test_name="configuration_check",
				status=ValidationStatus.FAILED,
				message=f"Missing required Google Drive configuration: {', '.join(missing)}",
				suggestions=[f"Set environment variable: {var}" for var in missing],
			)
		return ValidationResult(
			service_name="google_drive",
			test_name="configuration_check",
			status=ValidationStatus.PASSED,
			message="Google Drive configuration is valid",
		)

	async def _test_google_drive_authentication(self, service: GoogleDriveService) -> ValidationResult:
		try:
			auth_url = await service.authenticate()
			if auth_url:
				return ValidationResult(
					service_name="google_drive",
					test_name="authentication_test",
					status=ValidationStatus.PASSED,
					message="Google Drive authentication URL generated successfully",
				)
			return ValidationResult(
				service_name="google_drive",
				test_name="authentication_test",
				status=ValidationStatus.WARNING,
				message="Google Drive authentication not completed - requires OAuth flow",
				suggestions=["Complete OAuth authentication flow for Google Drive"],
			)
		except Exception as e:
			return ValidationResult(
				service_name="google_drive",
				test_name="authentication_test",
				status=ValidationStatus.FAILED,
				message=f"Google Drive authentication test failed: {e!r}",
				error=str(e),
			)

	async def _validate_vector_store_service(self) -> ServiceValidationReport:
		service_name = "vector_store"
		results: List[ValidationResult] = []
		try:
			vector_service = get_vector_store_service()
		except Exception as e:
			results.append(
				ValidationResult(
					service_name=service_name,
					test_name="service_initialization",
					status=ValidationStatus.FAILED,
					message=f"Failed to initialize Vector Store service: {e!r}",
					error=str(e),
				)
			)
			return self._create_service_report(service_name, results)

		results.append(await self._test_vector_store_health(vector_service))
		if results[-1].status == ValidationStatus.PASSED:
			results.append(await self._test_vector_store_functionality(vector_service))
		return self._create_service_report(service_name, results)

	async def _test_vector_store_health(self, service) -> ValidationResult:
		start = time.time()
		try:
			health_status = service.health_check()
			rt = (time.time() - start) * 1000
			if health_status.get("status") == "healthy":
				return ValidationResult(
					service_name="vector_store",
					test_name="health_check",
					status=ValidationStatus.PASSED,
					message="Vector Store health check passed",
					response_time_ms=rt,
					details=health_status,
				)
			return ValidationResult(
				service_name="vector_store",
				test_name="health_check",
				status=ValidationStatus.FAILED,
				message=f"Vector Store health check failed: {health_status.get('error', 'Unknown error')}",
				response_time_ms=rt,
				error=health_status.get("error"),
			)
		except Exception as e:
			rt = (time.time() - start) * 1000
			return ValidationResult(
				service_name="vector_store",
				test_name="health_check",
				status=ValidationStatus.FAILED,
				message=f"Vector Store health check failed: {e!r}",
				response_time_ms=rt,
				error=str(e),
			)

	async def _test_vector_store_functionality(self, service) -> ValidationResult:
		start = time.time()
		try:
			test_results = service.search_similar_clauses(query_text="liability limitation clause", n_results=3)
			rt = (time.time() - start) * 1000
			if test_results:
				return ValidationResult(
					service_name="vector_store",
					test_name="functionality_test",
					status=ValidationStatus.PASSED,
					message=f"Vector Store functionality test passed - found {len(test_results)} results",
					response_time_ms=rt,
					details={"results_count": len(test_results)},
				)
			return ValidationResult(
				service_name="vector_store",
				test_name="functionality_test",
				status=ValidationStatus.WARNING,
				message="Vector Store functionality test returned no results",
				response_time_ms=rt,
				suggestions=["Check if vector store has been populated with data"],
			)
		except Exception as e:
			rt = (time.time() - start) * 1000
			return ValidationResult(
				service_name="vector_store",
				test_name="functionality_test",
				status=ValidationStatus.FAILED,
				message=f"Vector Store functionality test failed: {e!r}",
				response_time_ms=rt,
				error=str(e),
			)

	def _create_service_report(self, service_name: str, results: List[ValidationResult]) -> ServiceValidationReport:
		total = len(results)
		passed = sum(1 for r in results if r.status == ValidationStatus.PASSED)
		failed = sum(1 for r in results if r.status == ValidationStatus.FAILED)
		warning = sum(1 for r in results if r.status == ValidationStatus.WARNING)
		skipped = sum(1 for r in results if r.status == ValidationStatus.SKIPPED)

		if any(r.status == ValidationStatus.NOT_CONFIGURED for r in results):
			overall = ValidationStatus.NOT_CONFIGURED
		elif failed > 0:
			overall = ValidationStatus.FAILED
		elif warning > 0:
			overall = ValidationStatus.WARNING
		else:
			overall = ValidationStatus.PASSED

		config_status = self._get_component_status([r for r in results if "configuration" in r.test_name])
		conn_status = self._get_component_status([r for r in results if "connectivity" in r.test_name])
		auth_status = self._get_component_status([r for r in results if "authentication" in r.test_name])
		func_status = self._get_component_status(
			[r for r in results if any(t in r.test_name for t in ["functionality", "health", "message", "template"])]
		)

		total_rt = sum(r.response_time_ms or 0.0 for r in results)
		recommendations: List[str] = []
		for r in results:
			if r.suggestions:
				recommendations.extend(r.suggestions)

		return ServiceValidationReport(
			service_name=service_name,
			overall_status=overall,
			configuration_status=config_status,
			connectivity_status=conn_status,
			authentication_status=auth_status,
			functionality_status=func_status,
			results=results,
			total_tests=total,
			passed_tests=passed,
			failed_tests=failed,
			warning_tests=warning,
			skipped_tests=skipped,
			total_response_time_ms=total_rt,
			recommendations=list(set(recommendations)),
		)

	def _get_component_status(self, results: List[ValidationResult]) -> ValidationStatus:
		if not results:
			return ValidationStatus.SKIPPED
		if any(r.status == ValidationStatus.NOT_CONFIGURED for r in results):
			return ValidationStatus.NOT_CONFIGURED
		if any(r.status == ValidationStatus.FAILED for r in results):
			return ValidationStatus.FAILED
		if any(r.status == ValidationStatus.WARNING for r in results):
			return ValidationStatus.WARNING
		return ValidationStatus.PASSED

	def _generate_validation_summary(self) -> None:
		total = len(self.validation_results)
		healthy = sum(1 for r in self.validation_results.values() if r.overall_status == ValidationStatus.PASSED)
		logger.info("External Service Validation Summary:")
		logger.info(f"  Total Services: {total}")
		logger.info(f"  Healthy Services: {healthy}")
		logger.info(f"  Services with Issues: {total - healthy}")
		for name, report in self.validation_results.items():
			logger.info(f"  {name}: {report.overall_status.value} ({report.passed_tests}/{report.total_tests} tests passed)")

	def get_validation_summary(self) -> Dict[str, Any]:
		if not self.validation_results:
			return {"error": "No validation results available"}
		total = len(self.validation_results)
		status_counts: Dict[str, int] = {}
		for status in ValidationStatus:
			status_counts[status.value] = sum(1 for r in self.validation_results.values() if r.overall_status == status)
		return {
			"total_services": total,
			"status_counts": status_counts,
			"services": {
				name: {
					"overall_status": r.overall_status.value,
					"passed_tests": r.passed_tests,
					"total_tests": r.total_tests,
					"response_time_ms": r.total_response_time_ms,
					"has_recommendations": bool(r.recommendations),
				}
				for name, r in self.validation_results.items()
			},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}


_external_service_validator: Optional[ExternalServiceValidator] = None


def get_external_service_validator() -> ExternalServiceValidator:
	global _external_service_validator
	if _external_service_validator is None:
		_external_service_validator = ExternalServiceValidator()
	return _external_service_validator
	return _external_service_validator
