"""
Configuration Validation System
Provides comprehensive validation for all configuration settings with helpful error messages.
"""

import os
import re
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse

import logging

logger = logging.getLogger(__name__)


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


class ConfigurationValidator:
    """Comprehensive configuration validator."""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.config = config_data
        self.report = ValidationReport(is_valid=True)
    
    def validate_all(self) -> ValidationReport:
        """Run all validation checks."""
        logger.info("Running comprehensive configuration validation...")
        
        # Core validation
        self._validate_required_settings()
        self._validate_api_configuration()
        self._validate_database_configuration()
        
        # Service validation
        self._validate_ai_services()
        self._validate_external_services()
        self._validate_storage_services()
        self._validate_communication_services()
        
        # Security validation
        self._validate_security_settings()
        
        # Performance validation
        self._validate_performance_settings()
        
        # File and directory validation
        self._validate_file_paths()
        
        # Set overall validity
        self.report.is_valid = len(self.report.errors) == 0
        
        logger.info(f"Validation completed: {len(self.report.errors)} errors, {len(self.report.warnings)} warnings")
        return self.report
    
    def _add_issue(self, level: str, category: str, key: str, message: str, 
                   suggestion: Optional[str] = None, doc_url: Optional[str] = None):
        """Add a validation issue to the report."""
        issue = ValidationIssue(
            level=level,
            category=category,
            key=key,
            message=message,
            suggestion=suggestion,
            documentation_url=doc_url
        )
        self.report.issues.append(issue)
    
    def _get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def _validate_required_settings(self):
        """Validate required configuration settings."""
        required_settings = {
            "OPENAI_API_KEY": {
                "message": "OpenAI API key is required for AI-powered job application tracking",
                "suggestion": "Get your API key at https://platform.openai.com/api-keys",
                "validation": lambda x: x and x.startswith("sk-")
            },
            "API_HOST": {
                "message": "API host must be specified",
                "suggestion": "Use '0.0.0.0' for all interfaces or '127.0.0.1' for localhost only",
                "validation": lambda x: x and isinstance(x, str)
            },
            "API_PORT": {
                "message": "API port must be specified",
                "suggestion": "Use a port between 1024-65535 (e.g., 8000)",
                "validation": lambda x: x and (isinstance(x, int) or (isinstance(x, str) and x.isdigit())) and 1024 <= int(x) <= 65535
            }
        }
        
        for key, config in required_settings.items():
            value = self._get_value(key)
            
            if not value:
                self._add_issue(
                    "error", "missing", key,
                    config["message"],
                    config["suggestion"]
                )
            elif "validation" in config and not config["validation"](value):
                self._add_issue(
                    "error", "invalid", key,
                    f"Invalid value for {key}: {value}",
                    config["suggestion"]
                )
    
    def _validate_api_configuration(self):
        """Validate API configuration."""
        # Validate API host
        api_host = self._get_value("API_HOST")
        if api_host:
            if api_host not in ["0.0.0.0", "127.0.0.1", "localhost"] and not self._is_valid_ip(api_host):
                self._add_issue(
                    "warning", "invalid", "API_HOST",
                    f"API host '{api_host}' may not be accessible",
                    "Use '0.0.0.0' for all interfaces or a valid IP address"
                )
        
        # Validate API port
        api_port = self._get_value("API_PORT")
        if api_port:
            if not isinstance(api_port, int):
                try:
                    api_port = int(api_port)
                except (ValueError, TypeError):
                    self._add_issue(
                        "error", "invalid", "API_PORT",
                        f"API port must be a number, got: {api_port}",
                        "Use a number between 1024-65535"
                    )
                    return
            
            if api_port < 1024:
                self._add_issue(
                    "warning", "security", "API_PORT",
                    f"API port {api_port} requires root privileges",
                    "Use a port >= 1024 for non-root deployment"
                )
            elif api_port > 65535:
                self._add_issue(
                    "error", "invalid", "API_PORT",
                    f"API port {api_port} is out of valid range",
                    "Use a port between 1-65535"
                )
        
        # Validate CORS origins
        cors_origins = self._get_value("CORS_ORIGINS", "")
        if cors_origins == "*":
            self._add_issue(
                "warning", "security", "CORS_ORIGINS",
                "CORS allows all origins - security risk in production",
                "Specify exact origins like 'http://localhost:8501'"
            )
    
    def _validate_database_configuration(self):
        """Validate database configuration."""
        database_url = self._get_value("DATABASE_URL")
        
        if not database_url:
            # Check for SQLite configuration
            sqlite_path = self._get_value("SQLITE_DATABASE_PATH")
            if sqlite_path:
                self._validate_sqlite_config(sqlite_path)
            else:
                self._add_issue(
                    "error", "missing", "DATABASE_URL",
                    "No database configuration found",
                    "Set DATABASE_URL or SQLITE_DATABASE_PATH"
                )
        else:
            self._validate_database_url(database_url)
    
    def _validate_sqlite_config(self, sqlite_path: str):
        """Validate SQLite configuration."""
        path = Path(sqlite_path)
        
        # Check if directory exists
        if not path.parent.exists():
            self._add_issue(
                "warning", "invalid", "SQLITE_DATABASE_PATH",
                f"SQLite directory does not exist: {path.parent}",
                f"Create directory: mkdir -p {path.parent}"
            )
        
        # Check write permissions
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            test_file = path.parent / ".write_test"
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            self._add_issue(
                "error", "invalid", "SQLITE_DATABASE_PATH",
                f"No write permission for SQLite directory: {path.parent}",
                f"Fix permissions: chmod 755 {path.parent}"
            )
    
    def _validate_database_url(self, database_url: str):
        """Validate database URL format."""
        try:
            parsed = urlparse(database_url)
            
            if parsed.scheme not in ["sqlite", "sqlite+aiosqlite", "postgresql", "postgresql+asyncpg", "mysql"]:
                self._add_issue(
                    "warning", "invalid", "DATABASE_URL",
                    f"Unsupported database scheme: {parsed.scheme}",
                    "Use sqlite, postgresql, or mysql"
                )
            
            if parsed.scheme.startswith("sqlite"):
                # Validate SQLite path
                db_path = database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
                if db_path.startswith("./"):
                    db_path = db_path[2:]
                self._validate_sqlite_config(db_path)
                
        except Exception as e:
            self._add_issue(
                "error", "invalid", "DATABASE_URL",
                f"Invalid database URL format: {e}",
                "Example: sqlite+aiosqlite:///./data/app.db"
            )
    
    def _validate_ai_services(self):
        """Validate AI service configurations."""
        # OpenAI validation
        openai_key = self._get_value("OPENAI_API_KEY")
        if openai_key:
            if not openai_key.startswith("sk-"):
                self._add_issue(
                    "error", "invalid", "OPENAI_API_KEY",
                    "OpenAI API key format is invalid",
                    "API keys should start with 'sk-'"
                )
            elif len(openai_key) < 20:
                self._add_issue(
                    "warning", "invalid", "OPENAI_API_KEY",
                    "OpenAI API key appears to be too short",
                    "Verify your API key is complete"
                )
            
            self.report.services_status["openai"] = "configured"
        else:
            self.report.services_status["openai"] = "missing"
        
        # Groq validation
        groq_key = self._get_value("GROQ_API_KEY")
        groq_enabled = self._get_value("GROQ_ENABLED", False)
        
        if groq_enabled and not groq_key:
            self._add_issue(
                "error", "missing", "GROQ_API_KEY",
                "Groq is enabled but API key is missing",
                "Get your API key at https://console.groq.com/keys"
            )
        elif groq_key:
            if not groq_key.startswith("gsk_"):
                self._add_issue(
                    "warning", "invalid", "GROQ_API_KEY",
                    "Groq API key format may be invalid",
                    "Groq API keys typically start with 'gsk_'"
                )
            self.report.services_status["groq"] = "configured"
        else:
            self.report.services_status["groq"] = "disabled"
    
    def _validate_external_services(self):
        """Validate external service configurations."""
        # DocuSign validation
        self._validate_docusign_config()
        
        # LangSmith validation
        self._validate_langsmith_config()
    
    def _validate_docusign_config(self):
        """Validate DocuSign configuration."""
        docusign_enabled = self._get_value("DOCUSIGN_ENABLED", False)
        sandbox_enabled = self._get_value("DOCUSIGN_SANDBOX_ENABLED", False)
        
        if docusign_enabled or sandbox_enabled:
            prefix = "DOCUSIGN_SANDBOX_" if sandbox_enabled else "DOCUSIGN_"
            
            required_keys = ["CLIENT_ID", "CLIENT_SECRET"]
            for key in required_keys:
                full_key = f"{prefix}{key}"
                if not self._get_value(full_key):
                    self._add_issue(
                        "error", "missing", full_key,
                        f"DocuSign {key.lower().replace('_', ' ')} is required when DocuSign is enabled",
                        "Get credentials at https://developers.docusign.com/"
                    )
            
            self.report.services_status["docusign"] = "configured" if all(
                self._get_value(f"{prefix}{key}") for key in required_keys
            ) else "incomplete"
        else:
            self.report.services_status["docusign"] = "disabled"
    
    def _validate_langsmith_config(self):
        """Validate LangSmith configuration."""
        langsmith_tracing = self._get_value("LANGSMITH_TRACING", False)
        langsmith_key = self._get_value("LANGSMITH_API_KEY")
        
        if langsmith_tracing and not langsmith_key:
            self._add_issue(
                "warning", "missing", "LANGSMITH_API_KEY",
                "LangSmith tracing is enabled but API key is missing",
                "Get your API key at https://smith.langchain.com/settings"
            )
        elif langsmith_key:
            if not langsmith_key.startswith("lsv2_"):
                self._add_issue(
                    "warning", "invalid", "LANGSMITH_API_KEY",
                    "LangSmith API key format may be invalid",
                    "LangSmith API keys typically start with 'lsv2_'"
                )
            self.report.services_status["langsmith"] = "configured"
        else:
            self.report.services_status["langsmith"] = "disabled"
    
    def _validate_storage_services(self):
        """Validate storage service configurations."""
        # Google Drive validation
        gdrive_enabled = self._get_value("GOOGLE_DRIVE_ENABLED", False)
        if gdrive_enabled:
            required_keys = ["GOOGLE_DRIVE_CLIENT_ID", "GOOGLE_DRIVE_CLIENT_SECRET"]
            for key in required_keys:
                if not self._get_value(key):
                    self._add_issue(
                        "error", "missing", key,
                        f"Google Drive {key.split('_')[-1].lower()} is required when Google Drive is enabled",
                        "Get credentials at https://console.cloud.google.com/apis/credentials"
                    )
            
            self.report.services_status["google_drive"] = "configured" if all(
                self._get_value(key) for key in required_keys
            ) else "incomplete"
        else:
            self.report.services_status["google_drive"] = "disabled"
    
    def _validate_communication_services(self):
        """Validate communication service configurations."""
        # Slack validation
        slack_enabled = self._get_value("SLACK_ENABLED", False)
        if slack_enabled:
            webhook_url = self._get_value("SLACK_WEBHOOK_URL")
            bot_token = self._get_value("SLACK_BOT_TOKEN")
            
            if not webhook_url and not bot_token:
                self._add_issue(
                    "error", "missing", "SLACK_WEBHOOK_URL",
                    "Slack is enabled but no webhook URL or bot token is configured",
                    "Get webhook URL at https://api.slack.com/messaging/webhooks"
                )
            elif webhook_url and not webhook_url.startswith("https://hooks.slack.com/"):
                self._add_issue(
                    "warning", "invalid", "SLACK_WEBHOOK_URL",
                    "Slack webhook URL format may be invalid",
                    "Webhook URLs should start with 'https://hooks.slack.com/'"
                )
            
            self.report.services_status["slack"] = "configured" if (webhook_url or bot_token) else "incomplete"
        else:
            self.report.services_status["slack"] = "disabled"
        
        # Gmail/SMTP validation
        smtp_enabled = self._get_value("SMTP_ENABLED", False)
        gmail_enabled = self._get_value("GMAIL_ENABLED", False)
        
        if smtp_enabled or gmail_enabled:
            if smtp_enabled:
                required_keys = ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"]
                for key in required_keys:
                    if not self._get_value(key):
                        self._add_issue(
                            "warning", "missing", key,
                            f"SMTP {key.split('_')[-1].lower()} is missing",
                            "Configure SMTP settings for email notifications"
                        )
            
            self.report.services_status["email"] = "configured" if smtp_enabled else "incomplete"
        else:
            self.report.services_status["email"] = "disabled"
    
    def _validate_security_settings(self):
        """Validate security configuration."""
        # JWT secret validation
        jwt_secret = self._get_value("JWT_SECRET_KEY")
        if jwt_secret:
            if jwt_secret == "your-secret-key-change-in-production":
                self._add_issue(
                    "error", "security", "JWT_SECRET_KEY",
                    "Default JWT secret key is being used",
                    "Generate a secure random key for production"
                )
            elif len(jwt_secret) < 32:
                self._add_issue(
                    "warning", "security", "JWT_SECRET_KEY",
                    "JWT secret key is too short",
                    "Use at least 32 characters for security"
                )
        
        # API key validation
        api_key_secret = self._get_value("API_KEY_SECRET")
        if not api_key_secret:
            self._add_issue(
                "warning", "security", "API_KEY_SECRET",
                "No API key secret configured",
                "Set API_KEY_SECRET for API authentication"
            )
        
        # Debug mode validation
        api_debug = self._get_value("API_DEBUG", False)
        environment = self._get_value("ENVIRONMENT", "development")
        
        # Convert string boolean to actual boolean
        if isinstance(api_debug, str):
            api_debug = api_debug.lower() in ['true', '1', 'yes', 'on']
        
        if api_debug and environment == "production":
            self._add_issue(
                "error", "security", "API_DEBUG",
                "Debug mode is enabled in production",
                "Set API_DEBUG=false for production deployment"
            )
    
    def _validate_performance_settings(self):
        """Validate performance-related settings."""
        # File size limits
        max_file_size = self._get_value("MAX_FILE_SIZE_MB", 50)
        if isinstance(max_file_size, (int, float)):
            if max_file_size > 100:
                self._add_issue(
                    "warning", "performance", "MAX_FILE_SIZE_MB",
                    f"Large file size limit: {max_file_size}MB",
                    "Consider reducing for better performance"
                )
            elif max_file_size <= 0:
                self._add_issue(
                    "error", "invalid", "MAX_FILE_SIZE_MB",
                    "File size limit must be positive",
                    "Set a reasonable limit like 50MB"
                )
        
        # Worker configuration
        max_workers = self._get_value("MAX_WORKERS", 4)
        if isinstance(max_workers, int) and max_workers > 8:
            self._add_issue(
                "warning", "performance", "MAX_WORKERS",
                f"High worker count: {max_workers}",
                "Monitor resource usage with high worker counts"
            )
    
    def _validate_file_paths(self):
        """Validate file paths and directories."""
        # Check data directory
        data_paths = [
            self._get_value("CHROMA_PERSIST_DIRECTORY", "data/chroma"),
            self._get_value("STORAGE_PATH", "data/storage"),
            "./logs"
        ]
        
        for path_str in data_paths:
            if path_str:
                # Convert absolute paths that start with /app to relative paths
                if path_str.startswith("/backend/app/"):
                    path_str = "." + path_str[4:]
                elif path_str.startswith("/app"):
                    path_str = "." + path_str[4:]
                
                path = Path(path_str)
                
                # Only try to create if it's a relative path or in current directory
                if not path.is_absolute() or str(path).startswith(str(Path.cwd())):
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                    except PermissionError:
                        self._add_issue(
                            "error", "invalid", "FILE_PERMISSIONS",
                            f"Cannot create directory: {path}",
                            f"Fix permissions: mkdir -p {path} && chmod 755 {path}"
                        )
                    except OSError as e:
                        if "Read-only file system" in str(e):
                            # Skip validation for read-only file systems
                            continue
                        else:
                            self._add_issue(
                                "warning", "invalid", "FILE_PATHS",
                                f"Cannot access directory: {path} - {e}",
                                f"Check if path is correct: {path}"
                            )
                else:
                    # Just check if absolute path exists, don't try to create
                    if not path.exists():
                        self._add_issue(
                            "warning", "invalid", "FILE_PATHS",
                            f"Directory does not exist: {path}",
                            f"Create directory: mkdir -p {path}"
                        )
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if string is a valid IP address."""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def get_formatted_report(self) -> str:
        """Get a formatted validation report."""
        lines = []
        
        # Header
        if self.report.is_valid:
            lines.append("✅ Configuration validation passed")
        else:
            lines.append("❌ Configuration validation failed")
        
        # Summary
        error_count = len(self.report.errors)
        warning_count = len(self.report.warnings)
        info_count = len(self.report.info)
        
        lines.append(f"📊 Summary: {error_count} errors, {warning_count} warnings, {info_count} info")
        
        # Errors
        if self.report.errors:
            lines.append(f"\n❌ Errors ({error_count}):")
            for issue in self.report.errors:
                lines.append(f"   • {issue.key}: {issue.message}")
                if issue.suggestion:
                    lines.append(f"     💡 {issue.suggestion}")
        
        # Warnings
        if self.report.warnings:
            lines.append(f"\n⚠️  Warnings ({warning_count}):")
            for issue in self.report.warnings:
                lines.append(f"   • {issue.key}: {issue.message}")
                if issue.suggestion:
                    lines.append(f"     💡 {issue.suggestion}")
        
        # Service status
        if self.report.services_status:
            lines.append("\n🔌 Service Status:")
            for service, status in self.report.services_status.items():
                status_icon = {
                    "configured": "✅",
                    "incomplete": "⚠️",
                    "disabled": "⏸️",
                    "missing": "❌"
                }.get(status, "❓")
                lines.append(f"   {status_icon} {service.title()}: {status}")
        
        return "\n".join(lines)


def validate_configuration(config_data: Dict[str, Any]) -> ValidationReport:
    """Validate configuration and return report."""
    validator = ConfigurationValidator(config_data)
    return validator.validate_all()


def validate_and_report(config_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate configuration and return success status and formatted report."""
    validator = ConfigurationValidator(config_data)
    report = validator.validate_all()
    return report.is_valid, validator.get_formatted_report()