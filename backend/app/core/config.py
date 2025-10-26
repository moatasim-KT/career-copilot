"""
Unified Configuration Management System

This module consolidates configuration loading, validation, and management functionality
from config.py, config_loader.py, config_manager.py, and config_validator.py into a
single, coherent interface while maintaining backward compatibility.
"""

import json
import os
import threading
import time
import yaml
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Tuple
from urllib.parse import urlparse

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    class FileSystemEventHandler:
        pass
    class Observer:
        pass

from pydantic import BaseModel, Field, ValidationError, SecretStr, ConfigDict
try:
    from pydantic import validator
except ImportError:
    from pydantic import field_validator as validator

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T', bound=BaseModel)


class ConfigurationError(Exception):
    """Configuration related error."""
    pass


class DeploymentMode(str, Enum):
    """Supported deployment modes."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    NATIVE = "native"


class ConfigFormat(str, Enum):
    """Supported configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    TOML = "toml"


class ConfigSource(Enum):
    """Configuration source types."""
    ENV_FILE = "env_file"
    YAML_FILE = "yaml_file"
    JSON_FILE = "json_file"
    ENVIRONMENT = "environment"


@dataclass
class ConfigValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    invalid_values: List[str] = field(default_factory=list)


@dataclass
class ValidationIssue:
    """Represents a configuration validation issue."""
    level: str  # "error", "warning", "info"
    category: str  # "missing", "invalid", "security", "performance"
    key: str
    message: str
    suggestion: Optional[str] = None
    documentation_url: Optional[str] = None


@dataclass
class ValidationReport:
    """Configuration validation report."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    services_status: Dict[str, str] = field(default_factory=dict)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == "error"]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]
    
    @property
    def info(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == "info"]


@dataclass
class ServiceConfig:
    """Configuration for external services."""
    name: str
    enabled: bool
    required: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigSourceDefinition:
    """Configuration source definition."""
    path: Path
    format: ConfigFormat
    required: bool = True
    watch: bool = False
    priority: int = 0  # Higher priority overrides lower priority


class Settings(BaseSettings):
    """Pydantic settings model for type-safe configuration."""
    
    # Application Settings
    environment: Optional[str] = "development"
    api_host: Optional[str] = "0.0.0.0"
    api_port: Optional[int] = 8002
    debug: Optional[bool] = True

    # Database Configuration
    database_url: Optional[str] = "sqlite:///./data/career_copilot.db"

    # Authentication & Security
    jwt_secret_key: SecretStr = "your-super-secret-key-min-32-chars"
    jwt_algorithm: Optional[str] = "HS256"
    jwt_expiration_hours: Optional[int] = 24
    disable_auth: Optional[bool] = False

    # AI/LLM Service API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # Email & Notifications
    smtp_enabled: Optional[bool] = False
    smtp_host: Optional[str] = "smtp.gmail.com"
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = "your-email@example.com"
    smtp_password: Optional[str] = "your-email-password"
    smtp_use_tls: Optional[bool] = True
    smtp_from_email: Optional[str] = "noreply@career-copilot.com"
    sendgrid_api_key: Optional[str] = None

    # Task Scheduling & Automation
    enable_scheduler: Optional[bool] = True
    enable_job_scraping: Optional[bool] = False
    job_api_key: Optional[str] = None
    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None
    adzuna_country: Optional[str] = "us"

    # LinkedIn API Configuration
    linkedin_api_client_id: Optional[str] = None
    linkedin_api_client_secret: Optional[str] = None
    linkedin_api_access_token: Optional[str] = None

    # Indeed API Configuration
    indeed_publisher_id: Optional[str] = None
    indeed_api_key: Optional[str] = None

    # Glassdoor API Configuration
    glassdoor_partner_id: Optional[str] = None
    glassdoor_api_key: Optional[str] = None

    # Celery Configuration
    celery_broker_url: Optional[str] = "redis://localhost:6379/0"
    celery_result_backend: Optional[str] = "redis://localhost:6379/0"

    # Logging Settings
    log_level: Optional[str] = "INFO"

    # Caching Settings
    enable_redis_caching: Optional[bool] = True
    redis_url: Optional[str] = "redis://localhost:6379/1"

    # CORS Settings
    cors_origins: Optional[str] = "http://localhost:3000,http://localhost:8000"

    # OAuth Social Authentication
    oauth_enabled: Optional[bool] = False
    firebase_project_id: Optional[str] = None
    firebase_service_account_key: Optional[str] = None

    # Google OAuth Configuration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = "http://localhost:8002/api/v1/auth/oauth/google/callback"

    # LinkedIn OAuth Configuration
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_redirect_uri: Optional[str] = "http://localhost:8002/api/v1/auth/oauth/linkedin/callback"

    # GitHub OAuth Configuration
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    github_redirect_uri: Optional[str] = "http://localhost:8002/api/v1/auth/oauth/github/callback"

    # Job Matching Configuration
    high_match_threshold: Optional[float] = 80.0
    medium_match_threshold: Optional[float] = 60.0
    instant_alert_threshold: Optional[float] = 85.0

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )


class ConfigurationValidator(ABC):
    """Abstract base class for configuration validators."""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        pass


class RequiredFieldValidator(ConfigurationValidator):
    """Validator for required configuration fields."""
    
    def __init__(self, required_fields: List[str]):
        self.required_fields = required_fields
    
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate that all required fields are present."""
        errors = []
        for field in self.required_fields:
            if not self._get_nested_value(config, field):
                errors.append(f"Required field '{field}' is missing or empty")
        return errors
    
    def _get_nested_value(self, config: Dict[str, Any], field: str) -> Any:
        """Get nested configuration value using dot notation."""
        keys = field.split('.')
        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value


