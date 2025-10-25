"""
Enhanced Configuration Management System for Production Readiness.

This module provides a centralized, type-safe, and environment-aware configuration
management system with support for dynamic reloading and validation.
"""

import json
import os
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
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

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from pydantic import BaseModel, Field, ValidationError
try:
    from pydantic import validator
except ImportError:
    # For newer pydantic versions
    from pydantic import field_validator as validator

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

import logging

# Use standard logging if custom logging module is not available
try:
    from .logging import get_logger
except ImportError:
    def get_logger(name):
        return logging.getLogger(name)

# Define ConfigurationError if not available
class ConfigurationError(Exception):
    """Configuration related error."""
    pass

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)


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


@dataclass
class ConfigSource:
    """Configuration source definition."""
    path: Path
    format: ConfigFormat
    required: bool = True
    watch: bool = False
    priority: int = 0  # Higher priority overrides lower priority


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


class TypeValidator(ConfigurationValidator):
    """Validator for configuration field types."""
    
    def __init__(self, type_specs: Dict[str, Type]):
        self.type_specs = type_specs
    
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate field types."""
        errors = []
        for field, expected_type in self.type_specs.items():
            value = self._get_nested_value(config, field)
            if value is not None and not isinstance(value, expected_type):
                errors.append(f"Field '{field}' should be of type {expected_type.__name__}, got {type(value).__name__}")
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


class RangeValidator(ConfigurationValidator):
    """Validator for numeric ranges."""
    
    def __init__(self, range_specs: Dict[str, tuple]):
        self.range_specs = range_specs
    
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate numeric ranges."""
        errors = []
        for field, (min_val, max_val) in self.range_specs.items():
            value = self._get_nested_value(config, field)
            if value is not None and isinstance(value, (int, float)):
                if value < min_val or value > max_val:
                    errors.append(f"Field '{field}' value {value} is outside valid range [{min_val}, {max_val}]")
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
    
    def __init__(self, config_manager: 'EnhancedConfigManager'):
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


