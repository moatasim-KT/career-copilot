"""
Secure file handling with automatic cleanup and memory management.
"""

import asyncio
import hashlib
import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import magic

from ..core.audit import AuditEventType, audit_logger
from ..core.config import get_settings
from ..core.exceptions import SecurityError, ValidationError
from ..core.logging import get_logger
from ..utils.security import generate_secure_token

logger = get_logger(__name__)


class FileSecurityValidator:
	"""Comprehensive file security validation."""

	def __init__(self):
		self.settings = get_settings()
		# Use a simple fallback for file type detection
		self.magic_mime = None

		# Dangerous file extensions
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
			".app",
			".deb",
			".pkg",
			".dmg",
			".iso",
			".msi",
			".run",
			".sh",
			".ps1",
			".php",
			".asp",
			".jsp",
			".py",
			".rb",
			".pl",
			".cgi",
		}

		# Malicious patterns in file content
		self.malicious_patterns = [
			b"<script",
			b"javascript:",
			b"vbscript:",
			b"onload=",
			b"onerror=",
			b"eval(",
			b"exec(",
			b"system(",
			b"shell_exec(",
			b"passthru(",
			b"<?php",
			b"<%",
			b"#!/bin/sh",
			b"#!/bin/bash",
			b"powershell",
			b"cmd.exe",
			b"/JavaScript",  # PDF JavaScript
			b"/JS",  # PDF JavaScript
			b"/OpenAction",  # PDF auto-execute
		]

	def validate_filename(self, filename: str) -> str:
		"""
		Validate and sanitize filename.

		Args:
			filename: Original filename

		Returns:
			str: Sanitized filename

		Raises:
			SecurityError: If filename is dangerous
		"""
		if not filename:
			raise ValidationError("Filename cannot be empty")

		# Remove path components
		filename = os.path.basename(filename)

		# Check for dangerous extensions
		file_ext = Path(filename).suffix.lower()
		if file_ext in self.dangerous_extensions:
			raise SecurityError(f"File extension '{file_ext}' is not allowed")

		# Check for reserved names (Windows)
		reserved_names = {
			"CON",
			"PRN",
			"AUX",
			"NUL",
			"COM1",
			"COM2",
			"COM3",
			"COM4",
			"COM5",
			"COM6",
			"COM7",
			"COM8",
			"COM9",
			"LPT1",
			"LPT2",
			"LPT3",
			"LPT4",
			"LPT5",
			"LPT6",
			"LPT7",
			"LPT8",
			"LPT9",
		}

		name_without_ext = Path(filename).stem.upper()
		if name_without_ext in reserved_names:
			raise SecurityError(f"Filename '{filename}' uses reserved name")

		# Sanitize filename
		sanitized = self._sanitize_filename(filename)

		# Log validation
		audit_logger.log_event(
			event_type=AuditEventType.FILE_UPLOAD,
			action="filename_validation",
			result="success",
			details={"original": filename, "sanitized": sanitized},
		)

		return sanitized

	def _sanitize_filename(self, filename: str) -> str:
		"""Sanitize filename by removing dangerous characters."""
		import re

		# Remove dangerous characters
		filename = re.sub(r'[<>:"|?*\x00-\x1f]', "_", filename)

		# Remove leading/trailing dots and spaces
		filename = filename.strip(". ")

		# Ensure filename is not empty
		if not filename:
			filename = f"file_{generate_secure_token(8)}"

		# Limit length
		if len(filename) > 255:
			name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
			max_name_length = 255 - len(ext) - 1 if ext else 255
			filename = name[:max_name_length] + ("." + ext if ext else "")

		return filename

	def validate_file_size(self, file_size: int) -> None:
		"""
		Validate file size.

		Args:
			file_size: File size in bytes

		Raises:
			ValidationError: If file size is invalid
		"""
		if file_size <= 0:
			raise ValidationError("File cannot be empty")

		if file_size > self.settings.max_file_size_bytes:
			raise ValidationError(f"File size ({file_size} bytes) exceeds maximum allowed ({self.settings.max_file_size_bytes} bytes)")

	def validate_mime_type(self, content: bytes, filename: str) -> str:
		"""
		Validate file MIME type using multiple detection methods.

		Args:
			content: File content
			filename: Filename

		Returns:
			str: Detected MIME type

		Raises:
			SecurityError: If MIME type is not allowed
			ValidationError: If MIME type detection fails
		"""
		detected_mime = self._detect_mime_type_robust(content, filename)
		
		# Get allowed MIME types from global settings
		from .config import get_settings

		settings = get_settings()
		allowed_mime_types = settings.allowed_mime_types

		# Check against allowed MIME types
		if detected_mime not in allowed_mime_types:
			raise SecurityError(f"File type '{detected_mime}' is not allowed. Allowed types: {', '.join(allowed_mime_types)}")

		# Additional validation for specific types
		if detected_mime == "application/pdf":
			self._validate_pdf_content(content)
		elif detected_mime.startswith("application/vnd.openxmlformats"):
			self._validate_office_document(content, filename)

		return detected_mime

	def _detect_mime_type_robust(self, content: bytes, filename: str) -> str:
		"""
		Robust MIME type detection using multiple methods with fallbacks.
		
		Args:
			content: File content bytes
			filename: Original filename
			
		Returns:
			str: Detected MIME type
			
		Raises:
			ValidationError: If MIME type cannot be determined
		"""
		if not content:
			raise ValidationError("Cannot detect MIME type of empty file")
		
		detection_methods = []
		
		# Method 1: Magic number detection (most reliable)
		magic_mime = self._detect_by_magic_numbers(content)
		if magic_mime:
			detection_methods.append(("magic_numbers", magic_mime))
		
		# Method 2: python-magic library (if available)
		try:
			import magic
			magic_mime_lib = magic.from_buffer(content, mime=True)
			if magic_mime_lib and magic_mime_lib != "application/octet-stream":
				detection_methods.append(("python_magic", magic_mime_lib))
		except (ImportError, Exception) as e:
			logger.debug(f"python-magic not available or failed: {e}")
		
		# Method 3: Content analysis
		content_mime = self._detect_by_content_analysis(content)
		if content_mime:
			detection_methods.append(("content_analysis", content_mime))
		
		# Method 4: File extension fallback
		extension_mime = self._detect_by_extension(filename)
		if extension_mime:
			detection_methods.append(("extension", extension_mime))
		
		# Validate consistency and choose best detection
		final_mime = self._choose_best_mime_detection(detection_methods, filename)
		
		if not final_mime:
			raise ValidationError(f"Unable to determine MIME type for file '{filename}'. Detection methods tried: {[method for method, _ in detection_methods]}")
		
		logger.debug(f"MIME type detection for '{filename}': {detection_methods} -> chosen: {final_mime}")
		return final_mime

	def _detect_by_magic_numbers(self, content: bytes) -> Optional[str]:
		"""Detect MIME type by file magic numbers (signatures)."""
		if len(content) < 4:
			return None
		
		# PDF files
		if content.startswith(b"%PDF-"):
			return "application/pdf"
		
		# Microsoft Office Open XML formats (ZIP-based)
		if content.startswith(b"PK\x03\x04") or content.startswith(b"PK\x05\x06") or content.startswith(b"PK\x07\x08"):
			# Look deeper into ZIP structure to identify Office documents
			if len(content) > 2048:
				content_sample = content[:2048].lower()
				if b"word/" in content_sample or b"[content_types].xml" in content_sample:
					# Check for specific DOCX indicators
					if b"wordprocessingml" in content[:4096].lower():
						return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
				elif b"xl/" in content_sample:
					return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
				elif b"ppt/" in content_sample:
					return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
			# Generic ZIP if we can't identify specific Office format
			return "application/zip"
		
		# Legacy Microsoft Office formats
		if content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
			return "application/msword"  # Could also be Excel or PowerPoint
		
		# RTF files
		if content.startswith(b"{\\rtf"):
			return "application/rtf"
		
		# HTML files
		if content.lstrip().lower().startswith(b"<!doctype html") or content.lstrip().lower().startswith(b"<html"):
			return "text/html"
		
		# XML files
		if content.lstrip().startswith(b"<?xml"):
			return "application/xml"
		
		return None

	def _detect_by_content_analysis(self, content: bytes) -> Optional[str]:
		"""Detect MIME type by analyzing file content patterns."""
		if len(content) == 0:
			return None
		
		# Sample first 2KB for analysis
		sample_size = min(2048, len(content))
		sample = content[:sample_size]
		
		# Check for text content
		try:
			# Try to decode as UTF-8
			decoded = sample.decode('utf-8', errors='ignore')
			
			# Calculate ratio of printable characters
			printable_chars = sum(1 for c in decoded if c.isprintable() or c.isspace())
			printable_ratio = printable_chars / len(decoded) if decoded else 0
			
			# If mostly printable characters, likely text
			if printable_ratio > 0.85:
				# Check for specific text patterns
				decoded_lower = decoded.lower()
				
				# HTML content
				if any(tag in decoded_lower for tag in ['<html', '<head', '<body', '<!doctype']):
					return "text/html"
				
				# XML content
				if decoded_lower.strip().startswith('<?xml'):
					return "application/xml"
				
				# CSV content (simple heuristic)
				lines = decoded.split('\n')[:5]  # Check first 5 lines
				if len(lines) > 1 and all(',' in line for line in lines if line.strip()):
					comma_count = sum(line.count(',') for line in lines)
					if comma_count > len(lines) * 2:  # At least 2 commas per line on average
						return "text/csv"
				
				# Plain text
				return "text/plain"
		
		except UnicodeDecodeError:
			# Try other encodings for text detection
			for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
				try:
					decoded = sample.decode(encoding, errors='ignore')
					printable_chars = sum(1 for c in decoded if c.isprintable() or c.isspace())
					printable_ratio = printable_chars / len(decoded) if decoded else 0
					
					if printable_ratio > 0.85:
						return "text/plain"
				except UnicodeDecodeError:
					continue
		
		# Binary content analysis
		# Check for common binary patterns
		if b"\x00" in sample[:100]:  # Null bytes early in file suggest binary
			return "application/octet-stream"
		
		return None

	def _detect_by_extension(self, filename: str) -> Optional[str]:
		"""Detect MIME type by file extension as fallback."""
		if not filename or '.' not in filename:
			return None
		
		extension = Path(filename).suffix.lower()
		
		extension_map = {
			'.pdf': 'application/pdf',
			'.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
			'.doc': 'application/msword',
			'.txt': 'text/plain',
			'.csv': 'text/csv',
			'.html': 'text/html',
			'.htm': 'text/html',
			'.xml': 'application/xml',
			'.rtf': 'application/rtf',
			'.zip': 'application/zip'
		}
		
		return extension_map.get(extension)

	def _choose_best_mime_detection(self, detection_methods: List[Tuple[str, str]], filename: str) -> Optional[str]:
		"""
		Choose the best MIME type from multiple detection methods.
		
		Args:
			detection_methods: List of (method_name, detected_mime) tuples
			filename: Original filename for context
			
		Returns:
			str: Best MIME type choice
		"""
		if not detection_methods:
			return None
		
		# If only one detection method succeeded, use it
		if len(detection_methods) == 1:
			return detection_methods[0][1]
		
		# Create a map of detected MIME types
		detections = {method: mime for method, mime in detection_methods}
		
		# Priority order for detection methods (most reliable first)
		method_priority = ["magic_numbers", "python_magic", "content_analysis", "extension"]
		
		# Check for consensus among methods
		mime_counts = {}
		for _, mime in detection_methods:
			mime_counts[mime] = mime_counts.get(mime, 0) + 1
		
		# If there's a clear consensus (majority agreement), use it
		max_count = max(mime_counts.values())
		consensus_mimes = [mime for mime, count in mime_counts.items() if count == max_count]
		
		if len(consensus_mimes) == 1 and max_count > 1:
			logger.debug(f"MIME type consensus reached: {consensus_mimes[0]} (agreed by {max_count} methods)")
			return consensus_mimes[0]
		
		# No consensus, use priority order
		for method in method_priority:
			if method in detections:
				chosen_mime = detections[method]
				logger.debug(f"MIME type chosen by priority: {chosen_mime} (method: {method})")
				
				# Validate the choice makes sense
				if self._validate_mime_consistency(chosen_mime, filename, detections):
					return chosen_mime
		
		# Fallback to first detection if no priority method worked
		return detection_methods[0][1]

	def _validate_mime_consistency(self, chosen_mime: str, filename: str, all_detections: Dict[str, str]) -> bool:
		"""
		Validate that the chosen MIME type is consistent with other evidence.
		
		Args:
			chosen_mime: The MIME type we want to validate
			filename: Original filename
			all_detections: All MIME types detected by different methods
			
		Returns:
			bool: True if the choice seems consistent
		"""
		# Get file extension
		extension = Path(filename).suffix.lower() if filename else ""
		
		# Define expected MIME types for extensions
		extension_mime_map = {
			'.pdf': 'application/pdf',
			'.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
			'.doc': 'application/msword',
			'.txt': 'text/plain',
			'.csv': 'text/csv'
		}
		
		expected_mime = extension_mime_map.get(extension)
		
		# If we have an expected MIME type based on extension, check consistency
		if expected_mime:
			if chosen_mime == expected_mime:
				return True
			
			# Some flexibility for text files
			if expected_mime == 'text/plain' and chosen_mime in ['text/csv', 'text/html']:
				return True
			
			# Log inconsistency but don't reject yet
			logger.warning(f"MIME type inconsistency: extension suggests {expected_mime}, but detected {chosen_mime}")
		
		# Check if the chosen MIME type appears in multiple detection methods
		mime_frequency = sum(1 for mime in all_detections.values() if mime == chosen_mime)
		
		return mime_frequency >= 1  # At least one method detected it

	def _validate_pdf_content(self, content: bytes) -> None:
		"""Validate PDF content for security issues."""
		content_lower = content.lower()

		# Check for JavaScript in PDF
		if b"/javascript" in content_lower or b"/js" in content_lower:
			raise SecurityError("PDF contains JavaScript which is not allowed")

		# Check for auto-execute actions
		if b"/openaction" in content_lower:
			raise SecurityError("PDF contains auto-execute actions which are not allowed")

		# Check for forms
		if b"/acroform" in content_lower:
			logger.warning("PDF contains forms - additional scrutiny recommended")

	def _validate_office_document(self, content: bytes, filename: str) -> None:
		"""Validate Office document content."""
		# Check for macro-enabled documents
		macro_extensions = {".docm", ".xlsm", ".pptm", ".dotm", ".xltm", ".potm"}
		file_ext = Path(filename).suffix.lower()

		if file_ext in macro_extensions:
			raise SecurityError("Macro-enabled documents are not allowed")

		# Check for embedded objects (basic check)
		if b"oleObject" in content or b"OLE" in content:
			logger.warning("Document may contain embedded objects")

	def scan_for_malicious_content(self, content: bytes, filename: str) -> None:
		"""
		Scan file content for malicious patterns.

		Args:
			content: File content
			filename: Filename

		Raises:
			SecurityError: If malicious content is detected
		"""
		if not self.settings.scan_uploaded_files:
			return

		content_lower = content.lower()

		for pattern in self.malicious_patterns:
			if pattern in content_lower:
				audit_logger.log_event(
					event_type=AuditEventType.MALICIOUS_FILE_DETECTED,
					action="malicious_pattern_detected",
					result="blocked",
					details={"filename": filename, "pattern": pattern.decode("utf-8", errors="ignore")},
					severity="high",
				)
				raise SecurityError(f"Malicious content detected in file: {filename}")

	def calculate_file_hash(self, content: bytes) -> str:
		"""Calculate SHA-256 hash of file content."""
		return hashlib.sha256(content).hexdigest()

	def validate_file(self, content: bytes, filename: str) -> Dict[str, str]:
		"""
		Comprehensive file validation.

		Args:
			content: File content
			filename: Original filename

		Returns:
			dict: Validation results

		Raises:
			SecurityError: If file fails security validation
			ValidationError: If file fails basic validation
		"""
		# Validate file size
		self.validate_file_size(len(content))

		# Validate and sanitize filename
		safe_filename = self.validate_filename(filename)

		# Validate MIME type
		mime_type = self.validate_mime_type(content, safe_filename)

		# Scan for malicious content
		self.scan_for_malicious_content(content, safe_filename)

		# Calculate file hash
		file_hash = self.calculate_file_hash(content)

		return {
			"original_filename": filename,
			"safe_filename": safe_filename,
			"mime_type": mime_type,
			"file_hash": file_hash,
			"file_size": len(content),
		}

	async def validate_upload_file(self, file) -> tuple[bytes, str, str]:
		"""
		Validate an uploaded file and return content, mime_type, and filename.

		Args:
			file: Uploaded file object

		Returns:
			tuple: (content, mime_type, validated_filename)

		Raises:
			SecurityError: If file fails security validation
			ValidationError: If file fails basic validation
		"""
		# Read file content
		content = await file.read()

		# Validate the file
		validation_result = self.validate_file(content, file.filename)

		# Return the required tuple
		return content, validation_result["mime_type"], validation_result["safe_filename"]


