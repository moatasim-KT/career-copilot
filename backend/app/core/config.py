"""Application configuration using pydantic-settings"""

from functools import lru_cache
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Application
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    debug: bool = True
    
    # Database
    database_url: str = "sqlite:///./data/career_copilot.db"
    
    # Security
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8501"
    
    # AI/LLM (optional)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    
    # Email (optional)
    smtp_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@career-copilot.local"
    sendgrid_api_key: str = ""
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Feature flags
    enable_caching: bool = True
    enable_analytics: bool = True
    enable_scheduler: bool = True
    
    # Job Scraping
    job_api_key: str = ""
    enable_job_scraping: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file
    
    def validate_required(self):
        """Validate required configuration on startup"""
        if self.environment == "production":
            if self.jwt_secret_key == "change-this-in-production":
                raise ValueError("JWT_SECRET_KEY must be changed in production")
            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters")


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_required()
    return settings
