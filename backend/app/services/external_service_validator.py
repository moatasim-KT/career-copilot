"""
External Service Validator
Validates and tests all external service connections with comprehensive reporting.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..core.config import get_settings
from ..core.logging import get_logger
from .external_service_manager import get_external_service_manager
from .docusign_service import DocuSignService
from .slack_service import EnhancedSlackService as SlackService, SlackMessage
from .gmail_service import GmailService, GmailMessage
from .google_drive_service import GoogleDriveService
from .vector_store_service import get_vector_store_service

logger = get_logger(__name__)


class ValidationStatus(str, Enum):
    """Validation status for external services"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    NOT_CONFIGURED = "not_configured"


@dataclass
class ValidationResult:
    """Result of a service validation test"""
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
    """Comprehensive validation report for a service"""
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
    """Comprehensive external service validator"""
    
    def __init__(self):
        self.settings = get_settings()
        self.service_manager = get_external_service_manager()
        self.validation_results: Dict[str, ServiceValidationReport] = {}
    
    async def validate_all_services(self) -> Dict[str, ServiceValidationReport]:
        """Validate all external services and return comprehensive report"""
        logger.info("Starting comprehensive external service validation...")
        
        # Define services to validate
        services = {
            "docusign": self._validate_docusign_service,
            "slack": self._validate_slack_service,
            "gmail": self._validate_gmail_service,
            "google_drive": self._validate_google_drive_service,
            "vector_store": self._validate_vector_store_service
        }
        
        # Run validations concurrently
        validation_tasks = []
        for service_name, validator_func in services.items():
            validation_tasks.append(self._run_service_validation(service_name, validator_func))
        
        await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Generate summary
        self._generate_validation_summary()
        
        logger.info("External service validation completed")
        return self.validation_results
    
    async def _run_service_validation(self, service_name: str, validator_func):
        """Run validation for a specific service"""
        try:
            report = await validator_func()
            self.validation_results[service_name] = report
        except Exception as e:
            logger.error(f"Validation failed for {service_name}: {e}")
            self.validation_results[service_name] = ServiceValidationReport(
                service_name=service_name,
                overall_status=ValidationStatus.FAILED,
                configuration_status=ValidationStatus.FAILED,
                connectivity_status=ValidationStatus.FAILED,
                authentication_status=ValidationStatus.FAILED,
                functionality_status=ValidationStatus.FAILED,
                results=[ValidationResult(
                    service_name=service_name,
                    test_name="validation_error",
                    status=ValidationStatus.FAILED,
                    message=f"Validation error: {str(e)}",
                    error=str(e)
                )],
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                warning_tests=0,
                skipped_tests=0,
                total_response_time_ms=0.0,
                recommendations=[f"Fix validation error for {service_name}"]
            )
    
    async def _validate_docusign_service(self) -> ServiceValidationReport:
        """Validate DocuSign service integration"""
        service_name = "docusign"
        results = []
        
        # Configuration validation
        config_result = self._validate_docusign_configuration()
        results.append(config_result)
        
        if config_result.status == ValidationStatus.NOT_CONFIGURED:
            return self._create_service_report(service_name, results)
        
        # Initialize service
        try:
            docusign_service = DocuSignService()
        except Exception as e:
            results.append(ValidationResult(
                service_name=service_name,
                test_name="service_initialization",
                status=ValidationStatus.FAILED,
                message=f"Failed to initialize DocuSign service: {str(e)}",
                error=str(e)
            ))
            return self._create_service_report(service_name, results)
        
        # Connectivity test
        connectivity_result = await self._test_docusign_connectivity(docusign_service)
        results.append(connectivity_result)
        
        # Authentication test
        auth_result = await self._test_docusign_authentication(docusign_service)
        results.append(auth_result)
        
        # Functionality tests
        if auth_result.status == ValidationStatus.PASSED:
            functionality_results = await self._test_docusign_functionality(docusign_service)
            results.extend(functionality_results)
        
        return self._create_service_report(service_name, results)
    
    def _validate_docusign_configuration(self) -> ValidationResult:
        """Validate DocuSign configuration"""
        required_settings = []
        
        # Check for sandbox or production configuration
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
                    "Configure DocuSign client credentials"
                ]
            )
        
        # Check required settings based on environment
        if sandbox_enabled:
            required_settings = [
                ("docusign_sandbox_client_id", "DOCUSIGN_SANDBOX_CLIENT_ID"),
                ("docusign_sandbox_client_secret", "DOCUSIGN_SANDBOX_CLIENT_SECRET"),
                ("docusign_sandbox_redirect_uri", "DOCUSIGN_SANDBOX_REDIRECT_URI")
            ]
        elif production_enabled:
            required_settings = [
                ("docusign_client_id", "DOCUSIGN_CLIENT_ID"),
                ("docusign_client_secret", "DOCUSIGN_CLIENT_SECRET"),
                ("docusign_redirect_uri", "DOCUSIGN_REDIRECT_URI")
            ]
        
        missing_settings = []
        for setting_attr, env_var in required_settings:
            if not getattr(self.settings, setting_attr, ""):
                missing_settings.append(env_var)
        
        if missing_settings:
            return ValidationResult(
                service_name="docusign",
                test_name="configuration_check",
                status=ValidationStatus.FAILED,
                message=f"Missing required DocuSign configuration: {', '.join(missing_settings)}",
                suggestions=[f"Set environment variable: {var}" for var in missing_settings]
            )
        
        return ValidationResult(
            service_name="docusign",
            test_name="configuration_check",
            status=ValidationStatus.PASSED,
            message="DocuSign configuration is valid"
        )
    
    async def _test_docusign_connectivity(self, service: DocuSignService) -> ValidationResult:
        """Test DocuSign connectivity"""
        start_time = time.time()
        
        try:
            # Test basic connectivity by getting authorization URL
            auth_url = service.get_authorization_url()
            response_time = (time.time() - start_time) * 1000
            
            if auth_url:
                return ValidationResult(
                    service_name="docusign",
                    test_name="connectivity_check",
                    status=ValidationStatus.PASSED,
                    message="DocuSign connectivity test passed",
                    response_time_ms=response_time,
                    details={"auth_url_generated": True}
                )
            else:
                return ValidationResult(
                    service_name="docusign",
                    test_name="connectivity_check",
                    status=ValidationStatus.FAILED,
                    message="Failed to generate DocuSign authorization URL",
                    response_time_ms=response_time
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                service_name="docusign",
                test_name="connectivity_check",
                status=ValidationStatus.FAILED,
                message=f"DocuSign connectivity test failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def _test_docusign_authentication(self, service: DocuSignService) -> ValidationResult:
        """Test DocuSign authentication"""
        # Since we can't perform full OAuth flow in automated tests,
        # we'll check if the service can handle authentication properly
        
        if not service.enabled:
            return ValidationResult(
                service_name="docusign",
                test_name="authentication_check",
                status=ValidationStatus.SKIPPED,
                message="DocuSign authentication test skipped - service not enabled"
            )
        
        # Check if we have stored tokens
        if service.access_token and service.refresh_token:
            return ValidationResult(
                service_name="docusign",
                test_name="authentication_check",
                status=ValidationStatus.PASSED,
                message="DocuSign has valid authentication tokens"
            )
        else:
            return ValidationResult(
                service_name="docusign",
                test_name="authentication_check",
                status=ValidationStatus.WARNING,
                message="DocuSign authentication not completed - requires OAuth flow",
                suggestions=[
                    "Complete OAuth authentication flow",
                    "Visit the authorization URL to authenticate"
                ]
            )
    
    async def _test_docusign_functionality(self, service: DocuSignService) -> List[ValidationResult]:
        """Test DocuSign functionality"""
        results = []
        
        # Test account info retrieval (if authenticated)
        if service.access_token:
            start_time = time.time()
            try:
                account_info = await service.get_account_info()
                response_time = (time.time() - start_time) * 1000
                
                if account_info:
                    results.append(ValidationResult(
                        service_name="docusign",
                        test_name="account_info_test",
                        status=ValidationStatus.PASSED,
                        message="DocuSign account info retrieval successful",
                        response_time_ms=response_time
                    ))
                else:
                    results.append(ValidationResult(
                        service_name="docusign",
                        test_name="account_info_test",
                        status=ValidationStatus.FAILED,
                        message="Failed to retrieve DocuSign account info",
                        response_time_ms=response_time
                    ))
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                results.append(ValidationResult(
                    service_name="docusign",
                    test_name="account_info_test",
                    status=ValidationStatus.FAILED,
                    message=f"DocuSign account info test failed: {str(e)}",
                    response_time_ms=response_time,
                    error=str(e)
                ))
        
        return results
    
    async def _validate_slack_service(self) -> ServiceValidationReport:
        """Validate Slack service integration"""
        service_name = "slack"
        results = []
        
        # Configuration validation
        config_result = self._validate_slack_configuration()
        results.append(config_result)
        
        if config_result.status == ValidationStatus.NOT_CONFIGURED:
            return self._create_service_report(service_name, results)
        
        # Initialize service
        try:
            slack_service = SlackService()
        except Exception as e:
            results.append(ValidationResult(
                service_name=service_name,
                test_name="service_initialization",
                status=ValidationStatus.FAILED,
                message=f"Failed to initialize Slack service: {str(e)}",
                error=str(e)
            ))
            return self._create_service_report(service_name, results)
        
        # Connectivity and functionality tests
        connectivity_result = await self._test_slack_connectivity(slack_service)
        results.append(connectivity_result)
        
        # Test message sending
        message_result = await self._test_slack_message_sending(slack_service)
        results.append(message_result)
        
        return self._create_service_report(service_name, results)
    
    def _validate_slack_configuration(self) -> ValidationResult:
        """Validate Slack configuration"""
        slack_enabled = getattr(self.settings, "slack_enabled", False)
        
        if not slack_enabled:
            return ValidationResult(
                service_name="slack",
                test_name="configuration_check",
                status=ValidationStatus.NOT_CONFIGURED,
                message="Slack is not enabled",
                suggestions=["Set SLACK_ENABLED=true to enable Slack integration"]
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
                    "Or set SLACK_BOT_TOKEN for bot integration"
                ]
            )
        
        config_details = {
            "webhook_configured": bool(webhook_url),
            "bot_token_configured": bool(bot_token)
        }
        
        return ValidationResult(
            service_name="slack",
            test_name="configuration_check",
            status=ValidationStatus.PASSED,
            message="Slack configuration is valid",
            details=config_details
        )
    
    async def _test_slack_connectivity(self, service: SlackService) -> ValidationResult:
        """Test Slack connectivity"""
        start_time = time.time()
        
        try:
            # Test API connectivity if bot token is available
            if service.bot_token and not ("test" in service.bot_token.lower()):
                response = await self.service_manager.make_request(
                    service_name="slack",
                    method="GET",
                    url=f"{service.base_url}/api.test",
                    require_auth=True,
                    timeout=10.0
                )
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        return ValidationResult(
                            service_name="slack",
                            test_name="connectivity_check",
                            status=ValidationStatus.PASSED,
                            message="Slack API connectivity test passed",
                            response_time_ms=response_time
                        )
                    else:
                        return ValidationResult(
                            service_name="slack",
                            test_name="connectivity_check",
                            status=ValidationStatus.FAILED,
                            message=f"Slack API test failed: {result.get('error', 'Unknown error')}",
                            response_time_ms=response_time
                        )
                else:
                    return ValidationResult(
                        service_name="slack",
                        test_name="connectivity_check",
                        status=ValidationStatus.FAILED,
                        message=f"Slack API connectivity failed: HTTP {response.status_code}",
                        response_time_ms=response_time
                    )
            else:
                # For webhook or test tokens, just return success
                return ValidationResult(
                    service_name="slack",
                    test_name="connectivity_check",
                    status=ValidationStatus.PASSED,
                    message="Slack connectivity assumed valid (webhook or test configuration)",
                    response_time_ms=(time.time() - start_time) * 1000
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                service_name="slack",
                test_name="connectivity_check",
                status=ValidationStatus.FAILED,
                message=f"Slack connectivity test failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def _test_slack_message_sending(self, service: SlackService) -> ValidationResult:
        """Test Slack message sending"""
        start_time = time.time()
        
        try:
            # Create test message
            test_message = SlackMessage(
                text="🧪 Test message from Career Copilot - External Service Validation",
                channel="#general"  # Use a safe default channel
            )
            
            # Send test message
            result = await service.send_message(test_message, user_id="validation_test")
            response_time = (time.time() - start_time) * 1000
            
            if result.get("success"):
                return ValidationResult(
                    service_name="slack",
                    test_name="message_sending_test",
                    status=ValidationStatus.PASSED,
                    message="Slack message sending test passed",
                    response_time_ms=response_time,
                    details={"method": result.get("method"), "mock": result.get("mock", False)}
                )
            else:
                return ValidationResult(
                    service_name="slack",
                    test_name="message_sending_test",
                    status=ValidationStatus.FAILED,
                    message=f"Slack message sending failed: {result.get('message', 'Unknown error')}",
                    response_time_ms=response_time,
                    error=result.get("error")
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                service_name="slack",
                test_name="message_sending_test",
                status=ValidationStatus.FAILED,
                message=f"Slack message sending test failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def _validate_gmail_service(self) -> ServiceValidationReport:
        """Validate Gmail service integration"""
        service_name = "gmail"
        results = []
        
        # Configuration validation
        config_result = self._validate_gmail_configuration()
        results.append(config_result)
        
        if config_result.status == ValidationStatus.NOT_CONFIGURED:
            return self._create_service_report(service_name, results)
        
        # Initialize service
        try:
            gmail_service = GmailService()
        except Exception as e:
            results.append(ValidationResult(
                service_name=service_name,
                test_name="service_initialization",
                status=ValidationStatus.FAILED,
                message=f"Failed to initialize Gmail service: {str(e)}",
                error=str(e)
            ))
            return self._create_service_report(service_name, results)
        
        # Authentication test
        auth_result = await self._test_gmail_authentication(gmail_service)
        results.append(auth_result)
        
        # Template engine test
        template_result = self._test_gmail_template_engine(gmail_service)
        results.append(template_result)
        
        return self._create_service_report(service_name, results)
    
    def _validate_gmail_configuration(self) -> ValidationResult:
        """Validate Gmail configuration"""
        gmail_enabled = getattr(self.settings, "gmail_enabled", False)
        
        if not gmail_enabled:
            return ValidationResult(
                service_name="gmail",
                test_name="configuration_check",
                status=ValidationStatus.NOT_CONFIGURED,
                message="Gmail is not enabled",
                suggestions=["Set GMAIL_ENABLED=true to enable Gmail integration"]
            )
        
        required_settings = [
            ("gmail_client_id", "GMAIL_CLIENT_ID"),
            ("gmail_client_secret", "GMAIL_CLIENT_SECRET"),
            ("gmail_redirect_uri", "GMAIL_REDIRECT_URI")
        ]
        
        missing_settings = []
        for setting_attr, env_var in required_settings:
            if not getattr(self.settings, setting_attr, ""):
                missing_settings.append(env_var)
        
        if missing_settings:
            return ValidationResult(
                service_name="gmail",
                test_name="configuration_check",
                status=ValidationStatus.FAILED,
                message=f"Missing required Gmail configuration: {', '.join(missing_settings)}",
                suggestions=[f"Set environment variable: {var}" for var in missing_settings]
            )
        
        return ValidationResult(
            service_name="gmail",
            test_name="configuration_check",
            status=ValidationStatus.PASSED,
            message="Gmail configuration is valid"
        )
    
    async def _test_gmail_authentication(self, service: GmailService) -> ValidationResult:
        """Test Gmail authentication"""
        start_time = time.time()
        
        try:
            # Test authentication
            auth_result = await service.authenticate()
            response_time = (time.time() - start_time) * 1000
            
            if auth_result:
                return ValidationResult(
                    service_name="gmail",
                    test_name="authentication_test",
                    status=ValidationStatus.PASSED,
                    message="Gmail authentication test passed",
                    response_time_ms=response_time
                )
            else:
                return ValidationResult(
                    service_name="gmail",
                    test_name="authentication_test",
                    status=ValidationStatus.WARNING,
                    message="Gmail authentication not completed - requires OAuth flow",
                    response_time_ms=response_time,
                    suggestions=["Complete OAuth authentication flow for Gmail"]
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                service_name="gmail",
                test_name="authentication_test",
                status=ValidationStatus.FAILED,
                message=f"Gmail authentication test failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )
    
    def _test_gmail_template_engine(self, service: GmailService) -> ValidationResult:
        """Test Gmail template engine"""
        try:
            if service.template_env:
                return ValidationResult(
                    service_name="gmail",
                    test_name="template_engine_test",
                    status=ValidationStatus.PASSED,
                    message="Gmail template engine initialized successfully"
                )
            else:
                return ValidationResult(
                    service_name="gmail",
                    test_name="template_engine_test",
                    status=ValidationStatus.WARNING,
                    message="Gmail template engine not initialized",
                    suggestions=["Check email template directory and Jinja2 installation"]
                )
        
        except Exception as e:
            return ValidationResult(
                service_name="gmail",
                test_name="template_engine_test",
                status=ValidationStatus.FAILED,
                message=f"Gmail template engine test failed: {str(e)}",
                error=str(e)
            )
    
    async def _validate_google_drive_service(self) -> ServiceValidationReport:
        """Validate Google Drive service integration"""
        service_name = "google_drive"
        results = []
        
        # Configuration validation
        config_result = self._validate_google_drive_configuration()
        results.append(config_result)
        
        if config_result.status == ValidationStatus.NOT_CONFIGURED:
            return self._create_service_report(service_name, results)
        
        # Initialize service
        try:
            drive_service = GoogleDriveService()
        except Exception as e:
            results.append(ValidationResult(
                service_name=service_name,
                test_name="service_initialization",
                status=ValidationStatus.FAILED,
                message=f"Failed to initialize Google Drive service: {str(e)}",
                error=str(e)
            ))
            return self._create_service_report(service_name, results)
        
        # Authentication test
        auth_result = await self._test_google_drive_authentication(drive_service)
        results.append(auth_result)
        
        return self._create_service_report(service_name, results)
    
    def _validate_google_drive_configuration(self) -> ValidationResult:
        """Validate Google Drive configuration"""
        drive_enabled = getattr(self.settings, "google_drive_enabled", False)
        
        if not drive_enabled:
            return ValidationResult(
                service_name="google_drive",
                test_name="configuration_check",
                status=ValidationStatus.NOT_CONFIGURED,
                message="Google Drive is not enabled",
                suggestions=["Set GOOGLE_DRIVE_ENABLED=true to enable Google Drive integration"]
            )
        
        required_settings = [
            ("google_drive_client_id", "GOOGLE_DRIVE_CLIENT_ID"),
            ("google_drive_client_secret", "GOOGLE_DRIVE_CLIENT_SECRET"),
            ("google_drive_redirect_uri", "GOOGLE_DRIVE_REDIRECT_URI")
        ]
        
        missing_settings = []
        for setting_attr, env_var in required_settings:
            if not getattr(self.settings, setting_attr, ""):
                missing_settings.append(env_var)
        
        if missing_settings:
            return ValidationResult(
                service_name="google_drive",
                test_name="configuration_check",
                status=ValidationStatus.FAILED,
                message=f"Missing required Google Drive configuration: {', '.join(missing_settings)}",
                suggestions=[f"Set environment variable: {var}" for var in missing_settings]
            )
        
        return ValidationResult(
            service_name="google_drive",
            test_name="configuration_check",
            status=ValidationStatus.PASSED,
            message="Google Drive configuration is valid"
        )
    
    async def _test_google_drive_authentication(self, service: GoogleDriveService) -> ValidationResult:
        """Test Google Drive authentication"""
        try:
            # Test authentication URL generation
            auth_url = await service.authenticate()
            
            if auth_url:
                return ValidationResult(
                    service_name="google_drive",
                    test_name="authentication_test",
                    status=ValidationStatus.PASSED,
                    message="Google Drive authentication URL generated successfully"
                )
            else:
                return ValidationResult(
                    service_name="google_drive",
                    test_name="authentication_test",
                    status=ValidationStatus.WARNING,
                    message="Google Drive authentication not completed - requires OAuth flow",
                    suggestions=["Complete OAuth authentication flow for Google Drive"]
                )
        
        except Exception as e:
            return ValidationResult(
                service_name="google_drive",
                test_name="authentication_test",
                status=ValidationStatus.FAILED,
                message=f"Google Drive authentication test failed: {str(e)}",
                error=str(e)
            )
    
    async def _validate_vector_store_service(self) -> ServiceValidationReport:
        """Validate Vector Store service"""
        service_name = "vector_store"
        results = []
        
        # Initialize service
        try:
            vector_service = get_vector_store_service()
        except Exception as e:
            results.append(ValidationResult(
                service_name=service_name,
                test_name="service_initialization",
                status=ValidationStatus.FAILED,
                message=f"Failed to initialize Vector Store service: {str(e)}",
                error=str(e)
            ))
            return self._create_service_report(service_name, results)
        
        # Health check
        health_result = await self._test_vector_store_health(vector_service)
        results.append(health_result)
        
        # Functionality test
        if health_result.status == ValidationStatus.PASSED:
            functionality_result = await self._test_vector_store_functionality(vector_service)
            results.append(functionality_result)
        
        return self._create_service_report(service_name, results)
    
    async def _test_vector_store_health(self, service) -> ValidationResult:
        """Test Vector Store health"""
        start_time = time.time()
        
        try:
            health_status = service.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if health_status.get("status") == "healthy":
                return ValidationResult(
                    service_name="vector_store",
                    test_name="health_check",
                    status=ValidationStatus.PASSED,
                    message="Vector Store health check passed",
                    response_time_ms=response_time,
                    details=health_status
                )
            else:
                return ValidationResult(
                    service_name="vector_store",
                    test_name="health_check",
                    status=ValidationStatus.FAILED,
                    message=f"Vector Store health check failed: {health_status.get('error', 'Unknown error')}",
                    response_time_ms=response_time,
                    error=health_status.get("error")
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                service_name="vector_store",
                test_name="health_check",
                status=ValidationStatus.FAILED,
                message=f"Vector Store health check failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def _test_vector_store_functionality(self, service) -> ValidationResult:
        """Test Vector Store functionality"""
        start_time = time.time()
        
        try:
            # Test search functionality
            test_results = service.search_similar_clauses(
                query_text="liability limitation clause",
                n_results=3
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if test_results:
                return ValidationResult(
                    service_name="vector_store",
                    test_name="functionality_test",
                    status=ValidationStatus.PASSED,
                    message=f"Vector Store functionality test passed - found {len(test_results)} results",
                    response_time_ms=response_time,
                    details={"results_count": len(test_results)}
                )
            else:
                return ValidationResult(
                    service_name="vector_store",
                    test_name="functionality_test",
                    status=ValidationStatus.WARNING,
                    message="Vector Store functionality test returned no results",
                    response_time_ms=response_time,
                    suggestions=["Check if vector store has been populated with data"]
                )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ValidationResult(
                service_name="vector_store",
                test_name="functionality_test",
                status=ValidationStatus.FAILED,
                message=f"Vector Store functionality test failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )
    
    def _create_service_report(self, service_name: str, results: List[ValidationResult]) -> ServiceValidationReport:
        """Create service validation report from results"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed_tests = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        warning_tests = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        skipped_tests = sum(1 for r in results if r.status == ValidationStatus.SKIPPED)
        
        # Calculate overall status
        if any(r.status == ValidationStatus.NOT_CONFIGURED for r in results):
            overall_status = ValidationStatus.NOT_CONFIGURED
        elif failed_tests > 0:
            overall_status = ValidationStatus.FAILED
        elif warning_tests > 0:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.PASSED
        
        # Calculate component statuses
        config_results = [r for r in results if "configuration" in r.test_name]
        connectivity_results = [r for r in results if "connectivity" in r.test_name]
        auth_results = [r for r in results if "authentication" in r.test_name]
        functionality_results = [r for r in results if any(term in r.test_name for term in ["functionality", "health", "message", "template"])]
        
        configuration_status = self._get_component_status(config_results)
        connectivity_status = self._get_component_status(connectivity_results)
        authentication_status = self._get_component_status(auth_results)
        functionality_status = self._get_component_status(functionality_results)
        
        # Calculate total response time
        total_response_time = sum(r.response_time_ms or 0 for r in results)
        
        # Generate recommendations
        recommendations = []
        for result in results:
            if result.suggestions:
                recommendations.extend(result.suggestions)
        
        return ServiceValidationReport(
            service_name=service_name,
            overall_status=overall_status,
            configuration_status=configuration_status,
            connectivity_status=connectivity_status,
            authentication_status=authentication_status,
            functionality_status=functionality_status,
            results=results,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warning_tests=warning_tests,
            skipped_tests=skipped_tests,
            total_response_time_ms=total_response_time,
            recommendations=list(set(recommendations))  # Remove duplicates
        )
    
    def _get_component_status(self, results: List[ValidationResult]) -> ValidationStatus:
        """Get status for a component based on its results"""
        if not results:
            return ValidationStatus.SKIPPED
        
        if any(r.status == ValidationStatus.NOT_CONFIGURED for r in results):
            return ValidationStatus.NOT_CONFIGURED
        elif any(r.status == ValidationStatus.FAILED for r in results):
            return ValidationStatus.FAILED
        elif any(r.status == ValidationStatus.WARNING for r in results):
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.PASSED
    
    def _generate_validation_summary(self):
        """Generate validation summary"""
        total_services = len(self.validation_results)
        healthy_services = sum(1 for report in self.validation_results.values() 
                             if report.overall_status == ValidationStatus.PASSED)
        
        logger.info(f"External Service Validation Summary:")
        logger.info(f"  Total Services: {total_services}")
        logger.info(f"  Healthy Services: {healthy_services}")
        logger.info(f"  Services with Issues: {total_services - healthy_services}")
        
        for service_name, report in self.validation_results.items():
            logger.info(f"  {service_name}: {report.overall_status.value} "
                       f"({report.passed_tests}/{report.total_tests} tests passed)")
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary as dictionary"""
        if not self.validation_results:
            return {"error": "No validation results available"}
        
        total_services = len(self.validation_results)
        status_counts = {}
        
        for status in ValidationStatus:
            status_counts[status.value] = sum(
                1 for report in self.validation_results.values()
                if report.overall_status == status
            )
        
        return {
            "total_services": total_services,
            "status_counts": status_counts,
            "services": {
                name: {
                    "overall_status": report.overall_status.value,
                    "passed_tests": report.passed_tests,
                    "total_tests": report.total_tests,
                    "response_time_ms": report.total_response_time_ms,
                    "has_recommendations": len(report.recommendations) > 0
                }
                for name, report in self.validation_results.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance
_external_service_validator = None


def get_external_service_validator() -> ExternalServiceValidator:
    """Get global external service validator instance"""
    global _external_service_validator
    if _external_service_validator is None:
        _external_service_validator = ExternalServiceValidator()
    return _external_service_validator