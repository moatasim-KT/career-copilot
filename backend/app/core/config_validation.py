"""
Configuration Validation System for Career Copilot.

This module provides comprehensive configuration validation with:
- Environment-specific validation rules
- Startup validation checks
- Runtime configuration monitoring
- Detailed error reporting and suggestions
"""

import os
import re
import socket
import urllib.parse
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from .logging import get_logger

logger = get_logger(__name__)


class ValidationLevel(str, Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(str, Enum):
    """Validation categories."""
    REQUIRED = "required"
    FORMAT = "format"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CONNECTIVITY = "connectivity"
    COMPATIBILITY = "compatibility"


@dataclass
class ValidationResult:
    """Result of a configuration validation check."""
    level: ValidationLevel
    category: ValidationCategory
    field: str
    message: str
    suggestion: Optional[str] = None
    current_value: Any = None
    expected_format: Optional[str] = None
    documentation_link: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report."""
    environment: str
    timestamp: datetime
    results: List[ValidationResult] = field(default_factory=list)
    errors: int = 0
    warnings: int = 0
    infos: int = 0
    
    def add_result(self, result: ValidationResult):
        """Add a validation result to the report."""
        self.results.append(result)
        if result.level == ValidationLevel.ERROR:
            self.errors += 1
        elif result.level == ValidationLevel.WARNING:
            self.warnings += 1
        elif result.level == ValidationLevel.INFO:
            self.infos += 1
    
    def has_errors(self) -> bool:
        """Check if the report contains any errors."""
        return self.errors > 0
    
    def get_summary(self) -> str:
        """Get a summary of the validation report."""
        return f"Validation completed: {self.errors} errors, {self.warnings} warnings, {self.infos} info messages"


class ConfigurationValidator:
    """Main configuration validator."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.report = ValidationReport(environment=environment, timestamp=datetime.utcnow())
    
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationReport:
        """Validate complete configuration."""
        logger.info(f"Starting configuration validation for {self.environment} environment")
        
        # Core validation checks
        self._validate_required_fields(config)
        self._validate_api_configuration(config)
        self._validate_database_configuration(config)
        self._validate_ai_configuration(config)
        self._validate_security_configuration(config)
        self._validate_external_services(config)
        self._validate_monitoring_configuration(config)
        self._validate_file_paths(config)
        self._validate_network_configuration(config)
        
        # Environment-specific validation
        if self.environment == "production":
            self._validate_production_requirements(config)
        elif self.environment == "development":
            self._validate_development_requirements(config)
        elif self.environment == "staging":
            self._validate_staging_requirements(config)
        
        logger.info(self.report.get_summary())
        return self.report
    
    def _validate_required_fields(self, config: Dict[str, Any]):
        """Validate required configuration fields."""
        required_fields = {
            "ai.openai.api_key": "OpenAI API key is required for AI functionality",
            "api.host": "API host configuration is required",
            "api.port": "API port configuration is required",
            "database.url": "Database URL is required"
        }
        
        for field_path, error_message in required_fields.items():
            value = self._get_nested_value(config, field_path)
            if not value:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.REQUIRED,
                    field=field_path,
                    message=error_message,
                    suggestion=f"Set the {field_path} configuration value",
                    documentation_link="https://docs.career-copilot.com/configuration"
                ))
    
    def _validate_api_configuration(self, config: Dict[str, Any]):
        """Validate API configuration."""
        api_config = config.get("api", {})
        
        # Validate port
        port = api_config.get("port")
        if port:
            if not isinstance(port, int) or port < 1 or port > 65535:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.FORMAT,
                    field="api.port",
                    message="API port must be an integer between 1 and 65535",
                    current_value=port,
                    expected_format="integer (1-65535)",
                    suggestion="Use a valid port number like 8000 or 8002"
                ))
            elif port < 1024 and self.environment == "production":
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.SECURITY,
                    field="api.port",
                    message="Using privileged port in production may require root access",
                    current_value=port,
                    suggestion="Consider using a port above 1024 for production"
                ))
        
        # Validate host
        host = api_config.get("host")
        if host and self.environment == "production":
            if host in ["127.0.0.1", "localhost"]:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.CONNECTIVITY,
                    field="api.host",
                    message="API host is set to localhost in production",
                    current_value=host,
                    suggestion="Use '0.0.0.0' to accept connections from all interfaces"
                ))
        
        # Validate debug mode
        debug = api_config.get("debug")
        if debug and self.environment == "production":
            self.report.add_result(ValidationResult(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.SECURITY,
                field="api.debug",
                message="Debug mode should be disabled in production",
                current_value=debug,
                suggestion="Set api.debug to false in production environment"
            ))
    
    def _validate_database_configuration(self, config: Dict[str, Any]):
        """Validate database configuration."""
        db_config = config.get("database", {})
        db_url = db_config.get("url")
        
        if db_url:
            # Parse database URL
            try:
                parsed = urllib.parse.urlparse(db_url)
                
                # Validate SQLite configuration
                if parsed.scheme.startswith("sqlite"):
                    db_path = parsed.path.lstrip("/")
                    if db_path != ":memory:":
                        db_file = Path(db_path)
                        if not db_file.parent.exists():
                            self.report.add_result(ValidationResult(
                                level=ValidationLevel.WARNING,
                                category=ValidationCategory.CONNECTIVITY,
                                field="database.url",
                                message=f"Database directory does not exist: {db_file.parent}",
                                suggestion="Ensure the database directory exists or will be created"
                            ))
                
                # Validate PostgreSQL configuration
                elif parsed.scheme.startswith("postgresql"):
                    if not parsed.hostname:
                        self.report.add_result(ValidationResult(
                            level=ValidationLevel.ERROR,
                            category=ValidationCategory.FORMAT,
                            field="database.url",
                            message="PostgreSQL URL missing hostname",
                            suggestion="Include hostname in database URL"
                        ))
                    
                    if self.environment == "production" and not parsed.password:
                        self.report.add_result(ValidationResult(
                            level=ValidationLevel.WARNING,
                            category=ValidationCategory.SECURITY,
                            field="database.url",
                            message="Database password not specified in production",
                            suggestion="Use a secure password for production database"
                        ))
            
            except Exception as e:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.FORMAT,
                    field="database.url",
                    message=f"Invalid database URL format: {e}",
                    current_value=db_url,
                    suggestion="Use a valid database URL format"
                ))
        
        # Validate pool settings
        pool_size = db_config.get("pool_size")
        if pool_size and self.environment == "production":
            if pool_size < 5:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.PERFORMANCE,
                    field="database.pool_size",
                    message="Database pool size may be too small for production",
                    current_value=pool_size,
                    suggestion="Consider increasing pool size to at least 10 for production"
                ))
    
    def _validate_ai_configuration(self, config: Dict[str, Any]):
        """Validate AI/LLM configuration."""
        ai_config = config.get("ai", {})
        
        # Validate OpenAI configuration
        openai_config = ai_config.get("openai", {})
        api_key = openai_config.get("api_key")
        
        if api_key:
            if isinstance(api_key, str):
                if not api_key.startswith("sk-"):
                    self.report.add_result(ValidationResult(
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.FORMAT,
                        field="ai.openai.api_key",
                        message="OpenAI API key format appears invalid",
                        suggestion="Ensure you're using a valid OpenAI API key starting with 'sk-'"
                    ))
                
                if len(api_key) < 20:
                    self.report.add_result(ValidationResult(
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.FORMAT,
                        field="ai.openai.api_key",
                        message="OpenAI API key appears too short",
                        suggestion="Verify the complete API key is configured"
                    ))
        
        # Validate temperature settings
        for provider in ["openai", "groq", "gemini", "anthropic"]:
            provider_config = ai_config.get(provider, {})
            temperature = provider_config.get("temperature")
            
            if temperature is not None:
                if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
                    self.report.add_result(ValidationResult(
                        level=ValidationLevel.ERROR,
                        category=ValidationCategory.FORMAT,
                        field=f"ai.{provider}.temperature",
                        message=f"Temperature must be between 0 and 2 for {provider}",
                        current_value=temperature,
                        expected_format="float (0.0-2.0)",
                        suggestion="Use a temperature value between 0.0 and 2.0"
                    ))
        
        # Check if at least one AI provider is enabled
        enabled_providers = []
        for provider in ["openai", "groq", "gemini", "anthropic", "ollama"]:
            provider_config = ai_config.get(provider, {})
            if provider_config.get("enabled", provider == "openai"):  # OpenAI enabled by default
                if provider_config.get("api_key") or provider == "ollama":
                    enabled_providers.append(provider)
        
        if not enabled_providers:
            self.report.add_result(ValidationResult(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.REQUIRED,
                field="ai",
                message="No AI providers are properly configured",
                suggestion="Configure at least one AI provider with valid credentials"
            ))
    
    def _validate_security_configuration(self, config: Dict[str, Any]):
        """Validate security configuration."""
        security_config = config.get("security", {})
        
        # Validate CORS origins
        cors_origins = security_config.get("cors_origins", [])
        if self.environment == "production":
            if not cors_origins:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.SECURITY,
                    field="security.cors_origins",
                    message="CORS origins not configured for production",
                    suggestion="Configure specific allowed origins for production"
                ))
            else:
                for origin in cors_origins:
                    if origin == "*":
                        self.report.add_result(ValidationResult(
                            level=ValidationLevel.ERROR,
                            category=ValidationCategory.SECURITY,
                            field="security.cors_origins",
                            message="Wildcard CORS origin is not secure for production",
                            suggestion="Specify exact allowed origins instead of '*'"
                        ))
                    elif origin.startswith("http://") and self.environment == "production":
                        self.report.add_result(ValidationResult(
                            level=ValidationLevel.WARNING,
                            category=ValidationCategory.SECURITY,
                            field="security.cors_origins",
                            message="HTTP origins in production are not secure",
                            current_value=origin,
                            suggestion="Use HTTPS origins in production"
                        ))
        
        # Validate JWT configuration
        jwt_config = security_config.get("jwt", {})
        jwt_secret = jwt_config.get("secret_key")
        
        if jwt_secret and self.environment == "production":
            if len(jwt_secret) < 32:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.SECURITY,
                    field="security.jwt.secret_key",
                    message="JWT secret key is too short for production",
                    suggestion="Use a JWT secret key of at least 32 characters"
                ))
            
            if jwt_secret in ["secret", "password", "changeme", "default"]:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.SECURITY,
                    field="security.jwt.secret_key",
                    message="JWT secret key is using a default/weak value",
                    suggestion="Generate a strong, unique JWT secret key"
                ))
        
        # Validate file upload limits
        file_config = security_config.get("file_upload", {})
        max_size = file_config.get("max_size_mb")
        
        if max_size and max_size > 100:
            self.report.add_result(ValidationResult(
                level=ValidationLevel.WARNING,
                category=ValidationCategory.PERFORMANCE,
                field="security.file_upload.max_size_mb",
                message="Large file upload limit may impact performance",
                current_value=max_size,
                suggestion="Consider if files larger than 100MB are necessary"
            ))
    
    def _validate_external_services(self, config: Dict[str, Any]):
        """Validate external service configurations."""
        external_config = config.get("external_services", {})
        
        for service_name, service_config in external_config.items():
            if not isinstance(service_config, dict):
                continue
            
            enabled = service_config.get("enabled", False)
            if not enabled:
                continue
            
            # Validate service-specific requirements
            if service_name == "docusign":
                required_fields = ["client_id", "client_secret", "redirect_uri"]
                for field in required_fields:
                    if not service_config.get(field):
                        self.report.add_result(ValidationResult(
                            level=ValidationLevel.WARNING,
                            category=ValidationCategory.REQUIRED,
                            field=f"external_services.{service_name}.{field}",
                            message=f"DocuSign {field} is required when service is enabled",
                            suggestion=f"Configure DocuSign {field} or disable the service"
                        ))
            
            elif service_name == "slack":
                if not service_config.get("webhook_url") and not service_config.get("bot_token"):
                    self.report.add_result(ValidationResult(
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.REQUIRED,
                        field=f"external_services.{service_name}",
                        message="Slack requires either webhook_url or bot_token",
                        suggestion="Configure Slack webhook URL or bot token"
                    ))
            
            # Validate timeout settings
            timeout = service_config.get("timeout")
            if timeout and timeout > 300:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.PERFORMANCE,
                    field=f"external_services.{service_name}.timeout",
                    message=f"Long timeout for {service_name} may impact user experience",
                    current_value=timeout,
                    suggestion="Consider reducing timeout to improve responsiveness"
                ))
    
    def _validate_monitoring_configuration(self, config: Dict[str, Any]):
        """Validate monitoring configuration."""
        monitoring_config = config.get("monitoring", {})
        
        if self.environment == "production":
            if not monitoring_config.get("enabled"):
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.PERFORMANCE,
                    field="monitoring.enabled",
                    message="Monitoring is disabled in production",
                    suggestion="Enable monitoring for production environments"
                ))
            
            prometheus_config = monitoring_config.get("prometheus", {})
            if monitoring_config.get("enabled") and not prometheus_config.get("enabled"):
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.INFO,
                    category=ValidationCategory.PERFORMANCE,
                    field="monitoring.prometheus.enabled",
                    message="Prometheus metrics are disabled",
                    suggestion="Consider enabling Prometheus for better observability"
                ))
    
    def _validate_file_paths(self, config: Dict[str, Any]):
        """Validate file paths and directories."""
        paths_to_check = [
            ("logging.file_path", "log file"),
            ("vector_db.persist_directory", "vector database directory"),
            ("storage.local.path", "local storage directory")
        ]
        
        for path_key, description in paths_to_check:
            path_value = self._get_nested_value(config, path_key)
            if path_value:
                path_obj = Path(path_value)
                
                # Check if parent directory exists or can be created
                try:
                    path_obj.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.report.add_result(ValidationResult(
                        level=ValidationLevel.ERROR,
                        category=ValidationCategory.CONNECTIVITY,
                        field=path_key,
                        message=f"Cannot create directory for {description}: {e}",
                        current_value=path_value,
                        suggestion=f"Ensure the parent directory exists and is writable"
                    ))
    
    def _validate_network_configuration(self, config: Dict[str, Any]):
        """Validate network-related configuration."""
        # Validate Redis connection if enabled
        cache_config = config.get("cache", {})
        redis_config = cache_config.get("redis", {})
        
        if redis_config.get("enabled"):
            host = redis_config.get("host", "localhost")
            port = redis_config.get("port", 6379)
            
            # Test Redis connectivity (non-blocking)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result != 0:
                    self.report.add_result(ValidationResult(
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.CONNECTIVITY,
                        field="cache.redis",
                        message=f"Cannot connect to Redis at {host}:{port}",
                        suggestion="Ensure Redis is running and accessible"
                    ))
            except Exception:
                self.report.add_result(ValidationResult(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.CONNECTIVITY,
                    field="cache.redis",
                    message="Redis connectivity check failed",
                    suggestion="Verify Redis configuration and network connectivity"
                ))
    
    def _validate_production_requirements(self, config: Dict[str, Any]):
        """Validate production-specific requirements."""
        # Security requirements
        security_config = config.get("security", {})
        
        if not security_config.get("rate_limiting", {}).get("enabled"):
            self.report.add_result(ValidationResult(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.SECURITY,
                field="security.rate_limiting.enabled",
                message="Rate limiting should be enabled in production",
                suggestion="Enable rate limiting to protect against abuse"
            ))
        
        if not security_config.get("encryption", {}).get("enabled"):
            self.report.add_result(ValidationResult(
                level=ValidationLevel.WARNING,
                category=ValidationCategory.SECURITY,
                field="security.encryption.enabled",
                message="Encryption is not enabled in production",
                suggestion="Enable encryption for sensitive data protection"
            ))
        
        # Performance requirements
        api_config = config.get("api", {})
        workers = api_config.get("workers", 1)
        
        if workers < 4:
            self.report.add_result(ValidationResult(
                level=ValidationLevel.WARNING,
                category=ValidationCategory.PERFORMANCE,
                field="api.workers",
                message="Low worker count for production environment",
                current_value=workers,
                suggestion="Consider increasing worker count for better performance"
            ))
    
    def _validate_development_requirements(self, config: Dict[str, Any]):
        """Validate development-specific requirements."""
        # Development-friendly warnings
        security_config = config.get("security", {})
        
        if security_config.get("rate_limiting", {}).get("enabled"):
            self.report.add_result(ValidationResult(
                level=ValidationLevel.INFO,
                category=ValidationCategory.PERFORMANCE,
                field="security.rate_limiting.enabled",
                message="Rate limiting is enabled in development",
                suggestion="Consider disabling rate limiting for easier development"
            ))
    
    def _validate_staging_requirements(self, config: Dict[str, Any]):
        """Validate staging-specific requirements."""
        # Staging should be production-like but with some flexibility
        monitoring_config = config.get("monitoring", {})
        
        if not monitoring_config.get("enabled"):
            self.report.add_result(ValidationResult(
                level=ValidationLevel.WARNING,
                category=ValidationCategory.PERFORMANCE,
                field="monitoring.enabled",
                message="Monitoring should be enabled in staging for production testing",
                suggestion="Enable monitoring to test production-like behavior"
            ))
    
    def _get_nested_value(self, config: Dict[str, Any], key_path: str) -> Any:
        """Get nested configuration value using dot notation."""
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value


