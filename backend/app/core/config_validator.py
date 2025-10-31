"""
Configuration Validation System for Career Copilot

This module provides a comprehensive, unified configuration validation system.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationIssue:
    """Represents a configuration validation issue."""
    level: str
    category: str
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

class ConfigurationValidator:
    """Comprehensive configuration validator."""
    def __init__(self, config_data: Dict[str, Any]):
        self.config = config_data
        self.report = ValidationReport(is_valid=True)

    def validate_all(self) -> ValidationReport:
        logger.info("Running comprehensive configuration validation...")
        self._validate_required_settings()
        self._validate_api_configuration()
        self._validate_database_configuration()
        self._validate_ai_services()
        self._validate_security_settings()
        self.report.is_valid = len(self.report.errors) == 0
        logger.info(f"Validation completed: {len(self.report.errors)} errors, {len(self.report.warnings)} warnings")
        return self.report

    def _add_issue(self, level: str, category: str, key: str, message: str, suggestion: Optional[str] = None, doc_url: Optional[str] = None):
        issue = ValidationIssue(level=level, category=category, key=key, message=message, suggestion=suggestion, documentation_url=doc_url)
        self.report.issues.append(issue)

    def _get_value(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def _validate_required_settings(self):
        required_settings = {
            "OPENAI_API_KEY": {
                "message": "OpenAI API key is required for AI-powered job application tracking",
                "suggestion": "Get your API key at https://platform.openai.com/api-keys",
                "validation": lambda x: x and x.startswith("sk-"),
            },
            "API_HOST": {
                "message": "API host must be specified",
                "suggestion": "Use '0.0.0.0' for all interfaces or '127.0.0.1' for localhost only",
                "validation": lambda x: x and isinstance(x, str),
            },
            "API_PORT": {
                "message": "API port must be specified",
                "suggestion": "Use a port between 1024-65535 (e.g., 8000)",
                "validation": lambda x: x and (isinstance(x, int) or (isinstance(x, str) and x.isdigit())) and 1024 <= int(x) <= 65535,
            },
        }
        for key, config in required_settings.items():
            value = self._get_value(key)
            if not value:
                self._add_issue("error", "missing", key, config["message"], config["suggestion"])
            elif "validation" in config and not config["validation"](value):
                self._add_issue("error", "invalid", key, f"Invalid value for {key}: {value}", config["suggestion"])

    def _validate_api_configuration(self):
        api_host = self._get_value("API_HOST")
        if api_host and api_host not in ["0.0.0.0", "127.0.0.1", "localhost"]:
            self._add_issue("warning", "invalid", "API_HOST", f"API host '{api_host}' may not be accessible", "Use '0.0.0.0' for all interfaces or a valid IP address")
        api_port = self._get_value("API_PORT")
        if api_port:
            if not isinstance(api_port, int):
                try:
                    api_port = int(api_port)
                except (ValueError, TypeError):
                    self._add_issue("error", "invalid", "API_PORT", f"API port must be a number, got: {api_port}", "Use a number between 1024-65535")
                    return
            if api_port < 1024:
                self._add_issue("warning", "security", "API_PORT", f"API port {api_port} requires root privileges", "Use a port >= 1024 for non-root deployment")
            elif api_port > 65535:
                self._add_issue("error", "invalid", "API_PORT", f"API port {api_port} is out of valid range", "Use a port between 1-65535")

    def _validate_database_configuration(self):
        database_url = self._get_value("DATABASE_URL")
        if not database_url:
            self._add_issue("error", "missing", "DATABASE_URL", "No database configuration found", "Set DATABASE_URL")
        else:
            try:
                parsed = urlparse(database_url)
                if parsed.scheme not in ["sqlite", "sqlite+aiosqlite", "postgresql", "postgresql+asyncpg", "mysql"]:
                    self._add_issue("warning", "invalid", "DATABASE_URL", f"Unsupported database scheme: {parsed.scheme}", "Use sqlite, postgresql, or mysql")
            except Exception as e:
                self._add_issue("error", "invalid", "DATABASE_URL", f"Invalid database URL format: {e}", "Example: sqlite+aiosqlite:///./data/app.db")

    def _validate_ai_services(self):
        openai_key = self._get_value("OPENAI_API_KEY")
        if openai_key:
            if not openai_key.startswith("sk-"):
                self._add_issue("error", "invalid", "OPENAI_API_KEY", "OpenAI API key format is invalid", "API keys should start with 'sk-'")
            self.report.services_status["openai"] = "configured"
        else:
            self.report.services_status["openai"] = "missing"

    def _validate_security_settings(self):
        jwt_secret = self._get_value("JWT_SECRET_KEY")
        if jwt_secret:
            if jwt_secret == "your-secret-key-change-in-production":
                self._add_issue("error", "security", "JWT_SECRET_KEY", "Default JWT secret key is being used", "Generate a secure random key for production")
            elif len(jwt_secret) < 32:
                self._add_issue("warning", "security", "JWT_SECRET_KEY", "JWT secret key is too short", "Use at least 32 characters for security")