"""
Configuration management for the Career Copilot application.
Handles environment variables and application settings.
"""

import os
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	"""Application settings loaded from environment variables."""

	model_config = {"extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}

	# Environment Configuration
	environment: str = Field(default="development", env="ENVIRONMENT")
	production_mode: bool = Field(default=False, env="PRODUCTION_MODE")
	development_mode: bool = Field(default=True, env="DEVELOPMENT_MODE")

	# API Configuration
	api_host: str = Field(default="0.0.0.0", env="API_HOST")
	api_port: int = Field(default=8000, env="API_PORT")
	api_debug: bool = Field(default=False, env="API_DEBUG")
	
	# Authentication Configuration
	disable_auth: bool = Field(default=False, env="DISABLE_AUTH")
	
	# Firebase Configuration
	firebase_project_id: Optional[str] = Field(default=None, env="FIREBASE_PROJECT_ID")
	firebase_service_account_key: Optional[str] = Field(default=None, env="FIREBASE_SERVICE_ACCOUNT_KEY")
	firebase_web_api_key: Optional[str] = Field(default=None, env="FIREBASE_WEB_API_KEY")
	firebase_auth_domain: Optional[str] = Field(default=None, env="FIREBASE_AUTH_DOMAIN")
	firebase_enabled: bool = Field(default=False, env="FIREBASE_ENABLED")

	# OpenAI Configuration
	openai_api_key: SecretStr = Field(..., env="OPENAI_API_KEY")
	openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
	openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")

	# GROQ Configuration
	groq_api_key: Optional[SecretStr] = Field(default=None, env="GROQ_API_KEY")
	groq_model: str = Field(default="mixtral-8x7b-32768", env="GROQ_MODEL")
	groq_temperature: float = Field(default=0.1, env="GROQ_TEMPERATURE")
	groq_enabled: bool = Field(default=False, env="GROQ_ENABLED")

	# Ollama Configuration
	ollama_enabled: bool = Field(default=False, env="OLLAMA_ENABLED")
	ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
	ollama_model: str = Field(default="llama2", env="OLLAMA_MODEL")
	ollama_temperature: float = Field(default=0.1, env="OLLAMA_TEMPERATURE")
	ollama_max_tokens: int = Field(default=4000, env="OLLAMA_MAX_TOKENS")

	# Database Configuration
	database_url: Optional[str] = Field(default=None, env="DATABASE_URL")

	# ChromaDB Configuration
	chroma_persist_directory: str = Field(default="data/chroma", env="CHROMA_PERSIST_DIRECTORY")
	chroma_collection_name: str = Field(default="precedent_clauses", env="CHROMA_COLLECTION_NAME")

	# Redis Configuration
	enable_redis_caching: bool = Field(default=True, env="ENABLE_REDIS_CACHING")
	redis_host: str = Field(default="localhost", env="REDIS_HOST")
	redis_port: int = Field(default=6379, env="REDIS_PORT")
	redis_db: int = Field(default=0, env="REDIS_DB")
	redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
	redis_max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
	redis_socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
	redis_socket_connect_timeout: int = Field(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")

	# LangSmith Configuration (Optional)
	langsmith_api_key: Optional[str] = Field(default=None, env="LANGSMITH_API_KEY")
	langsmith_project: str = Field(default="career-copilot", env="LANGSMITH_PROJECT")
	langsmith_tracing: bool = Field(default=False, env="LANGSMITH_TRACING")

	# Gmail Configuration
	gmail_client_id: Optional[str] = Field(default=None, env="GMAIL_CLIENT_ID")
	gmail_client_secret: Optional[str] = Field(default=None, env="GMAIL_CLIENT_SECRET")
	gmail_redirect_uri: Optional[str] = Field(default=None, env="GMAIL_REDIRECT_URI")
	gmail_scopes: str = Field(default="https://www.googleapis.com/auth/gmail.send", env="GMAIL_SCOPES")
	gmail_enabled: bool = Field(default=False, env="GMAIL_ENABLED")
	gmail_rate_limit_seconds: int = Field(default=5, env="GMAIL_RATE_LIMIT_SECONDS")
	gmail_daily_quota_limit: int = Field(default=100, env="GMAIL_DAILY_QUOTA_LIMIT")
	gmail_hourly_quota_limit: int = Field(default=20, env="GMAIL_HOURLY_QUOTA_LIMIT")
	gmail_max_attachment_size_mb: int = Field(default=25, env="GMAIL_MAX_ATTACHMENT_SIZE_MB")

	# SMTP Configuration
	smtp_enabled: bool = Field(default=False, env="SMTP_ENABLED")
	smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
	smtp_port: int = Field(default=587, env="SMTP_PORT")
	smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
	smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
	smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
	smtp_use_ssl: bool = Field(default=False, env="SMTP_USE_SSL")

	# Slack Configuration
	slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
	slack_bot_token: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")
	slack_default_channel: str = Field(default="#contracts", env="SLACK_DEFAULT_CHANNEL")
	slack_enabled: bool = Field(default=False, env="SLACK_ENABLED")

	# DocuSign Configuration
	docusign_client_id: Optional[str] = Field(default=None, env="DOCUSIGN_CLIENT_ID")
	docusign_client_secret: Optional[str] = Field(default=None, env="DOCUSIGN_CLIENT_SECRET")
	docusign_redirect_uri: Optional[str] = Field(default=None, env="DOCUSIGN_REDIRECT_URI")
	docusign_scopes: list = Field(default=["signature", "impersonation"], env="DOCUSIGN_SCOPES")
	docusign_enabled: bool = Field(default=False, env="DOCUSIGN_ENABLED")
	docusign_webhook_secret: Optional[str] = Field(default=None, env="DOCUSIGN_WEBHOOK_SECRET")
	docusign_webhook_url: Optional[str] = Field(default=None, env="DOCUSIGN_WEBHOOK_URL")
	docusign_max_retries: int = Field(default=3, env="DOCUSIGN_MAX_RETRIES")
	docusign_retry_delay: float = Field(default=1.0, env="DOCUSIGN_RETRY_DELAY")
	docusign_rate_limit: int = Field(default=1000, env="DOCUSIGN_RATE_LIMIT")
	docusign_timeout: float = Field(default=30.0, env="DOCUSIGN_TIMEOUT")

	# HubSpot Configuration
	hubspot_api_key: Optional[str] = Field(default=None, env="HUBSPOT_API_KEY")
	hubspot_enabled: bool = Field(default=False, env="HUBSPOT_ENABLED")

	# DocuSign Sandbox Configuration (for backward compatibility)
	docusign_sandbox_enabled: bool = Field(default=False, env="DOCUSIGN_SANDBOX_ENABLED")
	docusign_sandbox_client_id: Optional[str] = Field(default=None, env="DOCUSIGN_SANDBOX_CLIENT_ID")
	docusign_sandbox_client_secret: Optional[str] = Field(default=None, env="DOCUSIGN_SANDBOX_CLIENT_SECRET")
	docusign_sandbox_redirect_uri: Optional[str] = Field(default=None, env="DOCUSIGN_SANDBOX_REDIRECT_URI")
	docusign_sandbox_scopes: str = Field(default="signature,impersonation", env="DOCUSIGN_SANDBOX_SCOPES")
	docusign_sandbox_base_url: str = Field(default="https://demo.docusign.net/restapi", env="DOCUSIGN_SANDBOX_BASE_URL")

	# Google Drive Configuration
	google_drive_enabled: bool = Field(default=False, env="GOOGLE_DRIVE_ENABLED")
	google_drive_client_id: Optional[str] = Field(default=None, env="GOOGLE_DRIVE_CLIENT_ID")
	google_drive_client_secret: Optional[str] = Field(default=None, env="GOOGLE_DRIVE_CLIENT_SECRET")
	google_drive_redirect_uri: Optional[str] = Field(default=None, env="GOOGLE_DRIVE_REDIRECT_URI")
	google_drive_scopes: str = Field(default="https://www.googleapis.com/auth/drive.file", env="GOOGLE_DRIVE_SCOPES")

	# Cloud Storage Backup Configuration
	auto_backup_enabled: bool = Field(default=True, env="AUTO_BACKUP_ENABLED")
	backup_retention_days: int = Field(default=90, env="BACKUP_RETENTION_DAYS")
	max_backups_per_user: int = Field(default=100, env="MAX_BACKUPS_PER_USER")
	auto_cleanup_enabled: bool = Field(default=True, env="AUTO_CLEANUP_ENABLED")
	storage_quota_threshold: float = Field(default=85.0, env="STORAGE_QUOTA_THRESHOLD")
	backup_frequency_hours: int = Field(default=24, env="BACKUP_FREQUENCY_HOURS")
	default_backup_provider: str = Field(default="google_drive", env="DEFAULT_BACKUP_PROVIDER")

	# SQLite Configuration
	sqlite_database_path: str = Field(default="data/contract_analyzer.db", env="SQLITE_DATABASE_PATH")
	sqlite_enabled: bool = Field(default=True, env="SQLITE_ENABLED")

	# Monitoring Configuration
	enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
	enable_prometheus: bool = Field(default=True, env="ENABLE_PROMETHEUS")
	enable_opentelemetry: bool = Field(default=True, env="ENABLE_OPENTELEMETRY")
	metrics_port: int = Field(default=9090, env="METRICS_PORT")
	jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")
	otlp_endpoint: Optional[str] = Field(default=None, env="OTLP_ENDPOINT")

	# File Processing Configuration
	max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
	allowed_file_types: list[str] = Field(default=["pdf", "docx", "txt"], env="ALLOWED_FILE_TYPES")
	temp_file_cleanup_hours: int = Field(default=24, env="TEMP_FILE_CLEANUP_HOURS")

	# Security Configuration
	cors_origins: str = Field(default="http://localhost:8501", env="CORS_ORIGINS")
	api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
	
	# HTTPS Configuration
	enable_https: bool = Field(default=False, env="ENABLE_HTTPS")
	force_https: bool = Field(default=False, env="FORCE_HTTPS")

	# Enhanced Security Settings
	master_api_key: Optional[SecretStr] = Field(default=None, env="MASTER_API_KEY")
	client_api_keys: Optional[str] = Field(default=None, env="CLIENT_API_KEYS")
	jwt_secret_key: SecretStr = Field(default="your-secret-key-change-in-production", env="JWT_SECRET_KEY")
	jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
	jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

	# Rate Limiting
	rate_limit_requests_per_minute: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
	rate_limit_burst: int = Field(default=200, env="RATE_LIMIT_BURST")
	api_key_rate_limit_per_hour: int = Field(default=1000, env="API_KEY_RATE_LIMIT_PER_HOUR")

	# File Security
	max_file_size_bytes: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE_BYTES")  # 50MB
	allowed_mime_types: list[str] = Field(
		default=["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain", "text/csv"], env="ALLOWED_MIME_TYPES"
	)
	scan_uploaded_files: bool = Field(default=True, env="SCAN_UPLOADED_FILES")
	quarantine_suspicious_files: bool = Field(default=True, env="QUARANTINE_SUSPICIOUS_FILES")

	# Input Validation
	max_input_length: int = Field(default=10000, env="MAX_INPUT_LENGTH")
	enable_input_sanitization: bool = Field(default=True, env="ENABLE_INPUT_SANITIZATION")
	strict_validation: bool = Field(default=True, env="STRICT_VALIDATION")

	# Audit and Monitoring
	enable_audit_logging: bool = Field(default=True, env="ENABLE_AUDIT_LOGGING")
	audit_log_retention_days: int = Field(default=90, env="AUDIT_LOG_RETENTION_DAYS")
	security_alert_webhook: Optional[str] = Field(default=None, env="SECURITY_ALERT_WEBHOOK")
	audit_log_file: Optional[str] = Field(default="logs/audit.log", env="AUDIT_LOG_FILE")
	security_log_file: Optional[str] = Field(default="logs/security.log", env="SECURITY_LOG_FILE")

	# Session Security
	session_timeout_minutes: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
	secure_cookies: bool = Field(default=True, env="SECURE_COOKIES")

	# Encryption
	encryption_key: Optional[SecretStr] = Field(default=None, env="ENCRYPTION_KEY")
	encrypt_temp_files: bool = Field(default=True, env="ENCRYPT_TEMP_FILES")

	# IP Security
	allowed_ip_ranges: Optional[str] = Field(default=None, env="ALLOWED_IP_RANGES")
	blocked_ip_addresses: Optional[str] = Field(default=None, env="BLOCKED_IP_ADDRESSES")

	# Content Security Policy
	enable_csp: bool = Field(default=True, env="ENABLE_CSP")
	csp_report_uri: Optional[str] = Field(default=None, env="CSP_REPORT_URI")

	# Logging Configuration
	log_level: str = Field(default="INFO", env="LOG_LEVEL")
	log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
	log_file: Optional[str] = Field(default="logs/app.log", env="LOG_FILE")

	# Configuration moved to model_config above


# Global settings instance
_settings_instance: Optional["Settings"] = None


def get_settings() -> "Settings":
	"""Get the application settings instance (singleton)."""
	global _settings_instance
	if _settings_instance is None:
		_settings_instance = Settings()
	return _settings_instance


# Create settings instance
settings = get_settings()


def validate_required_settings() -> None:
	"""Validate that all required settings are present with environment-specific validation."""
	current_settings = get_settings()
	
	# Environment-specific validation
	if current_settings.environment == "production":
		validate_production_settings(current_settings)
	elif current_settings.environment == "development":
		validate_development_settings(current_settings)
	else:
		validate_basic_settings(current_settings)


def validate_production_settings(settings: Settings) -> None:
	"""Validate production-specific settings."""
	print("🔍 Validating production configuration...")
	
	required_settings = [
		("OPENAI_API_KEY", settings.openai_api_key),
		("JWT_SECRET_KEY", settings.jwt_secret_key),
		("DATABASE_URL", settings.database_url or settings.sqlite_database_path),
	]
	
	missing_settings = []
	for setting_name, setting_value in required_settings:
		if not setting_value or (hasattr(setting_value, 'get_secret_value') and not setting_value.get_secret_value()):
			missing_settings.append(setting_name)
	
	if missing_settings:
		raise ValueError(f"Missing required production environment variables: {', '.join(missing_settings)}")
	
	# Production-specific warnings
	warnings = []
	if settings.api_debug:
		warnings.append("API_DEBUG should be false in production")
	if settings.development_mode:
		warnings.append("DEVELOPMENT_MODE should be false in production")
	if not settings.production_mode:
		warnings.append("PRODUCTION_MODE should be true in production")
	
	if warnings:
		print("⚠️  Production configuration warnings:")
		for warning in warnings:
			print(f"   - {warning}")
	
	print("✅ Production configuration validation passed")


def validate_development_settings(settings: Settings) -> None:
	"""Validate development-specific settings."""
	print("🔍 Validating development configuration...")
	
	required_settings = [
		("OPENAI_API_KEY", settings.openai_api_key),
	]
	
	missing_settings = []
	for setting_name, setting_value in required_settings:
		if not setting_value or (hasattr(setting_value, 'get_secret_value') and not setting_value.get_secret_value()):
			missing_settings.append(setting_name)
	
	if missing_settings:
		raise ValueError(f"Missing required development environment variables: {', '.join(missing_settings)}")
	
	print("✅ Development configuration validation passed")


def validate_basic_settings(settings: Settings) -> None:
	"""Validate basic settings for any environment."""
	print("🔍 Validating basic configuration...")
	
	required_settings = [
		("OPENAI_API_KEY", settings.openai_api_key),
	]
	
	missing_settings = []
	for setting_name, setting_value in required_settings:
		if not setting_value or (hasattr(setting_value, 'get_secret_value') and not setting_value.get_secret_value()):
			missing_settings.append(setting_name)
	
	if missing_settings:
		raise ValueError(f"Missing required environment variables: {', '.join(missing_settings)}")
	
	print("✅ Basic configuration validation passed")


def setup_langsmith() -> None:
	"""Set up LangSmith tracing if configured."""
	current_settings = get_settings()
	if current_settings.langsmith_tracing and current_settings.langsmith_api_key:
		os.environ["LANGCHAIN_TRACING_V2"] = "true"
		os.environ["LANGCHAIN_API_KEY"] = current_settings.langsmith_api_key
		os.environ["LANGCHAIN_PROJECT"] = current_settings.langsmith_project
