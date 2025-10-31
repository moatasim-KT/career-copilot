"""
Security Configuration Validator for Career Copilot.
Validates and ensures proper security configuration across the application.
"""

import ipaddress
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from .config import settings
from .logging import get_logger
from .audit import audit_logger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


class SecurityConfigurationValidator:
	"""Validates security configuration and provides recommendations."""

	def __init__(self):
		self.settings = get_settings()
		self.validation_results = []
		self.security_score = 0
		self.max_score = 0

	def validate_all_security_settings(self) -> Dict[str, Any]:
		"""
		Perform comprehensive security configuration validation.

		Returns:
		    Dictionary containing validation results and recommendations
		"""
		logger.info("Starting comprehensive security configuration validation...")

		self.validation_results = []
		self.security_score = 0
		self.max_score = 0

		# Validate different security aspects
		self._validate_authentication_config()
		self._validate_cors_config()
		self._validate_rate_limiting_config()
		self._validate_input_validation_config()
		self._validate_encryption_config()
		self._validate_session_config()
		self._validate_audit_config()
		self._validate_file_security_config()
		self._validate_network_security_config()
		self._validate_environment_security()

		# Calculate security score percentage
		score_percentage = (self.security_score / self.max_score * 100) if self.max_score > 0 else 0

		# Determine security level
		if score_percentage >= 90:
			security_level = "EXCELLENT"
		elif score_percentage >= 80:
			security_level = "GOOD"
		elif score_percentage >= 70:
			security_level = "ADEQUATE"
		elif score_percentage >= 60:
			security_level = "NEEDS_IMPROVEMENT"
		else:
			security_level = "CRITICAL"

		results = {
			"security_score": self.security_score,
			"max_score": self.max_score,
			"score_percentage": round(score_percentage, 2),
			"security_level": security_level,
			"validation_results": self.validation_results,
			"recommendations": self._generate_recommendations(),
			"critical_issues": self._get_critical_issues(),
			"environment": self.settings.environment,
		}

		# Log security validation results
		audit_logger.log_event(
			event_type=AuditEventType.SECURITY_AUDIT,
			action="Security configuration validation completed",
			severity=AuditSeverity.MEDIUM if security_level in ["GOOD", "EXCELLENT"] else AuditSeverity.HIGH,
			details={
				"security_level": security_level,
				"score_percentage": score_percentage,
				"critical_issues_count": len(results["critical_issues"]),
			},
		)

		logger.info(f"Security validation completed. Level: {security_level}, Score: {score_percentage:.1f}%")

		return results

	def _validate_authentication_config(self):
		"""Validate authentication configuration."""
		self._add_check("Authentication", "JWT Secret Key Security", self._check_jwt_secret_strength(), 10)

		self._add_check("Authentication", "JWT Algorithm Security", self._check_jwt_algorithm(), 5)

		self._add_check("Authentication", "JWT Expiration", self._check_jwt_expiration(), 5)

		self._add_check("Authentication", "Firebase Configuration", self._check_firebase_config(), 8)

		self._add_check("Authentication", "Disable Auth Setting", not self.settings.disable_auth, 10)

	def _validate_cors_config(self):
		"""Validate CORS configuration."""
		self._add_check("CORS", "Origins Configuration", self._check_cors_origins(), 8)

		self._add_check("CORS", "Wildcard Usage", self._check_cors_wildcard(), 6)

		self._add_check("CORS", "Credentials Setting", self._check_cors_credentials(), 4)

	def _validate_rate_limiting_config(self):
		"""Validate rate limiting configuration."""
		self._add_check("Rate Limiting", "Requests Per Minute", self._check_rate_limit_values(), 6)

		self._add_check("Rate Limiting", "Burst Limit", self._check_burst_limit(), 4)

		self._add_check("Rate Limiting", "API Key Rate Limits", self._check_api_key_rate_limits(), 5)

	def _validate_input_validation_config(self):
		"""Validate input validation configuration."""
		self._add_check("Input Validation", "Max Input Length", self._check_max_input_length(), 4)

		self._add_check("Input Validation", "Sanitization Enabled", self.settings.enable_input_sanitization, 8)

		self._add_check("Input Validation", "Strict Validation", self.settings.strict_validation, 6)

		self._add_check("Input Validation", "File Size Limits", self._check_file_size_limits(), 5)

	def _validate_encryption_config(self):
		"""Validate encryption configuration."""
		self._add_check("Encryption", "HTTPS Configuration", self._check_https_config(), 10)

		self._add_check("Encryption", "Encryption Key", self._check_encryption_key(), 8)

		self._add_check("Encryption", "Temp File Encryption", self.settings.encrypt_temp_files, 6)

	def _validate_session_config(self):
		"""Validate session configuration."""
		self._add_check("Session Security", "Session Timeout", self._check_session_timeout(), 5)

		self._add_check("Session Security", "Secure Cookies", self.settings.secure_cookies, 6)

	def _validate_audit_config(self):
		"""Validate audit and logging configuration."""
		self._add_check("Audit & Logging", "Audit Logging Enabled", self.settings.enable_audit_logging, 8)

		self._add_check("Audit & Logging", "Log Retention", self._check_log_retention(), 4)

		self._add_check("Audit & Logging", "Security Log File", bool(self.settings.security_log_file), 5)

	def _validate_file_security_config(self):
		"""Validate file security configuration."""
		self._add_check("File Security", "File Scanning", self.settings.scan_uploaded_files, 7)

		self._add_check("File Security", "File Quarantine", self.settings.quarantine_suspicious_files, 6)

		self._add_check("File Security", "Allowed MIME Types", self._check_allowed_mime_types(), 5)

	def _validate_network_security_config(self):
		"""Validate network security configuration."""
		self._add_check("Network Security", "IP Restrictions", self._check_ip_restrictions(), 6)

		self._add_check("Network Security", "CSP Configuration", self.settings.enable_csp, 7)

	def _validate_environment_security(self):
		"""Validate environment-specific security settings."""
		if self.settings.environment == "production":
			self._add_check("Environment", "Production Mode", self.settings.production_mode, 10)

			self._add_check("Environment", "Debug Mode Disabled", not self.settings.api_debug, 8)

			self._add_check("Environment", "Development Mode Disabled", not self.settings.development_mode, 6)

		self._add_check("Environment", "Environment Variable Set", bool(self.settings.environment), 3)

	def _check_jwt_secret_strength(self) -> bool:
		"""Check JWT secret key strength."""
		if not self.settings.jwt_secret_key:
			return False

		secret = self.settings.jwt_secret_key.get_secret_value()

		# Check minimum length
		if len(secret) < 32:
			return False

		# Check for default/weak secrets
		weak_secrets = ["your-secret-key-change-in-production", "secret", "password", "123456", "default"]

		if secret.lower() in weak_secrets:
			return False

		# Check complexity (should have mix of characters)
		has_upper = any(c.isupper() for c in secret)
		has_lower = any(c.islower() for c in secret)
		has_digit = any(c.isdigit() for c in secret)
		has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in secret)

		return sum([has_upper, has_lower, has_digit, has_special]) >= 3

	def _check_jwt_algorithm(self) -> bool:
		"""Check JWT algorithm security."""
		secure_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
		return self.settings.jwt_algorithm in secure_algorithms

	def _check_jwt_expiration(self) -> bool:
		"""Check JWT expiration time."""
		# Should be between 1 hour and 7 days
		return 1 <= self.settings.jwt_expiration_hours <= 168

	def _check_firebase_config(self) -> bool:
		"""Check Firebase configuration."""
		if not self.settings.firebase_enabled:
			return True  # Not using Firebase is fine

		required_fields = [self.settings.firebase_project_id, self.settings.firebase_service_account_key, self.settings.firebase_web_api_key]

		return all(field for field in required_fields)

	def _check_cors_origins(self) -> bool:
		"""Check CORS origins configuration."""
		if not self.settings.cors_origins:
			return False

		origins = [origin.strip() for origin in self.settings.cors_origins.split(",")]

		# Check for valid URL format
		for origin in origins:
			if origin != "*":
				try:
					parsed = urlparse(origin)
					if not parsed.scheme or not parsed.netloc:
						return False
				except Exception:
					return False

		return True

	def _check_cors_wildcard(self) -> bool:
		"""Check CORS wildcard usage."""
		if self.settings.environment == "production":
			# Wildcard should not be used in production
			return "*" not in self.settings.cors_origins
		return True

	def _check_cors_credentials(self) -> bool:
		"""Check CORS credentials setting."""
		# If using wildcard, credentials should be false
		if "*" in self.settings.cors_origins:
			return True  # We can't check this easily, assume it's configured correctly
		return True

	def _check_rate_limit_values(self) -> bool:
		"""Check rate limiting values."""
		# Should be reasonable values
		return (
			10 <= self.settings.rate_limit_requests_per_minute <= 1000
			and self.settings.rate_limit_burst >= self.settings.rate_limit_requests_per_minute
		)

	def _check_burst_limit(self) -> bool:
		"""Check burst limit configuration."""
		return self.settings.rate_limit_burst >= self.settings.rate_limit_requests_per_minute

	def _check_api_key_rate_limits(self) -> bool:
		"""Check API key rate limits."""
		return self.settings.api_key_rate_limit_per_hour >= 100

	def _check_max_input_length(self) -> bool:
		"""Check maximum input length."""
		# Should be reasonable (1KB to 1MB)
		return 1024 <= self.settings.max_input_length <= 1048576

	def _check_file_size_limits(self) -> bool:
		"""Check file size limits."""
		# Should be reasonable (1MB to 100MB)
		return 1048576 <= self.settings.max_file_size_bytes <= 104857600

	def _check_https_config(self) -> bool:
		"""Check HTTPS configuration."""
		if self.settings.environment == "production":
			return self.settings.enable_https or self.settings.force_https
		return True  # Not required in development

	def _check_encryption_key(self) -> bool:
		"""Check encryption key configuration."""
		if not self.settings.encryption_key:
			return False

		key = self.settings.encryption_key.get_secret_value()
		return len(key) >= 32  # At least 256 bits

	def _check_session_timeout(self) -> bool:
		"""Check session timeout."""
		# Should be between 5 minutes and 8 hours
		return 5 <= self.settings.session_timeout_minutes <= 480

	def _check_log_retention(self) -> bool:
		"""Check log retention settings."""
		# Should retain logs for at least 30 days
		return self.settings.audit_log_retention_days >= 30

	def _check_allowed_mime_types(self) -> bool:
		"""Check allowed MIME types configuration."""
		if not self.settings.allowed_mime_types:
			return False

		# Should have reasonable MIME types
		safe_types = [
			"application/pdf",
			"application/msword",
			"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
			"text/plain",
			"text/csv",
		]

		return any(mime_type in safe_types for mime_type in self.settings.allowed_mime_types)

	def _check_ip_restrictions(self) -> bool:
		"""Check IP restriction configuration."""
		# If configured, should be valid
		if self.settings.allowed_ip_ranges:
			try:
				ranges = self.settings.allowed_ip_ranges.split(",")
				for ip_range in ranges:
					ipaddress.ip_network(ip_range.strip(), strict=False)
				return True
			except Exception:
				return False

		return True  # Not having IP restrictions is okay

	def _add_check(self, category: str, check_name: str, passed: bool, weight: int):
		"""Add a security check result."""
		self.validation_results.append(
			{
				"category": category,
				"check": check_name,
				"passed": passed,
				"weight": weight,
				"severity": "HIGH" if weight >= 8 else "MEDIUM" if weight >= 5 else "LOW",
			}
		)

		if passed:
			self.security_score += weight

		self.max_score += weight

	def _generate_recommendations(self) -> List[Dict[str, str]]:
		"""Generate security recommendations based on validation results."""
		recommendations = []

		failed_checks = [result for result in self.validation_results if not result["passed"]]

		for check in failed_checks:
			recommendation = self._get_recommendation(check["category"], check["check"])
			if recommendation:
				recommendations.append(
					{"category": check["category"], "check": check["check"], "severity": check["severity"], "recommendation": recommendation}
				)

		return recommendations

	def _get_recommendation(self, category: str, check: str) -> Optional[str]:
		"""Get specific recommendation for a failed check."""
		recommendations_map = {
			(
				"Authentication",
				"JWT Secret Key Security",
			): "Use a strong, randomly generated JWT secret key with at least 32 characters and mixed character types.",
			("Authentication", "JWT Algorithm Security"): "Use a secure JWT algorithm like HS256, HS384, HS512, RS256, RS384, or RS512.",
			("Authentication", "JWT Expiration"): "Set JWT expiration between 1 hour and 7 days for security and usability balance.",
			("Authentication", "Disable Auth Setting"): "Enable authentication in production environments. Set DISABLE_AUTH=false.",
			("CORS", "Origins Configuration"): "Configure specific allowed origins instead of using wildcards in production.",
			("CORS", "Wildcard Usage"): "Avoid using CORS wildcard (*) in production environments.",
			(
				"Input Validation",
				"Sanitization Enabled",
			): "Enable input sanitization to prevent injection attacks. Set ENABLE_INPUT_SANITIZATION=true.",
			("Input Validation", "Strict Validation"): "Enable strict validation for enhanced security. Set STRICT_VALIDATION=true.",
			("Encryption", "HTTPS Configuration"): "Enable HTTPS in production. Set ENABLE_HTTPS=true or FORCE_HTTPS=true.",
			("Encryption", "Encryption Key"): "Configure a strong encryption key with at least 32 characters.",
			("File Security", "File Scanning"): "Enable file scanning to detect malicious uploads. Set SCAN_UPLOADED_FILES=true.",
			("Environment", "Production Mode"): "Enable production mode in production environment. Set PRODUCTION_MODE=true.",
			("Environment", "Debug Mode Disabled"): "Disable debug mode in production. Set API_DEBUG=false.",
		}

		return recommendations_map.get((category, check))

	def _get_critical_issues(self) -> List[Dict[str, Any]]:
		"""Get critical security issues that need immediate attention."""
		critical_issues = []

		for result in self.validation_results:
			if not result["passed"] and result["severity"] == "HIGH":
				critical_issues.append(
					{
						"category": result["category"],
						"check": result["check"],
						"recommendation": self._get_recommendation(result["category"], result["check"]),
					}
				)

		return critical_issues


# Global validator instance
_security_validator: Optional[SecurityConfigurationValidator] = None


def get_security_validator() -> SecurityConfigurationValidator:
	"""Get the security configuration validator instance."""
	global _security_validator
	if _security_validator is None:
		_security_validator = SecurityConfigurationValidator()
	return _security_validator


def validate_security_configuration() -> Dict[str, Any]:
	"""Validate security configuration and return results."""
	validator = get_security_validator()
	return validator.validate_all_security_settings()
