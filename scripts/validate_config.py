import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

def validate_config():
    logger.info("🚀 Starting Career Copilot Configuration Validation...")
    settings = get_settings()

    all_checks_passed = True

    logger.info("\n--- Environment Variables Check ---")
    # Check JWT_SECRET_KEY
    if settings.jwt_secret_key == "your-super-secret-jwt-key-change-in-production-min-32-chars":
        logger.error("❌ CRITICAL: JWT_SECRET_KEY is still the default value. Please change it in your .env file for security.")
        all_checks_passed = False
    else:
        logger.info("✅ JWT_SECRET_KEY is set.")

    # Check DATABASE_URL
    if not settings.database_url:
        logger.error("❌ CRITICAL: DATABASE_URL is not set in your .env file.")
        all_checks_passed = False
    else:
        logger.info(f"✅ DATABASE_URL: {settings.database_url}")

    # Check SMTP settings if enabled
    if settings.smtp_enabled:
        logger.info("\n--- SMTP Configuration Check ---")
        if not settings.smtp_host or not settings.smtp_port or not settings.smtp_username or not settings.smtp_password or not settings.smtp_from_email:
            logger.error("❌ WARNING: SMTP is enabled but some SMTP credentials are missing. Email notifications may fail.")
            all_checks_passed = False
        else:
            logger.info("✅ SMTP credentials are set.")
    else:
        logger.info("☑️ SMTP is disabled. Skipping SMTP configuration check.")

    # Check Job Scraping settings if enabled
    if settings.enable_job_scraping:
        logger.info("\n--- Job Scraping Configuration Check ---")
        if not settings.job_api_key and (not settings.adzuna_app_id or not settings.adzuna_app_key):
            logger.error("❌ WARNING: Job scraping is enabled but no API keys (JOB_API_KEY or ADZUNA_APP_ID/KEY) are configured. Job scraping may not work.")
            all_checks_passed = False
        else:
            logger.info("✅ Job scraping API keys are configured.")
    else:
        logger.info("☑️ Job scraping is disabled. Skipping job scraping configuration check.")

    logger.info("\n--- Database Connectivity Check ---")
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful.")
    except OperationalError as e:
        logger.error(f"❌ Database connection failed: {e}")
        all_checks_passed = False
    except Exception as e:
        logger.error(f"❌ Unexpected error during database connection check: {e}")
        all_checks_passed = False

    logger.info("\n--- Final Summary ---")
    if all_checks_passed:
        logger.info("✅ All critical configuration checks passed. Your application should start successfully.")
        sys.exit(0)
    else:
        logger.error("❌ Some critical configuration checks failed. Please review the warnings/errors above.")
        sys.exit(1)

if __name__ == "__main__":
    validate_config()
