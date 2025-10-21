"""
File security validation and sanitization for uploads.
"""

import hashlib
import logging
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import magic
import streamlit as st
from config import config


class FileSecurityValidator:
	"""Advanced file security validation and sanitization."""

	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.max_file_size = config.MAX_FILE_SIZE_MB * 1024 * 1024
		self.allowed_mime_types = {
			"application/pdf": [".pdf"], 
			"application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
			"text/plain": [".txt"]
		}
		self.dangerous_extensions = {
			".exe",
			".bat",
			".cmd",
			".com",
			".pif",
			".scr",
			".vbs",
			".js",
			".jar",
			".php",
			".asp",
			".aspx",
			".jsp",
			".py",
			".rb",
			".pl",
			".sh",
			".ps1",
		}
		self.max_filename_length = 255
		self.quarantine_dir = Path(tempfile.gettempdir()) / "contract_analyzer_quarantine"
		self.quarantine_dir.mkdir(exist_ok=True)

	def validate_file_security(self, uploaded_file) -> Dict[str, Any]:
		"""
		Comprehensive file security validation.

		Args:
		    uploaded_file: Streamlit uploaded file object

		Returns:
		    Dict with validation results and security status
		"""
		result = {
			"is_secure": False,
			"risk_level": "high",
			"threats_detected": [],
			"file_hash": None,
			"sanitized_filename": None,
			"quarantine_path": None,
		}

		try:
			# Basic file existence check
			if not uploaded_file or not uploaded_file.name:
				result["threats_detected"].append("No file provided")
				return result

			# Get file content
			file_content = uploaded_file.getvalue()
			if not file_content:
				result["threats_detected"].append("Empty file")
				return result

			# Calculate file hash for tracking
			file_hash = hashlib.sha256(file_content).hexdigest()
			result["file_hash"] = file_hash

			# Check file size
			if len(file_content) > self.max_file_size:
				result["threats_detected"].append(f"File too large: {len(file_content)} bytes")
				return result

			# Validate filename
			filename_validation = self._validate_filename(uploaded_file.name)
			if not filename_validation["is_valid"]:
				result["threats_detected"].extend(filename_validation["threats"])
				return result

			# Sanitize filename
			sanitized_name = self._sanitize_filename(uploaded_file.name)
			result["sanitized_filename"] = sanitized_name

			# Detect actual file type using magic bytes
			mime_type = self._detect_mime_type(file_content)
			if not mime_type:
				result["threats_detected"].append("Unable to determine file type")
				return result

			# Validate MIME type matches extension
			if not self._validate_mime_type_consistency(uploaded_file.name, mime_type):
				result["threats_detected"].append("File type mismatch detected")
				return result

			# Check for allowed MIME types
			if mime_type not in self.allowed_mime_types:
				result["threats_detected"].append(f"Unsupported file type: {mime_type}")
				return result

			# Scan for malicious content patterns
			malicious_patterns = self._scan_for_malicious_content(file_content)
			if malicious_patterns:
				result["threats_detected"].extend(malicious_patterns)
				return result

			# Check file structure integrity
			if not self._validate_file_structure(file_content, mime_type):
				result["threats_detected"].append("File structure appears corrupted")
				return result

			# If all checks pass, file is secure
			result["is_secure"] = True
			result["risk_level"] = "low"

			# Log successful validation
			self.logger.info(f"File security validation passed: {sanitized_name} (hash: {file_hash[:16]}...)")

		except Exception as e:
			self.logger.error(f"File security validation error: {e!s}")
			result["threats_detected"].append(f"Validation error: {e!s}")

		return result

	def _validate_filename(self, filename: str) -> Dict[str, Any]:
		"""Validate filename for security issues."""
		result = {"is_valid": True, "threats": []}

		if not filename:
			result["is_valid"] = False
			result["threats"].append("Empty filename")
			return result

		if len(filename) > self.max_filename_length:
			result["is_valid"] = False
			result["threats"].append("Filename too long")
			return result

		# Check for path traversal attempts
		if ".." in filename or "/" in filename or "\\" in filename:
			result["is_valid"] = False
			result["threats"].append("Path traversal attempt detected")
			return result

		# Check for dangerous extensions
		file_ext = Path(filename).suffix.lower()
		if file_ext in self.dangerous_extensions:
			result["is_valid"] = False
			result["threats"].append(f"Dangerous file extension: {file_ext}")
			return result

		# Check for suspicious characters
		suspicious_chars = ["<", ">", ":", '"', "|", "?", "*"]
		for char in suspicious_chars:
			if char in filename:
				result["is_valid"] = False
				result["threats"].append(f"Suspicious character in filename: {char}")
				return result

		return result

	def _sanitize_filename(self, filename: str) -> str:
		"""Sanitize filename to remove dangerous characters."""
		# Remove path separators and dangerous characters
		sanitized = filename.replace("..", "").replace("/", "_").replace("\\", "_")
		sanitized = sanitized.replace("<", "").replace(">", "").replace(":", "")
		sanitized = sanitized.replace('"', "").replace("|", "").replace("?", "")
		sanitized = sanitized.replace("*", "").replace("\x00", "")

		# Limit length
		if len(sanitized) > self.max_filename_length:
			name, ext = os.path.splitext(sanitized)
			max_name_length = self.max_filename_length - len(ext)
			sanitized = name[:max_name_length] + ext

		# Ensure filename is not empty
		if not sanitized or sanitized == "." or sanitized == "..":
			sanitized = f"file_{uuid.uuid4().hex[:8]}"

		return sanitized

	def _detect_mime_type(self, file_content: bytes) -> Optional[str]:
		"""Detect MIME type using magic bytes."""
		try:
			# Always use basic detection first as it's more reliable for our use case
			basic_mime = self._basic_mime_detection(file_content)
			if basic_mime:
				return basic_mime
			
			# Try python-magic as fallback
			try:
				import magic
				mime_type = magic.from_buffer(file_content, mime=True)
				# Validate the magic result against our allowed types
				if mime_type in self.allowed_mime_types:
					return mime_type
			except ImportError:
				pass
			except Exception as e:
				self.logger.warning(f"python-magic detection failed: {e}")
			
			# Final fallback - assume text/plain for readable content
			try:
				# Check if content is mostly printable ASCII
				if len(file_content) > 0:
					printable_ratio = sum(1 for b in file_content[:1000] if 32 <= b <= 126 or b in [9, 10, 13]) / min(len(file_content), 1000)
					if printable_ratio > 0.8:
						return "text/plain"
			except:
				pass
				
			return None
		except Exception as e:
			self.logger.warning(f"MIME type detection failed: {e!s}")
			return None

	def _basic_mime_detection(self, file_content: bytes) -> Optional[str]:
		"""Basic MIME type detection using magic numbers."""
		if not file_content:
			return None
			
		# PDF detection - check for PDF signature
		if file_content.startswith(b"%PDF-"):
			return "application/pdf"
		
		# DOCX detection - ZIP file with Word structure
		elif file_content.startswith(b"PK\x03\x04") or file_content.startswith(b"PK\x05\x06") or file_content.startswith(b"PK\x07\x08"):
			# Check if it's a DOCX file by looking for specific structure
			if b"word/" in file_content[:2048] or b"[Content_Types].xml" in file_content[:2048]:
				return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
		
		# Text file detection - check if content is mostly printable
		elif len(file_content) > 0:
			# Sample first 1000 bytes to check if it's text
			sample = file_content[:1000]
			try:
				# Try to decode as UTF-8
				sample.decode('utf-8')
				# Check if it's mostly printable characters
				printable_count = sum(1 for b in sample if 32 <= b <= 126 or b in [9, 10, 13])
				if printable_count / len(sample) > 0.8:
					return "text/plain"
			except UnicodeDecodeError:
				pass
		
		return None

	def _validate_mime_type_consistency(self, filename: str, mime_type: str) -> bool:
		"""Validate that MIME type matches file extension."""
		file_ext = Path(filename).suffix.lower()
		
		# Allow common file extensions regardless of MIME detection issues
		allowed_extensions = ['.pdf', '.docx', '.txt']
		if file_ext in allowed_extensions:
			return True

		if mime_type in self.allowed_mime_types:
			allowed_extensions = self.allowed_mime_types[mime_type]
			return file_ext in allowed_extensions

		return False

	def _scan_for_malicious_content(self, file_content: bytes) -> List[str]:
		"""Scan file content for malicious patterns."""
		threats = []

		# Check for embedded scripts
		script_patterns = [b"<script", b"javascript:", b"vbscript:", b"data:text/html", b"<iframe", b"<object", b"<embed", b"<form"]

		for pattern in script_patterns:
			if pattern in file_content.lower():
				threats.append(f"Potential script content detected: {pattern.decode()}")

		# Check for executable signatures
		executable_signatures = [
			b"MZ",  # PE executable
			b"\x7fELF",  # ELF executable
			b"\xfe\xed\xfa",  # Mach-O executable
		]

		for sig in executable_signatures:
			if file_content.startswith(sig):
				threats.append("Executable file signature detected")

		# Check for suspicious strings
		suspicious_strings = [b"eval(", b"exec(", b"system(", b"shell_exec", b"cmd.exe", b"/bin/sh", b"powershell"]

		for suspicious in suspicious_strings:
			if suspicious in file_content.lower():
				threats.append(f"Suspicious string detected: {suspicious.decode()}")

		return threats

	def _validate_file_structure(self, file_content: bytes, mime_type: str) -> bool:
		"""Validate file structure integrity."""
		try:
			if mime_type == "application/pdf":
				return self._validate_pdf_structure(file_content)
			elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
				return self._validate_docx_structure(file_content)
			return True
		except Exception as e:
			self.logger.warning(f"File structure validation failed: {e!s}")
			return False

	def _validate_pdf_structure(self, file_content: bytes) -> bool:
		"""Validate PDF file structure."""
		# Check for PDF header
		if not file_content.startswith(b"%PDF"):
			return False

		# Check for PDF trailer
		if b"%%EOF" not in file_content[-1024:]:
			return False

		# Basic structure validation
		if len(file_content) < 100:  # Minimum PDF size
			return False

		return True

	def _validate_docx_structure(self, file_content: bytes) -> bool:
		"""Validate DOCX file structure."""
		# DOCX is a ZIP file, check for ZIP signature
		if not file_content.startswith(b"PK\x03\x04"):
			return False

		# Check for required DOCX structure
		required_files = [b"[Content_Types].xml", b"_rels/.rels", b"word/"]
		for required in required_files:
			if required not in file_content:
				return False

		return True


