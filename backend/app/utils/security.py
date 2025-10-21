"""
Security utilities for file upload validation, sanitization, and security measures.
"""

import hashlib
import hmac
import os
import re
import secrets
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import magic
from fastapi import HTTPException, UploadFile

from ..core.config import get_settings
from ..core.exceptions import SecurityError, ValidationError
from ..core.logging import get_logger

logger = get_logger(__name__)
audit_logger = get_logger("audit")

# Security constants
MAX_FILENAME_LENGTH = 255
DANGEROUS_EXTENSIONS = {
	".exe",
	".bat",
	".cmd",
	".com",
	".pif",
	".scr",
	".vbs",
	".js",
	".jar",
	".app",
	".deb",
	".pkg",
	".dmg",
	".sh",
	".ps1",
	".msi",
	".dll",
}

DANGEROUS_FILENAME_PATTERNS = [
	r"\.\./",  # Path traversal
	r"\\\.\\",  # Windows path traversal
	r'[<>:"|?*\x00-\x1f]',  # Invalid filename characters
	r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)",  # Windows reserved names
]

# MIME type validation mapping
ALLOWED_MIME_TYPES = {
	".pdf": ["application/pdf"],
	".docx": [
		"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
		"application/zip",  # DOCX files are ZIP archives
	],
	".doc": ["application/msword"],
	".txt": ["text/plain"],
}

# File signature validation (magic numbers)
FILE_SIGNATURES = {
	".pdf": [b"%PDF-"],
	".docx": [b"PK\x03\x04"],  # ZIP signature for DOCX
	".doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],  # OLE signature
}


class FileSecurityValidator:
	"""Comprehensive file security validation."""

	def __init__(self):
		self.settings = get_settings()
		self.allowed_extensions = set(self.settings.allowed_file_types)
		self.max_file_size = self.settings.max_file_size_mb * 1024 * 1024

	def validate_filename(self, filename: str) -> str:
		"""
		Validate and sanitize filename for security.

		Args:
		    filename: Original filename

		Returns:
		    str: Sanitized filename

		Raises:
		    SecurityError: If filename is dangerous
		    ValidationError: If filename is invalid
		"""
		if not filename:
			raise ValidationError("Filename cannot be empty")

		if len(filename) > MAX_FILENAME_LENGTH:
			raise ValidationError(f"Filename too long (max {MAX_FILENAME_LENGTH} characters)")

		# Check for dangerous patterns
		for pattern in DANGEROUS_FILENAME_PATTERNS:
			if re.search(pattern, filename, re.IGNORECASE):
				audit_logger.warning(f"Dangerous filename pattern detected: {filename}")
				raise SecurityError(f"Filename contains dangerous pattern: {pattern}")

		# Check for dangerous extensions
		file_ext = Path(filename).suffix.lower()
		if file_ext in DANGEROUS_EXTENSIONS:
			audit_logger.warning(f"Dangerous file extension detected: {filename}")
			raise SecurityError(f"File extension {file_ext} is not allowed")

		return self.sanitize_filename(filename)

	def sanitize_filename(self, filename: str) -> str:
		"""
		Sanitize filename by removing/replacing dangerous characters.

		Args:
		    filename: Original filename

		Returns:
		    str: Sanitized filename
		"""
		# Remove null bytes and control characters
		filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

		# Replace dangerous characters with underscores
		filename = re.sub(r'[<>:"|?*]', "_", filename)

		# Remove leading/trailing dots and spaces
		filename = filename.strip(". ")

		# Ensure filename is not empty after sanitization
		if not filename:
			filename = f"file_{secrets.token_hex(8)}"

		return filename

	def validate_file_content(self, file_content: bytes, filename: str) -> None:
		"""
		Validate file content using magic numbers and MIME type detection.

		Args:
		    file_content: File content bytes
		    filename: Filename for extension checking

		Raises:
		    SecurityError: If file content is suspicious
		    ValidationError: If file type is not supported
		"""
		if not file_content:
			raise ValidationError("File content is empty")

		file_ext = Path(filename).suffix.lower()

		# Check file signature (magic numbers)
		if file_ext in FILE_SIGNATURES:
			signatures = FILE_SIGNATURES[file_ext]
			if not any(file_content.startswith(sig) for sig in signatures):
				audit_logger.warning(f"File signature mismatch for {filename}")
				raise SecurityError(f"File signature does not match extension {file_ext}")

		# MIME type validation using python-magic
		try:
			detected_mime = magic.from_buffer(file_content, mime=True)
			allowed_mimes = ALLOWED_MIME_TYPES.get(file_ext, [])

			if allowed_mimes and detected_mime not in allowed_mimes:
				audit_logger.warning(f"MIME type mismatch: {detected_mime} for {filename}")
				raise SecurityError(f"MIME type {detected_mime} does not match file extension")

		except Exception as e:
			logger.warning(f"Could not detect MIME type for {filename}: {e}")

	def validate_file_size(self, file_size: int) -> None:
		"""
		Validate file size against limits.

		Args:
		    file_size: Size of file in bytes

		Raises:
		    ValidationError: If file size exceeds limits
		"""
		if file_size == 0:
			raise ValidationError("File is empty")

		if file_size > self.max_file_size:
			raise ValidationError(f"File size ({file_size} bytes) exceeds maximum limit ({self.max_file_size} bytes)")

	def scan_for_malicious_content(self, file_content: bytes, filename: str) -> None:
		"""
		Scan file content for potentially malicious patterns.

		Args:
		    file_content: File content bytes
		    filename: Filename for logging

		Raises:
		    SecurityError: If malicious content is detected
		"""
		# Check for embedded executables in PDF
		if filename.lower().endswith(".pdf"):
			suspicious_patterns = [
				b"/JavaScript",
				b"/JS",
				b"/Launch",
				b"/EmbeddedFile",
				b"%PDF-%PDF",  # Multiple PDF headers
			]

			for pattern in suspicious_patterns:
				if pattern in file_content:
					audit_logger.warning(f"Suspicious PDF content detected in {filename}: {pattern}")
					raise SecurityError(f"PDF contains potentially malicious content")

		# Check for macro-enabled documents
		if filename.lower().endswith((".docm", ".xlsm", ".pptm")):
			audit_logger.warning(f"Macro-enabled document uploaded: {filename}")
			raise SecurityError("Macro-enabled documents are not allowed")


