"""Application configuration using pydantic-settings"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List, Literal, Optional
import os
import logging


# Configure basic logging for config module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be configured via environment variables.
    See .env.example for documentation of each setting.
    """
    
    # --- Application Settings ---
    environment: Literal["development", "production", "testing"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    debug: bool = True  # Controls FastAPI docs and detailed error messages
    api_debug: bool = True
    
    # --- Database Configuration ---
    database_url: str = "sqlite:///./data/career_copilot.db"
    
    # --- Security Settings ---
    jwt_secret_key: str = "your-super-secret-key-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    disable_auth: bool = False  # For testing purposes
    
    # --- CORS Configuration ---
    cors_origins: str = "http://localhost:8501,http://localhost:3000"  # Comma-separated list
    
    # --- AI/LLM Service API Keys (Optional) ---
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    
    # --- Email Notification Settings (Optional) ---
    smtp_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""  # Changed from smtp_username for consistency
    smtp_username: str = ""  # Keep for backward compatibility
    smtp_password: str = ""
    smtp_from_email: str = "noreply@career-copilot.com"
    sendgrid_api_key: str = ""
    
    # --- Scheduler Settings ---
    enable_scheduler: bool = True
    
    # --- Job Scraping Settings ---
    enable_job_scraping: bool = False
    job_api_key: str = ""
    
    # --- Logging Settings ---
    log_level: Literal["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: str = "logs/app.log"
    
    # --- Feature Flags ---
    enable_caching: bool = True
    enable_analytics: bool = True
    
    # --- Celery Settings ---
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = False  # Environment variables are case-insensitive
        extra = "ignore"  # Ignore extra fields from .env file
    
    def get_smtp_user(self) -> str:
        """Get SMTP username, supporting both smtp_user and smtp_username"""
        return self.smtp_user or self.smtp_username
    
    def validate_required(self) -> None:
        """
        Validate required configuration on startup.
        
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        errors = []
        
        # Validate JWT configuration
        if not self.jwt_secret_key:
            errors.append("JWT_SECRET_KEY is required")
        elif self.jwt_secret_key == "your-super-secret-key-min-32-chars":
            if self.environment == "production":
                errors.append("JWT_SECRET_KEY must be changed in production")
            else:
                logger.warning("⚠️  Using default JWT_SECRET_KEY - change this in production!")
        elif len(self.jwt_secret_key) < 32:
            errors.append("JWT_SECRET_KEY must be at least 32 characters")
        
        # Validate database configuration
        if not self.database_url:
            errors.append("DATABASE_URL is required")
        
        # Production-specific validations
        if self.environment == "production":
            if self.debug:
                logger.warning("⚠️  DEBUG is enabled in production - consider disabling for security")
            
            if "sqlite" in self.database_url.lower():
                logger.warning("⚠️  Using SQLite in production - consider PostgreSQL for better performance")
        
        # Validate SMTP configuration if enabled
        if self.smtp_enabled:
            smtp_user = self.get_smtp_user()
            if not self.smtp_host:
                errors.append("SMTP_HOST is required when SMTP_ENABLED is True")
            if not smtp_user:
                errors.append("SMTP_USER is required when SMTP_ENABLED is True")
            if not self.smtp_password:
                errors.append("SMTP_PASSWORD is required when SMTP_ENABLED is True")
            if not self.smtp_from_email:
                errors.append("SMTP_FROM_EMAIL is required when SMTP_ENABLED is True")
        
        # Validate job scraping configuration if enabled
        if self.enable_job_scraping:
            if not self.job_api_key:
                errors.append("JOB_API_KEY is required when ENABLE_JOB_SCRAPING is True")
        
        # Raise all validation errors together
        if errors:
            error_message = "Configuration validation failed:\n  - " + "\n  - ".join(errors)
            raise ValueError(error_message)
    
    def log_configuration_summary(self) -> None:
        """Log a summary of the current configuration on startup"""
        logger.info("=" * 80)
        logger.info("Career Co-Pilot Configuration Summary")
        logger.info("=" * 80)
        
        # Application settings
        logger.info(f"Environment: {self.environment}")
        logger.info(f"API Server: {self.api_host}:{self.api_port}")
        logger.info(f"Debug Mode: {self.debug}")
        
        # Database
        db_type = "SQLite" if "sqlite" in self.database_url.lower() else "PostgreSQL"
        logger.info(f"Database: {db_type}")
        
        # Security
        logger.info(f"JWT Algorithm: {self.jwt_algorithm}")
        logger.info(f"JWT Expiration: {self.jwt_expiration_hours} hours")
        
        # Features
        logger.info(f"Scheduler: {'✓ Enabled' if self.enable_scheduler else '✗ Disabled'}")
        logger.info(f"Job Scraping: {'✓ Enabled' if self.enable_job_scraping else '✗ Disabled'}")
        logger.info(f"Email Notifications: {'✓ Enabled' if self.smtp_enabled else '✗ Disabled'}")
        logger.info(f"Caching: {'✓ Enabled' if self.enable_caching else '✗ Disabled'}")
        logger.info(f"Analytics: {'✓ Enabled' if self.enable_analytics else '✗ Disabled'}")
        
        # Optional services
        if self.smtp_enabled:
            logger.info(f"SMTP Server: {self.smtp_host}:{self.smtp_port}")
            logger.info(f"SMTP From: {self.smtp_from_email}")
        
        if self.enable_job_scraping:
            logger.info(f"Job API: {'✓ Configured' if self.job_api_key else '✗ Not configured'}")
        
        # AI Services
        ai_services = []
        if self.openai_api_key:
            ai_services.append("OpenAI")
        if self.anthropic_api_key:
            ai_services.append("Anthropic")
        if self.groq_api_key:
            ai_services.append("Groq")
        
        if ai_services:
            logger.info(f"AI Services: {', '.join(ai_services)}")
        
        # Logging
        logger.info(f"Log Level: {self.log_level}")
        logger.info(f"Log File: {self.log_file}")
        
        logger.info("=" * 80)
    
    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings singleton.
    
    Settings are loaded from environment variables and validated.
    This function is cached to ensure settings are loaded only once.
    
    Returns:
        Settings: The application settings instance
        
    Raises:
        ValueError: If required configuration is missing or invalid
    """
    settings = Settings()
    settings.validate_required()
    settings.log_configuration_summary()
    return settings
