"""
Configuration loader for the Career Copilot application.
Handles loading and merging of configuration files from multiple sources.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Load environment variables from .env file using python-dotenv package
# dotenv is a Python package for loading environment variables from .env files
from dotenv import load_dotenv
load_dotenv()


class Environment(Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    STAGING = "staging"
    TESTING = "testing"


@dataclass
class ConfigPaths:
    """Configuration file paths."""
    application_config: str = "config/application.yaml"
    environment_config: str = "config/environments/{environment}.yaml"
    services_dir: str = "config/services"
    templates_dir: str = "config/templates"
    feature_flags: str = "config/feature_flags.json"
    llm_config: str = "config/llm_config.json"
    monitoring_config: str = "config/monitoring.yaml"
    alembic_config: str = "config/alembic.ini"
    pytest_config: str = "config/pytest.ini"


class ConfigLoader:
    """Configuration loader with environment-specific overrides."""
    
    def __init__(self, environment: Optional[str] = None):
        """Initialize the configuration loader."""
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.config_paths = ConfigPaths()
        self._config_cache: Dict[str, Any] = {}
        
    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load a YAML configuration file."""
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            print(f"Warning: Configuration file {file_path} not found")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {file_path}: {e}")
            return {}
    
    def load_json(self, file_path: str) -> Dict[str, Any]:
        """Load a JSON configuration file."""
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Warning: Configuration file {file_path} not found")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file {file_path}: {e}")
            return {}
    
    def load_service_configs(self) -> Dict[str, Any]:
        """Load all service-specific configurations."""
        services_config = {}
        services_dir = Path(self.config_paths.services_dir)
        
        if not services_dir.exists():
            return services_config
            
        for config_file in services_dir.glob("*.yaml"):
            service_name = config_file.stem
            config = self.load_yaml(str(config_file))
            if config:
                services_config[service_name] = config
                
        return services_config
    
    def merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def substitute_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute environment variables in configuration values."""
        def substitute_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                default_value = None
                if ":" in env_var:
                    env_var, default_value = env_var.split(":", 1)
                return os.getenv(env_var, default_value)
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value
        
        return substitute_value(config)
    
    def load_complete_config(self) -> Dict[str, Any]:
        """Load and merge all configuration files."""
        # Start with unified application configuration
        config = self.load_yaml(self.config_paths.application_config)
        
        # Apply environment-specific overrides from the unified config
        env_overrides = config.get("environments", {}).get(self.environment, {})
        if env_overrides:
            config = self.merge_configs(config, env_overrides)
        
        # Load environment-specific configuration file if it exists
        env_config_path = self.config_paths.environment_config.format(environment=self.environment)
        env_config = self.load_yaml(env_config_path)
        if env_config:
            config = self.merge_configs(config, env_config)
        
        # Load service configurations
        services_config = self.load_service_configs()
        if services_config:
            if "services" not in config:
                config["services"] = {}
            config["services"].update(services_config)
        
        # Load feature flags
        feature_flags = self.load_json(self.config_paths.feature_flags)
        if feature_flags:
            config["feature_flags"] = feature_flags
        
        # Load LLM configuration
        llm_config = self.load_json(self.config_paths.llm_config)
        if llm_config:
            if "llm" in config:
                config["llm"] = self.merge_configs(config["llm"], llm_config)
            else:
                config["llm"] = llm_config
        
        # Load monitoring configuration
        monitoring_config = self.load_yaml(self.config_paths.monitoring_config)
        if monitoring_config:
            config["monitoring"] = self.merge_configs(
                config.get("monitoring", {}), 
                monitoring_config
            )
        
        # Substitute environment variables
        config = self.substitute_environment_variables(config)
        
        # Add environment metadata
        config["_metadata"] = {
            "environment": self.environment,
            "loaded_at": str(Path.cwd()),
            "config_files": {
                "application": self.config_paths.application_config,
                "environment": env_config_path,
                "services": self.config_paths.services_dir,
                "feature_flags": self.config_paths.feature_flags,
                "llm": self.config_paths.llm_config,
                "monitoring": self.config_paths.monitoring_config,
                "alembic": self.config_paths.alembic_config,
                "pytest": self.config_paths.pytest_config
            }
        }
        
        return config
    
    def get_config(self, reload: bool = False) -> Dict[str, Any]:
        """Get the complete configuration, with optional caching."""
        cache_key = f"config_{self.environment}"
        
        if not reload and cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        config = self.load_complete_config()
        self._config_cache[cache_key] = config
        
        return config
    
    def get_backend_config(self) -> Dict[str, Any]:
        """Get backend-specific configuration."""
        config = self.get_config()
        
        # Extract backend-related configuration from unified config
        backend_config = {
            "api": config.get("api", {}),
            "database": config.get("database", {}),
            "vector_db": config.get("vector_db", {}),
            "ai": config.get("ai", {}),
            "task_routing": config.get("task_routing", {}),
            "security": config.get("security", {}),
            "cache": config.get("cache", {}),
            "background_tasks": config.get("background_tasks", {}),
            "storage": config.get("storage", {}),
            "external_services": config.get("external_services", {}),
            "monitoring": config.get("monitoring", {}),
            "logging": config.get("logging", {}),
            "features": config.get("features", {})
        }
        
        return backend_config
    
    def get_frontend_config(self) -> Dict[str, Any]:
        """Get frontend-specific configuration."""
        config = self.get_config()
        
        # Extract frontend-related configuration from unified config
        frontend_config = config.get("frontend", {})
        
        return frontend_config
    
    def get_deployment_config(self) -> Dict[str, Any]:
        """Get deployment-specific configuration."""
        config = self.get_config()
        
        # Extract deployment-related configuration from unified config
        deployment_config = config.get("deployment", {})
        
        return deployment_config
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service."""
        config = self.get_config()
        service_config = config.get("services", {}).get(service_name, {})
        
        # Apply environment-specific overrides
        env_overrides = service_config.get("environments", {}).get(self.environment, {})
        if env_overrides:
            service_config = self.merge_configs(service_config, env_overrides)
        
        return service_config
    
    def get_feature_flags(self) -> Dict[str, Any]:
        """Get feature flags configuration."""
        config = self.get_config()
        return config.get("feature_flags", {})
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a specific feature is enabled."""
        feature_flags = self.get_feature_flags()
        feature_config = feature_flags.get("flags", {}).get(feature_name, {})
        
        if not feature_config:
            return False
        
        state = feature_config.get("state", "disabled")
        default_value = feature_config.get("default_value", False)
        
        if state == "enabled":
            return True
        elif state == "disabled":
            return False
        elif state == "rollout":
            # Handle rollout logic (simplified)
            rollout_config = feature_config.get("rollout_config", {})
            strategy = rollout_config.get("strategy", "percentage")
            
            if strategy == "environment":
                environments = rollout_config.get("environments", [])
                return self.environment in environments
            elif strategy == "percentage":
                # For simplicity, always return default_value for percentage rollouts
                return default_value
            else:
                return default_value
        else:
            return default_value
    
    def validate_config(self) -> List[str]:
        """Validate the configuration and return any issues."""
        issues = []
        config = self.get_config()
        
        # Check required environment variables
        required_env_vars = [
            "OPENAI_API_KEY",
            "DATABASE_URL",
            "JWT_SECRET_KEY"
        ]
        
        for env_var in required_env_vars:
            if not os.getenv(env_var):
                issues.append(f"Required environment variable {env_var} is not set")
        
        # Check database configuration
        db_config = config.get("database", {})
        if not db_config.get("url"):
            issues.append("Database URL is not configured")
        
        # Check AI configuration
        ai_config = config.get("ai", {})
        if not ai_config:
            issues.append("AI configuration is missing")
        
        # Check external services configuration
        external_services = config.get("external_services", {})
        for service, service_config in external_services.items():
            if service_config.get("enabled", False):
                # Check if required credentials are available
                if service == "docusign" and not os.getenv("DOCUSIGN_SANDBOX_CLIENT_ID"):
                    issues.append(f"DocuSign is enabled but credentials are missing")
                elif service == "slack" and not os.getenv("SLACK_WEBHOOK_URL"):
                    issues.append(f"Slack is enabled but webhook URL is missing")
                elif service == "gmail" and not os.getenv("GMAIL_CLIENT_ID"):
                    issues.append(f"Gmail is enabled but credentials are missing")
        
        # Validate configuration file references
        config_files = config.get("_metadata", {}).get("config_files", {})
        for config_type, config_path in config_files.items():
            if config_type != "services" and not Path(config_path).exists():
                issues.append(f"Configuration file {config_path} does not exist")
        
        return issues
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        config = self.get_config()
        
        return {
            "environment": self.environment,
            "loaded_files": list(config.get("_metadata", {}).get("config_files", {}).values()),
            "services_count": len(config.get("services", {})),
            "feature_flags_count": len(config.get("feature_flags", {}).get("flags", {})),
            "enabled_features": [
                name for name, flag in config.get("feature_flags", {}).get("flags", {}).items()
                if self.is_feature_enabled(name)
            ],
            "external_services": {
                name: service.get("enabled", False)
                for name, service in config.get("external_services", {}).items()
            },
            "validation_issues": self.validate_config()
        }


# Global configuration loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(environment: Optional[str] = None) -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    
    if _config_loader is None or (environment and _config_loader.environment != environment):
        _config_loader = ConfigLoader(environment)
    
    return _config_loader


def get_config(reload: bool = False) -> Dict[str, Any]:
    """Get the complete application configuration."""
    loader = get_config_loader()
    return loader.get_config(reload=reload)


def get_backend_config() -> Dict[str, Any]:
    """Get backend-specific configuration."""
    loader = get_config_loader()
    return loader.get_backend_config()


def get_frontend_config() -> Dict[str, Any]:
    """Get frontend-specific configuration."""
    loader = get_config_loader()
    return loader.get_frontend_config()


def get_deployment_config() -> Dict[str, Any]:
    """Get deployment-specific configuration."""
    loader = get_config_loader()
    return loader.get_deployment_config()


def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get configuration for a specific service."""
    loader = get_config_loader()
    return loader.get_service_config(service_name)


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a specific feature is enabled."""
    loader = get_config_loader()
    return loader.is_feature_enabled(feature_name)


def validate_configuration() -> List[str]:
    """Validate the current configuration."""
    loader = get_config_loader()
    return loader.validate_config()


def get_config_summary() -> Dict[str, Any]:
    """Get a summary of the current configuration."""
    loader = get_config_loader()
    return loader.get_config_summary()


# Environment detection helpers
def is_development() -> bool:
    """Check if running in development environment."""
    return os.getenv("ENVIRONMENT", "development") == "development"


def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv("ENVIRONMENT", "development") == "production"


def is_staging() -> bool:
    """Check if running in staging environment."""
    return os.getenv("ENVIRONMENT", "development") == "staging"


def is_testing() -> bool:
    """Check if running in testing environment."""
    return os.getenv("ENVIRONMENT", "development") == "testing"