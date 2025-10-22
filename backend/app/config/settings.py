from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
from pydantic import model_validator

class Settings(BaseSettings):
    # Application Settings
    environment: Optional[str] = "development"
    api_host: Optional[str] = "0.0.0.0"
    api_port: Optional[int] = 8002
    debug: Optional[bool] = True

    # Database Configuration
    database_url: Optional[str] = "sqlite:///./data/career_copilot.db"

    # Authentication & Security
    jwt_secret_key: Optional[str] = "your-super-secret-key-min-32-chars"
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
    smtp_username: Optional[str] = "your-email@example.com"
    smtp_password: Optional[str] = "your-email-password"
    smtp_from_email: Optional[str] = "noreply@career-copilot.com"
    sendgrid_api_key: Optional[str] = None

    # Task Scheduling & Automation
    enable_scheduler: Optional[bool] = True
    enable_job_scraping: Optional[bool] = False
    job_api_key: Optional[str] = None
    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None
    adzuna_country: Optional[str] = "us"
    
    # Celery Configuration
    celery_broker_url: Optional[str] = "redis://localhost:6379/0"
    celery_result_backend: Optional[str] = "redis://localhost:6379/0"

    # Logging Settings
    log_level: Optional[str] = "INFO"
    
    # CORS Settings
    cors_origins: Optional[str] = "http://localhost:3000,http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

def get_settings() -> Settings:
    return Settings()
