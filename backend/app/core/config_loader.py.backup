"""
Enhanced Configuration Loader with comprehensive validation and error handling.
This module provides a unified configuration loading system that handles multiple sources
and provides clear error messages for missing or invalid configuration.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Configuration related error."""
    pass


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
class ServiceConfig:
    """Configuration for external services."""
    name: str
    enabled: bool
    required: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)


class ConfigurationLoader:
    """Enhanced configuration loader with validation and error handling."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the configuration loader."""
        self.project_root = project_root or self._find_project_root()
        self.config_data: Dict[str, Any] = {}
        self.loaded_sources: List[str] = []
        self.validation_result: Optional[ConfigValidationResult] = None
        
        # Define required configuration keys
        self.required_keys = [
            "OPENAI_API_KEY"
        ]
        
        # Define optional keys with defaults
        self.optional_keys = {
            "API_HOST": "0.0.0.0",
            "API_PORT": 8000,
            "DATABASE_URL": "sqlite+aiosqlite:///./data/contract_analyzer.db"
        }
        
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
            "docusign": ServiceConfig(
                name="DocuSign",
                enabled=False,
                required=False,
                config={
                    "client_id": "DOCUSIGN_CLIENT_ID",
                    "client_secret": "DOCUSIGN_CLIENT_SECRET",
                    "sandbox": "DOCUSIGN_SANDBOX_ENABLED"
                }
            ),
            "slack": ServiceConfig(
                name="Slack",
                enabled=False,
                required=False,
                config={
                    "webhook_url": "SLACK_WEBHOOK_URL",
                    "bot_token": "SLACK_BOT_TOKEN"
                }
            ),
            "gmail": ServiceConfig(
                name="Gmail",
                enabled=False,
                required=False,
                config={
                    "client_id": "GMAIL_CLIENT_ID",
                    "client_secret": "GMAIL_CLIENT_SECRET"
                }
            )
        }
    
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
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from all available sources."""
        logger.info("Loading configuration from multiple sources...")
        
        # Load in priority order (later sources override earlier ones)
        self._load_yaml_config("config/base.yaml", required=False)
        self._load_yaml_config("config/development.yaml", required=False)
        self._load_yaml_config("config/local.yaml", required=False)
        self._load_env_file(".env.template", required=False)
        self._load_env_file(".env", required=False)
        self._load_environment_variables()
        
        # Validate configuration
        self.validation_result = self._validate_configuration()
        
        if not self.validation_result.is_valid:
            self._handle_validation_errors()
        
        logger.info(f"Configuration loaded successfully from {len(self.loaded_sources)} sources")
        return self.config_data
    
    def _load_yaml_config(self, relative_path: str, required: bool = True):
        """Load configuration from YAML file."""
        config_path = self.project_root / relative_path
        
        if not config_path.exists():
            if required:
                raise ConfigurationError(f"Required configuration file not found: {config_path}")
            logger.debug(f"Optional configuration file not found: {config_path}")
            return
        
        try:
            with open(config_path, 'r') as f:
                yaml_data = yaml.safe_load(f) or {}
            
            self._merge_config(yaml_data)
            self.loaded_sources.append(str(config_path))
            logger.debug(f"Loaded YAML configuration from: {config_path}")
            
        except Exception as e:
            error_msg = f"Failed to load YAML configuration from {config_path}: {e}"
            if required:
                raise ConfigurationError(error_msg)
            logger.warning(error_msg)
    
    def _load_env_file(self, relative_path: str, required: bool = True):
        """Load configuration from .env file."""
        env_path = self.project_root / relative_path
        
        if not env_path.exists():
            if required:
                raise ConfigurationError(f"Required environment file not found: {env_path}")
            logger.debug(f"Optional environment file not found: {env_path}")
            return
        
        try:
            # Load .env file
            load_dotenv(env_path, override=True)
            
            # Parse .env file manually for better control
            env_data = {}
            with open(env_path, 'r') as f:
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
                            
                            env_data[key] = value
                            
                        except ValueError as e:
                            logger.warning(f"Invalid line {line_num} in {env_path}: {line}")
            
            self._merge_config(env_data)
            self.loaded_sources.append(str(env_path))
            logger.debug(f"Loaded environment configuration from: {env_path}")
            
        except Exception as e:
            error_msg = f"Failed to load environment file {env_path}: {e}"
            if required:
                raise ConfigurationError(error_msg)
            logger.warning(error_msg)
    
    def _load_environment_variables(self):
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
        
        self._merge_config(env_data)
        self.loaded_sources.append("environment_variables")
        logger.debug("Loaded configuration from environment variables")
    
    def _is_float(self, value: str) -> bool:
        """Check if string represents a float."""
        try:
            float(value)
            return '.' in value
        except ValueError:
            return False
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration into existing config."""
        for key, value in new_config.items():
            if isinstance(value, dict) and key in self.config_data and isinstance(self.config_data[key], dict):
                # Recursively merge dictionaries
                self._merge_dict(self.config_data[key], value)
            else:
                self.config_data[key] = value
    
    def _merge_dict(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Recursively merge dictionaries."""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._merge_dict(target[key], value)
            else:
                target[key] = value
    
    def _validate_configuration(self) -> ConfigValidationResult:
        """Validate the loaded configuration."""
        result = ConfigValidationResult(is_valid=True)
        
        # Check required keys
        for key in self.required_keys:
            if not self.get_config_value(key):
                result.missing_required.append(key)
                result.errors.append(f"Required configuration key '{key}' is missing or empty")
        
        # Set defaults for optional keys
        for key, default_value in self.optional_keys.items():
            if not self.get_config_value(key):
                self.config_data[key] = default_value
        
        # Validate services
        for service_id, service_config in self.services.items():
            self._validate_service(service_id, service_config, result)
        
        # Validate specific configuration values
        self._validate_specific_values(result)
        
        # Set overall validity
        result.is_valid = len(result.errors) == 0
        
        return result
    
    def _validate_service(self, service_id: str, service_config: ServiceConfig, result: ConfigValidationResult):
        """Validate service configuration."""
        # Check if service is enabled
        enabled_key = f"{service_id.upper()}_ENABLED"
        is_enabled = self.get_config_value(enabled_key, service_config.enabled)
        
        if not is_enabled and not service_config.required:
            return  # Skip validation for disabled optional services
        
        # Validate required service configuration
        for config_key, env_key in service_config.config.items():
            value = self.get_config_value(env_key)
            
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
    
    def _validate_specific_values(self, result: ConfigValidationResult):
        """Validate specific configuration values."""
        # Validate API port
        api_port = self.get_config_value("API_PORT", 8000)
        if not isinstance(api_port, int) or not (1 <= api_port <= 65535):
            result.invalid_values.append("API_PORT must be an integer between 1 and 65535")
        
        # Validate file size limits
        max_file_size = self.get_config_value("MAX_FILE_SIZE_MB", 50)
        if not isinstance(max_file_size, (int, float)) or max_file_size <= 0:
            result.invalid_values.append("MAX_FILE_SIZE_MB must be a positive number")
        
        # Validate database URL format
        database_url = self.get_config_value("DATABASE_URL")
        if database_url and not any(database_url.startswith(prefix) for prefix in ["sqlite", "postgresql", "mysql"]):
            result.warnings.append("DATABASE_URL format may not be supported")
    
    def _handle_validation_errors(self):
        """Handle validation errors by providing helpful messages."""
        if not self.validation_result:
            return
        
        error_messages = []
        
        if self.validation_result.missing_required:
            error_messages.append("❌ Missing required configuration:")
            for key in self.validation_result.missing_required:
                error_messages.append(f"   - {key}")
                
                # Provide helpful hints
                if key == "OPENAI_API_KEY":
                    error_messages.append("     💡 Get your API key at: https://platform.openai.com/api-keys")
                elif key == "DATABASE_URL":
                    error_messages.append("     💡 Example: sqlite+aiosqlite:///./data/contract_analyzer.db")
        
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
            "   3. Restart the application",
            "\n📖 For detailed setup instructions, see: README.md"
        ])
        
        raise ConfigurationError("\n".join(error_messages))
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.config_data.get(key, default)
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service."""
        if service_name not in self.services:
            return {}
        
        service_config = self.services[service_name]
        result = {}
        
        for config_key, env_key in service_config.config.items():
            value = self.get_config_value(env_key)
            if value is not None:
                result[config_key] = value
        
        # Add enabled status
        enabled_key = f"{service_name.upper()}_ENABLED"
        result["enabled"] = self.get_config_value(enabled_key, service_config.enabled)
        
        return result
    
    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a service is enabled."""
        if service_name not in self.services:
            return False
        
        enabled_key = f"{service_name.upper()}_ENABLED"
        return self.get_config_value(enabled_key, self.services[service_name].enabled)
    
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
    
    def export_config(self, format: str = "yaml") -> str:
        """Export current configuration."""
        if format.lower() == "json":
            return json.dumps(self.config_data, indent=2, default=str)
        elif format.lower() == "yaml":
            return yaml.dump(self.config_data, default_flow_style=False, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global configuration loader instance
_config_loader: Optional[ConfigurationLoader] = None


def get_config_loader() -> ConfigurationLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigurationLoader()
    return _config_loader


def load_and_validate_config() -> Dict[str, Any]:
    """Load and validate configuration, raising errors if invalid."""
    loader = get_config_loader()
    return loader.load_configuration()


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value."""
    loader = get_config_loader()
    return loader.get_config_value(key, default)


def is_service_enabled(service_name: str) -> bool:
    """Check if a service is enabled."""
    loader = get_config_loader()
    return loader.is_service_enabled(service_name)


def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get service configuration."""
    loader = get_config_loader()
    return loader.get_service_config(service_name)