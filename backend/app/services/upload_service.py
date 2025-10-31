"""
Enhanced upload service with chunked upload support, validation, and progress tracking.
"""

import hashlib
import os
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import HTTPException
from ..core.logging import get_logger
from ..core.file_handler import temp_file_handler
from ..models.upload_models import (
	UploadSession,
	UploadProgress,
	UploadStatus,
	ChunkInfo,
	ChunkStatus,
	FileValidationResult,
	UploadRequest,
	DuplicateFileInfo,
)
from ..utils.security import file_validator

logger = get_logger(__name__)


class UploadSessionManager:
	"""Manages upload sessions for chunked uploads."""

	def __init__(self):
		self.active_sessions: Dict[str, UploadSession] = {}
		self.session_chunks: Dict[str, Dict[int, ChunkInfo]] = {}
		self.session_files: Dict[str, str] = {}  # session_id -> temp_file_path
		self.cleanup_interval = 3600  # 1 hour
		self._last_cleanup = time.time()

	async def create_session(self, request: UploadRequest) -> UploadSession:
		"""Create a new upload session."""
		session = UploadSession(
			filename=request.filename,
			total_size=request.total_size,
			chunk_size=request.chunk_size,
			total_chunks=(request.total_size + request.chunk_size - 1) // request.chunk_size,
			file_hash=request.file_hash,
			metadata=request.metadata,
			expires_at=datetime.now(timezone.utc) + timedelta(hours=24),  # 24 hour expiry
		)

		self.active_sessions[session.session_id] = session
		self.session_chunks[session.session_id] = {}

		# Create temporary file for chunks
		temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=f"upload_{session.session_id}_")
		self.session_files[session.session_id] = temp_file.name
		temp_file.close()

		logger.info(f"Created upload session {session.session_id} for file {request.filename}")
		return session

	def get_session(self, session_id: str) -> Optional[UploadSession]:
		"""Get an upload session by ID."""
		return self.active_sessions.get(session_id)

	async def upload_chunk(self, session_id: str, chunk_index: int, chunk_data: bytes, chunk_hash: str) -> Tuple[bool, str]:
		"""Upload a chunk to the session."""
		session = self.get_session(session_id)
		if not session:
			return False, "Session not found"

		if session.status not in [UploadStatus.PENDING, UploadStatus.IN_PROGRESS]:
			return False, f"Session is in {session.status} state"

		# Validate chunk hash
		calculated_hash = hashlib.sha256(chunk_data).hexdigest()
		if calculated_hash != chunk_hash:
			return False, "Chunk hash mismatch"

		# Validate chunk index
		if chunk_index >= session.total_chunks or chunk_index < 0:
			return False, f"Invalid chunk index {chunk_index}"

		# Check if chunk already uploaded
		if chunk_index in self.session_chunks[session_id]:
			existing_chunk = self.session_chunks[session_id][chunk_index]
			if existing_chunk.status == ChunkStatus.COMPLETED:
				return True, "Chunk already uploaded"

		try:
			# Write chunk to temporary file
			temp_file_path = self.session_files[session_id]
			with open(temp_file_path, "r+b") as f:
				f.seek(chunk_index * session.chunk_size)
				f.write(chunk_data)

			# Update chunk info
			chunk_info = ChunkInfo(
				chunk_index=chunk_index,
				chunk_size=len(chunk_data),
				chunk_hash=chunk_hash,
				status=ChunkStatus.COMPLETED,
				uploaded_at=datetime.now(timezone.utc),
			)
			self.session_chunks[session_id][chunk_index] = chunk_info

			# Update session progress
			session.uploaded_size += len(chunk_data)
			session.completed_chunks += 1
			session.updated_at = datetime.now(timezone.utc)
			session.status = UploadStatus.IN_PROGRESS

			# Check if upload is complete
			if session.completed_chunks >= session.total_chunks:
				await self._finalize_upload(session_id)

			logger.debug(f"Uploaded chunk {chunk_index} for session {session_id}")
			return True, "Chunk uploaded successfully"

		except Exception as e:
			logger.error(f"Error uploading chunk {chunk_index} for session {session_id}: {e}")
			return False, f"Failed to upload chunk: {e!s}"

	async def _finalize_upload(self, session_id: str) -> bool:
		"""Finalize the upload and validate the complete file."""
		session = self.get_session(session_id)
		if not session:
			return False

		try:
			temp_file_path = self.session_files[session_id]

			# Read complete file and calculate hash
			with open(temp_file_path, "rb") as f:
				file_content = f.read()

			calculated_hash = hashlib.sha256(file_content).hexdigest()

			# Validate file hash if provided
			if session.file_hash and session.file_hash != calculated_hash:
				session.status = UploadStatus.FAILED
				logger.error(f"File hash mismatch for session {session_id}")
				return False

			# Update session with calculated hash
			session.file_hash = calculated_hash
			session.status = UploadStatus.COMPLETED
			session.updated_at = datetime.now(timezone.utc)

			logger.info(f"Upload completed for session {session_id}")
			return True

		except Exception as e:
			session.status = UploadStatus.FAILED
			logger.error(f"Error finalizing upload for session {session_id}: {e}")
			return False

	def get_upload_progress(self, session_id: str) -> Optional[UploadProgress]:
		"""Get upload progress for a session."""
		session = self.get_session(session_id)
		if not session:
			return None

		return UploadProgress(
			session_id=session_id,
			filename=session.filename,
			progress_percentage=session.progress_percentage,
			uploaded_size=session.uploaded_size,
			total_size=session.total_size,
			current_chunk=session.completed_chunks,
			total_chunks=session.total_chunks,
			status=session.status,
		)

	async def cancel_session(self, session_id: str) -> bool:
		"""Cancel an upload session."""
		session = self.get_session(session_id)
		if not session:
			return False

		session.status = UploadStatus.CANCELLED
		session.updated_at = datetime.now(timezone.utc)

		# Clean up temporary file
		if session_id in self.session_files:
			temp_file_path = self.session_files[session_id]
			try:
				if os.path.exists(temp_file_path):
					os.unlink(temp_file_path)
			except Exception as e:
				logger.error(f"Error cleaning up temp file for session {session_id}: {e}")

		logger.info(f"Cancelled upload session {session_id}")
		return True

	async def cleanup_expired_sessions(self):
		"""Clean up expired upload sessions."""
		current_time = datetime.now(timezone.utc)
		expired_sessions = []

		for session_id, session in self.active_sessions.items():
			if session.expires_at and session.expires_at < current_time:
				expired_sessions.append(session_id)

		for session_id in expired_sessions:
			await self.cancel_session(session_id)
			del self.active_sessions[session_id]
			if session_id in self.session_chunks:
				del self.session_chunks[session_id]
			if session_id in self.session_files:
				del self.session_files[session_id]

		if expired_sessions:
			logger.info(f"Cleaned up {len(expired_sessions)} expired upload sessions")

	def get_completed_file_path(self, session_id: str) -> Optional[str]:
		"""Get the path to the completed uploaded file."""
		session = self.get_session(session_id)
		if not session or session.status != UploadStatus.COMPLETED:
			return None

		return self.session_files.get(session_id)


