"""
Input sanitization utilities to prevent injection attacks and ensure data safety.
"""

import html
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Union

from ..core.logging import get_logger

logger = get_logger(__name__)


class InputSanitizer:
	"""Comprehensive input sanitization for security."""

	# SQL injection patterns
	SQL_INJECTION_PATTERNS = [
		r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
		r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
		r"(--|#|/\*|\*/)",
		r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR)\b)",
		r"([\'\";])",
	]

	# XSS patterns
	XSS_PATTERNS = [
		r"<script[^>]*>.*?</script>",
		r"javascript:",
		r"vbscript:",
		r"onload\s*=",
		r"onerror\s*=",
		r"onclick\s*=",
		r"onmouseover\s*=",
		r"<iframe[^>]*>",
		r"<object[^>]*>",
		r"<embed[^>]*>",
		r"<link[^>]*>",
		r"<meta[^>]*>",
	]

	# Command injection patterns
	COMMAND_INJECTION_PATTERNS = [
		r"[;&|`$(){}[\]\\]",
		r"\b(rm|del|format|fdisk|mkfs)\b",
		r"\b(cat|type|more|less)\b",
		r"\b(wget|curl|nc|netcat)\b",
		r"\b(chmod|chown|sudo)\b",
	]

	# Path traversal patterns
	PATH_TRAVERSAL_PATTERNS = [
		r"\.\.[\\/]",
		r"[\\/]\.\.[\\/]",
		r"\.\.\\",
		r"\.\.\/",
		r"%2e%2e%2f",
		r"%2e%2e%5c",
		r"..%2f",
		r"..%5c",
	]

	def __init__(self):
		self.sql_regex = re.compile("|".join(self.SQL_INJECTION_PATTERNS), re.IGNORECASE)
		self.xss_regex = re.compile("|".join(self.XSS_PATTERNS), re.IGNORECASE)
		self.command_regex = re.compile("|".join(self.COMMAND_INJECTION_PATTERNS), re.IGNORECASE)
		self.path_regex = re.compile("|".join(self.PATH_TRAVERSAL_PATTERNS), re.IGNORECASE)

	def sanitize_string(self, value: str, max_length: Optional[int] = None) -> str:
		"""
		Sanitize a string input.

		Args:
		    value: Input string to sanitize
		    max_length: Optional maximum length

		Returns:
		    str: Sanitized string
		"""
		if not isinstance(value, str):
			value = str(value)

		# Remove null bytes and control characters
		value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)

		# Normalize whitespace
		value = re.sub(r"\s+", " ", value).strip()

		# Truncate if needed
		if max_length and len(value) > max_length:
			value = value[:max_length]
			logger.warning(f"String truncated to {max_length} characters")

		return value

	def sanitize_filename(self, filename: str) -> str:
		"""
		Sanitize filename for safe file operations.

		Args:
		    filename: Original filename

		Returns:
		    str: Sanitized filename
		"""
		if not filename:
			return "unnamed_file"

		# Remove path components
		filename = filename.split("/")[-1].split("\\")[-1]

		# Remove dangerous characters
		filename = re.sub(r'[<>:"|?*\x00-\x1f]', "_", filename)

		# Remove leading/trailing dots and spaces
		filename = filename.strip(". ")

		# Ensure filename is not empty
		if not filename:
			filename = "unnamed_file"

		# Limit length
		if len(filename) > 255:
			name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
			max_name_length = 255 - len(ext) - 1 if ext else 255
			filename = name[:max_name_length] + ("." + ext if ext else "")

		return filename

	def sanitize_email(self, email: str) -> Optional[str]:
		"""
		Sanitize and validate email address.

		Args:
		    email: Email address to sanitize

		Returns:
		    str: Sanitized email or None if invalid
		"""
		if not email:
			return None

		email = email.strip().lower()

		# Basic email validation
		email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
		if not re.match(email_pattern, email):
			return None

		return email

	def sanitize_url(self, url: str) -> Optional[str]:
		"""
		Sanitize and validate URL.

		Args:
		    url: URL to sanitize

		Returns:
		    str: Sanitized URL or None if invalid
		"""
		if not url:
			return None

		url = url.strip()

		# Parse URL
		try:
			parsed = urllib.parse.urlparse(url)

			# Check scheme
			if parsed.scheme not in ["http", "https"]:
				return None

			# Reconstruct clean URL
			clean_url = urllib.parse.urlunparse(parsed)
			return clean_url

		except Exception:
			return None

	def detect_sql_injection(self, value: str) -> bool:
		"""
		Detect potential SQL injection attempts.

		Args:
		    value: Input value to check

		Returns:
		    bool: True if potential SQL injection detected
		"""
		if not value:
			return False

		return bool(self.sql_regex.search(value))

	def detect_xss(self, value: str) -> bool:
		"""
		Detect potential XSS attempts.

		Args:
		    value: Input value to check

		Returns:
		    bool: True if potential XSS detected
		"""
		if not value:
			return False

		return bool(self.xss_regex.search(value))

	def detect_command_injection(self, value: str) -> bool:
		"""
		Detect potential command injection attempts.

		Args:
		    value: Input value to check

		Returns:
		    bool: True if potential command injection detected
		"""
		if not value:
			return False

		return bool(self.command_regex.search(value))

	def detect_path_traversal(self, value: str) -> bool:
		"""
		Detect potential path traversal attempts.

		Args:
		    value: Input value to check

		Returns:
		    bool: True if potential path traversal detected
		"""
		if not value:
			return False

		return bool(self.path_regex.search(value))

	def sanitize_html(self, value: str) -> str:
		"""
		Sanitize HTML content by escaping dangerous characters.

		Args:
		    value: HTML content to sanitize

		Returns:
		    str: Sanitized HTML
		"""
		if not value:
			return ""

		# HTML escape
		value = html.escape(value, quote=True)

		# Remove script tags and other dangerous elements
		dangerous_tags = ["script", "iframe", "object", "embed", "link", "meta", "style", "form", "input", "button", "textarea"]

		for tag in dangerous_tags:
			value = re.sub(f"<{tag}[^>]*>.*?</{tag}>", "", value, flags=re.IGNORECASE | re.DOTALL)
			value = re.sub(f"<{tag}[^>]*/?>", "", value, flags=re.IGNORECASE)

		return value

	def sanitize_json_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Sanitize JSON input data recursively.

		Args:
		    data: JSON data to sanitize

		Returns:
		    dict: Sanitized JSON data
		"""
		if isinstance(data, dict):
			return {self.sanitize_string(str(k)): self.sanitize_json_input(v) for k, v in data.items()}
		elif isinstance(data, list):
			return [self.sanitize_json_input(item) for item in data]
		elif isinstance(data, str):
			return self.sanitize_string(data)
		else:
			return data

	def validate_and_sanitize_input(self, value: str, input_type: str = "general", max_length: Optional[int] = None) -> str:
		"""
		Comprehensive input validation and sanitization.

		Args:
		    value: Input value to validate and sanitize
		    input_type: Type of input (general, filename, email, url)
		    max_length: Optional maximum length

		Returns:
		    str: Sanitized value

		Raises:
		    ValueError: If input contains malicious content
		"""
		if not isinstance(value, str):
			value = str(value)

		# Check for injection attempts
		if self.detect_sql_injection(value):
			logger.warning(f"SQL injection attempt detected: {value[:100]}")
			raise ValueError("Input contains potentially malicious SQL content")

		if self.detect_xss(value):
			logger.warning(f"XSS attempt detected: {value[:100]}")
			raise ValueError("Input contains potentially malicious script content")

		if self.detect_command_injection(value):
			logger.warning(f"Command injection attempt detected: {value[:100]}")
			raise ValueError("Input contains potentially malicious command content")

		if self.detect_path_traversal(value):
			logger.warning(f"Path traversal attempt detected: {value[:100]}")
			raise ValueError("Input contains potentially malicious path content")

		# Sanitize based on type
		if input_type == "filename":
			return self.sanitize_filename(value)
		elif input_type == "email":
			result = self.sanitize_email(value)
			if result is None:
				raise ValueError("Invalid email format")
			return result
		elif input_type == "url":
			result = self.sanitize_url(value)
			if result is None:
				raise ValueError("Invalid URL format")
			return result
		elif input_type == "html":
			return self.sanitize_html(value)
		else:
			return self.sanitize_string(value, max_length)


class RequestSanitizer:
	"""Sanitize FastAPI request data."""

	def __init__(self):
		self.input_sanitizer = InputSanitizer()

	def sanitize_query_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Sanitize query parameters.

		Args:
		    params: Query parameters dictionary

		Returns:
		    dict: Sanitized parameters
		"""
		sanitized = {}

		for key, value in params.items():
			try:
				# Sanitize key
				clean_key = self.input_sanitizer.sanitize_string(str(key), max_length=100)

				# Sanitize value
				if isinstance(value, list):
					clean_value = [self.input_sanitizer.sanitize_string(str(v), max_length=1000) for v in value]
				else:
					clean_value = self.input_sanitizer.sanitize_string(str(value), max_length=1000)

				sanitized[clean_key] = clean_value

			except ValueError as e:
				logger.warning(f"Malicious query parameter detected: {key}={value}")
				# Skip malicious parameters
				continue

		return sanitized

	def sanitize_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Sanitize form data.

		Args:
		    form_data: Form data dictionary

		Returns:
		    dict: Sanitized form data
		"""
		return self.input_sanitizer.sanitize_json_input(form_data)

	def sanitize_json_body(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Sanitize JSON request body.

		Args:
		    json_data: JSON data dictionary

		Returns:
		    dict: Sanitized JSON data
		"""
		return self.input_sanitizer.sanitize_json_input(json_data)


# Global instances
input_sanitizer = InputSanitizer()
request_sanitizer = RequestSanitizer()
