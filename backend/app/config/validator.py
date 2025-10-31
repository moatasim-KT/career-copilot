"""
Configuration validation utilities.

Provides functions to validate and check configuration at runtime.
"""

import logging
from typing import Dict, Tuple
from ..core.config import Settings

logger = logging.getLogger(__name__)


def validate_database_connection(settings: Settings) -> Tuple[bool, str]:
	"""
	Validate database connection configuration.

	Args:
	    settings: Application settings

	Returns:
	    Tuple of (is_valid, message)
	"""
	try:
		if not settings.database_url:
			return False, "DATABASE_URL is not configured"

		# Check for common database URL patterns
		if settings.database_url.startswith("sqlite"):
			return True, "SQLite database configured"
		elif settings.database_url.startswith("postgresql"):
			return True, "PostgreSQL database configured"
		else:
			return True, f"Database configured: {settings.database_url.split(':')[0]}"

	except Exception as e:
		return False, f"Database validation error: {e!s}"


def validate_smtp_configuration(settings: Settings) -> Tuple[bool, str]:
	"""
	Validate SMTP configuration.

	Args:
	    settings: Application settings

	Returns:
	    Tuple of (is_valid, message)
	"""
	if not settings.smtp_enabled:
		return True, "SMTP is disabled"

	issues = []

	if not settings.smtp_host:
		issues.append("SMTP_HOST is missing")
	if not settings.smtp_username:
		issues.append("SMTP_USER is missing")
	if not settings.smtp_password:
		issues.append("SMTP_PASSWORD is missing")
	if not settings.smtp_from_email:
		issues.append("SMTP_FROM_EMAIL is missing")

	if issues:
		return False, f"SMTP configuration incomplete: {', '.join(issues)}"

	return True, "SMTP configuration is valid"


def validate_scheduler_configuration(settings: Settings) -> Tuple[bool, str]:
	"""
	Validate scheduler configuration.

	Args:
	    settings: Application settings

	Returns:
	    Tuple of (is_valid, message)
	"""
	if not settings.enable_scheduler:
		return True, "Scheduler is disabled"

	warnings = []

	# Check if job scraping is enabled but no API key
	if settings.enable_job_scraping and not settings.job_api_key:
		warnings.append("Job scraping enabled but JOB_API_KEY not configured")

	# Check if SMTP is needed for notifications
	if not settings.smtp_enabled and not settings.sendgrid_api_key:
		warnings.append("Scheduler enabled but email notifications not configured")

	if warnings:
		return True, f"Scheduler enabled with warnings: {'; '.join(warnings)}"

	return True, "Scheduler configuration is valid"


def validate_security_configuration(settings: Settings) -> Tuple[bool, str]:
	"""
	Validate security configuration.

	Args:
	    settings: Application settings

	Returns:
	    Tuple of (is_valid, message)
	"""
	issues = []
	warnings = []

	# Check JWT secret key
	if settings.jwt_secret_key == "your-super-secret-key-min-32-chars":
		if settings.environment == "production":
			issues.append("Default JWT_SECRET_KEY in production")
		else:
			warnings.append("Using default JWT_SECRET_KEY")

	if len(settings.jwt_secret_key) < 32:
		issues.append("JWT_SECRET_KEY is too short (minimum 32 characters)")

	# Check debug mode in production
	if settings.environment == "production" and settings.debug:
		warnings.append("Debug mode enabled in production")

	if issues:
		return False, f"Security issues: {', '.join(issues)}"

	if warnings:
		return True, f"Security warnings: {', '.join(warnings)}"

	return True, "Security configuration is valid"


def run_full_validation(settings: Settings) -> Dict[str, Tuple[bool, str]]:
	"""
	Run full configuration validation.

	Args:
	    settings: Application settings

	Returns:
	    Dictionary mapping component names to (is_valid, message) tuples
	"""
	results = {
		"database": validate_database_connection(settings),
		"smtp": validate_smtp_configuration(settings),
		"scheduler": validate_scheduler_configuration(settings),
		"security": validate_security_configuration(settings),
	}

	return results


def log_validation_results(results: Dict[str, Tuple[bool, str]]) -> bool:
	"""
	Log validation results and return overall status.

	Args:
	    results: Validation results from run_full_validation

	Returns:
	    True if all validations passed, False otherwise
	"""
	logger.info("Configuration Validation Results:")
	logger.info("-" * 80)

	all_valid = True

	for component, (is_valid, message) in results.items():
		status = "✓" if is_valid else "✗"
		level = logging.INFO if is_valid else logging.ERROR
		logger.log(level, f"{status} {component.capitalize()}: {message}")

		if not is_valid:
			all_valid = False

	logger.info("-" * 80)

	if all_valid:
		logger.info("✓ All configuration validations passed")
	else:
		logger.error("✗ Some configuration validations failed")

	return all_valid
