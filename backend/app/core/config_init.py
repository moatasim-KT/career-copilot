"""
Configuration Initialization System for Career Copilot.

This module provides a unified initialization system that:
- Detects the current environment
- Loads environment-specific configurations
- Validates configuration on startup
- Sets up feature flags
- Initializes hot-reloading
- Provides configuration health checks
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .logging import get_logger
from .config import (
    get_config_manager, 
    initialize_configuration, 
    DeploymentMode
)
from .config_validation import (
    validate_startup_configuration,
    check_environment_readiness,
    ValidationLevel
)
from .config_hot_reload import (
    get_configuration_hot_reloader,
    start_configuration_hot_reload
)
from .feature_flags import get_feature_flag_manager
from .environment_config import (
    get_environment_config_manager,
    setup_environment
)

logger = get_logger(__name__)


@dataclass
class ConfigurationStatus:
    """Configuration initialization status."""
    environment: str
    config_loaded: bool = False
    validation_passed: bool = False
    feature_flags_loaded: bool = False
    hot_reload_enabled: bool = False
    errors: int = 0
    warnings: int = 0
    startup_time: float = 0.0


class ConfigurationInitializer:
    """Main configuration initialization system."""
    
    def __init__(self):
        self.status = ConfigurationStatus(environment="unknown")
        self.config_manager = None
        self.hot_reloader = None
        self.feature_flag_manager = None
        self.environment_manager = None
    
    def initialize(self, 
                  environment: Optional[str] = None,
                  enable_hot_reload: bool = True,
                  enable_validation: bool = True,
                  config_path: Optional[Path] = None) -> ConfigurationStatus:
        """Initialize the complete configuration system."""
        import time
        start_time = time.time()
        
        try:
            logger.info("Starting configuration system initialization...")
            
            # Step 1: Detect and setup environment
            detected_env = self._detect_environment(environment)
            self.status.environment = detected_env
            logger.info(f"Detected environment: {detected_env}")
            
            # Step 2: Setup environment-specific configuration
            self._setup_environment_config()
            
            # Step 3: Initialize configuration manager
            self._initialize_config_manager(detected_env, config_path)
            
            # Step 4: Load and validate configuration
            if enable_validation:
                self._validate_configuration()
            else:
                self.status.validation_passed = True
            
            # Step 5: Initialize feature flags
            self._initialize_feature_flags()
            
            # Step 6: Setup hot-reloading
            if enable_hot_reload and detected_env in ["development", "staging"]:
                self._setup_hot_reload()
            
            # Step 7: Final health check
            self._perform_health_check()
            
            self.status.startup_time = time.time() - start_time
            logger.info(f"Configuration system initialized successfully in {self.status.startup_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Configuration initialization failed: {e}")
            self.status.startup_time = time.time() - start_time
            raise
        
        return self.status
    
    def _detect_environment(self, override_env: Optional[str] = None) -> str:
        """Detect the current deployment environment."""
        if override_env:
            return override_env
        
        # Check environment variables in order of priority
        env_vars = [
            "ENVIRONMENT",
            "DEPLOYMENT_MODE", 
            "ENV",
            "NODE_ENV"
        ]
        
        for var in env_vars:
            env_value = os.getenv(var)
            if env_value:
                env_value = env_value.lower()
                if env_value in ["production", "prod"]:
                    return "production"
                elif env_value in ["staging", "stage"]:
                    return "staging"
                elif env_value in ["testing", "test"]:
                    return "testing"
                elif env_value in ["development", "dev"]:
                    return "development"
        
        # Check for production indicators
        if (os.getenv("PRODUCTION_MODE", "").lower() == "true" or
            os.getenv("PROD", "").lower() == "true"):
            return "production"
        
        # Check for testing indicators
        if ("pytest" in sys.modules or 
            "test" in sys.argv[0] or
            os.getenv("TESTING", "").lower() == "true"):
            return "testing"
        
        # Default to development
        return "development"
    
    def _setup_environment_config(self):
        """Setup environment-specific configuration."""
        try:
            self.environment_manager = get_environment_config_manager()
            setup_environment()
            logger.info("Environment configuration setup completed")
        except Exception as e:
            logger.error(f"Environment configuration setup failed: {e}")
            raise
    
    def _initialize_config_manager(self, environment: str, config_path: Optional[Path] = None):
        """Initialize the configuration manager."""
        try:
            # Map environment to deployment mode
            deployment_mode_map = {
                "development": DeploymentMode.DEVELOPMENT,
                "testing": DeploymentMode.TESTING,
                "staging": DeploymentMode.STAGING,
                "production": DeploymentMode.PRODUCTION
            }
            
            deployment_mode = deployment_mode_map.get(environment, DeploymentMode.DEVELOPMENT)
            
            # Initialize configuration manager
            self.config_manager = get_config_manager(deployment_mode)
            
            # Load configuration
            config_data = initialize_configuration(deployment_mode)
            self.status.config_loaded = True
            
            logger.info(f"Configuration manager initialized with {len(config_data)} configuration keys")
            
        except Exception as e:
            logger.error(f"Configuration manager initialization failed: {e}")
            raise
    
    def _validate_configuration(self):
        """Validate the loaded configuration."""
        try:
            if not self.config_manager or not self.config_manager.config_data:
                raise ValueError("No configuration data available for validation")
            
            # Run validation
            validation_report = validate_startup_configuration(
                self.config_manager.config_data, 
                self.status.environment
            )
            
            self.status.errors = validation_report.errors
            self.status.warnings = validation_report.warnings
            
            # Check if validation passed
            if validation_report.has_errors():
                logger.error("Configuration validation failed with errors")
                self.status.validation_passed = False
                
                # Log detailed errors
                for result in validation_report.results:
                    if result.level == ValidationLevel.ERROR:
                        logger.error(f"Config Error - {result.field}: {result.message}")
                        if result.suggestion:
                            logger.error(f"  Suggestion: {result.suggestion}")
                
                # In production, fail fast on validation errors
                if self.status.environment == "production":
                    raise ValueError("Configuration validation failed in production environment")
            else:
                self.status.validation_passed = True
                logger.info("Configuration validation passed")
            
            # Log warnings
            if validation_report.warnings > 0:
                logger.warning(f"Configuration validation completed with {validation_report.warnings} warnings")
        
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            self.status.validation_passed = False
            raise
    
    def _initialize_feature_flags(self):
        """Initialize the feature flags system."""
        try:
            self.feature_flag_manager = get_feature_flag_manager(self.status.environment)
            
            # Test feature flag system (basic initialization only)
            logger.debug("Feature flag system initialized successfully")
            
            self.status.feature_flags_loaded = True
            logger.info("Feature flags system initialized")
            
        except Exception as e:
            logger.error(f"Feature flags initialization failed: {e}")
            # Don't fail startup for feature flags issues
            self.status.feature_flags_loaded = False
    
    def _setup_hot_reload(self):
        """Setup configuration hot-reloading."""
        try:
            self.hot_reloader = get_configuration_hot_reloader(
                self.config_manager, 
                self.status.environment
            )
            
            # Add validation callback
            self.hot_reloader.add_validation_callback(self._validate_hot_reload_config)
            
            # Add reload callback for logging
            self.hot_reloader.add_reload_callback(self._on_config_reload)
            
            # Start watching
            start_configuration_hot_reload(self.config_manager, self.status.environment)
            
            self.status.hot_reload_enabled = True
            logger.info("Configuration hot-reloading enabled")
            
        except Exception as e:
            logger.error(f"Hot-reload setup failed: {e}")
            # Don't fail startup for hot-reload issues
            self.status.hot_reload_enabled = False
    
    def _validate_hot_reload_config(self, config: Dict[str, Any]) -> bool:
        """Custom validation callback for hot-reload."""
        try:
            # Run basic validation
            validation_report = validate_startup_configuration(config, self.status.environment)
            
            # Allow warnings but not errors
            if validation_report.has_errors():
                logger.error("Hot-reload validation failed - configuration will be rejected")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Hot-reload validation error: {e}")
            return False
    
    def _on_config_reload(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """Callback for configuration reload events."""
        logger.info("Configuration reloaded successfully")
        
        # Check for significant changes
        significant_changes = self._detect_significant_changes(old_config, new_config)
        if significant_changes:
            logger.warning(f"Significant configuration changes detected: {significant_changes}")
    
    def _detect_significant_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> list:
        """Detect significant configuration changes that may require attention."""
        significant_fields = [
            "api.port",
            "database.url",
            "ai.openai.api_key",
            "security.jwt.secret_key"
        ]
        
        changes = []
        for field in significant_fields:
            old_value = self._get_nested_value(old_config, field)
            new_value = self._get_nested_value(new_config, field)
            
            if old_value != new_value:
                changes.append(field)
        
        return changes
    
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
    
    def _perform_health_check(self):
        """Perform final health check."""
        try:
            # Check environment readiness
            ready = check_environment_readiness(self.status.environment)
            
            if not ready:
                logger.warning("Environment readiness check failed")
            
            # Check configuration manager
            if not self.config_manager or not self.config_manager.config_data:
                raise ValueError("Configuration manager not properly initialized")
            
            # Check critical configuration values
            critical_checks = [
                ("ai.openai.api_key", "OpenAI API key"),
                ("api.port", "API port"),
                ("database.url", "Database URL")
            ]
            
            for key_path, description in critical_checks:
                value = self._get_nested_value(self.config_manager.config_data, key_path)
                if not value:
                    logger.warning(f"Critical configuration missing: {description}")
            
            logger.info("Configuration health check completed")
            
        except Exception as e:
            logger.error(f"Configuration health check failed: {e}")
            raise
    
    def get_status(self) -> ConfigurationStatus:
        """Get current configuration status."""
        return self.status
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        if not self.config_manager:
            return {}
        
        config = self.config_manager.config_data
        
        return {
            "environment": self.status.environment,
            "api_port": self._get_nested_value(config, "api.port"),
            "database_type": "sqlite" if "sqlite" in str(self._get_nested_value(config, "database.url")) else "postgresql",
            "ai_providers": [
                provider for provider in ["openai", "groq", "gemini", "anthropic", "ollama"]
                if self._get_nested_value(config, f"ai.{provider}.enabled") or 
                   (provider == "openai" and self._get_nested_value(config, f"ai.{provider}.api_key"))
            ],
            "monitoring_enabled": self._get_nested_value(config, "monitoring.enabled"),
            "hot_reload_enabled": self.status.hot_reload_enabled,
            "feature_flags_loaded": self.status.feature_flags_loaded,
            "validation_status": "passed" if self.status.validation_passed else "failed",
            "errors": self.status.errors,
            "warnings": self.status.warnings
        }


# Global initializer instance
_config_initializer: Optional[ConfigurationInitializer] = None


def initialize_configuration_system(
    environment: Optional[str] = None,
    enable_hot_reload: bool = True,
    enable_validation: bool = True,
    config_path: Optional[Path] = None
) -> ConfigurationStatus:
    """Initialize the complete configuration system."""
    global _config_initializer
    
    _config_initializer = ConfigurationInitializer()
    return _config_initializer.initialize(
        environment=environment,
        enable_hot_reload=enable_hot_reload,
        enable_validation=enable_validation,
        config_path=config_path
    )


def get_configuration_status() -> Optional[ConfigurationStatus]:
    """Get the current configuration status."""
    if _config_initializer:
        return _config_initializer.get_status()
    return None


def get_configuration_summary() -> Dict[str, Any]:
    """Get a summary of the current configuration."""
    if _config_initializer:
        return _config_initializer.get_config_summary()
    return {}


def is_configuration_ready() -> bool:
    """Check if the configuration system is ready."""
    status = get_configuration_status()
    return (status is not None and 
            status.config_loaded and 
            status.validation_passed)


async def reload_configuration_system() -> bool:
    """Reload the entire configuration system."""
    try:
        if _config_initializer and _config_initializer.hot_reloader:
            from .config_hot_reload import ReloadTrigger
            event = await _config_initializer.hot_reloader.reload_configuration(
                trigger=ReloadTrigger.API_REQUEST
            )
            return event.status.value == "success"
        return False
    except Exception as e:
        logger.error(f"Configuration system reload failed: {e}")
        return False