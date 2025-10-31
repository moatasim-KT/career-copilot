"""
Comprehensive file validation system with magic number detection and security checks.
"""

import hashlib
import magic
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List

from ..core.logging import get_logger

logger = get_logger(__name__)


class FileType(Enum):
	"""Supported file types."""

	PDF = "pdf"
	DOCX = "docx"
	TXT = "txt"
	UNKNOWN = "unknown"


class ValidationStatus(Enum):
	"""File validation status."""

	VALID = "valid"
	INVALID = "invalid"
	SUSPICIOUS = "suspicious"
	QUARANTINED = "quarantined"


@dataclass
class FileValidationResult:
	"""Result of file validation."""

	is_valid: bool
	file_type: FileType
	mime_type: str
	file_size: int
	file_hash: str
	status: ValidationStatus
	threats_detected: List[str]
	warnings: List[str]
	metadata: Dict[str, any]


class FileSecurityValidator:
	"""Comprehensive file security validator with magic number detection."""

	# Allowed MIME types with their corresponding file extensions
	ALLOWED_MIME_TYPES = {
		"application/pdf": FileType.PDF,
		"application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,
		"text/plain": FileType.TXT,
	}

	# File extensions to MIME type mapping
	EXTENSION_TO_MIME = {
		".pdf": "application/pdf",
		".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
		".txt": "text/plain",
	}

	# Magic number signatures for file type detection
	MAGIC_SIGNATURES = {
		b"%PDF-": FileType.PDF,
		b"PK\x03\x04": FileType.DOCX,  # ZIP-based format
	}

	# Maximum file sizes (in bytes)
	MAX_FILE_SIZES = {
		FileType.PDF: 50 * 1024 * 1024,  # 50MB
		FileType.DOCX: 25 * 1024 * 1024,  # 25MB
		FileType.TXT: 10 * 1024 * 1024,  # 10MB
	}

	# Suspicious patterns to detect
	SUSPICIOUS_PATTERNS = [
		b"<script",
		b"javascript:",
		b"vbscript:",
		b"onload=",
		b"onerror=",
		b"eval(",
		b"document.write",
		b"<?php",
		b"<%",
		b"exec(",
		b"system(",
		b"shell_exec(",
		b"passthru(",
	]

	# Dangerous file extensions that should never be allowed
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
		".iso",
		".msi",
		".dll",
		".so",
		".dylib",
		".php",
		".asp",
		".jsp",
		".py",
		".rb",
		".pl",
		".ps1",
		".psm1",
		".psd1",
		".ps1xml",
		".pssc",
		".psrc",
		".cdxml",
		".wsf",
		".wsh",
		".hta",
		".cpl",
		".msc",
		".reg",
		".lnk",
		".url",
		".inf",
		".ins",
		".isp",
		".isu",
		".job",
		".jse",
		".ksh",
		".mad",
		".maf",
		".mag",
		".mam",
		".maq",
		".mar",
		".mas",
		".mat",
		".mau",
		".mav",
		".maw",
		".mcf",
		".mda",
		".mdb",
		".mde",
		".mdt",
		".mdw",
		".mdz",
		".msc",
		".msi",
		".msp",
		".mst",
		".ops",
		".pcd",
		".pif",
		".prf",
		".prg",
		".pst",
		".scf",
		".scr",
		".sct",
		".shb",
		".shs",
		".tmp",
		".url",
		".vb",
		".vbe",
		".vbs",
		".vxd",
		".wsc",
		".wsf",
		".wsh",
		".xnk",
		".application",
		".gadget",
		".msp",
		".mst",
	}

	def __init__(self):
		"""Initialize the file validator."""
		self.magic_detector = magic.Magic(mime=True)

	async def validate_file(self, file_content: bytes, filename: str) -> FileValidationResult:
		"""
		Perform comprehensive file validation.

		Args:
		    file_content: Raw file content as bytes
		    filename: Original filename

		Returns:
		    FileValidationResult with validation details
		"""
		logger.info(f"Starting validation for file: {filename}")

		# Initialize result
		result = FileValidationResult(
			is_valid=False,
			file_type=FileType.UNKNOWN,
			mime_type="",
			file_size=len(file_content),
			file_hash="",
			status=ValidationStatus.INVALID,
			threats_detected=[],
			warnings=[],
			metadata={},
		)

		try:
			# Generate file hash
			result.file_hash = hashlib.sha256(file_content).hexdigest()

			# Basic filename validation
			filename_issues = self._validate_filename(filename)
			if filename_issues:
				result.warnings.extend(filename_issues)

			# Check for dangerous extensions
			if self._has_dangerous_extension(filename):
				result.threats_detected.append("Dangerous file extension detected")
				result.status = ValidationStatus.QUARANTINED
				return result

			# Detect MIME type using magic numbers
			detected_mime = self._detect_mime_type(file_content)
			result.mime_type = detected_mime

			# Validate file type against allowed types
			file_type = self._get_file_type_from_mime(detected_mime)
			result.file_type = file_type

			# Check file size limits first (even for unknown types)
			size_valid = self._validate_file_size(file_type, len(file_content))
			if not size_valid:
				result.threats_detected.append(f"File size exceeds limit for {file_type.value}")
				result.status = ValidationStatus.INVALID
				return result

			if file_type == FileType.UNKNOWN:
				result.threats_detected.append(f"Unsupported file type: {detected_mime}")
				result.status = ValidationStatus.INVALID
				return result

			# Validate file extension matches content
			extension_valid = self._validate_extension_match(filename, detected_mime)
			if not extension_valid:
				result.threats_detected.append("File extension does not match content")
				result.status = ValidationStatus.SUSPICIOUS

			# Scan for suspicious patterns
			suspicious_patterns = self._scan_for_suspicious_patterns(file_content)
			if suspicious_patterns:
				result.threats_detected.extend(suspicious_patterns)
				result.status = ValidationStatus.SUSPICIOUS

			# Perform file-type specific validation
			type_specific_issues = await self._validate_file_type_specific(file_content, file_type)
			if type_specific_issues:
				result.warnings.extend(type_specific_issues)

			# Extract metadata
			result.metadata = self._extract_metadata(file_content, file_type, filename)

			# Determine final validation status
			if not result.threats_detected:
				result.is_valid = True
				result.status = ValidationStatus.VALID
			elif result.status == ValidationStatus.INVALID:
				result.is_valid = False
			else:
				# Suspicious files are considered invalid for security
				result.is_valid = False

			logger.info(f"Validation completed for {filename}: {result.status.value}")
			return result

		except Exception as e:
			logger.error(f"Error during file validation: {e}", exc_info=True)
			result.threats_detected.append(f"Validation error: {e!s}")
			result.status = ValidationStatus.INVALID
			return result

	def _validate_filename(self, filename: str) -> List[str]:
		"""Validate filename for security issues."""
		issues = []

		if not filename:
			issues.append("Empty filename")
			return issues

		# Check filename length
		if len(filename) > 255:
			issues.append("Filename too long")

		# Check for dangerous characters
		dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\0", "\n", "\r"]
		for char in dangerous_chars:
			if char in filename:
				issues.append(f"Dangerous character in filename: {char}")

		# Check for path traversal attempts
		if ".." in filename or "/" in filename or "\\" in filename:
			issues.append("Path traversal attempt detected in filename")

		# Check for hidden files
		if filename.startswith("."):
			issues.append("Hidden file detected")

		return issues

	def _has_dangerous_extension(self, filename: str) -> bool:
		"""Check if filename has a dangerous extension."""
		path = Path(filename)
		extension = path.suffix.lower()
		return extension in self.DANGEROUS_EXTENSIONS

	def _detect_mime_type(self, file_content: bytes) -> str:
		"""Detect MIME type using magic numbers."""
		try:
			# Use python-magic for accurate detection
			mime_type = self.magic_detector.from_buffer(file_content)
			return mime_type
		except Exception as e:
			logger.warning(f"Magic number detection failed: {e}")
			return "application/octet-stream"

	def _get_file_type_from_mime(self, mime_type: str) -> FileType:
		"""Get FileType enum from MIME type."""
		return self.ALLOWED_MIME_TYPES.get(mime_type, FileType.UNKNOWN)

	def _validate_extension_match(self, filename: str, detected_mime: str) -> bool:
		"""Validate that file extension matches detected MIME type."""
		path = Path(filename)
		extension = path.suffix.lower()

		expected_mime = self.EXTENSION_TO_MIME.get(extension)
		return expected_mime == detected_mime

	def _validate_file_size(self, file_type: FileType, file_size: int) -> bool:
		"""Validate file size against limits."""
		max_size = self.MAX_FILE_SIZES.get(file_type, 1024 * 1024)  # 1MB default for unknown types
		return file_size <= max_size

	def _scan_for_suspicious_patterns(self, file_content: bytes) -> List[str]:
		"""Scan file content for suspicious patterns."""
		threats = []

		# Convert to lowercase for case-insensitive matching
		content_lower = file_content.lower()

		for pattern in self.SUSPICIOUS_PATTERNS:
			if pattern in content_lower:
				threats.append(f"Suspicious pattern detected: {pattern.decode('utf-8', errors='ignore')}")

		# Check for excessive null bytes (potential binary injection)
		null_count = file_content.count(b"\x00")
		if null_count > 100:  # Arbitrary threshold
			threats.append(f"Excessive null bytes detected: {null_count}")

		# Check for very long lines (potential buffer overflow attempt)
		lines = file_content.split(b"\n")
		for i, line in enumerate(lines[:100]):  # Check first 100 lines
			if len(line) > 10000:  # 10KB line limit
				threats.append(f"Extremely long line detected at line {i + 1}")
				break

		return threats

	async def _validate_file_type_specific(self, file_content: bytes, file_type: FileType) -> List[str]:
		"""Perform file-type specific validation."""
		warnings = []

		if file_type == FileType.PDF:
			warnings.extend(self._validate_pdf_specific(file_content))
		elif file_type == FileType.DOCX:
			warnings.extend(self._validate_docx_specific(file_content))
		elif file_type == FileType.TXT:
			warnings.extend(self._validate_txt_specific(file_content))

		return warnings

	def _validate_pdf_specific(self, file_content: bytes) -> List[str]:
		"""PDF-specific validation."""
		warnings = []

		# Check PDF version
		if file_content.startswith(b"%PDF-"):
			version_line = file_content.split(b"\n")[0]
			if b"%PDF-1." in version_line:
				version = version_line[6:9]
				if version < b"1.4":
					warnings.append(f"Old PDF version detected: {version.decode()}")

		# Check for JavaScript in PDF
		if b"/JavaScript" in file_content or b"/JS" in file_content:
			warnings.append("JavaScript detected in PDF")

		# Check for forms
		if b"/AcroForm" in file_content:
			warnings.append("PDF contains forms")

		# Check for embedded files
		if b"/EmbeddedFile" in file_content:
			warnings.append("PDF contains embedded files")

		return warnings

	def _validate_docx_specific(self, file_content: bytes) -> List[str]:
		"""DOCX-specific validation."""
		warnings = []

		# DOCX files are ZIP archives, basic ZIP validation
		if not file_content.startswith(b"PK"):
			warnings.append("Invalid DOCX structure")

		# Check for macros (simplified check)
		if b"vbaProject.bin" in file_content:
			warnings.append("DOCX contains macros")

		# Check for external links
		if b"http://" in file_content or b"https://" in file_content:
			warnings.append("DOCX contains external links")

		return warnings

	def _validate_txt_specific(self, file_content: bytes) -> List[str]:
		"""TXT-specific validation."""
		warnings = []

		# Check encoding
		try:
			file_content.decode("utf-8")
		except UnicodeDecodeError:
			warnings.append("Non-UTF-8 encoding detected")

		# Check for binary content in text file
		if b"\x00" in file_content:
			warnings.append("Binary content detected in text file")

		return warnings

	def _extract_metadata(self, file_content: bytes, file_type: FileType, filename: str) -> Dict[str, any]:
		"""Extract file metadata."""
		metadata = {
			"filename": filename,
			"file_size": len(file_content),
			"file_type": file_type.value,
		}

		# Add file-type specific metadata
		if file_type == FileType.PDF:
			metadata.update(self._extract_pdf_metadata(file_content))
		elif file_type == FileType.DOCX:
			metadata.update(self._extract_docx_metadata(file_content))
		elif file_type == FileType.TXT:
			metadata.update(self._extract_txt_metadata(file_content))

		return metadata

	def _extract_pdf_metadata(self, file_content: bytes) -> Dict[str, any]:
		"""Extract PDF metadata."""
		metadata = {}

		# Extract PDF version
		if file_content.startswith(b"%PDF-"):
			version_line = file_content.split(b"\n")[0]
			metadata["pdf_version"] = version_line.decode("utf-8", errors="ignore")

		# Count pages (simplified)
		page_count = file_content.count(b"/Type /Page")
		metadata["estimated_pages"] = page_count

		return metadata

	def _extract_docx_metadata(self, file_content: bytes) -> Dict[str, any]:
		"""Extract DOCX metadata."""
		metadata = {}

		# Basic ZIP structure validation
		metadata["is_zip_format"] = file_content.startswith(b"PK")

		return metadata

	def _extract_txt_metadata(self, file_content: bytes) -> Dict[str, any]:
		"""Extract TXT metadata."""
		metadata = {}

		try:
			text_content = file_content.decode("utf-8")
			metadata["line_count"] = text_content.count("\n") + 1
			metadata["character_count"] = len(text_content)
			metadata["encoding"] = "utf-8"
		except UnicodeDecodeError:
			metadata["encoding"] = "unknown"

		return metadata
