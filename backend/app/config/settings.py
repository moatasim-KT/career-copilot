from pathlib import Path
from typing import Optional

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	# Application Settings
	environment: Optional[str] = "development"
	api_host: Optional[str] = "0.0.0.0"
	api_port: Optional[int] = 8002
	debug: Optional[bool] = True

	# Database Configuration
	database_url: Optional[str] = "sqlite:///./data/career_copilot.db"

	# Authentication & Security
	jwt_secret_key: Optional[SecretStr] = None
	jwt_secret_file: Optional[Path] = Path("secrets/jwt_secret.txt")
	jwt_algorithm: Optional[str] = "HS256"
	jwt_expiration_hours: Optional[int] = 24
	disable_auth: Optional[bool] = False

	# AI/LLM Service API Keys
	openai_api_key: Optional[str] = None
	anthropic_api_key: Optional[str] = None
	groq_api_key: Optional[str] = None

	# Email & Notifications
	smtp_enabled: Optional[bool] = False
	smtp_host: Optional[str] = "smtp.gmail.com"
	smtp_port: Optional[int] = 587
	smtp_username: Optional[str] = None
	smtp_password: Optional[SecretStr] = None
	smtp_use_tls: Optional[bool] = True
	smtp_from_email: Optional[str] = "noreply@career-copilot.com"
	sendgrid_api_key: Optional[SecretStr] = None

	# Task Scheduling & Automation
	enable_scheduler: Optional[bool] = True
	enable_job_scraping: Optional[bool] = False
	job_api_key: Optional[str] = None
	adzuna_app_id: Optional[str] = None
	adzuna_app_key: Optional[str] = None
	adzuna_country: Optional[str] = "us"
	adzuna_country: Optional[str] = "us"

	# LinkedIn API Configuration
	linkedin_api_client_id: Optional[str] = None
	linkedin_api_client_secret: Optional[str] = None
	linkedin_api_access_token: Optional[str] = None

	# Indeed API Configuration
	indeed_publisher_id: Optional[str] = None
	indeed_api_key: Optional[str] = None

	# Glassdoor API Configuration
	glassdoor_partner_id: Optional[str] = None
	glassdoor_api_key: Optional[str] = None

	# Celery Configuration
	celery_broker_url: Optional[str] = "redis://localhost:6379/0"
	celery_result_backend: Optional[str] = "redis://localhost:6379/0"

	# Logging Settings
	log_level: Optional[str] = "INFO"

	# Caching Settings
	enable_redis_caching: Optional[bool] = True
	redis_url: Optional[str] = "redis://localhost:6379/1"

	# CORS Settings
	cors_origins: Optional[str] = "http://localhost:3000,http://localhost:8000"

	# OAuth Social Authentication
	oauth_enabled: Optional[bool] = False
	firebase_project_id: Optional[str] = None
	firebase_service_account_key: Optional[str] = None

	# Google OAuth Configuration
	google_client_id: Optional[str] = None
	google_client_secret: Optional[str] = None
	google_redirect_uri: Optional[str] = "http://localhost:8002/api/v1/auth/oauth/google/callback"

	# LinkedIn OAuth Configuration
	linkedin_client_id: Optional[str] = None
	linkedin_client_secret: Optional[str] = None
	linkedin_redirect_uri: Optional[str] = "http://localhost:8002/api/v1/auth/oauth/linkedin/callback"

	# GitHub OAuth Configuration
	github_client_id: Optional[str] = None
	github_client_secret: Optional[str] = None
	github_redirect_uri: Optional[str] = "http://localhost:8002/api/v1/auth/oauth/github/callback"

	# Job Matching Configuration
	high_match_threshold: Optional[float] = 80.0
	medium_match_threshold: Optional[float] = 60.0
	instant_alert_threshold: Optional[float] = 85.0

	@model_validator(mode="after")
	def _ensure_jwt_secret(self) -> "Settings":
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

	model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
	return Settings()
