"""
Enhanced contract upload API with chunked upload support and real-time progress tracking.
"""

import asyncio
from typing import Dict, Optional, Any

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ...core.logging import get_logger
from ...models.upload_models import (
	UploadRequest,
	UploadResponse,
	ChunkUploadResponse,
	UploadProgress,
	UploadStatus,
)
from ...services.upload_service import upload_service
from ...api.websockets import manager as websocket_manager

logger = get_logger(__name__)
router = APIRouter()


class InitiateUploadRequest(BaseModel):
	"""Request to initiate a chunked upload."""

	filename: str
	total_size: int
	chunk_size: int = 1024 * 1024  # 1MB default
	file_hash: Optional[str] = None
	metadata: Dict[str, Any] = {}


class InitiateUploadResponse(BaseModel):
	"""Response for upload initiation."""

	success: bool
	message: str
	session_id: str
	upload_url: str
	websocket_url: str
	chunk_size: int
	total_chunks: int


@router.post("/upload/initiate", response_model=InitiateUploadResponse, tags=["Enhanced Upload"])
async def initiate_upload(request: InitiateUploadRequest, background_tasks: BackgroundTasks) -> InitiateUploadResponse:
	"""
	Initiate a chunked file upload session.

	This endpoint creates an upload session for large files that will be uploaded in chunks.
	It performs initial validation and returns URLs for chunk upload and progress tracking.

	Args:
	    request: Upload initiation request with file metadata
	    background_tasks: FastAPI background tasks for cleanup

	Returns:
	    InitiateUploadResponse: Session details and upload URLs

	Raises:
	    HTTPException: For validation errors or duplicate files
	"""
	try:
		logger.info(f"Initiating chunked upload for file: {request.filename} ({request.total_size} bytes)")

		# Create upload request
		upload_request = UploadRequest(
			filename=request.filename,
			total_size=request.total_size,
			chunk_size=request.chunk_size,
			file_hash=request.file_hash,
			metadata=request.metadata,
		)

		# Create upload session
		session, validation_result = await upload_service.create_upload_session(upload_request)

		# Schedule cleanup task
		background_tasks.add_task(schedule_session_cleanup, session.session_id)

		return InitiateUploadResponse(
			success=True,
			message="Upload session created successfully",
			session_id=session.session_id,
			upload_url=f"/api/v1/upload/chunk/{session.session_id}",
			websocket_url=f"/ws/upload/{session.session_id}",
			chunk_size=session.chunk_size,
			total_chunks=session.total_chunks,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error initiating upload: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Failed to initiate upload: {e!s}")


@router.post("/upload/chunk/{session_id}", response_model=ChunkUploadResponse, tags=["Enhanced Upload"])
async def upload_chunk(
	session_id: str, chunk_index: int, chunk_hash: str, file: UploadFile = File(..., description="File chunk to upload"), is_final_chunk: bool = False
) -> ChunkUploadResponse:
	"""
	Upload a file chunk to an existing upload session.

	Args:
	    session_id: Upload session ID
	    chunk_index: Index of the chunk (0-based)
	    chunk_hash: SHA-256 hash of the chunk for validation
	    file: The chunk data as an uploaded file
	    is_final_chunk: Whether this is the final chunk

	Returns:
	    ChunkUploadResponse: Upload result and progress information

	Raises:
	    HTTPException: For validation errors or upload failures
	"""
	try:
		logger.debug(f"Uploading chunk {chunk_index} for session {session_id}")

		# Read chunk data
		chunk_data = await file.read()

		# Upload chunk
		success, message, progress = await upload_service.upload_chunk(session_id, chunk_index, chunk_data, chunk_hash)

		if not success:
			raise HTTPException(status_code=400, detail=message)

		# Broadcast progress update via WebSocket
		if progress:
			await broadcast_upload_progress(session_id, progress)

		# Determine if upload is complete
		upload_complete = progress and progress.status == UploadStatus.COMPLETED

		# Generate next chunk URL if not complete
		next_chunk_url = None
		if not upload_complete and progress:
			next_chunk_index = progress.current_chunk
			if next_chunk_index < progress.total_chunks:
				next_chunk_url = f"/api/v1/upload/chunk/{session_id}"

		return ChunkUploadResponse(
			success=True,
			message=message,
			chunk_index=chunk_index,
			session_id=session_id,
			progress=progress,
			next_chunk_url=next_chunk_url,
			upload_complete=upload_complete,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error uploading chunk {chunk_index} for session {session_id}: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Failed to upload chunk: {e!s}")


@router.post("/upload/finalize/{session_id}", response_model=UploadResponse, tags=["Enhanced Upload"])
async def finalize_upload(session_id: str) -> UploadResponse:
	"""
	Finalize an upload session and perform final validation.

	Args:
	    session_id: Upload session ID

	Returns:
	    UploadResponse: Final upload result with file information

	Raises:
	    HTTPException: For validation errors or finalization failures
	"""
	try:
		logger.info(f"Finalizing upload for session {session_id}")

		success, file_path, validation_result = await upload_service.finalize_upload(session_id)

		if not success:
			raise HTTPException(status_code=400, detail=file_path)  # file_path contains error message

		# Broadcast completion via WebSocket
		progress = upload_service.get_session_progress(session_id)
		if progress:
			progress.status = UploadStatus.COMPLETED
			await broadcast_upload_progress(session_id, progress)

		return UploadResponse(
			success=True,
			message="Upload completed and validated successfully",
			file_id=validation_result.file_hash,
			validation_result=validation_result,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error finalizing upload for session {session_id}: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Failed to finalize upload: {e!s}")


@router.get("/upload/progress/{session_id}", response_model=UploadProgress, tags=["Enhanced Upload"])
async def get_upload_progress(session_id: str) -> UploadProgress:
	"""
	Get upload progress for a session.

	Args:
	    session_id: Upload session ID

	Returns:
	    UploadProgress: Current upload progress

	Raises:
	    HTTPException: If session not found
	"""
	progress = upload_service.get_session_progress(session_id)
	if not progress:
		raise HTTPException(status_code=404, detail="Upload session not found")

	return progress


@router.delete("/upload/cancel/{session_id}", tags=["Enhanced Upload"])
async def cancel_upload(session_id: str) -> Dict[str, Any]:
	"""
	Cancel an upload session.

	Args:
	    session_id: Upload session ID

	Returns:
	    Dict: Cancellation result

	Raises:
	    HTTPException: If session not found or cannot be cancelled
	"""
	try:
		success = await upload_service.cancel_upload(session_id)

		if not success:
			raise HTTPException(status_code=404, detail="Upload session not found")

		# Broadcast cancellation via WebSocket
		progress = UploadProgress(
			session_id=session_id, filename="", progress_percentage=0, uploaded_size=0, total_size=0, status=UploadStatus.CANCELLED
		)
		await broadcast_upload_progress(session_id, progress)

		return {"success": True, "message": "Upload session cancelled successfully"}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error cancelling upload session {session_id}: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Failed to cancel upload: {e!s}")


@router.post("/upload/simple", response_model=UploadResponse, tags=["Enhanced Upload"])
async def simple_upload(file: UploadFile = File(..., description="Contract file to upload"), metadata: Optional[str] = None) -> UploadResponse:
	"""
	Simple single-request file upload for smaller files.

	This endpoint provides a traditional upload method for files that don't require chunking.
	It includes the same validation and duplicate detection as chunked uploads.

	Args:
	    file: File to upload
	    metadata: Optional JSON metadata string

	Returns:
	    UploadResponse: Upload result with file information

	Raises:
	    HTTPException: For validation errors or upload failures
	"""
	try:
		logger.info(f"Simple upload requested for file: {file.filename}")

		# Read file content
		file_content = await file.read()

		# Parse metadata
		import json

		parsed_metadata = {}
		if metadata:
			try:
				parsed_metadata = json.loads(metadata)
			except json.JSONDecodeError:
				logger.warning(f"Invalid metadata JSON provided: {metadata}")

		# Validate file content
		validation_result = await upload_service.validate_file_content(file_content, file.filename)

		if not validation_result.is_valid:
			raise HTTPException(
				status_code=400,
				detail={"error": "File validation failed", "errors": validation_result.errors, "warnings": validation_result.warnings},
			)

		# Check for duplicates
		if validation_result.duplicate_detected:
			return UploadResponse(
				success=True,
				message="File already exists (duplicate detected)",
				file_id=validation_result.existing_file_id,
				validation_result=validation_result,
				duplicate_info={"existing_file_id": validation_result.existing_file_id, "message": "This file has already been uploaded"},
			)

		# Save file using temp_file_handler
		from ...core.file_handler import temp_file_handler

		temp_file_path = temp_file_handler.save_temporary_file(
			file_content,
			validation_result.safe_filename,
			validate=False,  # Already validated
		)

		logger.info(f"Simple upload completed for file: {file.filename}")

		return UploadResponse(
			success=True, message="File uploaded and validated successfully", file_id=validation_result.file_hash, validation_result=validation_result
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error in simple upload: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail=f"Upload failed: {e!s}")


@router.websocket("/ws/upload/{session_id}")
async def upload_progress_websocket(websocket: WebSocket, session_id: str):
	"""
	WebSocket endpoint for real-time upload progress updates.

	Args:
	    websocket: WebSocket connection
	    session_id: Upload session ID to track
	"""
	await websocket_manager.connect(websocket, "upload", session_id, {"session_id": session_id})

	try:
		# Send initial progress
		progress = upload_service.get_session_progress(session_id)
		if progress:
			await websocket.send_json({"type": "progress_update", "session_id": session_id, "progress": progress.dict()})
		else:
			await websocket.send_json({"type": "error", "message": f"Upload session {session_id} not found"})

		# Keep connection alive and handle client messages
		while True:
			try:
				# Check for incoming messages (non-blocking)
				message = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
				await handle_upload_client_message(websocket, session_id, message)
			except asyncio.TimeoutError:
				# No message received, send periodic updates
				progress = upload_service.get_session_progress(session_id)
				if progress:
					await websocket.send_json({"type": "progress_update", "session_id": session_id, "progress": progress.dict()})

					# Close connection if upload is finished
					if progress.status in [UploadStatus.COMPLETED, UploadStatus.FAILED, UploadStatus.CANCELLED]:
						break
				else:
					# Session not found, close connection
					break

			await asyncio.sleep(0.5)  # Update every 500ms

	except WebSocketDisconnect:
		logger.info(f"WebSocket disconnected for upload session {session_id}")
	except Exception as e:
		logger.error(f"WebSocket error for upload session {session_id}: {e}")
	finally:
		websocket_manager.disconnect(websocket, "upload", session_id)


async def handle_upload_client_message(websocket: WebSocket, session_id: str, message: Dict[str, Any]):
	"""Handle messages from upload WebSocket clients."""
	try:
		message_type = message.get("type")

		if message_type == "ping":
			await websocket.send_json({"type": "pong"})
		elif message_type == "get_progress":
			progress = upload_service.get_session_progress(session_id)
			if progress:
				await websocket.send_json({"type": "progress_update", "session_id": session_id, "progress": progress.dict()})
		elif message_type == "cancel_upload":
			success = await upload_service.cancel_upload(session_id)
			await websocket.send_json({"type": "upload_cancelled" if success else "cancel_failed", "session_id": session_id})
		else:
			logger.warning(f"Unknown message type from upload client: {message_type}")

	except Exception as e:
		logger.error(f"Error handling upload client message: {e}")


async def broadcast_upload_progress(session_id: str, progress: UploadProgress):
	"""Broadcast upload progress to WebSocket clients."""
	try:
		await websocket_manager.send_to_task(session_id, {"type": "progress_update", "session_id": session_id, "progress": progress.dict()})
	except Exception as e:
		logger.error(f"Error broadcasting upload progress: {e}")


async def schedule_session_cleanup(session_id: str):
	"""Schedule cleanup of upload session after delay."""
	# Wait 24 hours before cleanup
	await asyncio.sleep(24 * 3600)

	try:
		await upload_service.cleanup_expired_sessions()
		logger.info(f"Cleanup completed for expired upload sessions")
	except Exception as e:
		logger.error(f"Error during session cleanup: {e}")


# Background task to periodically clean up expired sessions
@router.on_event("startup")
async def start_cleanup_task():
	"""Start background cleanup task."""

	async def cleanup_loop():
		while True:
			try:
				await upload_service.cleanup_expired_sessions()
				await asyncio.sleep(3600)  # Run every hour
			except Exception as e:
				logger.error(f"Error in cleanup loop: {e}")
				await asyncio.sleep(300)  # Wait 5 minutes on error

	asyncio.create_task(cleanup_loop())
