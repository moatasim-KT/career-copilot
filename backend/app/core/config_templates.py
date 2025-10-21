"""
Configuration templates for different deployment modes.

This module provides pre-configured templates for various deployment scenarios
to ensure consistent and optimized configurations across environments.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .config_manager import DeploymentMode, ConfigFormat
import logging

# Use standard logging if custom logging module is not available
try:
    from .logging import get_logger
except ImportError:
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


@dataclass
class ConfigTemplate:
    """Configuration template definition."""
    name: str
    description: str
    deployment_mode: DeploymentMode
    config_data: Dict[str, Any]
    required_env_vars: List[str]
    optional_env_vars: List[str]
    recommendations: List[str]


class ConfigTemplateManager:
    """Manager for configuration templates."""
    
    def __init__(self):
        self.templates: Dict[str, ConfigTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize all configuration templates."""
        self._create_development_template()
        self._create_testing_template()
        self._create_staging_template()
        self._create_production_template()
        self._create_docker_template()
        self._create_kubernetes_template()
        self._create_native_template()
    
    def _create_development_template(self):
        """Create development environment template."""
        config_data = {
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
                "debug": True,
                "reload": True,
                "workers": 1
            },
            "database": {
                "url": "sqlite+aiosqlite:///./data/contract_analyzer_dev.db",
                "echo": True,
                "pool_size": 5,
                "max_overflow": 10
            },
            "redis": {
                "enabled": False,
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/dev.log"
            },
            "security": {
                "cors_origins": ["http://localhost:8501", "http://127.0.0.1:8501"],
                "rate_limiting": False,
                "audit_logging": False
            },
            "ai": {
                "openai": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                "fallback_enabled": False
            },
            "monitoring": {
                "enabled": False,
                "prometheus": False,
                "tracing": False
            },
            "file_processing": {
                "max_size_mb": 10,
                "temp_cleanup_hours": 1
            }
        }
        
        template = ConfigTemplate(
            name="development",
            description="Development environment with debugging enabled",
            deployment_mode=DeploymentMode.DEVELOPMENT,
            config_data=config_data,
            required_env_vars=["OPENAI_API_KEY"],
            optional_env_vars=["LANGSMITH_API_KEY", "SLACK_WEBHOOK_URL"],
            recommendations=[
                "Use SQLite for local development",
                "Enable debug mode for detailed error messages",
                "Disable Redis for simplicity",
                "Use smaller file size limits for testing"
            ]
        )
        
        self.templates["development"] = template
    
    def _create_testing_template(self):
        """Create testing environment template."""
        config_data = {
            "api": {
                "host": "127.0.0.1",
                "port": 8001,
                "debug": False,
                "reload": False,
                "workers": 1
            },
            "database": {
                "url": "sqlite+aiosqlite:///./data/test.db",
                "echo": False,
                "pool_size": 2,
                "max_overflow": 5
            },
            "redis": {
                "enabled": False,
                "host": "localhost",
                "port": 6379,
                "db": 1
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/test.log"
            },
            "security": {
                "cors_origins": ["http://localhost:8501"],
                "rate_limiting": True,
                "audit_logging": True
            },
            "ai": {
                "openai": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.0,
                    "max_tokens": 1000
                },
                "fallback_enabled": True
            },
            "monitoring": {
                "enabled": True,
                "prometheus": False,
                "tracing": False
            },
            "file_processing": {
                "max_size_mb": 5,
                "temp_cleanup_hours": 1
            }
        }
        
        template = ConfigTemplate(
            name="testing",
            description="Testing environment for automated tests",
            deployment_mode=DeploymentMode.TESTING,
            config_data=config_data,
            required_env_vars=["OPENAI_API_KEY"],
            optional_env_vars=[],
            recommendations=[
                "Use separate test database",
                "Enable rate limiting for realistic testing",
                "Use deterministic AI settings (temperature=0)",
                "Enable monitoring for test metrics"
            ]
        )
        
        self.templates["testing"] = template
    
    def _create_staging_template(self):
        """Create staging environment template."""
        config_data = {
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "reload": False,
                "workers": 2
            },
            "database": {
                "url": "${DATABASE_URL}",
                "echo": False,
                "pool_size": 10,
                "max_overflow": 20
            },
            "redis": {
                "enabled": True,
                "host": "${REDIS_HOST}",
                "port": 6379,
                "db": 0,
                "password": "${REDIS_PASSWORD}"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/staging.log"
            },
            "security": {
                "cors_origins": ["${FRONTEND_URL}"],
                "rate_limiting": True,
                "audit_logging": True
            },
            "ai": {
                "openai": {
                    "model": "gpt-4",
                    "temperature": 0.1,
                    "max_tokens": 4000
                },
                "fallback_enabled": True
            },
            "monitoring": {
                "enabled": True,
                "prometheus": True,
                "tracing": True
            },
            "file_processing": {
                "max_size_mb": 50,
                "temp_cleanup_hours": 24
            }
        }
        
        template = ConfigTemplate(
            name="staging",
            description="Staging environment for pre-production testing",
            deployment_mode=DeploymentMode.STAGING,
            config_data=config_data,
            required_env_vars=[
                "OPENAI_API_KEY", "DATABASE_URL", "REDIS_HOST", "FRONTEND_URL"
            ],
            optional_env_vars=[
                "REDIS_PASSWORD", "LANGSMITH_API_KEY", "SLACK_WEBHOOK_URL",
                "DOCUSIGN_CLIENT_ID", "GMAIL_CLIENT_ID"
            ],
            recommendations=[
                "Use production-like database (PostgreSQL)",
                "Enable Redis for caching",
                "Enable full monitoring stack",
                "Use production AI models",
                "Test all integrations"
            ]
        )
        
        self.templates["staging"] = template
    
    def _create_production_template(self):
        """Create production environment template."""
        config_data = {
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "reload": False,
                "workers": 4
            },
            "database": {
                "url": "${DATABASE_URL}",
                "echo": False,
                "pool_size": 20,
                "max_overflow": 40,
                "pool_timeout": 30,
                "pool_recycle": 3600
            },
            "redis": {
                "enabled": True,
                "host": "${REDIS_HOST}",
                "port": 6379,
                "db": 0,
                "password": "${REDIS_PASSWORD}",
                "max_connections": 50,
                "socket_timeout": 5
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/production.log",
                "rotation": "1 day",
                "retention": "30 days"
            },
            "security": {
                "cors_origins": ["${FRONTEND_URL}"],
                "rate_limiting": True,
                "audit_logging": True,
                "encryption_enabled": True,
                "secure_cookies": True
            },
            "ai": {
                "openai": {
                    "model": "gpt-4",
                    "temperature": 0.1,
                    "max_tokens": 4000
                },
                "groq": {
                    "enabled": True,
                    "model": "mixtral-8x7b-32768"
                },
                "fallback_enabled": True,
                "cost_optimization": True
            },
            "monitoring": {
                "enabled": True,
                "prometheus": True,
                "tracing": True,
                "alerting": True,
                "health_checks": True
            },
            "file_processing": {
                "max_size_mb": 100,
                "temp_cleanup_hours": 24,
                "virus_scanning": True
            },
            "backup": {
                "enabled": True,
                "frequency": "daily",
                "retention_days": 30
            }
        }
        
        template = ConfigTemplate(
            name="production",
            description="Production environment with full security and monitoring",
            deployment_mode=DeploymentMode.PRODUCTION,
            config_data=config_data,
            required_env_vars=[
                "OPENAI_API_KEY", "DATABASE_URL", "REDIS_HOST", "REDIS_PASSWORD",
                "FRONTEND_URL", "JWT_SECRET_KEY", "ENCRYPTION_KEY"
            ],
            optional_env_vars=[
                "GROQ_API_KEY", "LANGSMITH_API_KEY", "SLACK_WEBHOOK_URL",
                "DOCUSIGN_CLIENT_ID", "GMAIL_CLIENT_ID", "HUBSPOT_API_KEY"
            ],
            recommendations=[
                "Use PostgreSQL with connection pooling",
                "Enable Redis with authentication",
                "Configure comprehensive monitoring",
                "Enable all security features",
                "Set up automated backups",
                "Use multiple AI providers for redundancy"
            ]
        )
        
        self.templates["production"] = template
    
    def _create_docker_template(self):
        """Create Docker deployment template."""
        config_data = {
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "reload": False,
                "workers": "${WORKERS:-2}"
            },
            "database": {
                "url": "${DATABASE_URL:-sqlite+aiosqlite:///./data/contract_analyzer.db}",
                "echo": False,
                "pool_size": 10,
                "max_overflow": 20
            },
            "redis": {
                "enabled": "${REDIS_ENABLED:-true}",
                "host": "${REDIS_HOST:-redis}",
                "port": 6379,
                "db": 0,
                "password": "${REDIS_PASSWORD}"
            },
            "logging": {
                "level": "${LOG_LEVEL:-INFO}",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None  # Use stdout in containers
            },
            "security": {
                "cors_origins": ["${FRONTEND_URL:-http://localhost:8501}"],
                "rate_limiting": True,
                "audit_logging": True
            },
            "ai": {
                "openai": {
                    "model": "${OPENAI_MODEL:-gpt-4}",
                    "temperature": 0.1,
                    "max_tokens": 4000
                },
                "fallback_enabled": True
            },
            "monitoring": {
                "enabled": True,
                "prometheus": True,
                "tracing": "${ENABLE_TRACING:-false}"
            },
            "file_processing": {
                "max_size_mb": "${MAX_FILE_SIZE_MB:-50}",
                "temp_cleanup_hours": 24
            }
        }
        
        template = ConfigTemplate(
            name="docker",
            description="Docker containerized deployment",
            deployment_mode=DeploymentMode.DOCKER,
            config_data=config_data,
            required_env_vars=["OPENAI_API_KEY"],
            optional_env_vars=[
                "DATABASE_URL", "REDIS_HOST", "REDIS_PASSWORD", "FRONTEND_URL",
                "WORKERS", "LOG_LEVEL", "OPENAI_MODEL", "MAX_FILE_SIZE_MB"
            ],
            recommendations=[
                "Use environment variables for configuration",
                "Log to stdout for container orchestration",
                "Use external Redis and database services",
                "Configure health checks",
                "Use multi-stage Docker builds"
            ]
        )
        
        self.templates["docker"] = template
    
    def _create_kubernetes_template(self):
        """Create Kubernetes deployment template."""
        config_data = {
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "reload": False,
                "workers": "${WORKERS:-4}"
            },
            "database": {
                "url": "${DATABASE_URL}",
                "echo": False,
                "pool_size": 15,
                "max_overflow": 30,
                "pool_timeout": 30
            },
            "redis": {
                "enabled": True,
                "host": "${REDIS_SERVICE_HOST}",
                "port": "${REDIS_SERVICE_PORT}",
                "db": 0,
                "password": "${REDIS_PASSWORD}"
            },
            "logging": {
                "level": "${LOG_LEVEL:-INFO}",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,  # Use stdout
                "structured": True
            },
            "security": {
                "cors_origins": ["${FRONTEND_URL}"],
                "rate_limiting": True,
                "audit_logging": True,
                "encryption_enabled": True
            },
            "ai": {
                "openai": {
                    "model": "${OPENAI_MODEL:-gpt-4}",
                    "temperature": 0.1,
                    "max_tokens": 4000
                },
                "fallback_enabled": True,
                "load_balancing": True
            },
            "monitoring": {
                "enabled": True,
                "prometheus": True,
                "tracing": True,
                "metrics_port": 9090,
                "health_port": 8080
            },
            "file_processing": {
                "max_size_mb": "${MAX_FILE_SIZE_MB:-100}",
                "temp_cleanup_hours": 24
            },
            "kubernetes": {
                "namespace": "${KUBERNETES_NAMESPACE:-default}",
                "service_account": "${SERVICE_ACCOUNT:-career-copilot}",
                "pod_name": "${HOSTNAME}",
                "node_name": "${NODE_NAME}"
            }
        }
        
        template = ConfigTemplate(
            name="kubernetes",
            description="Kubernetes orchestrated deployment",
            deployment_mode=DeploymentMode.KUBERNETES,
            config_data=config_data,
            required_env_vars=[
                "OPENAI_API_KEY", "DATABASE_URL", "REDIS_SERVICE_HOST",
                "REDIS_SERVICE_PORT", "FRONTEND_URL"
            ],
            optional_env_vars=[
                "REDIS_PASSWORD", "WORKERS", "LOG_LEVEL", "OPENAI_MODEL",
                "MAX_FILE_SIZE_MB", "KUBERNETES_NAMESPACE", "SERVICE_ACCOUNT"
            ],
            recommendations=[
                "Use Kubernetes secrets for sensitive data",
                "Configure resource limits and requests",
                "Use service discovery for internal communication",
                "Enable horizontal pod autoscaling",
                "Configure liveness and readiness probes",
                "Use persistent volumes for data storage"
            ]
        )
        
        self.templates["kubernetes"] = template
    
    def _create_native_template(self):
        """Create native deployment template."""
        config_data = {
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
                "debug": False,
                "reload": False,
                "workers": 2
            },
            "database": {
                "url": "postgresql://contract_user:${DB_PASSWORD}@localhost:5432/contract_analyzer",
                "echo": False,
                "pool_size": 10,
                "max_overflow": 20
            },
            "redis": {
                "enabled": True,
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": "${REDIS_PASSWORD}"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "/var/log/career-copilot/app.log",
                "rotation": "1 day",
                "retention": "30 days"
            },
            "security": {
                "cors_origins": ["http://localhost:8501"],
                "rate_limiting": True,
                "audit_logging": True,
                "file_permissions": "600"
            },
            "ai": {
                "openai": {
                    "model": "gpt-4",
                    "temperature": 0.1,
                    "max_tokens": 4000
                },
                "ollama": {
                    "enabled": True,
                    "base_url": "http://localhost:11434",
                    "model": "llama2"
                },
                "fallback_enabled": True
            },
            "monitoring": {
                "enabled": True,
                "prometheus": True,
                "tracing": False,
                "log_file": "/var/log/career-copilot/metrics.log"
            },
            "file_processing": {
                "max_size_mb": 50,
                "temp_cleanup_hours": 24,
                "storage_path": "/var/lib/career-copilot/files"
            },
            "systemd": {
                "service_name": "career-copilot",
                "user": "career-copilot",
                "group": "career-copilot"
            }
        }
        
        template = ConfigTemplate(
            name="native",
            description="Native system deployment with systemd",
            deployment_mode=DeploymentMode.NATIVE,
            config_data=config_data,
            required_env_vars=[
                "OPENAI_API_KEY", "DB_PASSWORD"
            ],
            optional_env_vars=[
                "REDIS_PASSWORD", "OLLAMA_ENABLED", "LANGSMITH_API_KEY"
            ],
            recommendations=[
                "Install PostgreSQL and Redis locally",
                "Create dedicated system user",
                "Configure systemd service",
                "Set up log rotation",
                "Configure firewall rules",
                "Use Ollama for local AI processing"
            ]
        )
        
        self.templates["native"] = template
    
    def get_template(self, name: str) -> Optional[ConfigTemplate]:
        """Get configuration template by name."""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self.templates.keys())
    
    def generate_config_file(self, template_name: str, output_path: Path, format: ConfigFormat = ConfigFormat.YAML) -> bool:
        """Generate configuration file from template."""
        template = self.get_template(template_name)
        if not template:
            logger.error(f"Template '{template_name}' not found")
            return False
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == ConfigFormat.YAML:
                with open(output_path, 'w') as f:
                    # Add header comment
                    f.write(f"# Configuration for {template.description}\n")
                    f.write(f"# Generated from template: {template_name}\n")
                    f.write(f"# Deployment mode: {template.deployment_mode.value}\n\n")
                    
                    # Write configuration data
                    yaml.dump(template.config_data, f, default_flow_style=False, indent=2)
                    
                    # Add footer with recommendations
                    f.write("\n# Configuration recommendations:\n")
                    for rec in template.recommendations:
                        f.write(f"# - {rec}\n")
                    
                    # Add required environment variables
                    f.write("\n# Required environment variables:\n")
                    for var in template.required_env_vars:
                        f.write(f"# - {var}\n")
                    
                    if template.optional_env_vars:
                        f.write("\n# Optional environment variables:\n")
                        for var in template.optional_env_vars:
                            f.write(f"# - {var}\n")
            
            logger.info(f"Generated configuration file: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate configuration file: {e}")
            return False
    
    def validate_template_requirements(self, template_name: str) -> Dict[str, List[str]]:
        """Validate that template requirements are met."""
        template = self.get_template(template_name)
        if not template:
            return {"errors": [f"Template '{template_name}' not found"]}
        
        import os
        
        missing_required = []
        missing_optional = []
        
        for var in template.required_env_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in template.optional_env_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        return {
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "recommendations": template.recommendations
        }


