"""
Input sanitization to prevent injection attacks.
"""

import html
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union


class InputSanitizer:
	"""Comprehensive input sanitization for security."""

	def __init__(self):
		self.logger = logging.getLogger(__name__)

		# Dangerous patterns for various injection attacks
		self.sql_patterns = [
			r"(union\s+select|select\s+.*\s+from|insert\s+into|update\s+.*\s+set|delete\s+from)",
			r"(drop\s+table|create\s+table|alter\s+table)",
			r"(exec\s*\(|execute\s*\(|sp_executesql)",
			r"(xp_cmdshell|sp_configure)",
			r"(\bor\b\s+\d+\s*=\s*\d+|\band\b\s+\d+\s*=\s*\d+)",
			r"(;\s*--|;\s*#|;\s*\/\*)",
			r"(\'\s*or\s*\'|\"\s*or\s*\"|\'\s*and\s*\'|\"\s*and\s*\")",
		]

		self.xss_patterns = [
			r"<script[^>]*>.*?</script>",
			r"<iframe[^>]*>.*?</iframe>",
			r"<object[^>]*>.*?</object>",
			r"<embed[^>]*>.*?</embed>",
			r"<form[^>]*>.*?</form>",
			r"<input[^>]*>",
			r"<textarea[^>]*>.*?</textarea>",
			r"<select[^>]*>.*?</select>",
			r"<option[^>]*>.*?</option>",
			r"<link[^>]*>",
			r"<meta[^>]*>",
			r"<style[^>]*>.*?</style>",
			r"<link[^>]*>",
			r"javascript:",
			r"vbscript:",
			r"data:text/html",
			r"data:application/javascript",
			r"on\w+\s*=",
			r"expression\s*\(",
			r"url\s*\(",
			r"@import",
		]

		self.command_injection_patterns = [
			r"[;&|`$]",
			r"(rm\s+-rf|del\s+\/s|format\s+)",
			r"(wget|curl|nc|netcat)",
			r"(cat\s+\/etc\/passwd|type\s+c:\\windows\\system32\\drivers\\etc\\hosts)",
			r"(ps\s+aux|tasklist)",
			r"(whoami|id|who)",
			r"(uname\s+-a|systeminfo)",
			r"(ping\s+|traceroute)",
			r"(chmod\s+777|icacls)",
			r"(sudo\s+|runas)",
		]

		self.path_traversal_patterns = [
			r"\.\./",
			r"\.\.\\",
			r"%2e%2e%2f",
			r"%2e%2e%5c",
			r"\.\.%2f",
			r"\.\.%5c",
			r"%252e%252e%252f",
			r"%252e%252e%255c",
		]

	def sanitize_text_input(self, text: str, max_length: int = 1000) -> str:
		"""
		Sanitize text input for general use.

		Args:
		    text: Input text to sanitize
		    max_length: Maximum allowed length

		Returns:
		    Sanitized text
		"""
		if not isinstance(text, str):
			return ""

		# Remove null bytes and control characters
		text = text.replace("\x00", "")
		text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

		# Limit length
		text = text[:max_length]

		# HTML encode special characters
		text = html.escape(text, quote=True)

		# Remove excessive whitespace
		text = re.sub(r"\s+", " ", text).strip()

		return text

	def sanitize_filename(self, filename: str) -> str:
		"""
		Sanitize filename for safe file operations.

		Args:
		    filename: Filename to sanitize

		Returns:
		    Sanitized filename
		"""
		if not isinstance(filename, str):
			return "unnamed_file"

		# Remove path traversal attempts
		filename = re.sub(r"[\.]{2,}", "", filename)
		filename = filename.replace("..", "")
		filename = filename.replace("/", "_")
		filename = filename.replace("\\", "_")

		# Remove dangerous characters
		dangerous_chars = r'[<>:"|?*\x00-\x1f]'
		filename = re.sub(dangerous_chars, "_", filename)

		# Remove leading/trailing dots and spaces
		filename = filename.strip(". ")

		# Ensure filename is not empty
		if not filename:
			filename = "unnamed_file"

		# Limit length
		filename = filename[:255]

		return filename

	def sanitize_json_input(self, data: Union[str, dict]) -> Optional[dict]:
		"""
		Sanitize JSON input data.

		Args:
		    data: JSON string or dict to sanitize

		Returns:
		    Sanitized dict or None if invalid
		"""
		try:
			if isinstance(data, str):
				# Parse JSON
				parsed_data = json.loads(data)
			else:
				parsed_data = data

			if not isinstance(parsed_data, dict):
				return None

			# Recursively sanitize all string values
			sanitized = self._sanitize_dict_recursive(parsed_data)

			return sanitized

		except (json.JSONDecodeError, TypeError, ValueError) as e:
			self.logger.warning(f"JSON sanitization failed: {e!s}")
			return None

	def _sanitize_dict_recursive(self, data: Any) -> Any:
		"""Recursively sanitize dictionary values."""
		if isinstance(data, dict):
			return {key: self._sanitize_dict_recursive(value) for key, value in data.items()}
		elif isinstance(data, list):
			return [self._sanitize_dict_recursive(item) for item in data]
		elif isinstance(data, str):
			return self.sanitize_text_input(data)
		else:
			return data

	def detect_sql_injection(self, text: str) -> bool:
		"""
		Detect potential SQL injection attempts.

		Args:
		    text: Text to analyze

		Returns:
		    True if SQL injection pattern detected
		"""
		if not isinstance(text, str):
			return False

		text_lower = text.lower()

		for pattern in self.sql_patterns:
			if re.search(pattern, text_lower, re.IGNORECASE):
				self.logger.warning(f"SQL injection pattern detected: {pattern}")
				return True

		return False

	def detect_xss_attack(self, text: str) -> bool:
		"""
		Detect potential XSS attacks.

		Args:
		    text: Text to analyze

		Returns:
		    True if XSS pattern detected
		"""
		if not isinstance(text, str):
			return False

		for pattern in self.xss_patterns:
			if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
				self.logger.warning(f"XSS pattern detected: {pattern}")
				return True

		return False

	def detect_command_injection(self, text: str) -> bool:
		"""
		Detect potential command injection attempts.

		Args:
		    text: Text to analyze

		Returns:
		    True if command injection pattern detected
		"""
		if not isinstance(text, str):
			return False

		text_lower = text.lower()

		for pattern in self.command_injection_patterns:
			if re.search(pattern, text_lower):
				self.logger.warning(f"Command injection pattern detected: {pattern}")
				return True

		return False

	def detect_path_traversal(self, text: str) -> bool:
		"""
		Detect potential path traversal attempts.

		Args:
		    text: Text to analyze

		Returns:
		    True if path traversal pattern detected
		"""
		if not isinstance(text, str):
			return False

		for pattern in self.path_traversal_patterns:
			if re.search(pattern, text, re.IGNORECASE):
				self.logger.warning(f"Path traversal pattern detected: {pattern}")
				return True

		return False

	def sanitize_for_display(self, text: str) -> str:
		"""
		Sanitize text for safe display in HTML.

		Args:
		    text: Text to sanitize

		Returns:
		    Sanitized text safe for HTML display
		"""
		if not isinstance(text, str):
			return ""

		# HTML encode
		text = html.escape(text, quote=True)

		# Remove any remaining script tags
		text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)

		# Remove event handlers
		text = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', "", text, flags=re.IGNORECASE)

		return text

	def sanitize_api_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Sanitize input data for API calls.

		Args:
		    data: Input data dictionary

		Returns:
		    Sanitized data dictionary
		"""
		if not isinstance(data, dict):
			return {}

		sanitized = {}

		for key, value in data.items():
			# Sanitize key
			clean_key = self.sanitize_text_input(str(key), max_length=100)

			# Sanitize value based on type
			if isinstance(value, str):
				clean_value = self.sanitize_text_input(value)
			elif isinstance(value, dict):
				clean_value = self.sanitize_api_input(value)
			elif isinstance(value, list):
				clean_value = [self.sanitize_text_input(str(item)) if isinstance(item, str) else item for item in value]
			else:
				clean_value = value

			sanitized[clean_key] = clean_value

		return sanitized

	def validate_email(self, email: str) -> bool:
		"""
		Validate email format and check for injection attempts.

		Args:
		    email: Email address to validate

		Returns:
		    True if email is valid and safe
		"""
		if not isinstance(email, str):
			return False

		# Basic email regex
		email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

		if not re.match(email_pattern, email):
			return False

		# Check for injection patterns
		if self.detect_sql_injection(email) or self.detect_xss_attack(email) or self.detect_command_injection(email):
			return False

		return True

	def sanitize_file_content(self, content: bytes) -> bytes:
		"""
		Sanitize file content for security.

		Args:
		    content: File content as bytes

		Returns:
		    Sanitized content
		"""
		if not isinstance(content, bytes):
			return b""

		# Remove null bytes
		content = content.replace(b"\x00", b"")

		# Remove control characters except newlines and tabs
		content = re.sub(b"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", b"", content)

		return content