class SecureFileHandler:
	"""Secure temporary file handling with automatic cleanup."""

	def __init__(self):
		self.settings = get_settings()
		self.temp_dir = Path(tempfile.gettempdir()) / "contract_analyzer_secure"
		self.temp_dir.mkdir(exist_ok=True, mode=0o700)  # Secure permissions
		self.active_files: Dict[str, Path] = {}

	def save_secure_temp_file(self, content: bytes, filename: str) -> Tuple[str, Path]:
		"""
		Save file content to a secure temporary location.

		Args:
		    content: File content bytes
		    filename: Original filename

		Returns:
		    Tuple[str, Path]: (file_id, temp_file_path)
		"""
		# Generate secure file ID
		file_id = secrets.token_urlsafe(32)

		# Create secure filename
		sanitized_name = FileSecurityValidator().sanitize_filename(filename)
		temp_filename = f"{file_id}_{sanitized_name}"
		temp_path = self.temp_dir / temp_filename

		# Write file with secure permissions
		with open(temp_path, "wb") as f:
			f.write(content)

		# Set secure file permissions (owner read/write only)
		temp_path.chmod(0o600)

		# Track active file
		self.active_files[file_id] = temp_path

		logger.info(f"Saved secure temp file: {file_id}")
		return file_id, temp_path

	def get_temp_file_path(self, file_id: str) -> Optional[Path]:
		"""Get temporary file path by ID."""
		return self.active_files.get(file_id)

	def cleanup_temp_file(self, file_id: str) -> bool:
		"""
		Securely delete temporary file.

		Args:
		    file_id: File ID to cleanup

		Returns:
		    bool: True if file was cleaned up
		"""
		if file_id not in self.active_files:
			return False

		temp_path = self.active_files[file_id]

		try:
			if temp_path.exists():
				# Secure deletion - overwrite with random data
				with open(temp_path, "r+b") as f:
					length = f.seek(0, 2)  # Get file size
					f.seek(0)
					f.write(secrets.token_bytes(length))
					f.flush()
					os.fsync(f.fileno())

				# Remove file
				temp_path.unlink()

			del self.active_files[file_id]
			logger.info(f"Cleaned up temp file: {file_id}")
			return True

		except Exception as e:
			logger.error(f"Failed to cleanup temp file {file_id}: {e}")
			return False

	def cleanup_old_files(self, max_age_hours: int = 24) -> int:
		"""
		Clean up old temporary files.

		Args:
		    max_age_hours: Maximum age in hours before cleanup

		Returns:
		    int: Number of files cleaned up
		"""
		import time

		current_time = time.time()
		max_age_seconds = max_age_hours * 3600
		cleaned_count = 0

		files_to_cleanup = []

		for file_id, temp_path in self.active_files.items():
			try:
				if temp_path.exists():
					file_age = current_time - temp_path.stat().st_mtime
					if file_age > max_age_seconds:
						files_to_cleanup.append(file_id)
				else:
					# File doesn't exist, remove from tracking
					files_to_cleanup.append(file_id)
			except Exception as e:
				logger.error(f"Error checking file age for {file_id}: {e}")
				files_to_cleanup.append(file_id)

		for file_id in files_to_cleanup:
			if self.cleanup_temp_file(file_id):
				cleaned_count += 1

		if cleaned_count > 0:
			logger.info(f"Cleaned up {cleaned_count} old temporary files")

		return cleaned_count


