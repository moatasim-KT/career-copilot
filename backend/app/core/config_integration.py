"""
Integration layer between enhanced configuration system and existing configuration.

This module provides backward compatibility and migration utilities to integrate
the new enhanced configuration system with the existing Pydantic-based configuration.
"""

import os
from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from .config import Settings as LegacySettings
from .config_manager import (
    DeploymentMode,
    EnhancedConfigManager,
    get_config_manager,
    initialize_configuration
)
import logging

# Use standard logging if custom logging module is not available
try:
    from .logging import get_logger
except ImportError:
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


class EnhancedSettings(BaseSettings):
    """Enhanced settings class that integrates with the new configuration system."""
    
    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }
    
    def __init__(self, **kwargs):
        # Initialize enhanced configuration system
        deployment_mode = self._detect_deployment_mode()
        self.config_manager = get_config_manager(deployment_mode)
        
        # Load configuration if not already loaded
        if not self.config_manager.config_data:
            try:
                initialize_configuration(deployment_mode)
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced configuration: {e}")
        
        super().__init__(**kwargs)
    
    def _detect_deployment_mode(self) -> DeploymentMode:
        """Detect deployment mode from environment variables."""
        mode = os.getenv('DEPLOYMENT_MODE', os.getenv('ENVIRONMENT', 'development')).lower()
        
        # Map common environment names to deployment modes
        mode_mapping = {
            'dev': DeploymentMode.DEVELOPMENT,
            'development': DeploymentMode.DEVELOPMENT,
            'test': DeploymentMode.TESTING,
            'testing': DeploymentMode.TESTING,
            'stage': DeploymentMode.STAGING,
            'staging': DeploymentMode.STAGING,
            'prod': DeploymentMode.PRODUCTION,
            'production': DeploymentMode.PRODUCTION,
            'docker': DeploymentMode.DOCKER,
            'k8s': DeploymentMode.KUBERNETES,
            'kubernetes': DeploymentMode.KUBERNETES,
            'native': DeploymentMode.NATIVE
        }
        
        return mode_mapping.get(mode, DeploymentMode.DEVELOPMENT)
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value from enhanced config system."""
        try:
            return self.config_manager.get(key, default)
        except Exception as e:
            logger.warning(f"Failed to get config value '{key}': {e}")
            return default
    
    def set_config_value(self, key: str, value: Any):
        """Set configuration value in enhanced config system."""
        try:
            self.config_manager.set(key, value)
        except Exception as e:
            logger.warning(f"Failed to set config value '{key}': {e}")


class ConfigMigrator:
    """Utility class to migrate from legacy to enhanced configuration."""
    
    def __init__(self):
        self.legacy_settings = LegacySettings()
        self.enhanced_manager = get_config_manager()
    
    def migrate_to_enhanced(self) -> Dict[str, Any]:
        """Migrate legacy configuration to enhanced format."""
        logger.info("Migrating legacy configuration to enhanced format")
        
        # Create enhanced configuration structure
        enhanced_config = {
            "api": {
                "host": self.legacy_settings.api_host,
                "port": self.legacy_settings.api_port,
                "debug": self.legacy_settings.api_debug
            },
            "database": {
                "url": self.legacy_settings.database_url or f"sqlite+aiosqlite:///{self.legacy_settings.sqlite_database_path}"
            },
            "redis": {
                "enabled": self.legacy_settings.enable_redis_caching,
                "host": self.legacy_settings.redis_host,
                "port": self.legacy_settings.redis_port,
                "db": self.legacy_settings.redis_db,
                "password": self.legacy_settings.redis_password,
                "max_connections": self.legacy_settings.redis_max_connections,
                "socket_timeout": self.legacy_settings.redis_socket_timeout
            },
            "logging": {
                "level": self.legacy_settings.log_level,
                "format": self.legacy_settings.log_format,
                "file": self.legacy_settings.log_file
            },
            "security": {
                "cors_origins": self.legacy_settings.cors_origins.split(",") if self.legacy_settings.cors_origins else [],
                "rate_limiting": True,  # Default enabled
                "audit_logging": self.legacy_settings.enable_audit_logging,
                "max_file_size_mb": self.legacy_settings.max_file_size_mb,
                "allowed_file_types": self.legacy_settings.allowed_file_types,
                "encryption_enabled": bool(self.legacy_settings.encryption_key)
            },
            "ai": {
                "openai": {
                    "api_key": self.legacy_settings.openai_api_key.get_secret_value(),
                    "model": self.legacy_settings.openai_model,
                    "temperature": self.legacy_settings.openai_temperature
                },
                "langsmith": {
                    "enabled": self.legacy_settings.langsmith_tracing,
                    "api_key": self.legacy_settings.langsmith_api_key,
                    "project": self.legacy_settings.langsmith_project
                }
            },
            "monitoring": {
                "enabled": self.legacy_settings.enable_monitoring,
                "prometheus": self.legacy_settings.enable_prometheus,
                "tracing": self.legacy_settings.enable_opentelemetry,
                "metrics_port": self.legacy_settings.metrics_port
            },
            "integrations": {
                "docusign": {
                    "enabled": self.legacy_settings.docusign_enabled,
                    "client_id": self.legacy_settings.docusign_client_id,
                    "client_secret": self.legacy_settings.docusign_client_secret,
                    "redirect_uri": self.legacy_settings.docusign_redirect_uri,
                    "scopes": self.legacy_settings.docusign_scopes
                },
                "gmail": {
                    "enabled": self.legacy_settings.gmail_enabled,
                    "client_id": self.legacy_settings.gmail_client_id,
                    "client_secret": self.legacy_settings.gmail_client_secret,
                    "redirect_uri": self.legacy_settings.gmail_redirect_uri
                },
                "slack": {
                    "enabled": self.legacy_settings.slack_enabled,
                    "webhook_url": self.legacy_settings.slack_webhook_url,
                    "bot_token": self.legacy_settings.slack_bot_token,
                    "default_channel": self.legacy_settings.slack_default_channel
                },
                "hubspot": {
                    "enabled": self.legacy_settings.hubspot_enabled,
                    "api_key": self.legacy_settings.hubspot_api_key
                }
            },
            "vector_db": {
                "persist_directory": self.legacy_settings.chroma_persist_directory,
                "collection_name": self.legacy_settings.chroma_collection_name
            }
        }
        
        # Update enhanced configuration manager
        for key, value in self._flatten_dict(enhanced_config).items():
            if value is not None:
                self.enhanced_manager.set(key, value)
        
        logger.info("Configuration migration completed")
        return enhanced_config
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary with dot notation keys."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def create_migration_report(self) -> Dict[str, Any]:
        """Create a report of the migration process."""
        report = {
            "migration_status": "completed",
            "legacy_fields_migrated": 0,
            "enhanced_fields_created": 0,
            "warnings": [],
            "errors": []
        }
        
        try:
            # Count legacy fields
            legacy_dict = self.legacy_settings.model_dump()
            report["legacy_fields_migrated"] = len([v for v in legacy_dict.values() if v is not None])
            
            # Count enhanced fields
            enhanced_dict = self.enhanced_manager.config_data
            report["enhanced_fields_created"] = len(self._flatten_dict(enhanced_dict))
            
            # Check for missing required fields
            required_fields = ["api.host", "api.port", "ai.openai.api_key"]
            for field in required_fields:
                if not self.enhanced_manager.get(field):
                    report["warnings"].append(f"Required field '{field}' is missing")
            
        except Exception as e:
            report["errors"].append(f"Migration report generation failed: {e}")
            report["migration_status"] = "completed_with_errors"
        
        return report


class ConfigurationAdapter:
    """Adapter to provide backward compatibility with legacy configuration access patterns."""
    
    def __init__(self):
        self.enhanced_manager = get_config_manager()
        self._legacy_mapping = self._create_legacy_mapping()
    
    def _create_legacy_mapping(self) -> Dict[str, str]:
        """Create mapping from legacy field names to enhanced config paths."""
        return {
            # API settings
            "api_host": "api.host",
            "api_port": "api.port",
            "api_debug": "api.debug",
            
            # Database settings
            "database_url": "database.url",
            "sqlite_database_path": "database.sqlite_path",
            
            # Redis settings
            "enable_redis_caching": "redis.enabled",
            "redis_host": "redis.host",
            "redis_port": "redis.port",
            "redis_db": "redis.db",
            "redis_password": "redis.password",
            
            # OpenAI settings
            "openai_api_key": "ai.openai.api_key",
            "openai_model": "ai.openai.model",
            "openai_temperature": "ai.openai.temperature",
            
            # Monitoring settings
            "enable_monitoring": "monitoring.enabled",
            "enable_prometheus": "monitoring.prometheus",
            "metrics_port": "monitoring.metrics_port",
            
            # Security settings
            "cors_origins": "security.cors_origins",
            "max_file_size_mb": "security.max_file_size_mb",
            
            # Logging settings
            "log_level": "logging.level",
            "log_format": "logging.format",
            "log_file": "logging.file"
        }
    
    def get_legacy_value(self, legacy_field: str, default: Any = None) -> Any:
        """Get value using legacy field name."""
        enhanced_path = self._legacy_mapping.get(legacy_field)
        if enhanced_path:
            return self.enhanced_manager.get(enhanced_path, default)
        else:
            logger.warning(f"Legacy field '{legacy_field}' not mapped to enhanced configuration")
            return default
    
    def set_legacy_value(self, legacy_field: str, value: Any):
        """Set value using legacy field name."""
        enhanced_path = self._legacy_mapping.get(legacy_field)
        if enhanced_path:
            self.enhanced_manager.set(enhanced_path, value)
        else:
            logger.warning(f"Legacy field '{legacy_field}' not mapped to enhanced configuration")


# Global instances
_enhanced_settings: Optional[EnhancedSettings] = None
_config_adapter: Optional[ConfigurationAdapter] = None


def get_enhanced_settings() -> EnhancedSettings:
    """Get the global enhanced settings instance."""
    global _enhanced_settings
    if _enhanced_settings is None:
        _enhanced_settings = EnhancedSettings()
    return _enhanced_settings


def get_config_adapter() -> ConfigurationAdapter:
    """Get the global configuration adapter instance."""
    global _config_adapter
    if _config_adapter is None:
        _config_adapter = ConfigurationAdapter()
    return _config_adapter


def migrate_legacy_configuration() -> Dict[str, Any]:
    """Migrate legacy configuration to enhanced system."""
    migrator = ConfigMigrator()
    enhanced_config = migrator.migrate_to_enhanced()
    report = migrator.create_migration_report()
    
    logger.info(f"Configuration migration report: {report}")
    return report


# Alias for backward compatibility
ConfigManager = EnhancedConfigManager