class EnhancedConfigManager:
    """Enhanced configuration manager with dynamic reloading and validation."""
    
    def __init__(self, deployment_mode: DeploymentMode = DeploymentMode.DEVELOPMENT):
        self.deployment_mode = deployment_mode
        self.config_sources: List[ConfigSource] = []
        self.validators: List[ConfigurationValidator] = []
        self.config_data: Dict[str, Any] = {}
        self.config_lock = threading.RLock()
        self.observer: Optional[Observer] = None
        self.reload_callbacks: List[callable] = []
        self._setup_default_sources()
        self._setup_default_validators()
    
    def _setup_default_sources(self):
        """Setup default configuration sources based on deployment mode."""
        # Find the project root directory (where config directory should be)
        current_path = Path(__file__).resolve()
        project_root = None
        
        # Start from current working directory and work up
        search_paths = [Path.cwd()]
        
        # Add parent directories of the current file
        for parent in current_path.parents:
            search_paths.append(parent)
        
        # Look for config directory
        for path in search_paths:
            if (path / "config").exists():
                project_root = path
                break
        
        # If still not found, use current working directory
        if project_root is None:
            project_root = Path.cwd()
        
        logger.debug(f"Using project root: {project_root}")
        logger.debug(f"Config directory exists: {(project_root / 'config').exists()}")
        
        # List config files for debugging
        config_dir = project_root / "config"
        if config_dir.exists():
            config_files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml")) + list(config_dir.glob("*.json"))
            logger.debug(f"Found config files: {[f.name for f in config_files]}")
        
        # Base configuration
        self.add_source(ConfigSource(
            path=project_root / "config" / "base.yaml",
            format=ConfigFormat.YAML,
            required=False,
            priority=0
        ))
        
        # Environment-specific configuration
        env_config_path = project_root / "config" / f"{self.deployment_mode.value}.yaml"
        self.add_source(ConfigSource(
            path=env_config_path,
            format=ConfigFormat.YAML,
            required=False,
            priority=10
        ))
        
        # Local overrides
        self.add_source(ConfigSource(
            path=project_root / "config" / "local.yaml",
            format=ConfigFormat.YAML,
            required=False,
            priority=20,
            watch=True
        ))
        
        # Environment variables (highest priority)
        self.add_source(ConfigSource(
            path=project_root / ".env",
            format=ConfigFormat.ENV,
            required=False,
            priority=30,
            watch=True
        ))
    
    def _setup_default_validators(self):
        """Setup default configuration validators."""
        # Required fields validator - using dot notation for nested config
        # Note: These will be populated from environment variables
        required_fields = []  # Make optional for now since we load from .env
        self.add_validator(RequiredFieldValidator(required_fields))
        
        # Type validator
        type_specs = {
            "api_port": int,
            "api_debug": bool,
            "openai_temperature": float,
            "redis_port": int,
            "max_file_size_mb": int
        }
        self.add_validator(TypeValidator(type_specs))
        
        # Range validator
        range_specs = {
            "api_port": (1, 65535),
            "openai_temperature": (0.0, 2.0),
            "redis_port": (1, 65535),
            "max_file_size_mb": (1, 1000)
        }
        self.add_validator(RangeValidator(range_specs))
    
    def add_source(self, source: ConfigSource):
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
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from all sources."""
        with self.config_lock:
            merged_config = {}
            
            for source in self.config_sources:
                try:
                    logger.debug(f"Attempting to load configuration from: {source.path}")
                    config_data = self._load_source(source)
                    if config_data:
                        merged_config = self._merge_configs(merged_config, config_data)
                        logger.debug(f"Loaded configuration from: {source.path} ({len(config_data)} keys)")
                    else:
                        logger.debug(f"No data loaded from: {source.path}")
                except Exception as e:
                    if source.required:
                        raise ConfigurationError(f"Failed to load required configuration from {source.path}: {e}")
                    else:
                        logger.warning(f"Failed to load optional configuration from {source.path}: {e}")
            
            # Validate merged configuration
            validation_errors = self._validate_configuration(merged_config)
            if validation_errors:
                error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
                raise ConfigurationError(error_msg)
            
            self.config_data = merged_config
            logger.info(f"Configuration loaded successfully for {self.deployment_mode.value} mode")
            return self.config_data
    
    def _load_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """Load configuration from a single source."""
        if not source.path.exists():
            return None
        
        try:
            if source.format == ConfigFormat.JSON:
                with open(source.path, 'r') as f:
                    return json.load(f)
            elif source.format == ConfigFormat.YAML:
                if not YAML_AVAILABLE:
                    logger.warning("YAML not available - skipping YAML configuration files")
                    return None
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
        
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    # Convert to appropriate type
                    if value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    elif value.isdigit():
                        value = int(value)
                    elif self._is_float(value):
                        value = float(value)
                    
                    # Handle nested configuration using dot notation
                    self._set_nested_value(config, key.lower(), value)
        
        return config
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """Set nested configuration value using dot notation."""
        # Handle special mappings for common environment variables
        key_mappings = {
            'openai_api_key': 'ai.openai.api_key',
            'api_host': 'api.host',
            'api_port': 'api.port',
            'database_url': 'database.url',
            'redis_host': 'cache.redis.host',
            'redis_port': 'cache.redis.port',
            'redis_password': 'cache.redis.password',
            'log_level': 'logging.level',
            'cors_origins': 'security.cors_origins',
            'groq_api_key': 'ai.groq.api_key',
            'gemini_api_key': 'ai.gemini.api_key',
            'anthropic_api_key': 'ai.anthropic.api_key'
        }
        
        # Use mapping if available, otherwise use key as-is
        mapped_key = key_mappings.get(key, key)
        keys = mapped_key.split('.')
        
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _is_float(self, value: str) -> bool:
        """Check if string represents a float."""
        try:
            float(value)
            return True
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
    
    def _validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration using all validators."""
        all_errors = []
        
        for validator in self.validators:
            try:
                errors = validator.validate(config)
                all_errors.extend(errors)
            except Exception as e:
                all_errors.append(f"Validator {validator.__class__.__name__} failed: {e}")
        
        return all_errors
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        with self.config_lock:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set(self, key: str, value: Any):
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
            self.load_configuration()
            
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
        if self.observer is not None:
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
    
    def export_configuration(self, format: ConfigFormat = ConfigFormat.YAML) -> str:
        """Export current configuration to string."""
        with self.config_lock:
            if format == ConfigFormat.JSON:
                return json.dumps(self.config_data, indent=2)
            elif format == ConfigFormat.YAML:
                if not YAML_AVAILABLE:
                    raise ValueError("YAML not available for export")
                return yaml.dump(self.config_data, default_flow_style=False, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")
    
    def save_configuration(self, path: Path, format: ConfigFormat = ConfigFormat.YAML):
        """Save current configuration to file."""
        config_str = self.export_configuration(format)
        with open(path, 'w') as f:
            f.write(config_str)
        logger.info(f"Configuration saved to: {path}")


# Global configuration manager instance
_config_manager: Optional[EnhancedConfigManager] = None
_config_lock = threading.Lock()


def get_config_manager(deployment_mode: Optional[DeploymentMode] = None) -> EnhancedConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    
    with _config_lock:
        if _config_manager is None:
            if deployment_mode is None:
                # Detect deployment mode from environment
                env_mode = os.getenv('DEPLOYMENT_MODE', os.getenv('ENVIRONMENT', 'development')).lower()
                try:
                    deployment_mode = DeploymentMode(env_mode)
                except ValueError:
                    deployment_mode = DeploymentMode.DEVELOPMENT
                    logger.warning(f"Unknown deployment mode '{env_mode}', using development")
            
            _config_manager = EnhancedConfigManager(deployment_mode)
            logger.info(f"Created configuration manager for {deployment_mode.value} mode")
        
        return _config_manager


def initialize_configuration(deployment_mode: Optional[DeploymentMode] = None) -> Dict[str, Any]:
    """Initialize and load configuration."""
    config_manager = get_config_manager(deployment_mode)
    config_data = config_manager.load_configuration()
    config_manager.start_watching()
    return config_data


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value by key."""
    config_manager = get_config_manager()
    return config_manager.get(key, default)


def set_config(key: str, value: Any):
    """Set configuration value by key."""
    config_manager = get_config_manager()
    config_manager.set(key, value)


def reload_config():
    """Reload configuration from all sources."""
    config_manager = get_config_manager()
    config_manager.reload_configuration()