def sanitize_filename(filename: str) -> str:
	"""
	Sanitize filename for security (convenience function).

	Args:
	    filename: Original filename

	Returns:
	    str: Sanitized filename
	"""
	validator = FileSecurityValidator()
	return validator.sanitize_filename(filename)


def validate_upload_file(file: UploadFile) -> bytes:
	"""
	Comprehensive validation of uploaded file.

	Args:
	    file: FastAPI UploadFile object

	Returns:
	    bytes: Validated file content

	Raises:
	    SecurityError: If file fails security validation
	    ValidationError: If file fails basic validation
	"""
	validator = FileSecurityValidator()

	# Validate filename
	if not file.filename:
		raise ValidationError("Filename is required")

	sanitized_filename = validator.validate_filename(file.filename)

	# Read and validate file content
	file_content = file.file.read()
	file.file.seek(0)  # Reset file pointer

	validator.validate_file_size(len(file_content))
	validator.validate_file_content(file_content, sanitized_filename)
	validator.scan_for_malicious_content(file_content, sanitized_filename)

	audit_logger.info(f"File validation passed: {sanitized_filename}")
	return file_content


def generate_secure_token(length: int = 32) -> str:
	"""Generate cryptographically secure token."""
	return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str, salt: Optional[str] = None) -> Tuple[str, str]:
	"""
	Hash sensitive data with salt.

	Args:
	    data: Data to hash
	    salt: Optional salt (generated if not provided)

	Returns:
	    Tuple[str, str]: (hashed_data, salt)
	"""
	if salt is None:
		salt = secrets.token_hex(32)

	hashed = hashlib.pbkdf2_hmac("sha256", data.encode(), salt.encode(), 100000)
	return hashed.hex(), salt


def verify_hmac_signature(data: str, signature: str, secret: str) -> bool:
	"""
	Verify HMAC signature for data integrity.

	Args:
	    data: Original data
	    signature: HMAC signature to verify
	    secret: Secret key

	Returns:
	    bool: True if signature is valid
	"""
	try:
		expected_signature = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()

		return hmac.compare_digest(signature, expected_signature)
	except Exception:
		return False


# Global instances
file_validator = FileSecurityValidator()
secure_file_handler = SecureFileHandler()