def validate_startup_configuration(config: Dict[str, Any], environment: str = "development") -> ValidationReport:
    """Validate configuration at startup."""
    validator = ConfigurationValidator(environment)
    report = validator.validate_configuration(config)
    
    # Log validation results
    if report.has_errors():
        logger.error("Configuration validation failed with errors:")
        for result in report.results:
            if result.level == ValidationLevel.ERROR:
                logger.error(f"  {result.field}: {result.message}")
                if result.suggestion:
                    logger.error(f"    Suggestion: {result.suggestion}")
    
    if report.warnings > 0:
        logger.warning(f"Configuration validation completed with {report.warnings} warnings")
        for result in report.results:
            if result.level == ValidationLevel.WARNING:
                logger.warning(f"  {result.field}: {result.message}")
    
    return report


def check_environment_readiness(environment: str = "development") -> bool:
    """Check if the environment is ready for the application to start."""
    try:
        # Import here to avoid circular imports
        from .config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config_data = config_manager.config_data
        
        if not config_data:
            logger.error("No configuration data available")
            return False
        
        report = validate_startup_configuration(config_data, environment)
        
        if report.has_errors():
            logger.error("Environment readiness check failed due to configuration errors")
            return False
        
        logger.info("Environment readiness check passed")
        return True
    
    except Exception as e:
        logger.error(f"Environment readiness check failed: {e}")
        return False