# Global template manager instance
_template_manager: Optional[ConfigTemplateManager] = None


def get_template_manager() -> ConfigTemplateManager:
    """Get the global template manager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = ConfigTemplateManager()
    return _template_manager


def generate_config_for_deployment(deployment_mode: DeploymentMode, config_dir: Path) -> bool:
    """Generate configuration files for a specific deployment mode."""
    template_manager = get_template_manager()
    template_name = deployment_mode.value
    
    # Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate main configuration file
    config_file = config_dir / f"{template_name}.yaml"
    success = template_manager.generate_config_file(template_name, config_file)
    
    if success:
        logger.info(f"Generated configuration for {deployment_mode.value} deployment")
        
        # Generate environment file template
        template = template_manager.get_template(template_name)
        if template:
            env_file = config_dir / f"{template_name}.env"
            _generate_env_template(template, env_file)
    
    return success


def _generate_env_template(template: ConfigTemplate, env_file: Path):
    """Generate environment file template."""
    try:
        with open(env_file, 'w') as f:
            f.write(f"# Environment variables for {template.description}\n")
            f.write(f"# Deployment mode: {template.deployment_mode.value}\n\n")
            
            f.write("# Required environment variables:\n")
            for var in template.required_env_vars:
                f.write(f"{var}=\n")
            
            if template.optional_env_vars:
                f.write("\n# Optional environment variables:\n")
                for var in template.optional_env_vars:
                    f.write(f"# {var}=\n")
            
            f.write(f"\n# Deployment mode\n")
            f.write(f"DEPLOYMENT_MODE={template.deployment_mode.value}\n")
        
        logger.info(f"Generated environment template: {env_file}")
        
    except Exception as e:
        logger.error(f"Failed to generate environment template: {e}")