class ConfigFileWatcher(FileSystemEventHandler):
    """File system watcher for configuration files."""
    
    def __init__(self, config_manager: 'ConfigurationManager'):
        self.config_manager = config_manager
        self.last_reload = 0
        self.reload_debounce = 1.0  # 1 second debounce
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        current_time = time.time()
        if current_time - self.last_reload < self.reload_debounce:
            return
        
        file_path = Path(event.src_path)
        if self.config_manager.is_watched_file(file_path):
            logger.info(f"Configuration file changed: {file_path}")
            try:
                self.config_manager.reload_configuration()
                self.last_reload = current_time
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")


class ConfigurationManager:
    """
    Unified configuration manager that consolidates functionality from:
    - config.py: Basic settings access
    - config_loader.py: Multi-source configuration loading
    - config_manager.py: Enhanced management with hot reload
    - config_validator.py: Comprehensive validation
    """
    
    def __init__(self, deployment_mode: Optional[DeploymentMode] = None):
        """Initialize the configuration manager."""
        # Detect deployment mode
        if deployment_mode is None:
            env_mode = os.getenv('DEPLOYMENT_MODE', os.getenv('ENVIRONMENT', 'development')).lower()
            try:
                deployment_mode = DeploymentMode(env_mode)
            except ValueError:
                deployment_mode = DeploymentMode.DEVELOPMENT
                logger.warning(f"Unknown deployment mode '{env_mode}', using development")
        
        self.deployment_mode = deployment_mode
        self.project_root = self._find_project_root()
        self.config_data: Dict[str, Any] = {}
        self.config_sources: List[ConfigSourceDefinition] = []
        self.validators: List[ConfigurationValidator] = []
        self.loaded_sources: List[str] = []
        self.validation_result: Optional[ConfigValidationResult] = None
        self.config_lock = threading.RLock()
        self.observer: Optional[Observer] = None
        self.reload_callbacks: List[callable] = []
        
        # Pydantic settings instance
        self._settings: Optional[Settings] = None
        
        # Define service configurations
        self.services = {
            "openai": ServiceConfig(
                name="OpenAI",
                enabled=True,
                required=True,
                config={"api_key": "OPENAI_API_KEY", "model": "OPENAI_MODEL"},
                validation_rules={"api_key": {"startswith": "sk-"}}
            ),
            "groq": ServiceConfig(
                name="Groq",
                enabled=False,
                required=False,
                config={"api_key": "GROQ_API_KEY", "model": "GROQ_MODEL"},
                validation_rules={"api_key": {"startswith": "gsk_"}}
            ),
            "anthropic": ServiceConfig(
                name="Anthropic",
                enabled=False,
                required=False,
                config={"api_key": "ANTHROPIC_API_KEY"},
                validation_rules={"api_key": {"startswith": "sk-ant-"}}
            )
        }
        
        # Setup default configuration sources and validators
        self._setup_default_sources()
        self._setup_default_validators()
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current_path = Path(__file__).resolve()
        
        # Look for project indicators
        for parent in current_path.parents:
            if any((parent / indicator).exists() for indicator in [
                "backend", "frontend", "config", ".env.template", "requirements.txt"
            ]):
                return parent
        
        # Fallback to current working directory
        return Path.cwd()
    
    def _setup_default_sources(self):
        """Setup default configuration sources based on deployment mode."""
        # Base configuration
        self.add_source(ConfigSourceDefinition(
            path=self.project_root / "config" / "base.yaml",
            format=ConfigFormat.YAML,
            required=False,
            priority=0
        ))
        
        # Environment-specific configuration
        env_config_path = self.project_root / "config" / f"{self.deployment_mode.value}.yaml"
        self.add_source(ConfigSourceDefinition(
            path=env_config_path,
            format=ConfigFormat.YAML,
            required=False,
            priority=10
        ))
        
        # Local overrides
        self.add_source(ConfigSourceDefinition(
            path=self.project_root / "config" / "local.yaml",
            format=ConfigFormat.YAML,
            required=False,
            priority=20,
            watch=True
        ))
        
        # Environment variables (highest priority)
        self.add_source(ConfigSourceDefinition(
            path=self.project_root / ".env",
            format=ConfigFormat.ENV,
            required=False,
            priority=30,
            watch=True
        ))
    
    def _setup_default_validators(self):
        """Setup default configuration validators."""
        # Required fields - make optional for now since we load from .env
        required_fields = []
        self.add_validator(RequiredFieldValidator(required_fields))
    
    def add_source(self, source: ConfigSourceDefinition):
        """Add a configuration source."""
        self.config_sources.append(source)
        self.config_sources.sort(key=lambda s: s.priority)
        logger.debug(f"Added configuration source: {source.path} (priority: {source.priority})")
    
    def add_validator(self, validator: ConfigurationValidator):
        """Add a configuration validator."""
        self.validators.append(validator)
        logger.debug(f"Added configuration validator: {validator.__class__.__name__}")
    
    def add_reload_callback(self, callback: callable):
        """Add a callback to be called when configuration is reloaded."""
        self.reload_callbacks.append(callback)
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from all sources.
        
        This method consolidates functionality from config_loader.py and config_manager.py
        to provide a unified configuration loading interface.
        """
        with self.config_lock:
            merged_config = {}
            
            # Load from multiple sources in priority order
            for source in self.config_sources:
                try:
                    logger.debug(f"Attempting to load configuration from: {source.path}")
                    config_data = self._load_source(source)
                    if config_data:
                        merged_config = self._merge_configs(merged_config, config_data)
                        self.loaded_sources.append(str(source.path))
                        logger.debug(f"Loaded configuration from: {source.path} ({len(config_data)} keys)")
                    else:
                        logger.debug(f"No data loaded from: {source.path}")
                except Exception as e:
                    if source.required:
                        raise ConfigurationError(f"Failed to load required configuration from {source.path}: {e}")
                    else:
                        logger.warning(f"Failed to load optional configuration from {source.path}: {e}")
            
            # Load environment variables directly
            self._load_environment_variables(merged_config)
            
            # Validate merged configuration
            self.validation_result = self._validate_configuration(merged_config)
            
            if not self.validation_result.is_valid:
                self._handle_validation_errors()
            
            self.config_data = merged_config
            
            # Initialize Pydantic settings
            self._settings = Settings()
            
            logger.info(f"Configuration loaded successfully for {self.deployment_mode.value} mode")
            return self.config_data
    
    def _load_source(self, source: ConfigSourceDefinition) -> Optional[Dict[str, Any]]:
        """Load configuration from a single source."""
        if not source.path.exists():
            return None
        
        try:
            if source.format == ConfigFormat.JSON:
                with open(source.path, 'r') as f:
                    return json.load(f)
            elif source.format == ConfigFormat.YAML:
                with open(source.path, 'r') as f:
                    return yaml.safe_load(f)
            elif source.format == ConfigFormat.ENV:
                return self._load_env_file(source.path)
            else:
                logger.warning(f"Unsupported configuration format: {source.format}")
                return None
        except Exception as e:
            logger.error(f"Error loading configuration from {source.path}: {e}")
            raise
    
    def _load_env_file(self, path: Path) -> Dict[str, Any]:
        """Load environment variables from .env file."""
        config = {}
        if not path.exists():
            return config
        
        # Load .env file
        load_dotenv(path, override=True)
        
        # Parse .env file manually for better control
        with open(path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # Convert boolean values
                        if value.lower() in ('true', 'false'):
                            value = value.lower() == 'true'
                        # Convert numeric values
                        elif value.isdigit():
                            value = int(value)
                        elif self._is_float(value):
                            value = float(value)
                        
                        config[key] = value
                        
                    except ValueError as e:
                        logger.warning(f"Invalid line {line_num} in {path}: {line}")
        
        return config
    
    def _load_environment_variables(self, config: Dict[str, Any]):
        """Load configuration from environment variables."""
        env_data = {}
        
        # Load all environment variables that match our patterns
        for key, value in os.environ.items():
            # Convert boolean values
            if isinstance(value, str):
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif self._is_float(value):
                    value = float(value)
            
            env_data[key] = value
        
        # Merge environment variables
        self._merge_configs(config, env_data)
        self.loaded_sources.append("environment_variables")
        logger.debug("Loaded configuration from environment variables")
    
    def _is_float(self, value: str) -> bool:
        """Check if string represents a float."""
        try:
            float(value)
            return '.' in value
        except ValueError:
            return False
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_configuration(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """Validate the loaded configuration."""
        result = ConfigValidationResult(is_valid=True)
        
        # Run all validators
        for validator in self.validators:
            try:
                errors = validator.validate(config)
                result.errors.extend(errors)
            except Exception as e:
                result.errors.append(f"Validator {validator.__class__.__name__} failed: {e}")
        
        # Validate services
        for service_id, service_config in self.services.items():
            self._validate_service(service_id, service_config, result)
        
        # Set overall validity
        result.is_valid = len(result.errors) == 0
        
        return result
    
    def _validate_service(self, service_id: str, service_config: ServiceConfig, result: ConfigValidationResult):
        """Validate service configuration."""
        # Check if service is enabled
        enabled_key = f"{service_id.upper()}_ENABLED"
        is_enabled = self.get_setting(enabled_key, service_config.enabled)
        
        if not is_enabled and not service_config.required:
            return  # Skip validation for disabled optional services
        
        # Validate required service configuration
        for config_key, env_key in service_config.config.items():
            value = self.get_setting(env_key)
            
            if not value:
                if service_config.required or is_enabled:
                    result.errors.append(f"Service '{service_config.name}' requires '{env_key}' to be configured")
                else:
                    result.warnings.append(f"Service '{service_config.name}' is enabled but '{env_key}' is not configured")
            else:
                # Apply validation rules
                if config_key in service_config.validation_rules:
                    rules = service_config.validation_rules[config_key]
                    if "startswith" in rules and not str(value).startswith(rules["startswith"]):
                        result.invalid_values.append(f"'{env_key}' should start with '{rules['startswith']}'")
    
    def _handle_validation_errors(self):
        """Handle validation errors by providing helpful messages."""
        if not self.validation_result:
            return
        
        error_messages = []
        
        if self.validation_result.missing_required:
            error_messages.append("❌ Missing required configuration:")
            for key in self.validation_result.missing_required:
                error_messages.append(f"   - {key}")
        
        if self.validation_result.invalid_values:
            error_messages.append("\n❌ Invalid configuration values:")
            for error in self.validation_result.invalid_values:
                error_messages.append(f"   - {error}")
        
        if self.validation_result.warnings:
            error_messages.append("\n⚠️  Configuration warnings:")
            for warning in self.validation_result.warnings:
                error_messages.append(f"   - {warning}")
        
        # Add setup instructions
        error_messages.extend([
            "\n🔧 To fix these issues:",
            "   1. Copy .env.template to .env",
            "   2. Edit .env and add your configuration values",
            "   3. Restart the application"
        ])
        
        raise ConfigurationError("\n".join(error_messages))
    
    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """
        Validate configuration and return detailed report.
        
        This method consolidates functionality from config_validator.py
        """
        if config is None:
            config = self.config_data
        
        report = ValidationReport(is_valid=True)
        
        # Validate required settings
        self._validate_required_settings(config, report)
        
        # Validate API configuration
        self._validate_api_configuration(config, report)
        
        # Validate database configuration
        self._validate_database_configuration(config, report)
        
        # Validate AI services
        self._validate_ai_services(config, report)
        
        # Validate security settings
        self._validate_security_settings(config, report)
        
        # Set overall validity
        report.is_valid = len(report.errors) == 0
        
        return report
    
    def _validate_required_settings(self, config: Dict[str, Any], report: ValidationReport):
        """Validate required configuration settings."""
        required_settings = {
            "API_HOST": "API host must be specified",
            "API_PORT": "API port must be specified"
        }
        
        for key, message in required_settings.items():
            value = config.get(key)
            if not value:
                self._add_validation_issue(report, "error", "missing", key, message)
    
    def _validate_api_configuration(self, config: Dict[str, Any], report: ValidationReport):
        """Validate API configuration."""
        api_port = config.get("API_PORT")
        if api_port:
            try:
                port_num = int(api_port)
                if port_num < 1 or port_num > 65535:
                    self._add_validation_issue(
                        report, "error", "invalid", "API_PORT",
                        f"API port {port_num} is out of valid range (1-65535)"
                    )
            except (ValueError, TypeError):
                self._add_validation_issue(
                    report, "error", "invalid", "API_PORT",
                    f"API port must be a number, got: {api_port}"
                )
    
    def _validate_database_configuration(self, config: Dict[str, Any], report: ValidationReport):
        """Validate database configuration."""
        database_url = config.get("DATABASE_URL")
        if database_url:
            try:
                parsed = urlparse(database_url)
                if parsed.scheme not in ["sqlite", "sqlite+aiosqlite", "postgresql", "postgresql+asyncpg", "mysql"]:
                    self._add_validation_issue(
                        report, "warning", "invalid", "DATABASE_URL",
                        f"Unsupported database scheme: {parsed.scheme}"
                    )
            except Exception as e:
                self._add_validation_issue(
                    report, "error", "invalid", "DATABASE_URL",
                    f"Invalid database URL format: {e}"
                )
    
    def _validate_ai_services(self, config: Dict[str, Any], report: ValidationReport):
        """Validate AI service configurations."""
        # OpenAI validation
        openai_key = config.get("OPENAI_API_KEY")
        if openai_key:
            if not openai_key.startswith("sk-"):
                self._add_validation_issue(
                    report, "error", "invalid", "OPENAI_API_KEY",
                    "OpenAI API key format is invalid - should start with 'sk-'"
                )
            report.services_status["openai"] = "configured"
        else:
            report.services_status["openai"] = "missing"
    
    def _validate_security_settings(self, config: Dict[str, Any], report: ValidationReport):
        """Validate security configuration."""
        # JWT secret validation
        jwt_secret = config.get("JWT_SECRET_KEY")
        if jwt_secret:
            if jwt_secret == "your-super-secret-key-min-32-chars":
                self._add_validation_issue(
                    report, "error", "security", "JWT_SECRET_KEY",
                    "Default JWT secret key is being used"
                )
            elif len(str(jwt_secret)) < 32:
                self._add_validation_issue(
                    report, "warning", "security", "JWT_SECRET_KEY",
                    "JWT secret key is too short - use at least 32 characters"
                )
    
    def _add_validation_issue(self, report: ValidationReport, level: str, category: str, 
                            key: str, message: str, suggestion: Optional[str] = None):
        """Add a validation issue to the report."""
        issue = ValidationIssue(
            level=level,
            category=category,
            key=key,
            message=message,
            suggestion=suggestion
        )
        report.issues.append(issue)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        This method provides backward compatibility with existing access patterns
        while supporting both flat keys and nested dot notation.
        """
        with self.config_lock:
            # First try direct key access
            if key in self.config_data:
                return self.config_data[key]
            
            # Try dot notation for nested access
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    # Try Pydantic settings as fallback
                    if self._settings:
                        try:
                            return getattr(self._settings, key.lower(), default)
                        except AttributeError:
                            pass
                    return default
            
            return value
    
    def set_setting(self, key: str, value: Any):
        """Set configuration value by key (supports dot notation)."""
        with self.config_lock:
            keys = key.split('.')
            config = self.config_data
            
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            logger.debug(f"Configuration value set: {key} = {value}")
    
    def reload_configuration(self):
        """Reload configuration from all sources."""
        logger.info("Reloading configuration...")
        try:
            old_config = self.config_data.copy()
            self.load_config()
            
            # Notify callbacks
            for callback in self.reload_callbacks:
                try:
                    callback(old_config, self.config_data)
                except Exception as e:
                    logger.error(f"Configuration reload callback failed: {e}")
            
            logger.info("Configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            raise
    
    def start_watching(self):
        """Start watching configuration files for changes."""
        if not WATCHDOG_AVAILABLE or self.observer is not None:
            return
        
        watched_paths = set()
        for source in self.config_sources:
            if source.watch and source.path.exists():
                watched_paths.add(source.path.parent)
        
        if not watched_paths:
            logger.info("No configuration files to watch")
            return
        
        self.observer = Observer()
        event_handler = ConfigFileWatcher(self)
        
        for path in watched_paths:
            self.observer.schedule(event_handler, str(path), recursive=False)
            logger.info(f"Watching configuration directory: {path}")
        
        self.observer.start()
        logger.info("Configuration file watching started")
    
    def stop_watching(self):
        """Stop watching configuration files."""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Configuration file watching stopped")
    
    def is_watched_file(self, file_path: Path) -> bool:
        """Check if a file is being watched for changes."""
        for source in self.config_sources:
            if source.watch and source.path == file_path:
                return True
        return False
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service."""
        if service_name not in self.services:
            return {}
        
        service_config = self.services[service_name]
        result = {}
        
        for config_key, env_key in service_config.config.items():
            value = self.get_setting(env_key)
            if value is not None:
                result[config_key] = value
        
        # Add enabled status
        enabled_key = f"{service_name.upper()}_ENABLED"
        result["enabled"] = self.get_setting(enabled_key, service_config.enabled)
        
        return result
    
    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a service is enabled."""
        if service_name not in self.services:
            return False
        
        enabled_key = f"{service_name.upper()}_ENABLED"
        return self.get_setting(enabled_key, self.services[service_name].enabled)
    
    def export_configuration(self, format: ConfigFormat = ConfigFormat.YAML) -> str:
        """Export current configuration to string."""
        with self.config_lock:
            if format == ConfigFormat.JSON:
                return json.dumps(self.config_data, indent=2, default=str)
            elif format == ConfigFormat.YAML:
                return yaml.dump(self.config_data, default_flow_style=False, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")
    
    def get_validation_report(self) -> str:
        """Get a formatted validation report."""
        if not self.validation_result:
            return "Configuration not validated yet."
        
        lines = []
        
        if self.validation_result.is_valid:
            lines.append("✅ Configuration validation passed")
        else:
            lines.append("❌ Configuration validation failed")
        
        if self.validation_result.errors:
            lines.append(f"\nErrors ({len(self.validation_result.errors)}):")
            for error in self.validation_result.errors:
                lines.append(f"  - {error}")
        
        if self.validation_result.warnings:
            lines.append(f"\nWarnings ({len(self.validation_result.warnings)}):")
            for warning in self.validation_result.warnings:
                lines.append(f"  - {warning}")
        
        lines.append(f"\nLoaded from {len(self.loaded_sources)} sources:")
        for source in self.loaded_sources:
            lines.append(f"  - {source}")
        
        return "\n".join(lines)


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None
_config_lock = threading.Lock()


def get_config_manager(deployment_mode: Optional[DeploymentMode] = None) -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    
    with _config_lock:
        if _config_manager is None:
            _config_manager = ConfigurationManager(deployment_mode)
            logger.info(f"Created configuration manager for {_config_manager.deployment_mode.value} mode")
        
        return _config_manager


def initialize_configuration(deployment_mode: Optional[DeploymentMode] = None) -> Dict[str, Any]:
    """Initialize and load configuration."""
    config_manager = get_config_manager(deployment_mode)
    config_data = config_manager.load_config()
    config_manager.start_watching()
    return config_data


# Backward compatibility functions
@lru_cache()
def get_settings() -> Settings:
    """Get Pydantic settings instance (backward compatibility)."""
    return Settings()


def get_config_loader() -> ConfigurationManager:
    """Get the configuration loader (backward compatibility)."""
    return get_config_manager()


def load_and_validate_config() -> Dict[str, Any]:
    """Load and validate configuration (backward compatibility)."""
    config_manager = get_config_manager()
    return config_manager.load_config()


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value (backward compatibility)."""
    config_manager = get_config_manager()
    return config_manager.get_setting(key, default)


def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value by key (backward compatibility)."""
    config_manager = get_config_manager()
    return config_manager.get_setting(key, default)


def set_config(key: str, value: Any):
    """Set configuration value by key (backward compatibility)."""
    config_manager = get_config_manager()
    config_manager.set_setting(key, value)


def reload_config():
    """Reload configuration from all sources (backward compatibility)."""
    config_manager = get_config_manager()
    config_manager.reload_configuration()


def is_service_enabled(service_name: str) -> bool:
    """Check if a service is enabled (backward compatibility)."""
    config_manager = get_config_manager()
    return config_manager.is_service_enabled(service_name)


def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get service configuration (backward compatibility)."""
    config_manager = get_config_manager()
    return config_manager.get_service_config(service_name)


def validate_configuration(config_data: Dict[str, Any]) -> ValidationReport:
    """Validate configuration and return report (backward compatibility)."""
    config_manager = get_config_manager()
    return config_manager.validate_config(config_data)


def validate_and_report(config_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate configuration and return success status and formatted report (backward compatibility)."""
    config_manager = get_config_manager()
    report = config_manager.validate_config(config_data)
    formatted_report = "\n".join([
        "✅ Configuration validation passed" if report.is_valid else "❌ Configuration validation failed",
        f"Errors: {len(report.errors)}, Warnings: {len(report.warnings)}"
    ])
    return report.is_valid, formatted_report