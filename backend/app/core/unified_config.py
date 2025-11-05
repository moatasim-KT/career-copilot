"""
Unified Configuration Management

Consolidates all configuration management into a single Pydantic-based system.
Provides environment-specific settings, validation, and easy access to config values.

Usage:
    from backend.app.core.config import get_config, ConfigManager

    # Get settings
    settings = get_config()

    # Get specific value with default
    api_key = settings.get_value("openai_api_key", default=None)

    # Load environment-specific config
    config_manager = ConfigManager(environment="production")
    config = config_manager.load_config()
"""

import json
import os
import secrets
import string
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logging import get_logger

logger = get_logger(__name__)


class UnifiedSettings(BaseSettings):
	"""Unified application settings with Pydantic validation."""

	# ==================== Application Settings ====================
	environment: str = "development"
	api_host: str = "0.0.0.0"
	api_port: int = 8002
	debug: bool = True
	app_name: str = "Career Copilot"
	app_version: str = "1.0.0"

	# ==================== Database Configuration ====================
	database_url: str = "sqlite:///./data/career_copilot.db"
	database_pool_size: int = 10
	database_max_overflow: int = 20
	database_echo: bool = False

	# ==================== Authentication & Security ====================
	jwt_secret_key: Optional[SecretStr] = None
	jwt_secret_file: Path = Path("secrets/jwt_secret.txt")
	jwt_algorithm: str = "HS256"
	jwt_expiration_hours: int = 24
	disable_auth: bool = False
	password_min_length: int = 8
	session_timeout_minutes: int = 30

	# ==================== AI/LLM Service API Keys ====================
	openai_api_key: Optional[str] = None
	anthropic_api_key: Optional[str] = None
	groq_api_key: Optional[str] = None
	groq_api_key_file: Optional[Path] = Path("secrets/groq_api_key.txt")

	# Default LLM settings
	default_llm_provider: str = "groq"
	default_llm_model: str = "mixtral-8x7b-32768"
	llm_temperature: float = 0.7
	llm_max_tokens: int = 2000

	# ==================== Email & Notifications ====================
	smtp_enabled: bool = False
	smtp_host: str = "smtp.gmail.com"
	smtp_port: int = 587
	smtp_username: str = "your-email@example.com"
	smtp_password: Optional[str] = None
	smtp_use_tls: bool = True
	smtp_from_email: str = "noreply@career-copilot.com"
	sendgrid_api_key: Optional[str] = None

	notification_batch_size: int = 50
	notification_retry_max_attempts: int = 3
	notification_retry_delay_seconds: int = 60

	# ==================== Task Scheduling & Automation ====================
	enable_scheduler: bool = True
	enable_job_scraping: bool = False
	job_scraping_interval_hours: int = 24

	# Job Board API Keys
	job_api_key: Optional[str] = None
	adzuna_app_id: Optional[str] = None
	adzuna_app_key: Optional[str] = None
	adzuna_country: str = "us"
	linkedin_api_client_id: Optional[str] = None
	linkedin_api_client_secret: Optional[str] = None
	linkedin_api_access_token: Optional[str] = None
	indeed_publisher_id: Optional[str] = None
	indeed_api_key: Optional[str] = None
	glassdoor_partner_id: Optional[str] = None
	glassdoor_api_key: Optional[str] = None

	# The Muse API
	themuse_api_key: Optional[str] = None
	themuse_base_url: str = "https://www.themuse.com/api/public"

	# RapidAPI JSEarch
	rapidapi_jsearch_key: Optional[str] = None

	# ==================== Celery Configuration ====================
	celery_broker_url: str = "redis://localhost:6379/0"
	celery_result_backend: str = "redis://localhost:6379/0"
	celery_task_serializer: str = "json"
	celery_result_serializer: str = "json"
	celery_accept_content: List[str] = ["json"]
	celery_timezone: str = "UTC"
	celery_worker_concurrency: int = 4
	celery_worker_prefetch_multiplier: int = 4

	# ==================== Caching Settings ====================
	enable_redis_caching: bool = True
	redis_url: str = "redis://localhost:6379/1"
	redis_cache_ttl_seconds: int = 3600
	redis_max_connections: int = 50

	# ==================== Logging Settings ====================
	log_level: str = "INFO"
	log_format: str = "json"
	log_file: Optional[Path] = Path("logs/app/application.log")
	log_rotation_size_mb: int = 100
	log_retention_days: int = 30
	enable_audit_logging: bool = True

	# ==================== CORS Settings ====================
	cors_origins: List[str] | str = "http://localhost:3000,http://localhost:8000"
	cors_allow_credentials: bool = True
	cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
	cors_allow_headers: List[str] = ["*"]

	# ==================== OAuth Social Authentication ====================
	oauth_enabled: bool = False
	firebase_project_id: Optional[str] = None
	firebase_service_account_key: Optional[str] = None

	# Google OAuth
	google_client_id: Optional[str] = None
	google_client_secret: Optional[str] = None
	google_redirect_uri: str = "http://localhost:8002/api/v1/auth/oauth/google/callback"

	# LinkedIn OAuth
	linkedin_client_id: Optional[str] = None
	linkedin_client_secret: Optional[str] = None
	linkedin_redirect_uri: str = "http://localhost:8002/api/v1/auth/oauth/linkedin/callback"

	# GitHub OAuth
	github_client_id: Optional[str] = None
	github_client_secret: Optional[str] = None
	github_redirect_uri: str = "http://localhost:8002/api/v1/auth/oauth/github/callback"

	# ==================== Job Matching Configuration ====================
	high_match_threshold: float = 80.0
	medium_match_threshold: float = 60.0
	instant_alert_threshold: float = 85.0
	recommendation_batch_size: int = 10
	max_recommendations_per_user: int = 50

	# ==================== Storage Configuration ====================
	local_storage_path: str = "data/storage"
	max_file_size_mb: int = 100
	enable_file_versioning: bool = True
	file_cleanup_days: int = 90

	# Cloud storage
	enable_cloud_backup: bool = False
	backup_retention_days: int = 90
	storage_quota_threshold: float = 85.0

	# ==================== Vector Database Configuration ====================
	chroma_host: str = "localhost"
	chroma_port: int = 8000
	chroma_persist_directory: str = "data/chroma"
	embedding_model: str = "all-MiniLM-L6-v2"
	vector_search_top_k: int = 10

	# ==================== Rate Limiting ====================
	rate_limit_enabled: bool = True
	rate_limit_per_minute: int = 60
	rate_limit_per_hour: int = 1000

	# ==================== Feature Flags ====================
	enable_analytics: bool = True
	enable_recommendations: bool = True
	enable_notifications: bool = True
	enable_resume_parsing: bool = True
	enable_interview_practice: bool = True

	# ==================== Monitoring & Observability ====================
	enable_metrics: bool = True
	metrics_port: int = 9090
	prometheus_port: int = 9090
	enable_tracing: bool = False
	enable_opentelemetry: bool = False
	otlp_endpoint: str = "http://localhost:4317"
	service_name: str = "career-copilot-api"
	jaeger_endpoint: Optional[str] = None

	@field_validator("cors_origins", mode="before")
	@classmethod
	def split_cors_origins(cls, v: Any) -> List[str]:
		"""Convert comma-separated CORS origins to list."""
		if isinstance(v, str):
			return [origin.strip() for origin in v.split(",")]
		return v

	@model_validator(mode="after")
	def ensure_jwt_secret(self) -> "UnifiedSettings":
		"""Ensure JWT secret is loaded from environment or file."""
		secret = self.jwt_secret_key.get_secret_value() if self.jwt_secret_key else ""

		if not secret and self.jwt_secret_file:
			candidate_path = Path(self.jwt_secret_file).expanduser()
			if candidate_path.exists():
				candidate = candidate_path.read_text(encoding="utf-8").strip()
				if candidate:
					self.jwt_secret_key = SecretStr(candidate)
					secret = candidate

		if not secret:
			raise ValueError("JWT secret key must be supplied via JWT_SECRET_KEY environment variable or secrets/jwt_secret.txt")

		return self

	@model_validator(mode="after")
	def load_groq_api_key(self) -> "UnifiedSettings":
		"""Load Groq API key from file if not set via environment."""
		if not self.groq_api_key and self.groq_api_key_file:
			candidate_path = Path(self.groq_api_key_file).expanduser()
			if candidate_path.exists():
				self.groq_api_key = candidate_path.read_text(encoding="utf-8").strip()

		return self

	def get_value(self, key: str, default: Any = None) -> Any:
		"""Get configuration value with fallback to default.

		Args:
			key: Configuration key
			default: Default value if key not found

		Returns:
			Configuration value or default
		"""
		return getattr(self, key, default)

	def is_production(self) -> bool:
		"""Check if running in production environment."""
		return self.environment.lower() == "production"

	def is_development(self) -> bool:
		"""Check if running in development environment."""
		return self.environment.lower() == "development"

	def get_cors_origins_list(self) -> List[str]:
		"""Get CORS origins as a list."""
		if isinstance(self.cors_origins, str):
			return [origin.strip() for origin in self.cors_origins.split(",")]
		return self.cors_origins

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
		case_sensitive=False,
	)