class EnhancedUploadService:
	"""Enhanced upload service with comprehensive validation and progress tracking."""

	def __init__(self):
		self.session_manager = UploadSessionManager()
		self.duplicate_cache: Dict[str, DuplicateFileInfo] = {}
		self._load_existing_files()

	def _load_existing_files(self):
		"""Load existing files for duplicate detection."""
		try:
			# Load from temp_file_handler active files
			for file_path, file_info in temp_file_handler.active_files.items():
				file_hash = file_info.get("file_hash") or file_info.get("file_id")
				if file_hash:
					self.duplicate_cache[file_hash] = DuplicateFileInfo(
						file_id=file_hash,
						filename=file_info.get("filename", "unknown"),
						file_size=file_info.get("size", 0),
						upload_date=datetime.fromtimestamp(file_info.get("created_at", time.time())),
						file_hash=file_hash,
						metadata=file_info.get("metadata", {}),
					)
		except Exception as e:
			logger.error(f"Error loading existing files for duplicate detection: {e}")

	async def validate_upload_request(self, request: UploadRequest) -> FileValidationResult:
		"""Validate an upload request."""
		try:
			# Basic validation
			if not request.filename:
				raise ValueError("Filename is required")

			if request.total_size <= 0:
				raise ValueError("File size must be greater than 0")

			if request.total_size > 100 * 1024 * 1024:  # 100MB limit
				raise ValueError("File size exceeds maximum limit of 100MB")

			# Validate filename
			safe_filename = file_validator.validate_filename(request.filename)

			# Check for duplicates if hash provided
			duplicate_detected = False
			existing_file_id = None
			if request.file_hash and request.file_hash in self.duplicate_cache:
				duplicate_detected = True
				existing_file_id = request.file_hash

			return FileValidationResult(
				is_valid=True,
				mime_type="application/octet-stream",  # Will be determined from content
				detected_type="unknown",
				file_size=request.total_size,
				file_hash=request.file_hash or "",
				safe_filename=safe_filename,
				original_filename=request.filename,
				duplicate_detected=duplicate_detected,
				existing_file_id=existing_file_id,
			)

		except Exception as e:
			return FileValidationResult(
				is_valid=False,
				mime_type="",
				detected_type="",
				file_size=request.total_size,
				file_hash="",
				safe_filename="",
				original_filename=request.filename,
				errors=[str(e)],
			)

	async def validate_file_content(self, file_content: bytes, filename: str) -> FileValidationResult:
		"""Validate complete file content."""
		try:
			# Calculate file hash first
			file_hash = hashlib.sha256(file_content).hexdigest()

			# Check for duplicates
			duplicate_detected = file_hash in self.duplicate_cache
			existing_file_id = file_hash if duplicate_detected else None

			# Use existing file validator methods
			safe_filename = file_validator.validate_filename(filename)

			# Validate file size
			file_validator.validate_file_size(len(file_content))

			# Validate file content
			file_validator.validate_file_content(file_content, safe_filename)

			# Scan for malicious content
			file_validator.scan_for_malicious_content(file_content, safe_filename)

			# Detect MIME type
			import magic

			try:
				mime_type = magic.from_buffer(file_content, mime=True)
			except Exception:
				mime_type = "application/octet-stream"

			# Determine file type from extension
			file_ext = Path(safe_filename).suffix.lower()
			detected_type = {".pdf": "pdf", ".docx": "docx", ".doc": "doc", ".txt": "txt"}.get(file_ext, "unknown")

			return FileValidationResult(
				is_valid=True,
				mime_type=mime_type,
				detected_type=detected_type,
				file_size=len(file_content),
				file_hash=file_hash,
				safe_filename=safe_filename,
				original_filename=filename,
				warnings=[],
				errors=[],
				security_scan_passed=True,
				duplicate_detected=duplicate_detected,
				existing_file_id=existing_file_id,
			)

		except Exception as e:
			logger.error(f"Error validating file content: {e}")
			file_hash = hashlib.sha256(file_content).hexdigest()

			return FileValidationResult(
				is_valid=False,
				mime_type="",
				detected_type="",
				file_size=len(file_content),
				file_hash=file_hash,
				safe_filename="",
				original_filename=filename,
				errors=[f"Validation error: {e!s}"],
			)

	async def create_upload_session(self, request: UploadRequest) -> Tuple[UploadSession, FileValidationResult]:
		"""Create a new upload session with validation."""
		# Validate the request
		validation_result = await self.validate_upload_request(request)

		if not validation_result.is_valid:
			raise HTTPException(
				status_code=400, detail={"error": "Validation failed", "errors": validation_result.errors, "warnings": validation_result.warnings}
			)

		# Check for duplicates
		if validation_result.duplicate_detected:
			duplicate_info = self.duplicate_cache[validation_result.existing_file_id]
			raise HTTPException(
				status_code=409,
				detail={
					"error": "Duplicate file detected",
					"message": f"File with hash {validation_result.file_hash} already exists",
					"duplicate_info": duplicate_info.dict(),
					"existing_file_id": validation_result.existing_file_id,
				},
			)

		# Create session
		session = await self.session_manager.create_session(request)

		return session, validation_result

	async def upload_chunk(self, session_id: str, chunk_index: int, chunk_data: bytes, chunk_hash: str) -> Tuple[bool, str, Optional[UploadProgress]]:
		"""Upload a chunk and return progress."""
		success, message = await self.session_manager.upload_chunk(session_id, chunk_index, chunk_data, chunk_hash)
		progress = self.session_manager.get_upload_progress(session_id)

		return success, message, progress

	async def finalize_upload(self, session_id: str) -> Tuple[bool, Optional[str], Optional[FileValidationResult]]:
		"""Finalize upload and perform final validation."""
		session = self.session_manager.get_session(session_id)
		if not session:
			return False, "Session not found", None

		if session.status != UploadStatus.COMPLETED:
			return False, f"Upload not completed (status: {session.status})", None

		try:
			# Get completed file
			file_path = self.session_manager.get_completed_file_path(session_id)
			if not file_path or not os.path.exists(file_path):
				return False, "Uploaded file not found", None

			# Read and validate complete file
			with open(file_path, "rb") as f:
				file_content = f.read()

			validation_result = await self.validate_file_content(file_content, session.filename)

			if not validation_result.is_valid:
				return False, "File validation failed", validation_result

			# Move file to permanent storage
			permanent_path = temp_file_handler.save_temporary_file(
				file_content,
				validation_result.safe_filename,
				validate=False,  # Already validated
			)

			# Update duplicate cache
			self.duplicate_cache[validation_result.file_hash] = DuplicateFileInfo(
				file_id=validation_result.file_hash,
				filename=validation_result.safe_filename,
				file_size=validation_result.file_size,
				upload_date=datetime.now(timezone.utc),
				file_hash=validation_result.file_hash,
				metadata=session.metadata,
			)

			# Clean up temporary upload file
			try:
				os.unlink(file_path)
			except Exception as e:
				logger.warning(f"Failed to clean up temporary upload file: {e}")

			logger.info(f"Upload finalized for session {session_id}, file saved as {permanent_path}")
			return True, permanent_path, validation_result

		except Exception as e:
			logger.error(f"Error finalizing upload for session {session_id}: {e}")
			return False, f"Finalization error: {e!s}", None

	def get_session_progress(self, session_id: str) -> Optional[UploadProgress]:
		"""Get upload progress for a session."""
		return self.session_manager.get_upload_progress(session_id)

	async def cancel_upload(self, session_id: str) -> bool:
		"""Cancel an upload session."""
		return await self.session_manager.cancel_session(session_id)

	async def cleanup_expired_sessions(self):
		"""Clean up expired upload sessions."""
		await self.session_manager.cleanup_expired_sessions()


# Global instance
upload_service = EnhancedUploadService()
