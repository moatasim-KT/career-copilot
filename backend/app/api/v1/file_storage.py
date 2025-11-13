"""
File Storage API Endpoints

Provides REST API endpoints for file storage operations using database storage.
"""

import base64
import io
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.dependencies import get_current_user

from ...core.exceptions import StorageError, ValidationError
from ...core.logging import get_logger
from ...services.database_storage_service import ChromaStorageService

logger = get_logger(__name__)

router = APIRouter(prefix="/file-storage", tags=["File Storage"])


class FileUploadRequest(BaseModel):
	"""File upload request model."""

	content: str = Field(description="Base64 encoded file content")
	filename: str = Field(description="Original filename")
	mime_type: Optional[str] = Field(default=None, description="MIME type")
	document_type: str = Field(default="upload", description="Type of document")


class FileUpdateRequest(BaseModel):
	"""File update request model."""

	content: str = Field(description="Base64 encoded file content")
	filename: Optional[str] = Field(default=None, description="New filename")
	mime_type: Optional[str] = Field(default=None, description="MIME type")


class FileListResponse(BaseModel):
	"""File list response model."""

	files: List[Dict[str, Any]] = Field(description="List of files")
	total_count: int = Field(description="Total number of files")


class CleanupRequest(BaseModel):
	"""Cleanup request model."""

	policy_name: str = Field(default="default", description="Cleanup policy to use")
	dry_run: bool = Field(default=False, description="Perform dry run without actual cleanup")


@router.get("/", response_model=Dict[str, str])
async def get_file_storage_info():
	"""Get file storage service information."""
	try:
		return {
			"service": "ChromaDB Storage Service",
			"version": "1.0.0",
			"storage_backend": "ChromaDB + PostgreSQL",
			"status": "operational",
			"endpoints": {
				"upload": "POST /file-storage/upload - Upload a new file",
				"get": "GET /file-storage/{stored_filename} - Get file content",
				"delete": "DELETE /file-storage/{stored_filename} - Delete file",
				"list": "GET /file-storage/list - List user files",
				"info": "GET /file-storage/{stored_filename}/info - Get file metadata",
			},
		}
	except Exception as e:
		logger.error(f"Failed to get file storage info: {e}")
		raise HTTPException(status_code=500, detail="Failed to get service information")


@router.post("/upload", response_model=Dict[str, Any])
async def upload_file(request: FileUploadRequest, current_user: Optional[Dict] = Depends(get_current_user)):
	"""Upload a new file to storage."""
	try:
		# Decode base64 content
		try:
			content = base64.b64decode(request.content)
		except Exception as e:
			raise HTTPException(status_code=400, detail=f"Invalid base64 content: {e!s}")

		# Get user ID
		user_id = current_user.get("id") if current_user else 1

		# Store file using ChromaDB storage
		storage_service = ChromaStorageService()
		stored_filename = await storage_service.store_file(
			user_id=user_id,
			file_content=content,
			original_filename=request.filename,
			document_type=request.document_type,
			mime_type=request.mime_type,
		)

		# Get file metadata
		file_metadata = await storage_service.get_file_metadata(stored_filename)

		logger.info(f"File uploaded successfully: {request.filename} -> {stored_filename}")
		return file_metadata

	except ValidationError as e:
		raise HTTPException(status_code=400, detail=str(e))
	except StorageError as e:
		raise HTTPException(status_code=500, detail=str(e))
	except Exception as e:
		logger.error(f"Failed to upload file: {e}")
		raise HTTPException(status_code=500, detail="Failed to upload file")


@router.get("/{stored_filename}")
async def get_file(
	stored_filename: str,
	download: bool = Query(False, description="Download as attachment"),
	current_user: Optional[Dict] = Depends(get_current_user),
):
	"""Get file content."""
	try:
		storage_service = ChromaStorageService()
		content = await storage_service.get_file(stored_filename)

		if not content:
			raise HTTPException(status_code=404, detail="File not found")

		# Get metadata for headers
		metadata = await storage_service.get_file_metadata(stored_filename)

		# Prepare response headers
		headers = {
			"Content-Type": metadata.get("mime_type", "application/octet-stream"),
			"Content-Length": str(len(content)),
			"X-Stored-Filename": stored_filename,
		}

		if download:
			headers["Content-Disposition"] = f'attachment; filename="{metadata.get("original_filename", stored_filename)}"'

		return StreamingResponse(io.BytesIO(content), media_type=metadata.get("mime_type", "application/octet-stream"), headers=headers)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get file {stored_filename}: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve file")

	except StorageError as e:
		if "not found" in str(e).lower():
			raise HTTPException(status_code=404, detail=str(e))
		raise HTTPException(status_code=500, detail=str(e))
	except Exception as e:
		logger.error(f"Failed to get file {file_id}: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve file")


@router.delete("/{stored_filename}")
async def delete_file(
	stored_filename: str,
	current_user: Optional[Dict] = Depends(get_current_user),
):
	"""Delete a file."""
	try:
		storage_service = ChromaStorageService()
		success = await storage_service.delete_file(stored_filename)

		if not success:
			raise HTTPException(status_code=404, detail="File not found")

		logger.info(f"File deleted successfully: {stored_filename}")
		return {"message": "File deleted successfully"}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to delete file {stored_filename}: {e}")
		raise HTTPException(status_code=500, detail="Failed to delete file")