class ConfigManager:
	"""Manages configuration loading and environment-specific overrides."""

	def __init__(self, environment: Optional[str] = None):
		"""Initialize configuration manager.

		Args:
			environment: Environment name (development, production, staging, testing)
		"""
		self.environment = environment or os.getenv("ENVIRONMENT", "development")
		self.project_root = Path(__file__).parent.parent.parent.parent.parent
		self.config_dir = self.project_root / "config"

	def load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
		"""Load YAML configuration file.

		Args:
			file_path: Path to YAML file

		Returns:
			Configuration dictionary
		"""
		try:
			if not file_path.exists():
				logger.warning(f"Configuration file not found: {file_path}")
				return {}

			with open(file_path, "r") as f:
				return yaml.safe_load(f) or {}

		except Exception as e:
			logger.error(f"Failed to load YAML file {file_path}: {e}")
			return {}

	def load_json_file(self, file_path: Path) -> Dict[str, Any]:
		"""Load JSON configuration file.

		Args:
			file_path: Path to JSON file

		Returns:
			Configuration dictionary
		"""
		try:
			if not file_path.exists():
				logger.warning(f"Configuration file not found: {file_path}")
				return {}

			with open(file_path, "r") as f:
				return json.load(f)

		except Exception as e:
			logger.error(f"Failed to load JSON file {file_path}: {e}")
			return {}

	def load_environment_config(self) -> Dict[str, Any]:
		"""Load environment-specific configuration.

		Returns:
			Environment configuration dictionary
		"""
		env_file = self.config_dir / "environments" / f"{self.environment}.yaml"
		return self.load_yaml_file(env_file)

	def load_feature_flags(self) -> Dict[str, Any]:
		"""Load feature flags configuration.

		Returns:
			Feature flags dictionary
		"""
		flags_file = self.config_dir / "feature_flags.json"
		return self.load_json_file(flags_file)

	def load_llm_config(self) -> Dict[str, Any]:
		"""Load LLM configuration.

		Returns:
			LLM configuration dictionary
		"""
		llm_file = self.config_dir / "llm_config.json"
		return self.load_json_file(llm_file)

	def load_config(self) -> Dict[str, Any]:
		"""Load complete configuration with environment overrides.

		Returns:
			Complete configuration dictionary
		"""
		# Load base application config
		app_config = self.load_yaml_file(self.config_dir / "application.yaml")

		# Load environment-specific overrides
		env_config = self.load_environment_config()

		# Load feature flags
		feature_flags = self.load_feature_flags()

		# Load LLM config
		llm_config = self.load_llm_config()

		# Merge configurations (environment overrides base)
		config = {**app_config, **env_config}

		# Add feature flags and LLM config
		config["feature_flags"] = feature_flags
		config["llm_config"] = llm_config

		return config

	def generate_secret_key(self, length: int = 32) -> str:
		"""Generate a secure random secret key.

		Args:
			length: Length of the secret key

		Returns:
			Random secret key string
		"""
		alphabet = string.ascii_letters + string.digits + string.punctuation
		return "".join(secrets.choice(alphabet) for _ in range(length))

	def setup_secrets(self, force: bool = False):
		"""Set up required secrets (JWT, API keys, etc.).

		Args:
			force: Force regeneration of existing secrets
		"""
		secrets_dir = self.project_root / "secrets"
		secrets_dir.mkdir(parents=True, exist_ok=True)

		# Set restrictive permissions
		os.chmod(secrets_dir, 0o700)

		# Generate JWT secret if needed
		jwt_secret_file = secrets_dir / "jwt_secret.txt"
		if force or not jwt_secret_file.exists():
			jwt_secret = self.generate_secret_key(64)
			jwt_secret_file.write_text(jwt_secret)
			os.chmod(jwt_secret_file, 0o600)
			logger.info("Generated new JWT secret")


# Global settings instance
_settings: Optional[UnifiedSettings] = None


def get_config() -> UnifiedSettings:
	"""Get global configuration instance.

	Returns:
		UnifiedSettings instance
	"""
	global _settings

	if _settings is None:
		_settings = UnifiedSettings()

	return _settings


def get_config_value(key: str, default: Any = None) -> Any:
	"""Convenience function to get a configuration value.

	Args:
		key: Configuration key
		default: Default value if key not found

	Returns:
		Configuration value or default

	Example:
		from backend.app.core.config import get_config_value

		api_key = get_config_value("openai_api_key")
		debug = get_config_value("debug", default=False)
	"""
	settings = get_config()
	return settings.get_value(key, default)


# Maintain backward compatibility with old imports
def get_settings() -> UnifiedSettings:
	"""Backward compatibility alias for get_config()."""
	return get_config()