class TemporaryFileHandler:
	"""Secure temporary file handler with automatic cleanup."""

	def __init__(self):
		self.settings = get_settings()
		self.temp_base_dir = Path(tempfile.gettempdir()) / "contract_analyzer"
		self.temp_base_dir.mkdir(exist_ok=True, mode=0o700)

		# Security validator
		self.validator = FileSecurityValidator()

		# Track active temporary files
		self.active_files: Dict[str, Dict] = {}
		self.cleanup_task: Optional[asyncio.Task] = None

		# Cleanup task will be started when needed
		# self._start_cleanup_task()

	def _start_cleanup_task(self):
		"""Start background cleanup task."""
		if self.cleanup_task is None or self.cleanup_task.done():
			try:
				self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
			except RuntimeError:
				# No event loop running, skip cleanup task for now
				pass

	async def _periodic_cleanup(self):
		"""Periodic cleanup of old temporary files."""
		while True:
			try:
				await asyncio.sleep(3600)  # Run every hour
				self.cleanup_old_files()
			except asyncio.CancelledError:
				break
			except Exception as e:
				logger.error(f"Error in periodic cleanup: {e}")

	def save_temporary_file(self, content: bytes, filename: str, validate: bool = True) -> str:
		"""
		Save content to a secure temporary file.

		Args:
		    content: File content bytes
		    filename: Original filename (for extension)
		    validate: Whether to perform security validation

		Returns:
		    str: Path to temporary file

		Raises:
			SecurityError: If file fails security validation
			ValidationError: If file fails basic validation
		"""
		# Validate file if requested
		if validate:
			validation_result = self.validator.validate_file(content, filename)
			safe_filename = validation_result["safe_filename"]
			file_hash = validation_result["file_hash"]
		else:
			safe_filename = self.validator._sanitize_filename(filename)
			file_hash = self.validator.calculate_file_hash(content)

		# Generate secure temporary filename
		file_id = generate_secure_token(16)
		file_ext = Path(safe_filename).suffix
		temp_filename = f"{file_id}{file_ext}"
		temp_path = self.temp_base_dir / temp_filename

		# Encrypt content if enabled
		if self.settings.encrypt_temp_files:
			content = self._encrypt_content(content)

		# Write file with secure permissions
		with open(temp_path, "wb") as f:
			f.write(content)

		# Set secure permissions (owner read/write only)
		temp_path.chmod(0o600)

		# Track the file
		self.active_files[str(temp_path)] = {
			"created_at": time.time(),
			"filename": filename,
			"safe_filename": safe_filename,
			"size": len(content),
			"file_id": file_id,
			"file_hash": file_hash,
			"encrypted": self.settings.encrypt_temp_files,
		}

		# Log file creation
		audit_logger.log_event(
			event_type=AuditEventType.FILE_UPLOAD,
			action="temp_file_created",
			result="success",
			details={"file_id": file_id, "original_filename": filename, "safe_filename": safe_filename, "file_hash": file_hash, "size": len(content)},
		)

		logger.debug(f"Created temporary file: {temp_path}")
		return str(temp_path)

	def _encrypt_content(self, content: bytes) -> bytes:
		"""Encrypt file content if encryption is enabled."""
		if not self.settings.encryption_key:
			logger.warning("Encryption requested but no encryption key configured")
			return content

		try:
			from cryptography.fernet import Fernet

			# Use the configured encryption key or generate one
			key = self.settings.encryption_key.get_secret_value().encode()
			if len(key) != 32:
				# Derive a proper key from the configured key
				import hashlib

				key = hashlib.sha256(key).digest()

			# Encode key for Fernet
			import base64

			fernet_key = base64.urlsafe_b64encode(key)
			fernet = Fernet(fernet_key)

			return fernet.encrypt(content)
		except ImportError:
			logger.warning("Cryptography library not available for encryption")
			return content
		except Exception as e:
			logger.error(f"Failed to encrypt content: {e}")
			return content

	def _decrypt_content(self, content: bytes) -> bytes:
		"""Decrypt file content if it was encrypted."""
		if not self.settings.encryption_key:
			return content

		try:
			from cryptography.fernet import Fernet

			key = self.settings.encryption_key.get_secret_value().encode()
			if len(key) != 32:
				import hashlib

				key = hashlib.sha256(key).digest()

			import base64

			fernet_key = base64.urlsafe_b64encode(key)
			fernet = Fernet(fernet_key)

			return fernet.decrypt(content)
		except ImportError:
			return content
		except Exception as e:
			logger.error(f"Failed to decrypt content: {e}")
			return content

	@contextmanager
	def temporary_file(self, content: bytes, filename: str):
		"""
		Context manager for temporary file that ensures cleanup.

		Args:
		    content: File content bytes
		    filename: Original filename

		Yields:
		    str: Path to temporary file
		"""
		temp_path = None
		try:
			temp_path = self.save_temporary_file(content, filename)
			yield temp_path
		finally:
			if temp_path:
				self.cleanup_file(temp_path)

	def cleanup_file(self, file_path: str) -> bool:
		"""
		Securely delete a temporary file.

		Args:
		    file_path: Path to file to cleanup

		Returns:
		    bool: True if file was cleaned up successfully
		"""
		try:
			path = Path(file_path)

			if path.exists():
				# Secure deletion - overwrite with random data first
				try:
					with open(path, "r+b") as f:
						size = f.seek(0, 2)  # Get file size
						f.seek(0)
						f.write(os.urandom(size))
						f.flush()
						os.fsync(f.fileno())
				except Exception as e:
					logger.warning(f"Could not securely overwrite {file_path}: {e}")

				# Remove the file
				path.unlink()
				logger.debug(f"Cleaned up temporary file: {file_path}")

			# Remove from tracking
			if file_path in self.active_files:
				del self.active_files[file_path]

			return True

		except Exception as e:
			logger.error(f"Failed to cleanup temporary file {file_path}: {e}")
			return False

	def cleanup_old_files(self, max_age_hours: Optional[int] = None) -> int:
		"""
		Clean up old temporary files.

		Args:
		    max_age_hours: Maximum age in hours (uses config default if None)

		Returns:
		    int: Number of files cleaned up
		"""
		if max_age_hours is None:
			max_age_hours = self.settings.temp_file_cleanup_hours

		current_time = time.time()
		max_age_seconds = max_age_hours * 3600
		cleaned_count = 0

		# Find files to cleanup
		files_to_cleanup = []

		for file_path, file_info in self.active_files.items():
			file_age = current_time - file_info["created_at"]
			if file_age > max_age_seconds:
				files_to_cleanup.append(file_path)

		# Also check for orphaned files in temp directory
		try:
			for temp_file in self.temp_base_dir.glob("*"):
				if temp_file.is_file():
					file_age = current_time - temp_file.stat().st_mtime
					if file_age > max_age_seconds and str(temp_file) not in self.active_files:
						files_to_cleanup.append(str(temp_file))
		except Exception as e:
			logger.error(f"Error scanning temp directory: {e}")

		# Cleanup identified files
		for file_path in files_to_cleanup:
			if self.cleanup_file(file_path):
				cleaned_count += 1

		if cleaned_count > 0:
			logger.info(f"Cleaned up {cleaned_count} old temporary files")

		return cleaned_count

	def get_active_files_info(self) -> Dict:
		"""Get information about active temporary files."""
		total_size = sum(info["size"] for info in self.active_files.values())

		return {
			"count": len(self.active_files),
			"total_size_bytes": total_size,
			"total_size_mb": total_size / (1024 * 1024),
			"files": [
				{"path": path, "filename": info["filename"], "size_bytes": info["size"], "age_seconds": time.time() - info["created_at"]}
				for path, info in self.active_files.items()
			],
		}

	def file_exists(self, file_id: str) -> bool:
		"""
		Check if a file exists by file ID.
		
		Args:
		    file_id: The file ID (hash) to check
		    
		Returns:
		    bool: True if file exists
		"""
		# Look for file by file_id in active files
		for file_path, file_info in self.active_files.items():
			if file_info.get("file_id") == file_id or file_info.get("file_hash") == file_id:
				# Verify file actually exists on disk
				return Path(file_path).exists()
		return False
	
	def get_file_info(self, file_id: str) -> Optional[Dict]:
		"""
		Get file information by file ID.
		
		Args:
		    file_id: The file ID (hash) to get info for
		    
		Returns:
		    dict: File information or None if not found
		"""
		# Look for file by file_id in active files
		for file_path, file_info in self.active_files.items():
			if file_info.get("file_id") == file_id or file_info.get("file_hash") == file_id:
				# Verify file actually exists on disk
				if Path(file_path).exists():
					# Add additional info
					file_info_copy = file_info.copy()
					file_info_copy.update({
						"temp_path": file_path,
						"upload_timestamp": datetime.fromtimestamp(file_info["created_at"]).isoformat(),
						"expires_at": datetime.fromtimestamp(
							file_info["created_at"] + (self.settings.temp_file_cleanup_hours * 3600)
						).isoformat(),
						"age_seconds": time.time() - file_info["created_at"]
					})
					return file_info_copy
		return None
	
	def get_file_path_by_id(self, file_id: str) -> Optional[str]:
		"""
		Get file path by file ID.
		
		Args:
		    file_id: The file ID (hash) to get path for
		    
		Returns:
		    str: File path or None if not found
		"""
		for file_path, file_info in self.active_files.items():
			if file_info.get("file_id") == file_id or file_info.get("file_hash") == file_id:
				if Path(file_path).exists():
					return file_path
		return None

	def cleanup_all(self) -> int:
		"""
		Clean up all temporary files.

		Returns:
		    int: Number of files cleaned up
		"""
		files_to_cleanup = list(self.active_files.keys())
		cleaned_count = 0

		for file_path in files_to_cleanup:
			if self.cleanup_file(file_path):
				cleaned_count += 1

		# Cancel cleanup task
		if self.cleanup_task and not self.cleanup_task.done():
			self.cleanup_task.cancel()

		logger.info(f"Cleaned up all {cleaned_count} temporary files")
		return cleaned_count

	def __del__(self):
		"""Cleanup on destruction."""
		try:
			self.cleanup_all()
		except Exception:
			pass