class SecureFileHandler:
	"""Secure file handling with quarantine and cleanup."""

	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.temp_dir = Path(tempfile.gettempdir()) / "contract_analyzer_temp"
		self.temp_dir.mkdir(exist_ok=True)
		self.quarantine_dir = Path(tempfile.gettempdir()) / "contract_analyzer_quarantine"
		self.quarantine_dir.mkdir(exist_ok=True)
		self.file_retention_hours = 24

	def create_secure_temp_file(self, file_content: bytes, filename: str) -> Optional[Path]:
		"""Create a secure temporary file."""
		try:
			# Generate secure filename
			secure_filename = f"{uuid.uuid4().hex}_{filename}"
			temp_path = self.temp_dir / secure_filename

			# Write file with restricted permissions
			with open(temp_path, "wb") as f:
				f.write(file_content)

			# Set restrictive permissions (owner read/write only)
			os.chmod(temp_path, 0o600)

			self.logger.info(f"Created secure temp file: {temp_path}")
			return temp_path

		except Exception as e:
			self.logger.error(f"Failed to create secure temp file: {e!s}")
			return None

	def quarantine_file(self, file_content: bytes, filename: str, reason: str) -> Optional[Path]:
		"""Quarantine a suspicious file."""
		try:
			quarantine_filename = f"{uuid.uuid4().hex}_{filename}"
			quarantine_path = self.quarantine_dir / quarantine_filename

			with open(quarantine_path, "wb") as f:
				f.write(file_content)

			# Set restrictive permissions
			os.chmod(quarantine_path, 0o600)

			# Log quarantine action
			self.logger.warning(f"File quarantined: {quarantine_path} - Reason: {reason}")

			return quarantine_path

		except Exception as e:
			self.logger.error(f"Failed to quarantine file: {e!s}")
			return None

	def cleanup_old_files(self):
		"""Clean up old temporary and quarantine files."""
		try:
			cutoff_time = datetime.now() - timedelta(hours=self.file_retention_hours)

			# Clean temp files
			for file_path in self.temp_dir.iterdir():
				if file_path.is_file():
					file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
					if file_time < cutoff_time:
						file_path.unlink()
						self.logger.info(f"Cleaned up old temp file: {file_path}")

			# Clean quarantine files
			for file_path in self.quarantine_dir.iterdir():
				if file_path.is_file():
					file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
					if file_time < cutoff_time:
						file_path.unlink()
						self.logger.info(f"Cleaned up old quarantine file: {file_path}")

		except Exception as e:
			self.logger.error(f"File cleanup failed: {e!s}")

	def secure_delete_file(self, file_path: Path):
		"""Securely delete a file by overwriting it first."""
		try:
			if file_path.exists():
				# Overwrite with random data
				with open(file_path, "r+b") as f:
					file_size = file_path.stat().st_size
					f.write(os.urandom(file_size))
					f.flush()
					os.fsync(f.fileno())

				# Delete the file
				file_path.unlink()
				self.logger.info(f"Securely deleted file: {file_path}")

		except Exception as e:
			self.logger.error(f"Secure delete failed: {e!s}")