@router.get("/list", response_model=FileListResponse)
async def list_files(
	document_type: Optional[str] = Query(None, description="Filter by document type"),
	current_user: Optional[Dict] = Depends(get_current_user),
):
	"""List user files."""
	try:
		user_id = current_user.get("id") if current_user else 1
		storage_service = ChromaStorageService()
		files = await storage_service.list_user_files(user_id, document_type)

		return FileListResponse(files=files, total_count=len(files))

	except Exception as e:
		logger.error(f"Failed to list files: {e}")
		raise HTTPException(status_code=500, detail="Failed to list files")


@router.get("/{stored_filename}/info", response_model=Dict[str, Any])
async def get_file_info(
	stored_filename: str,
	current_user: Optional[Dict] = Depends(get_current_user),
):
	"""Get file metadata."""
	try:
		storage_service = ChromaStorageService()
		metadata = await storage_service.get_file_metadata(stored_filename)

		if not metadata:
			raise HTTPException(status_code=404, detail="File not found")

		return metadata

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get file info {stored_filename}: {e}")
		raise HTTPException(status_code=500, detail="Failed to get file information")
		file_record = await file_storage_service.get_file_info(file_id)

		if not file_record:
			raise HTTPException(status_code=404, detail="File not found")

		# Sort versions by creation date (newest first)
		versions = sorted(file_record.versions, key=lambda v: v.created_at, reverse=True)
		return versions

	except Exception as e:
		logger.error(f"Failed to get file versions {file_id}: {e}")
		raise HTTPException(status_code=500, detail="Failed to get file versions")


@router.get("/stats", response_model=StorageStats)
async def get_storage_stats(current_user: Optional[str] = Depends(get_current_user)):
	"""Get storage statistics."""
	try:
		stats = await file_storage_service.get_storage_stats()
		return stats

	except Exception as e:
		logger.error(f"Failed to get storage stats: {e}")
		raise HTTPException(status_code=500, detail="Failed to get storage statistics")


@router.post("/cleanup")
async def cleanup_files(request: CleanupRequest = Body(...), current_user: Optional[str] = Depends(get_current_user)):
	"""Clean up old files according to policy."""
	try:
		if request.dry_run:
			# For dry run, we would need to implement a preview function
			# For now, just return the policy information
			policies = file_storage_service.get_cleanup_policies()
			policy = policies.get(request.policy_name)

			if not policy:
				raise HTTPException(status_code=400, detail=f"Unknown cleanup policy: {request.policy_name}")

			return {"dry_run": True, "policy": policy.dict(), "message": "Dry run completed - no files were actually deleted"}
		else:
			# Perform actual cleanup
			stats = await file_storage_service.cleanup_files(request.policy_name)

			logger.info(f"Cleanup completed with policy '{request.policy_name}': {stats}")

			return {"success": True, "policy_name": request.policy_name, "cleanup_stats": stats}

	except ValidationError as e:
		raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:
		logger.error(f"Failed to cleanup files: {e}")
		raise HTTPException(status_code=500, detail="Failed to cleanup files")


@router.get("/policies", response_model=Dict[str, CleanupPolicy])
async def get_cleanup_policies(current_user: Optional[str] = Depends(get_current_user)):
	"""Get all cleanup policies."""
	try:
		policies = file_storage_service.get_cleanup_policies()
		return policies

	except Exception as e:
		logger.error(f"Failed to get cleanup policies: {e}")
		raise HTTPException(status_code=500, detail="Failed to get cleanup policies")


@router.post("/policies", response_model=Dict[str, str])
async def add_cleanup_policy(policy: CleanupPolicy, current_user: Optional[str] = Depends(get_current_user)):
	"""Add a new cleanup policy."""
	try:
		file_storage_service.add_cleanup_policy(policy)

		return {"success": True, "message": f"Cleanup policy '{policy.name}' added successfully", "policy_name": policy.name}

	except Exception as e:
		logger.error(f"Failed to add cleanup policy: {e}")
		raise HTTPException(status_code=500, detail="Failed to add cleanup policy")


@router.post("/start-background-cleanup")
async def start_background_cleanup(current_user: Optional[str] = Depends(get_current_user)):
	"""Start background cleanup task."""
	try:
		await file_storage_service.start_background_cleanup()

		return {"success": True, "message": "Background cleanup task started"}

	except Exception as e:
		logger.error(f"Failed to start background cleanup: {e}")
		raise HTTPException(status_code=500, detail="Failed to start background cleanup")


@router.post("/stop-background-cleanup")
async def stop_background_cleanup(current_user: Optional[str] = Depends(get_current_user)):
	"""Stop background cleanup task."""
	try:
		await file_storage_service.stop_background_cleanup()

		return {"success": True, "message": "Background cleanup task stopped"}

	except Exception as e:
		logger.error(f"Failed to stop background cleanup: {e}")
		raise HTTPException(status_code=500, detail="Failed to stop background cleanup")