class MemoryManager:
	"""Memory usage monitoring and management."""

	def __init__(self):
		self.settings = get_settings()
		self.memory_threshold_mb = 1024  # 1GB threshold
		self.active_processes: Set[str] = set()

	def check_memory_usage(self) -> Dict:
		"""
		Check current memory usage.

		Returns:
		    dict: Memory usage information
		"""
		try:
			import psutil

			process = psutil.Process()
			memory_info = process.memory_info()

			return {
				"rss_mb": memory_info.rss / (1024 * 1024),
				"vms_mb": memory_info.vms / (1024 * 1024),
				"percent": process.memory_percent(),
				"available_mb": psutil.virtual_memory().available / (1024 * 1024),
				"threshold_mb": self.memory_threshold_mb,
				"over_threshold": memory_info.rss / (1024 * 1024) > self.memory_threshold_mb,
			}
		except ImportError:
			logger.warning("psutil not available for memory monitoring")
			return {"error": "psutil not available"}
		except Exception as e:
			logger.error(f"Error checking memory usage: {e}")
			return {"error": str(e)}

	def register_process(self, process_id: str) -> None:
		"""Register an active process for monitoring."""
		self.active_processes.add(process_id)
		logger.debug(f"Registered process: {process_id}")

	def unregister_process(self, process_id: str) -> None:
		"""Unregister a completed process."""
		self.active_processes.discard(process_id)
		logger.debug(f"Unregistered process: {process_id}")

	def get_active_processes(self) -> Set[str]:
		"""Get set of active process IDs."""
		return self.active_processes.copy()

	def force_garbage_collection(self) -> None:
		"""Force garbage collection to free memory."""
		import gc

		before_count = len(gc.get_objects())
		collected = gc.collect()
		after_count = len(gc.get_objects())

		logger.info(f"Garbage collection: {collected} objects collected, objects before: {before_count}, after: {after_count}")


# Global instances
temp_file_handler = TemporaryFileHandler()
memory_manager = MemoryManager()
