"""
Environment-specific configuration management for Career Copilot.

This module provides environment-specific configuration management,
ensuring proper settings for development, production, and testing environments.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .logging import get_logger

logger = get_logger(__name__)


class Environment(Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration."""
    name: str
    debug: bool
    log_level: str
    enable_monitoring: bool
    enable_security: bool
    enable_auth: bool
    database_pool_size: int
    worker_count: int
    cors_origins: List[str]
    allowed_hosts: List[str]
    rate_limit_enabled: bool
    file_upload_max_size: int
    session_timeout: int


class EnvironmentConfigManager:
    """Manages environment-specific configurations."""
    
    def __init__(self):
        self.current_env = self._detect_environment()
        self.config = self._load_environment_config()
        
    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables."""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        
        # Check for production indicators
        if (env_name == "production" or 
            os.getenv("PRODUCTION_MODE", "false").lower() == "true" or
            os.getenv("PROD", "false").lower() == "true"):
            return Environment.PRODUCTION
        
        # Check for testing indicators
        if (env_name == "testing" or 
            os.getenv("TESTING", "false").lower() == "true" or
            "pytest" in os.environ.get("_", "")):
            return Environment.TESTING
        
        # Default to development
        return Environment.DEVELOPMENT
    
    def _load_environment_config(self) -> EnvironmentConfig:
        """Load configuration for current environment."""
        if self.current_env == Environment.PRODUCTION:
            return self._get_production_config()
        elif self.current_env == Environment.TESTING:
            return self._get_testing_config()
        else:
            return self._get_development_config()
    
    def _get_development_config(self) -> EnvironmentConfig:
        """Get development environment configuration."""
        return EnvironmentConfig(
            name="development",
            debug=True,
            log_level="DEBUG",
            enable_monitoring=False,
            enable_security=False,
            enable_auth=False,
            database_pool_size=5,
            worker_count=1,
            cors_origins=[
                "http://localhost:8501",
                "http://127.0.0.1:8501",
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ],
            allowed_hosts=["localhost", "127.0.0.1"],
            rate_limit_enabled=False,
            file_upload_max_size=50 * 1024 * 1024,  # 50MB
            session_timeout=3600  # 1 hour
        )
    
    def _get_production_config(self) -> EnvironmentConfig:
        """Get production environment configuration."""
        return EnvironmentConfig(
            name="production",
            debug=False,
            log_level="INFO",
            enable_monitoring=True,
            enable_security=True,
            enable_auth=True,
            database_pool_size=20,
            worker_count=4,
            cors_origins=self._get_production_cors_origins(),
            allowed_hosts=self._get_production_allowed_hosts(),
            rate_limit_enabled=True,
            file_upload_max_size=25 * 1024 * 1024,  # 25MB
            session_timeout=1800  # 30 minutes
        )
    
    def _get_testing_config(self) -> EnvironmentConfig:
        """Get testing environment configuration."""
        return EnvironmentConfig(
            name="testing",
            debug=True,
            log_level="WARNING",
            enable_monitoring=False,
            enable_security=False,
            enable_auth=False,
            database_pool_size=2,
            worker_count=1,
            cors_origins=["http://localhost:8501"],
            allowed_hosts=["localhost", "127.0.0.1"],
            rate_limit_enabled=False,
            file_upload_max_size=10 * 1024 * 1024,  # 10MB
            session_timeout=300  # 5 minutes
        )
    
    def _get_production_cors_origins(self) -> List[str]:
        """Get production CORS origins from environment."""
        cors_env = os.getenv("CORS_ORIGINS", "")
        if cors_env:
            return [origin.strip() for origin in cors_env.split(",") if origin.strip()]
        
        # Default production CORS origins
        return [
            "https://your-domain.com",
            "https://www.your-domain.com"
        ]
    
    def _get_production_allowed_hosts(self) -> List[str]:
        """Get production allowed hosts from environment."""
        hosts_env = os.getenv("ALLOWED_HOSTS", "")
        if hosts_env:
            return [host.strip() for host in hosts_env.split(",") if host.strip()]
        
        # Default production allowed hosts
        return ["your-domain.com", "www.your-domain.com"]
    
    def get_config(self) -> EnvironmentConfig:
        """Get current environment configuration."""
        return self.config
    
    def get_environment(self) -> Environment:
        """Get current environment."""
        return self.current_env
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.current_env == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.current_env == Environment.PRODUCTION
    
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.current_env == Environment.TESTING
    
    def apply_environment_overrides(self) -> None:
        """Apply environment-specific overrides to os.environ."""
        config = self.config
        
        # Set environment variables based on config
        os.environ["DEBUG"] = str(config.debug).lower()
        os.environ["LOG_LEVEL"] = config.log_level
        os.environ["ENABLE_MONITORING"] = str(config.enable_monitoring).lower()
        os.environ["ENABLE_SECURITY"] = str(config.enable_security).lower()
        os.environ["DISABLE_AUTH"] = str(not config.enable_auth).lower()
        os.environ["RATE_LIMIT_ENABLED"] = str(config.rate_limit_enabled).lower()
        os.environ["MAX_FILE_SIZE_BYTES"] = str(config.file_upload_max_size)
        os.environ["SESSION_TIMEOUT_MINUTES"] = str(config.session_timeout // 60)
        
        # Set CORS origins
        os.environ["CORS_ORIGINS"] = ",".join(config.cors_origins)
        
        logger.info(f"Applied {config.name} environment configuration")
    
    def validate_environment_consistency(self) -> List[str]:
        """Validate environment configuration consistency."""
        issues = []
        config = self.config
        
        # Check environment variable consistency
        env_debug = os.getenv("DEBUG", "false").lower() == "true"
        if env_debug != config.debug:
            issues.append(f"DEBUG environment variable ({env_debug}) doesn't match config ({config.debug})")
        
        env_production = os.getenv("PRODUCTION_MODE", "false").lower() == "true"
        if self.is_production() and not env_production:
            issues.append("PRODUCTION_MODE should be true in production environment")
        
        env_development = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"
        if not self.is_development() and env_development:
            issues.append("DEVELOPMENT_MODE should be false in non-development environments")
        
        # Check security settings in production
        if self.is_production():
            if not config.enable_security:
                issues.append("Security should be enabled in production")
            if not config.enable_auth:
                issues.append("Authentication should be enabled in production")
            if not config.rate_limit_enabled:
                issues.append("Rate limiting should be enabled in production")
        
        return issues
    
    def create_environment_directories(self) -> Dict[str, bool]:
        """Create environment-specific directories."""
        directories = {
            "data": Path("./data"),
            "logs": Path("./logs"),
            "logs/audit": Path("logs/audit"),
            "data/chroma": Path("data/chroma"),
            "data/uploads": Path("data/uploads"),
            "storage": Path("data/storage"),
        }
        
        # Add production-specific directories
        if self.is_production():
            directories.update({
                "backups": Path("./backups"),
                "secrets": Path("./secrets"),
                "monitoring": Path("./monitoring"),
            })
        
        results = {}
        for name, path in directories.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
                # Set secure permissions for production
                if self.is_production():
                    path.chmod(0o750)
                else:
                    path.chmod(0o755)
                results[name] = True
                logger.debug(f"Created directory: {path}")
            except Exception as e:
                logger.error(f"Failed to create directory {path}: {e}")
                results[name] = False
        
        return results
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get environment-specific database configuration."""
        config = self.config
        
        base_config = {
            "pool_size": config.database_pool_size,
            "max_overflow": config.database_pool_size * 2,
            "pool_timeout": 30,
            "pool_recycle": 3600,
        }
        
        if self.is_production():
            base_config.update({
                "pool_pre_ping": True,
                "pool_recycle": 1800,  # 30 minutes
                "echo": False,
            })
        elif self.is_development():
            base_config.update({
                "echo": True,  # Log SQL queries in development
                "pool_pre_ping": False,
            })
        else:  # testing
            base_config.update({
                "pool_size": 1,
                "max_overflow": 0,
                "echo": False,
            })
        
        return base_config
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get environment-specific logging configuration."""
        config = self.config
        
        base_config = {
            "level": config.log_level,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }
        
        if self.is_production():
            base_config.update({
                "handlers": ["file", "console"],
                "file_path": "logs/app.log",
                "max_bytes": 100 * 1024 * 1024,  # 100MB
                "backup_count": 10,
                "structured": True,
            })
        elif self.is_development():
            base_config.update({
                "handlers": ["console"],
                "structured": False,
            })
        else:  # testing
            base_config.update({
                "handlers": ["console"],
                "level": "WARNING",
                "structured": False,
            })
        
        return base_config


# Global instance
_env_config_manager: Optional[EnvironmentConfigManager] = None


def get_environment_config_manager() -> EnvironmentConfigManager:
    """Get the global environment configuration manager."""
    global _env_config_manager
    if _env_config_manager is None:
        _env_config_manager = EnvironmentConfigManager()
    return _env_config_manager


def get_current_environment() -> Environment:
    """Get the current environment."""
    return get_environment_config_manager().get_environment()


def get_environment_config() -> EnvironmentConfig:
    """Get the current environment configuration."""
    return get_environment_config_manager().get_config()


def is_development() -> bool:
    """Check if running in development mode."""
    return get_environment_config_manager().is_development()


def is_production() -> bool:
    """Check if running in production mode."""
    return get_environment_config_manager().is_production()


def is_testing() -> bool:
    """Check if running in testing mode."""
    return get_environment_config_manager().is_testing()


def setup_environment() -> None:
    """Setup environment-specific configuration."""
    manager = get_environment_config_manager()
    
    logger.info(f"Setting up {manager.get_environment().value} environment")
    
    # Apply environment overrides
    manager.apply_environment_overrides()
    
    # Create necessary directories
    dir_results = manager.create_environment_directories()
    created_dirs = [name for name, success in dir_results.items() if success]
    failed_dirs = [name for name, success in dir_results.items() if not success]
    
    if created_dirs:
        logger.info(f"Created directories: {', '.join(created_dirs)}")
    if failed_dirs:
        logger.warning(f"Failed to create directories: {', '.join(failed_dirs)}")
    
    # Validate configuration consistency
    issues = manager.validate_environment_consistency()
    if issues:
        logger.warning("Environment configuration issues:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("Environment configuration validation passed")