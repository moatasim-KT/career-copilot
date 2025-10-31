"""
Input Validation and Sanitization Module
Prevents SQL injection, XSS, path traversal, and other injection attacks
"""

import re
from typing import Any, Optional
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, status


class InputValidator:
	"""Comprehensive input validation and sanitization"""

	# Dangerous patterns
	SQL_INJECTION_PATTERNS = [
		r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
		r"(--|;|\/\*|\*\/|xp_|sp_)",
		r"(\bOR\b.*=.*|1=1|'=')",
	]

	XSS_PATTERNS = [
		r"<script[^>]*>.*?</script>",
		r"javascript:",
		r"on\w+\s*=",
		r"<iframe",
		r"<object",
		r"<embed",
	]

	PATH_TRAVERSAL_PATTERNS = [
		r"\.\./",
		r"\.\.",
		r"%2e%2e",
		r"\.\.\\",
	]

	COMMAND_INJECTION_PATTERNS = [
		r"[;&|`$]",
		r"\$\(",
		r">\s*/",
	]

	@staticmethod
	def sanitize_string(value: str, max_length: int = 1000) -> str:
		"""Sanitize string input"""
		if not isinstance(value, str):
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input type: expected string")

		# Trim whitespace
		value = value.strip()

		# Check length
		if len(value) > max_length:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Input exceeds maximum length of {max_length}")

		# Remove null bytes
		value = value.replace("\x00", "")

		return value

	@classmethod
	def validate_no_sql_injection(cls, value: str) -> str:
		"""Check for SQL injection patterns"""
		for pattern in cls.SQL_INJECTION_PATTERNS:
			if re.search(pattern, value, re.IGNORECASE):
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: potential SQL injection detected")
		return value

	@classmethod
	def validate_no_xss(cls, value: str) -> str:
		"""Check for XSS patterns"""
		for pattern in cls.XSS_PATTERNS:
			if re.search(pattern, value, re.IGNORECASE):
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: potential XSS detected")
		return value

	@classmethod
	def validate_no_path_traversal(cls, value: str) -> str:
		"""Check for path traversal patterns"""
		for pattern in cls.PATH_TRAVERSAL_PATTERNS:
			if re.search(pattern, value, re.IGNORECASE):
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: path traversal detected")
		return value

	@classmethod
	def validate_no_command_injection(cls, value: str) -> str:
		"""Check for command injection patterns"""
		for pattern in cls.COMMAND_INJECTION_PATTERNS:
			if re.search(pattern, value):
				raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input: command injection detected")
		return value

	@staticmethod
	def validate_email(email: str) -> str:
		"""Validate email format"""
		email = email.strip().lower()
		pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
		if not re.match(pattern, email):
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
		return email

	@staticmethod
	def validate_url(url: str) -> str:
		"""Validate URL format"""
		try:
			result = urlparse(url)
			if not all([result.scheme, result.netloc]):
				raise ValueError
			if result.scheme not in ["http", "https"]:
				raise ValueError
			return url
		except:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL format")

	@staticmethod
	def validate_filename(filename: str) -> str:
		"""Validate filename"""
		# Remove path components
		filename = Path(filename).name

		# Check for dangerous characters
		if re.search(r'[<>:"/\\|?*\x00-\x1f]', filename):
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename: contains illegal characters")

		# Check length
		if len(filename) > 255:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename too long")

		return filename

	@staticmethod
	def validate_integer(value: Any, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
		"""Validate integer with optional range"""
		try:
			int_val = int(value)
		except (ValueError, TypeError):
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid integer value")

		if min_val is not None and int_val < min_val:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Value must be at least {min_val}")

		if max_val is not None and int_val > max_val:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Value must be at most {max_val}")

		return int_val

	@classmethod
	def sanitize_search_query(cls, query: str) -> str:
		"""Sanitize search query input"""
		query = cls.sanitize_string(query, max_length=500)
		query = cls.validate_no_sql_injection(query)
		query = cls.validate_no_xss(query)
		return query

	@classmethod
	def sanitize_user_input(cls, value: str) -> str:
		"""General user input sanitization"""
		value = cls.sanitize_string(value)
		value = cls.validate_no_sql_injection(value)
		value = cls.validate_no_xss(value)
		value = cls.validate_no_command_injection(value)
		return value


# Convenience functions
def validate_and_sanitize(value: str, field_name: str = "input") -> str:
	"""Validate and sanitize general input"""
	try:
		return InputValidator.sanitize_user_input(value)
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field_name}: {e!s}")
