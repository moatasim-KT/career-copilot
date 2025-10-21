"""
Contract analysis endpoints.
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ...core.auth import APIKey
from ...core.exceptions import (
	DocumentProcessingError,
	InvalidFileTypeError,
	ResourceExhaustionError,
	SecurityError,
	ValidationError,
	WorkflowExecutionError,
)

# Define FileSizeError if not already defined
class FileSizeError(ValidationError):
	"""Exception raised when file size exceeds limits."""
	def __init__(self, message: str, file_size: int = 0, max_size: int = 0):
		super().__init__(message)
		self.file_size = file_size
		self.max_size = max_size
from ...core.file_handler import FileSecurityValidator, temp_file_handler
from ...core.logging import get_logger
from ...core.monitoring import log_audit_event
from ...services.upload_service import upload_service
from ...models.upload_models import (
	UploadRequest, UploadResponse, ChunkUploadRequest, ChunkUploadResponse,
	UploadProgress, UploadStatus, FileValidationResult
)
from ...models.api_models import (
	AnalysisResponse,
	AnalysisStatusResponse,
	AnalysisTask,
	AsyncAnalysisRequest,
	AsyncAnalysisResponse,
	ErrorResponse,
	ProgressUpdate,
)
from ...services.document_processor import DocumentProcessingService
from ...services.production_contract_analysis import get_production_contract_analysis_service
from ...services.workflow_service import workflow_service
from ...utils.sanitization import input_sanitizer
from ...utils.security import sanitize_filename, validate_upload_file
from ...workflows.core import create_workflow

logger = get_logger(__name__)
router = APIRouter()

# Initialize document processor and workflow
document_processor = DocumentProcessingService()
workflow = create_workflow()  # Initialize the LangGraph workflow

# Allowed file types and size limits
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Task management for async processing
active_tasks: Dict[str, AnalysisTask] = {}
MAX_CONCURRENT_TASKS = 10
TASK_CLEANUP_INTERVAL = 3600  # 1 hour


async def validate_file(file: UploadFile) -> Dict[str, Any]:
	"""
	Comprehensive file validation with detailed error messages using FileSecurityValidator.

	Args:
	    file: The uploaded file to validate

	Returns:
	    Dict[str, Any]: Validation results with file metadata

	Raises:
	    ValidationError: If file validation fails
	    InvalidFileTypeError: If file type is not supported
	    SecurityError: If file fails security validation
	"""
	# Check if file is provided
	if not file:
		raise ValidationError("No file provided")

	# Check filename
	if not file.filename:
		raise ValidationError("Filename is required")

	# Use FileSecurityValidator for comprehensive validation
	file_validator = FileSecurityValidator()
	
	try:
		# Read file content
		file_content = await file.read()
		file.file.seek(0)  # Reset file pointer
		
		# Validate using security validator
		validation_result = file_validator.validate_file(file_content, file.filename)
		
		logger.info(f"File validation successful for {file.filename}: {validation_result}")
		
		# Add additional metadata
		validation_result.update({
			"content_length": len(file_content),
			"validation_timestamp": datetime.utcnow().isoformat(),
			"is_valid": True
		})
		
		return validation_result
		
	except (ValidationError, SecurityError) as e:
		# Re-raise validation and security errors
		raise e
	except Exception as e:
		logger.error(f"Unexpected error during file validation: {e}")
		raise ValidationError(f"File validation failed: {str(e)}")


def cleanup_old_tasks() -> None:
	"""Clean up old completed tasks to prevent memory leaks."""
	current_time = datetime.utcnow()
	tasks_to_remove = []

	for task_id, task in active_tasks.items():
		# Remove tasks older than cleanup interval
		if task.end_time and (current_time - task.end_time).total_seconds() > TASK_CLEANUP_INTERVAL:
			tasks_to_remove.append(task_id)
		# Remove abandoned tasks (no end time but very old)
		elif not task.end_time and (current_time - task.start_time).total_seconds() > TASK_CLEANUP_INTERVAL * 2:
			tasks_to_remove.append(task_id)

	for task_id in tasks_to_remove:
		if task_id in active_tasks:
			task = active_tasks[task_id]
			if task.future and not task.future.done():
				task.future.cancel()
			del active_tasks[task_id]

	if tasks_to_remove:
		logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")


async def execute_analysis_with_timeout(task: AnalysisTask) -> None:
	"""
	Execute analysis with timeout and proper error handling.

	Args:
	    task: The analysis task to execute
	"""
	from ...utils.error_handler import get_error_handler, ErrorCategory, ErrorSeverity
	
	error_handler = get_error_handler()
	
	try:
		task.status = "running"
		logger.info(f"Starting analysis task {task.task_id} for {task.contract_filename}")

		# Execute workflow with timeout
		result = await asyncio.wait_for(
			workflow.execute(task.contract_text, task.contract_filename), 
			timeout=task.timeout_seconds
		)

		task.result = result
		task.status = "completed"
		task.end_time = datetime.utcnow()

		logger.info(f"Analysis task {task.task_id} completed successfully")

	except asyncio.TimeoutError as e:
		error_msg = f"Analysis timed out after {task.timeout_seconds} seconds"
		task.error = error_msg
		task.status = "timeout"
		task.end_time = datetime.utcnow()
		
		# Log timeout error
		error_context = error_handler.handle_error(
			error=e,
			category=ErrorCategory.SYSTEM,
			severity=ErrorSeverity.MEDIUM,
			user_message="Analysis is taking longer than expected",
			technical_details={
				"task_id": task.task_id,
				"timeout_seconds": task.timeout_seconds,
				"filename": task.contract_filename
			}
		)
		
		logger.warning(f"Analysis task {task.task_id} timed out", extra={"error_id": error_context.error_id})

	except (DocumentProcessingError, WorkflowExecutionError, ValidationError) as e:
		# Handle known application errors
		task.error = e.user_message
		task.status = "failed"
		task.end_time = datetime.utcnow()
		
		error_context = error_handler.handle_error(
			error=e,
			category=e.category,
			severity=e.severity,
			user_message=e.user_message,
			technical_details={**e.details, "task_id": task.task_id}
		)
		
		logger.error(f"Analysis task {task.task_id} failed with {type(e).__name__}: {e.message}", 
					extra={"error_id": error_context.error_id})

	except Exception as e:
		# Handle unexpected errors
		error_msg = f"Analysis failed: {e!s}"
		task.error = error_msg
		task.status = "failed"
		task.end_time = datetime.utcnow()
		
		error_context = error_handler.handle_error(
			error=e,
			category=ErrorCategory.SYSTEM,
			severity=ErrorSeverity.HIGH,
			user_message="An unexpected error occurred during analysis",
			technical_details={
				"task_id": task.task_id,
				"filename": task.contract_filename,
				"error_type": type(e).__name__
			}
		)
		
		logger.error(f"Analysis task {task.task_id} failed with unexpected error: {error_msg}", 
					exc_info=True, extra={"error_id": error_context.error_id})


def convert_workflow_result_to_response(workflow_result: dict, processing_time: Optional[float] = None) -> AnalysisResponse:
	"""
	Convert workflow result to API response format.

	Args:
	    workflow_result: Result from workflow execution
	    processing_time: Optional processing time override

	Returns:
	    AnalysisResponse: Formatted API response
	"""
	# Extract processing time from workflow result if not provided
	if processing_time is None:
		processing_time = workflow_result.get("processing_metadata", {}).get("processing_duration")

	# Convert workflow status enum to string
	status = workflow_result.get("status")
	if hasattr(status, "value"):
		status = status.value

	return AnalysisResponse(
		risky_clauses=workflow_result.get("risky_clauses", []),
		suggested_redlines=workflow_result.get("suggested_redlines", []),
		email_draft=workflow_result.get("email_draft", ""),
		processing_time=processing_time,
		status=status or "unknown",
		overall_risk_score=workflow_result.get("overall_risk_score"),
		warnings=workflow_result.get("processing_metadata", {}).get("warnings", []),
		errors=workflow_result.get("errors", []),
	)


from ...core.audit import AuditEventType, audit_logger
from ...core.file_handler import temp_file_handler
from ...utils.security import file_validator, sanitize_filename


@router.get(
	"/contracts", 
	response_model=dict, 
	tags=["Contract Analysis"],
	summary="Get Contract API Information",
	description="Retrieve comprehensive information about available contract endpoints and operations",
	responses={
		200: {
			"description": "Contract API information retrieved successfully",
			"content": {
				"application/json": {
					"example": {
						"success": True,
						"message": "Contract API endpoints",
						"data": {
							"endpoints": {
								"upload": "POST /api/v1/contracts/upload - Upload a contract file",
								"analyze": "POST /api/v1/analyze-contract - Analyze contract"
							},
							"supported_formats": ["pdf", "docx", "txt"],
							"max_file_size_mb": 50
						}
					}
				}
			}
		}
	}
)
async def get_contracts_info() -> dict:
	"""
	Get information about contract endpoints and available operations.
	
	This endpoint provides a comprehensive overview of all available contract-related
	operations, supported file formats, size limits, and feature capabilities.
	
	Returns:
		dict: Available contract endpoints and operations with metadata
		
	Examples:
		>>> response = requests.get("/api/v1/contracts")
		>>> print(response.json()["data"]["supported_formats"])
		["pdf", "docx", "txt"]
	"""
	return {
		"success": True,
		"message": "Contract API endpoints",
		"data": {
			"endpoints": {
				"upload": "POST /api/v1/contracts/upload - Upload a contract file",
				"validate": "POST /api/v1/contracts/validate - Validate a contract file",
				"list": "GET /api/v1/contracts/list - List uploaded contracts",
				"status": "GET /api/v1/contracts/{file_id}/status - Get contract status",
				"download": "GET /api/v1/contracts/{file_id}/download - Download contract",
				"delete": "DELETE /api/v1/contracts/{file_id} - Delete contract",
				"analyze": "POST /api/v1/analyze-contract - Analyze contract"
			},
			"supported_formats": ["pdf", "docx", "txt"],
			"max_file_size_mb": 50,
			"features": [
				"File upload and validation",
				"Contract analysis",
				"Risk assessment",
				"Clause identification",
				"Redline generation"
			]
		}
	}


@router.post(
	"/contracts/upload", 
	response_model=dict, 
	tags=["Enhanced Contract Upload"],
	summary="Upload Contract File",
	description="Upload and validate contract files with comprehensive security scanning and duplicate detection",
	responses={
		200: {
			"description": "Contract uploaded successfully",
			"content": {
				"application/json": {
					"example": {
						"success": True,
						"message": "Contract uploaded and validated successfully",
						"data": {
							"file_id": "abc123def456",
							"filename": "contract_sanitized.pdf",
							"file_size": 2048576,
							"ready_for_analysis": True,
							"security_scan_passed": True
						}
					}
				}
			}
		},
		400: {
			"description": "Validation error",
			"content": {
				"application/json": {
					"example": {
						"error": "Validation Error",
						"message": "File size exceeds maximum allowed limit",
						"suggestions": ["Reduce file size", "Contact support"]
					}
				}
			}
		},
		403: {
			"description": "Security violation",
			"content": {
				"application/json": {
					"example": {
						"error": "Security Violation",
						"message": "File failed security validation"
					}
				}
			}
		},
		413: {
			"description": "File too large",
			"content": {
				"application/json": {
					"example": {
						"error": "File Too Large",
						"message": "File size exceeds 50MB limit",
						"file_size_mb": 52.3,
						"max_size_mb": 50.0
					}
				}
			}
		}
	}
)
async def upload_contract(
	request: Request, 
	file: UploadFile = File(
		..., 
		description="Contract file to upload. Supported formats: PDF, DOCX, TXT. Maximum size: 50MB"
	),
	analysis_options: Optional[dict] = None
) -> dict:
	"""
	Enhanced contract upload with comprehensive validation, duplicate detection, and progress tracking.
	
	This endpoint provides enterprise-grade file upload capabilities with:
	
	**Security Features:**
	- Comprehensive file validation (MIME type, size, content structure)
	- Malware scanning and threat detection
	- SHA-256 hash-based duplicate detection
	- Input sanitization and filename normalization
	
	**Processing Features:**
	- Document structure analysis and metadata extraction
	- OCR support for scanned documents
	- Multi-format support (PDF, DOCX, TXT)
	- Real-time progress tracking via WebSocket
	
	**Audit & Compliance:**
	- Complete audit trail logging
	- User activity tracking
	- Compliance validation
	- Error tracking and recovery
	
	Args:
		request: FastAPI request object containing user context and metadata
		file: Contract file to upload (.pdf, .docx, or .txt format)
		analysis_options: Optional dictionary containing analysis preferences:
			- include_risk_assessment (bool): Enable risk scoring
			- include_redlines (bool): Generate redline suggestions
			- analysis_depth (str): "quick", "standard", or "comprehensive"
			- jurisdiction (str): Legal jurisdiction for analysis
			- contract_type (str): Type of contract for specialized analysis
		
	Returns:
		dict: Upload confirmation with comprehensive metadata:
			- success (bool): Upload operation status
			- message (str): Human-readable status message
			- data (dict): File metadata and processing results
				- file_id (str): Unique identifier for the uploaded file
				- filename (str): Sanitized filename
				- file_size (int): File size in bytes
				- ready_for_analysis (bool): Whether file is ready for analysis
				- security_scan_passed (bool): Security validation status
				- duplicate (bool): Whether file is a duplicate
		
	Raises:
		HTTPException: 
			- 400: Validation errors (invalid format, corrupted file)
			- 403: Security violations (malware detected, policy violation)
			- 413: File size exceeds limits
			- 422: Document processing errors
			- 500: Internal server errors
		
	Examples:
		Basic upload with cURL:
		```bash
		curl -X POST "http://localhost:8000/api/v1/contracts/upload" \\
		     -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
		     -F "file=@contract.pdf" \\
		     -F 'analysis_options={"include_risk_assessment":true}'
		```
		
		Python client example:
		```python
		import requests
		
		files = {'file': open('contract.pdf', 'rb')}
		data = {'analysis_options': '{"include_risk_assessment": true}'}
		headers = {'Authorization': 'Bearer YOUR_JWT_TOKEN'}
		
		response = requests.post(
		    'http://localhost:8000/api/v1/contracts/upload',
		    files=files,
		    data=data,
		    headers=headers
		)
		```
	
	Note:
		For large files (>10MB), consider using the chunked upload endpoints
		(/api/v1/contracts/upload/initiate) for better performance and reliability.
	
	See Also:
		- POST /api/v1/contracts/upload/initiate: Initiate chunked upload
		- GET /api/v1/contracts/upload/progress/{session_id}: Track upload progress
		- POST /api/v1/analyze-contract: Analyze uploaded contract
	"""
	start_time = time.time()
	request_id = getattr(request.state, "request_id", "unknown")
	
	logger.info(f"Enhanced contract upload requested for file: {file.filename}", extra={"request_id": request_id})
	
	try:
		# Read file content for validation
		file_content = await file.read()
		file.file.seek(0)  # Reset file pointer
		
		# Use enhanced upload service for validation
		validation_result = await upload_service.validate_file_content(file_content, file.filename)
		
		if not validation_result.is_valid:
			raise HTTPException(status_code=400, detail={
				"error": "File validation failed",
				"errors": validation_result.errors,
				"warnings": validation_result.warnings,
				"suggestions": ["Please check file format and content", "Ensure file is not corrupted"]
			})
		
		# Check for duplicates
		if validation_result.duplicate_detected:
			logger.info(f"Duplicate file detected: {validation_result.file_hash}")
			
			# Get existing file info from duplicate cache
			existing_info = upload_service.duplicate_cache.get(validation_result.existing_file_id)
			
			return {
				"success": True,
				"message": "File already exists in storage (duplicate detected)",
				"data": {
					"file_id": validation_result.file_hash,
					"filename": validation_result.safe_filename,
					"original_filename": validation_result.original_filename,
					"file_size": validation_result.file_size,
					"mime_type": validation_result.mime_type,
					"upload_timestamp": existing_info.upload_date.isoformat() if existing_info else datetime.utcnow().isoformat(),
					"ready_for_analysis": True,
					"duplicate": True,
					"existing_file_id": validation_result.existing_file_id,
					"file_hash": validation_result.file_hash
				}
			}
		
		# Save file to secure temporary location
		temp_file_path = temp_file_handler.save_temporary_file(
			file_content, 
			validation_result.safe_filename,
			validate=False  # Already validated
		)
		
		# Extract basic document metadata and process document
		try:
			processed_doc = await document_processor.process_document(temp_file_path, validation_result.safe_filename)
			
			# Check if document processing was successful
			if processed_doc.status.value == "failed":
				raise DocumentProcessingError(f"Document processing failed: {'; '.join(processed_doc.errors)}")
			
			content_length = len(processed_doc.content)
			processing_warnings = processed_doc.warnings
			
		except Exception as e:
			logger.error(f"Document processing failed for {file.filename}: {e}")
			# Clean up temp file on processing failure
			temp_file_handler.cleanup_file(temp_file_path)
			raise DocumentProcessingError(f"Failed to process document: {str(e)}")
		
		# Update duplicate cache with new file
		from ...models.upload_models import DuplicateFileInfo
		upload_service.duplicate_cache[validation_result.file_hash] = DuplicateFileInfo(
			file_id=validation_result.file_hash,
			filename=validation_result.safe_filename,
			file_size=validation_result.file_size,
			upload_date=datetime.utcnow(),
			file_hash=validation_result.file_hash,
			metadata={"analysis_options": analysis_options or {}}
		)
		
		# Log successful upload
		user_id = getattr(request.state, "user_id", None)
		log_audit_event(
			"contract_upload_success",
			details={
				"filename": validation_result.safe_filename,
				"file_size": validation_result.file_size,
				"file_hash": validation_result.file_hash,
				"mime_type": validation_result.mime_type,
				"processing_time": time.time() - start_time,
				"user_id": user_id,
				"content_length": content_length,
				"security_scan_passed": validation_result.security_scan_passed,
				"warnings": validation_result.warnings
			}
		)
		
		return {
			"success": True,
			"message": "Contract uploaded and validated successfully",
			"data": {
				"file_id": validation_result.file_hash,
				"filename": validation_result.safe_filename,
				"original_filename": validation_result.original_filename,
				"file_size": validation_result.file_size,
				"mime_type": validation_result.mime_type,
				"detected_type": validation_result.detected_type,
				"content_length": content_length,
				"upload_timestamp": datetime.utcnow().isoformat(),
				"temp_file_path": temp_file_path,
				"ready_for_analysis": True,
				"processing_warnings": processing_warnings,
				"document_type": processed_doc.document_type.value,
				"processing_status": processed_doc.status.value,
				"file_hash": validation_result.file_hash,
				"security_scan_passed": validation_result.security_scan_passed,
				"validation_warnings": validation_result.warnings,
				"duplicate": False
			}
		}
		
	except ValidationError as e:
		# Handle validation errors
		log_audit_event(
			"contract_upload_validation_failed",
			details={
				"filename": file.filename, 
				"error": e.user_message, 
				"error_code": e.error_code,
				"field": getattr(e, "field", None)
			}
		)
		raise HTTPException(
			status_code=400, 
			detail={
				"error": "Validation Error",
				"message": e.user_message,
				"suggestions": e.recovery_suggestions,
				"error_code": e.error_code
			}
		)
		
	except InvalidFileTypeError as e:
		# Handle file type errors
		log_audit_event(
			"contract_upload_invalid_type",
			details={
				"filename": file.filename, 
				"file_type": getattr(e, "file_type", "unknown"),
				"supported_types": getattr(e, "supported_types", [])
			}
		)
		raise HTTPException(
			status_code=400, 
			detail={
				"error": "Invalid File Type",
				"message": e.user_message,
				"supported_types": getattr(e, "supported_types", []),
				"suggestions": e.recovery_suggestions
			}
		)
		
	except FileSizeError as e:
		# Handle file size errors
		log_audit_event(
			"contract_upload_size_exceeded",
			details={
				"filename": file.filename, 
				"file_size": getattr(e, "file_size", 0),
				"max_size": getattr(e, "max_size", 0)
			}
		)
		raise HTTPException(
			status_code=413, 
			detail={
				"error": "File Too Large",
				"message": e.user_message,
				"file_size_mb": round(getattr(e, "file_size", 0) / (1024 * 1024), 2),
				"max_size_mb": round(getattr(e, "max_size", 0) / (1024 * 1024), 2),
				"suggestions": e.recovery_suggestions
			}
		)
		
	except SecurityError as e:
		# Handle security errors
		log_audit_event(
			"contract_upload_security_violation",
			details={
				"filename": file.filename, 
				"violation_type": getattr(e, "violation_type", "unknown"),
				"severity": e.severity.value
			}
		)
		raise HTTPException(
			status_code=403, 
			detail={
				"error": "Security Violation",
				"message": "File failed security validation",
				"suggestions": e.recovery_suggestions
			}
		)
		
	except DocumentProcessingError as e:
		# Handle document processing errors
		log_audit_event(
			"contract_upload_processing_failed",
			details={
				"filename": file.filename, 
				"processing_stage": getattr(e, "processing_stage", "unknown"),
				"error": e.user_message
			}
		)
		raise HTTPException(
			status_code=422, 
			detail={
				"error": "Document Processing Error",
				"message": e.user_message,
				"processing_stage": getattr(e, "processing_stage", "unknown"),
				"suggestions": e.recovery_suggestions
			}
		)
		
	except Exception as e:
		# Handle unexpected errors
		from ...utils.error_handler import get_error_handler, ErrorCategory, ErrorSeverity
		
		error_handler = get_error_handler()
		error_context = error_handler.handle_error(
			error=e,
			category=ErrorCategory.SYSTEM,
			severity=ErrorSeverity.HIGH,
			user_message="An unexpected error occurred during file upload",
			technical_details={
				"filename": file.filename,
				"request_id": request_id,
				"error_type": type(e).__name__
			},
			request_id=request_id
		)
		
		log_audit_event(
			"contract_upload_unexpected_error",
			details={
				"filename": file.filename, 
				"error": str(e),
				"error_id": error_context.error_id,
				"request_id": request_id
			}
		)
		
		raise HTTPException(
			status_code=500, 
			detail={
				"error": "Internal Server Error",
				"message": "An unexpected error occurred during file upload",
				"error_id": error_context.error_id,
				"suggestions": [
					"Please try again",
					"If the problem persists, contact support with the error ID"
				]
			}
		)
	
	finally:
		if hasattr(file, "file") and file.file:
			file.file.close()


# Enhanced Upload Endpoints for Chunked Upload Support

from pydantic import BaseModel

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


@router.post("/contracts/upload/initiate", response_model=InitiateUploadResponse, tags=["Enhanced Contract Upload"])
async def initiate_contract_upload(
	request: Request,
	upload_request: InitiateUploadRequest,
	background_tasks: BackgroundTasks
) -> InitiateUploadResponse:
	"""
	Initiate a chunked contract upload session.
	
	This endpoint creates an upload session for large contract files that will be uploaded in chunks.
	It performs initial validation and returns URLs for chunk upload and progress tracking.
	
	Args:
		request: FastAPI request object
		upload_request: Upload initiation request with file metadata
		background_tasks: FastAPI background tasks for cleanup
		
	Returns:
		InitiateUploadResponse: Session details and upload URLs
		
	Raises:
		HTTPException: For validation errors or duplicate files
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		logger.info(f"Initiating chunked contract upload for file: {upload_request.filename} ({upload_request.total_size} bytes)", 
				   extra={"request_id": request_id})
		
		# Create upload request
		upload_req = UploadRequest(
			filename=upload_request.filename,
			total_size=upload_request.total_size,
			chunk_size=upload_request.chunk_size,
			file_hash=upload_request.file_hash,
			metadata=upload_request.metadata
		)
		
		# Create upload session
		session, validation_result = await upload_service.create_upload_session(upload_req)
		
		# Schedule cleanup task
		background_tasks.add_task(schedule_session_cleanup, session.session_id)
		
		# Log session creation
		log_audit_event(
			"contract_upload_session_created",
			details={
				"session_id": session.session_id,
				"filename": upload_request.filename,
				"total_size": upload_request.total_size,
				"chunk_size": upload_request.chunk_size,
				"total_chunks": session.total_chunks,
				"request_id": request_id
			}
		)
		
		return InitiateUploadResponse(
			success=True,
			message="Contract upload session created successfully",
			session_id=session.session_id,
			upload_url=f"/api/v1/contracts/upload/chunk/{session.session_id}",
			websocket_url=f"/ws/contracts/upload/{session.session_id}",
			chunk_size=session.chunk_size,
			total_chunks=session.total_chunks
		)
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error initiating contract upload: {e}", exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail=f"Failed to initiate contract upload: {str(e)}")


@router.post("/contracts/upload/chunk/{session_id}", response_model=ChunkUploadResponse, tags=["Enhanced Contract Upload"])
async def upload_contract_chunk(
	request: Request,
	session_id: str,
	chunk_index: int,
	chunk_hash: str,
	file: UploadFile = File(..., description="Contract file chunk to upload"),
	is_final_chunk: bool = False
) -> ChunkUploadResponse:
	"""
	Upload a contract file chunk to an existing upload session.
	
	Args:
		request: FastAPI request object
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
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		logger.debug(f"Uploading contract chunk {chunk_index} for session {session_id}", 
					extra={"request_id": request_id})
		
		# Read chunk data
		chunk_data = await file.read()
		
		# Upload chunk
		success, message, progress = await upload_service.upload_chunk(
			session_id, chunk_index, chunk_data, chunk_hash
		)
		
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
				next_chunk_url = f"/api/v1/contracts/upload/chunk/{session_id}"
		
		# Log chunk upload
		log_audit_event(
			"contract_chunk_uploaded",
			details={
				"session_id": session_id,
				"chunk_index": chunk_index,
				"chunk_size": len(chunk_data),
				"progress_percentage": progress.progress_percentage if progress else 0,
				"upload_complete": upload_complete,
				"request_id": request_id
			}
		)
		
		return ChunkUploadResponse(
			success=True,
			message=message,
			chunk_index=chunk_index,
			session_id=session_id,
			progress=progress,
			next_chunk_url=next_chunk_url,
			upload_complete=upload_complete
		)
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error uploading contract chunk {chunk_index} for session {session_id}: {e}", 
					exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail=f"Failed to upload contract chunk: {str(e)}")


@router.post("/contracts/upload/finalize/{session_id}", response_model=UploadResponse, tags=["Enhanced Contract Upload"])
async def finalize_contract_upload(request: Request, session_id: str) -> UploadResponse:
	"""
	Finalize a contract upload session and perform final validation.
	
	Args:
		request: FastAPI request object
		session_id: Upload session ID
		
	Returns:
		UploadResponse: Final upload result with file information
		
	Raises:
		HTTPException: For validation errors or finalization failures
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		logger.info(f"Finalizing contract upload for session {session_id}", extra={"request_id": request_id})
		
		success, file_path, validation_result = await upload_service.finalize_upload(session_id)
		
		if not success:
			raise HTTPException(status_code=400, detail=file_path)  # file_path contains error message
		
		# Process the finalized contract document
		try:
			processed_doc = await document_processor.process_document(file_path, validation_result.safe_filename)
			
			# Check if document processing was successful
			if processed_doc.status.value == "failed":
				raise DocumentProcessingError(f"Document processing failed: {'; '.join(processed_doc.errors)}")
			
		except Exception as e:
			logger.error(f"Document processing failed for finalized upload {session_id}: {e}")
			raise DocumentProcessingError(f"Failed to process finalized document: {str(e)}")
		
		# Broadcast completion via WebSocket
		progress = upload_service.get_session_progress(session_id)
		if progress:
			progress.status = UploadStatus.COMPLETED
			await broadcast_upload_progress(session_id, progress)
		
		# Log successful finalization
		log_audit_event(
			"contract_upload_finalized",
			details={
				"session_id": session_id,
				"file_id": validation_result.file_hash,
				"filename": validation_result.safe_filename,
				"file_size": validation_result.file_size,
				"document_type": processed_doc.document_type.value,
				"processing_status": processed_doc.status.value,
				"request_id": request_id
			}
		)
		
		return UploadResponse(
			success=True,
			message="Contract upload completed and validated successfully",
			file_id=validation_result.file_hash,
			validation_result=validation_result
		)
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error finalizing contract upload for session {session_id}: {e}", 
					exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail=f"Failed to finalize contract upload: {str(e)}")


@router.get("/contracts/upload/progress/{session_id}", response_model=UploadProgress, tags=["Enhanced Contract Upload"])
async def get_contract_upload_progress(request: Request, session_id: str) -> UploadProgress:
	"""
	Get contract upload progress for a session.
	
	Args:
		request: FastAPI request object
		session_id: Upload session ID
		
	Returns:
		UploadProgress: Current upload progress
		
	Raises:
		HTTPException: If session not found
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		progress = upload_service.get_session_progress(session_id)
		if not progress:
			raise HTTPException(status_code=404, detail="Contract upload session not found")
		
		return progress
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting contract upload progress for session {session_id}: {e}", 
					exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail="Failed to get upload progress")


@router.delete("/contracts/upload/cancel/{session_id}", tags=["Enhanced Contract Upload"])
async def cancel_contract_upload(request: Request, session_id: str) -> Dict[str, Any]:
	"""
	Cancel a contract upload session.
	
	Args:
		request: FastAPI request object
		session_id: Upload session ID
		
	Returns:
		Dict: Cancellation result
		
	Raises:
		HTTPException: If session not found or cannot be cancelled
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		success = await upload_service.cancel_upload(session_id)
		
		if not success:
			raise HTTPException(status_code=404, detail="Contract upload session not found")
		
		# Broadcast cancellation via WebSocket
		progress = UploadProgress(
			session_id=session_id,
			filename="",
			progress_percentage=0,
			uploaded_size=0,
			total_size=0,
			status=UploadStatus.CANCELLED
		)
		await broadcast_upload_progress(session_id, progress)
		
		# Log cancellation
		log_audit_event(
			"contract_upload_cancelled",
			details={
				"session_id": session_id,
				"request_id": request_id
			}
		)
		
		return {
			"success": True,
			"message": "Contract upload session cancelled successfully"
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error cancelling contract upload session {session_id}: {e}", 
					exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail=f"Failed to cancel contract upload: {str(e)}")


# WebSocket endpoint for contract upload progress
@router.websocket("/ws/contracts/upload/{session_id}")
async def contract_upload_progress_websocket(websocket: WebSocket, session_id: str):
	"""
	WebSocket endpoint for real-time contract upload progress updates.
	
	Args:
		websocket: WebSocket connection
		session_id: Upload session ID to track
	"""
	from ...api.websockets import manager as websocket_manager
	
	await websocket_manager.connect(websocket, "upload", session_id, {"session_id": session_id, "type": "contract"})
	
	try:
		# Send initial progress
		progress = upload_service.get_session_progress(session_id)
		if progress:
			await websocket.send_json({
				"type": "progress_update",
				"session_id": session_id,
				"progress": progress.dict()
			})
		else:
			await websocket.send_json({
				"type": "error",
				"message": f"Contract upload session {session_id} not found"
			})
		
		# Keep connection alive and handle client messages
		while True:
			try:
				# Check for incoming messages (non-blocking)
				message = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
				await handle_contract_upload_client_message(websocket, session_id, message)
			except asyncio.TimeoutError:
				# No message received, send periodic updates
				progress = upload_service.get_session_progress(session_id)
				if progress:
					await websocket.send_json({
						"type": "progress_update",
						"session_id": session_id,
						"progress": progress.dict()
					})
					
					# Close connection if upload is finished
					if progress.status in [UploadStatus.COMPLETED, UploadStatus.FAILED, UploadStatus.CANCELLED]:
						break
				else:
					# Session not found, close connection
					break
			
			await asyncio.sleep(0.5)  # Update every 500ms
			
	except WebSocketDisconnect:
		logger.info(f"WebSocket disconnected for contract upload session {session_id}")
	except Exception as e:
		logger.error(f"WebSocket error for contract upload session {session_id}: {e}")
	finally:
		websocket_manager.disconnect(websocket, "upload", session_id)


async def handle_contract_upload_client_message(websocket: WebSocket, session_id: str, message: Dict[str, Any]):
	"""Handle messages from contract upload WebSocket clients."""
	try:
		message_type = message.get("type")
		
		if message_type == "ping":
			await websocket.send_json({"type": "pong"})
		elif message_type == "get_progress":
			progress = upload_service.get_session_progress(session_id)
			if progress:
				await websocket.send_json({
					"type": "progress_update",
					"session_id": session_id,
					"progress": progress.dict()
				})
		elif message_type == "cancel_upload":
			success = await upload_service.cancel_upload(session_id)
			await websocket.send_json({
				"type": "upload_cancelled" if success else "cancel_failed",
				"session_id": session_id
			})
		else:
			logger.warning(f"Unknown message type from contract upload client: {message_type}")
			
	except Exception as e:
		logger.error(f"Error handling contract upload client message: {e}")


async def broadcast_upload_progress(session_id: str, progress: UploadProgress):
	"""Broadcast contract upload progress to WebSocket clients."""
	try:
		from ...api.websockets import manager as websocket_manager
		await websocket_manager.send_to_task(session_id, {
			"type": "progress_update",
			"session_id": session_id,
			"progress": progress.dict()
		})
	except Exception as e:
		logger.error(f"Error broadcasting contract upload progress: {e}")


async def schedule_session_cleanup(session_id: str):
	"""Schedule cleanup of contract upload session after delay."""
	# Wait 24 hours before cleanup
	await asyncio.sleep(24 * 3600)
	
	try:
		await upload_service.cleanup_expired_sessions()
		logger.info(f"Cleanup completed for expired contract upload sessions")
	except Exception as e:
		logger.error(f"Error during contract upload session cleanup: {e}")


@router.post("/contracts/validate", response_model=dict, tags=["Contract Upload"])
async def validate_contract_file(
	request: Request,
	file: UploadFile = File(..., description="Contract file to validate")
) -> dict:
	"""
	Validate a contract file without uploading or processing.
	
	Args:
		request: FastAPI request object
		file: Contract file to validate
		
	Returns:
		dict: Validation results and file metadata
		
	Raises:
		HTTPException: For validation errors
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	logger.info(f"Contract validation requested for file: {file.filename}", extra={"request_id": request_id})
	
	try:
		# Perform comprehensive validation
		validation_result = await validate_file(file)
		
		# Read file content for additional analysis
		file_content = await file.read()
		file.file.seek(0)  # Reset file pointer
		
		# Basic content analysis using magic
		try:
			import magic
			file_magic = magic.from_buffer(file_content)
		except ImportError:
			# Fallback if python-magic is not available
			file_magic = f"File type: {validation_result.get('mime_type', 'unknown')}"
		except Exception:
			file_magic = "Unable to determine file type"
		
		# Calculate file hash
		import hashlib
		file_hash = hashlib.sha256(file_content).hexdigest()
		
		# Estimate processing time based on file size and type
		base_time = len(file_content) / 50000  # Base processing rate
		file_ext = validation_result.get("safe_filename", "").lower().split('.')[-1]
		
		# Adjust time based on file type complexity
		type_multipliers = {
			'pdf': 2.0,    # PDFs require more processing
			'docx': 1.5,   # DOCX files are moderately complex
			'txt': 0.5     # Text files are simple
		}
		
		multiplier = type_multipliers.get(file_ext, 1.0)
		estimated_processing_time = min(max(base_time * multiplier, 10), 300)  # 10s to 5min
		
		# Check if file already exists
		file_exists = temp_file_handler.file_exists(file_hash)
		
		return {
			"success": True,
			"message": "File validation completed successfully",
			"data": {
				"filename": validation_result["safe_filename"],
				"original_filename": validation_result["original_filename"],
				"file_size": len(file_content),
				"mime_type": validation_result.get("mime_type"),
				"file_type_description": file_magic,
				"file_hash": file_hash,
				"is_valid": True,
				"already_uploaded": file_exists,
				"estimated_processing_time_seconds": int(estimated_processing_time),
				"supported_file_types": ["pdf", "docx", "txt"],
				"max_file_size_mb": 50,
				"security_checks_passed": True,
				"supported_analysis_features": [
					"risk_assessment",
					"clause_identification", 
					"redline_generation",
					"precedent_matching",
					"contract_structure_analysis"
				],
				"validation_timestamp": validation_result.get("validation_timestamp")
			}
		}
		
	except (ValidationError, SecurityError) as e:
		# Return detailed validation failure information
		return {
			"success": False,
			"message": "File validation failed",
			"data": {
				"filename": file.filename,
				"is_valid": False,
				"error": str(e),
				"error_type": type(e).__name__,
				"suggestions": _get_validation_suggestions(e, file.filename),
				"supported_file_types": ["pdf", "docx", "txt"],
				"max_file_size_mb": 50
			}
		}
		
	except Exception as e:
		logger.error(f"Unexpected error during file validation: {e}", exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail="An unexpected error occurred during file validation")
	
	finally:
		if hasattr(file, "file") and file.file:
			file.file.close()


def _get_validation_suggestions(error: Exception, filename: str) -> List[str]:
	"""Generate helpful suggestions based on validation error."""
	suggestions = []
	error_msg = str(error).lower()
	
	if "file size" in error_msg or "exceeds" in error_msg:
		suggestions.extend([
			"Try compressing the file or reducing its size",
			"Maximum file size is 50MB",
			"Consider splitting large documents into smaller sections"
		])
	
	if "extension" in error_msg or "file type" in error_msg:
		suggestions.extend([
			"Supported file types are: PDF, DOCX, TXT",
			"Convert your file to one of the supported formats",
			"Ensure the file extension matches the actual file type"
		])
	
	if "mime type" in error_msg:
		suggestions.extend([
			"The file content doesn't match its extension",
			"Try re-saving the file in the correct format",
			"Ensure the file is not corrupted"
		])
	
	if "empty" in error_msg:
		suggestions.extend([
			"The file appears to be empty",
			"Ensure the file contains text content",
			"Try uploading a different file"
		])
	
	if "malicious" in error_msg or "security" in error_msg:
		suggestions.extend([
			"The file contains potentially unsafe content",
			"Remove any embedded scripts or macros",
			"Use a clean version of the document"
		])
	
	# Default suggestions if no specific ones apply
	if not suggestions:
		suggestions.extend([
			"Ensure the file is a valid PDF, DOCX, or TXT document",
			"Check that the file is not corrupted",
			"Try uploading a different version of the file"
		])
	
	return suggestions


@router.get("/contracts/{file_id}/status", response_model=dict, tags=["Contract Upload"])
async def get_contract_status(file_id: str) -> dict:
	"""
	Get the status of an uploaded contract file.
	
	Args:
		file_id: The file ID (hash) of the uploaded contract
		
	Returns:
		dict: Contract file status and metadata
		
	Raises:
		HTTPException: If file not found
	"""
	try:
		# Check if file exists in temporary storage
		if temp_file_handler.file_exists(file_id):
			file_info = temp_file_handler.get_file_info(file_id)
			
			# Calculate time remaining before expiration
			import time
			current_time = time.time()
			created_time = file_info.get("created_at", current_time)
			age_seconds = current_time - created_time
			max_age_seconds = temp_file_handler.settings.temp_file_cleanup_hours * 3600
			remaining_seconds = max(0, max_age_seconds - age_seconds)
			
			return {
				"success": True,
				"message": "Contract file found",
				"data": {
					"file_id": file_id,
					"status": "uploaded",
					"upload_timestamp": file_info.get("upload_timestamp"),
					"filename": file_info.get("filename"),
					"safe_filename": file_info.get("safe_filename"),
					"file_size": file_info.get("size"),
					"file_hash": file_info.get("file_hash"),
					"ready_for_analysis": True,
					"expires_at": file_info.get("expires_at"),
					"age_seconds": int(age_seconds),
					"remaining_seconds": int(remaining_seconds),
					"encrypted": file_info.get("encrypted", False)
				}
			}
		else:
			raise HTTPException(status_code=404, detail="Contract file not found or expired")
			
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error checking contract status: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Error checking contract status")


@router.get("/contracts/{file_id}/download", tags=["Contract Upload"])
async def download_contract_file(file_id: str) -> dict:
	"""
	Download a contract file by its ID.
	
	Args:
		file_id: The file ID (hash) of the uploaded contract
		
	Returns:
		dict: File download information or error
		
	Raises:
		HTTPException: If file not found or cannot be accessed
	"""
	try:
		# Check if file exists
		if not temp_file_handler.file_exists(file_id):
			raise HTTPException(status_code=404, detail="Contract file not found or expired")
		
		# Get file information
		file_info = temp_file_handler.get_file_info(file_id)
		file_path = temp_file_handler.get_file_path_by_id(file_id)
		
		if not file_path or not Path(file_path).exists():
			raise HTTPException(status_code=404, detail="Contract file not found on disk")
		
		# Read file content
		with open(file_path, 'rb') as f:
			file_content = f.read()
		
		# Decrypt if necessary
		if file_info.get("encrypted", False):
			try:
				file_content = temp_file_handler._decrypt_content(file_content)
			except Exception as e:
				logger.error(f"Failed to decrypt file {file_id}: {e}")
				raise HTTPException(status_code=500, detail="Failed to decrypt file")
		
		# Return file information (in a real implementation, you'd return the actual file)
		return {
			"success": True,
			"message": "File ready for download",
			"data": {
				"file_id": file_id,
				"filename": file_info.get("filename"),
				"safe_filename": file_info.get("safe_filename"),
				"file_size": len(file_content),
				"mime_type": "application/octet-stream",  # Generic for download
				"download_timestamp": datetime.utcnow().isoformat(),
				"content_available": True
			}
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error downloading contract file {file_id}: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Error downloading contract file")


@router.delete("/contracts/{file_id}", tags=["Contract Upload"])
async def delete_contract_file(file_id: str) -> dict:
	"""
	Delete a contract file by its ID.
	
	Args:
		file_id: The file ID (hash) of the uploaded contract
		
	Returns:
		dict: Deletion confirmation
		
	Raises:
		HTTPException: If file not found or cannot be deleted
	"""
	try:
		# Check if file exists
		if not temp_file_handler.file_exists(file_id):
			raise HTTPException(status_code=404, detail="Contract file not found or expired")
		
		# Get file information before deletion
		file_info = temp_file_handler.get_file_info(file_id)
		file_path = temp_file_handler.get_file_path_by_id(file_id)
		
		# Delete the file
		success = temp_file_handler.cleanup_file(file_path)
		
		if success:
			# Log file deletion
			log_audit_event(
				"contract_file_deleted",
				details={
					"file_id": file_id,
					"filename": file_info.get("filename"),
					"file_size": file_info.get("size")
				}
			)
			
			return {
				"success": True,
				"message": "Contract file deleted successfully",
				"data": {
					"file_id": file_id,
					"filename": file_info.get("filename"),
					"deletion_timestamp": datetime.utcnow().isoformat()
				}
			}
		else:
			raise HTTPException(status_code=500, detail="Failed to delete contract file")
			
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error deleting contract file {file_id}: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Error deleting contract file")


@router.post("/analyze-contract", response_model=AnalysisResponse, tags=["Contract Analysis"])
async def analyze_contract(
	request: Request, file: UploadFile = File(..., description="Contract file to analyze (.pdf or .docx)")
) -> AnalysisResponse:
	"""
	Analyze a contract document for risky clauses and generate negotiation suggestions.
	Updated to use working simple analysis service.
	"""
	start_time = time.time()
	request_id = getattr(request.state, "request_id", "unknown")

	logger.info(f"Contract analysis requested for file: {file.filename}", extra={"request_id": request_id})

	try:
		# Validate and process file
		file_content = await file.read()
		file.file.seek(0)
		
		if not file_content:
			raise HTTPException(status_code=400, detail="Empty file")
		
		# Save to temporary location for processing
		temp_file_path = temp_file_handler.save_temporary_file(file_content, file.filename)
		
		try:
			# Process document to extract text
			processed_doc = await document_processor.process_document(temp_file_path, file.filename)
			contract_text = processed_doc.content
			
			if not contract_text.strip():
				raise HTTPException(status_code=400, detail="No text content found in document")
			
			# Use production analysis service with unified AI backend
			analysis_service = get_production_contract_analysis_service()
			
			# Determine analysis type based on request parameters or file size
			analysis_type = "standard"  # Default to standard analysis
			if len(contract_text) < 1000:
				analysis_type = "quick"
			elif len(contract_text) > 5000:
				analysis_type = "comprehensive"
			
			logger.info(f"Using production analysis service with {analysis_type} analysis")
			analysis_result = await analysis_service.analyze_contract(
				contract_text=contract_text,
				filename=file.filename,
				analysis_type=analysis_type,
				use_cache=True
			)
			
		finally:
			# Clean up temp file
			temp_file_handler.cleanup_file(temp_file_path)
		
		# Convert to AnalysisResponse format
		return AnalysisResponse(
			risky_clauses=analysis_result.get("risky_clauses", []),
			suggested_redlines=analysis_result.get("suggested_redlines", []),
			email_draft=analysis_result.get("email_draft", ""),
			processing_time=analysis_result.get("processing_time", time.time() - start_time),
			status=analysis_result.get("status", "completed"),
			overall_risk_score=analysis_result.get("overall_risk_score", 0.0),
			warnings=analysis_result.get("warnings", []),
			errors=analysis_result.get("errors", []),
		)
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Analysis failed: {e}", exc_info=True)
		raise HTTPException(
			status_code=500,
			detail=f"Analysis failed: {str(e)}"
		)
	finally:
		if hasattr(file, "file") and file.file:
			file.file.close()

@router.post("/analyze-contract/async", response_model=AsyncAnalysisResponse, tags=["Contract Analysis"])
async def analyze_contract_async(
	request: Request,
	background_tasks: BackgroundTasks,
	file: UploadFile = File(..., description="Contract file to analyze (.pdf or .docx)"),
	analysis_request: AsyncAnalysisRequest = AsyncAnalysisRequest(),
) -> AsyncAnalysisResponse:
	"""
	Start asynchronous job application tracking with enhanced progress tracking and resource management.

	Args:
	    request: FastAPI request object
	    background_tasks: FastAPI background tasks
	    file: Uploaded contract file
	    analysis_request: Analysis configuration

	Returns:
	    AsyncAnalysisResponse: Task information for status tracking

	Raises:
	    HTTPException: For various error conditions
	"""
	request_id = getattr(request.state, "request_id", "unknown")

	logger.info(f"Enhanced async job application tracking requested for file: {file.filename}", extra={"request_id": request_id})

	try:
		# Validate the uploaded file
		await validate_file(file)

		# Read file content
		file_content = await file.read()
		if not file_content:
			raise ValidationError("Uploaded file is empty")

		# Process the document to extract text
		logger.debug(f"Processing document: {file.filename}", extra={"request_id": request_id})
		processed_doc = document_processor.process_document(file_content, file.filename)
		contract_text = processed_doc.content

		if not contract_text.strip():
			raise DocumentProcessingError("No text content could be extracted from the document")

		# Start analysis using the enhanced workflow service
		resource_limits = {
			"max_memory_mb": 2048,  # 2GB memory limit
			"max_cpu_percent": 85.0,  # 85% CPU limit
		}

		task_id = await workflow_service.start_analysis(
			contract_text=contract_text,
			contract_filename=file.filename,
			timeout_seconds=analysis_request.timeout_seconds or 300,
			enable_progress=analysis_request.enable_progress_tracking,
			resource_limits=resource_limits,
		)

		# Estimate completion time
		estimated_completion = datetime.utcnow() + timedelta(seconds=analysis_request.timeout_seconds or 300)

		logger.info(f"Started enhanced async analysis task {task_id} for {file.filename}", extra={"request_id": request_id})

		return AsyncAnalysisResponse(
			task_id=task_id, status="pending", estimated_completion_time=estimated_completion, status_url=f"/analyze-contract/async/{task_id}/status"
		)

	except (ValidationError, DocumentProcessingError) as e:
		raise e

	except ResourceExhaustionError as e:
		raise HTTPException(status_code=429, detail=str(e))

	except Exception as e:
		logger.error(f"Unexpected error starting async analysis: {e}", exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail="Failed to start analysis task")

	finally:
		# Ensure file is properly closed
		if hasattr(file, "file") and file.file:
			file.file.close()


@router.get("/analyze-contract/async/{task_id}/status", response_model=AnalysisStatusResponse, tags=["Contract Analysis"])
async def get_async_analysis_status(task_id: str) -> AnalysisStatusResponse:
	"""
	Get the status of an asynchronous analysis task with enhanced progress tracking.

	Args:
	    task_id: The ID of the analysis task

	Returns:
	    AnalysisStatusResponse: Current task status with progress updates and resource metrics

	Raises:
	    HTTPException: If task not found
	"""
	status_response = await workflow_service.get_task_status(task_id)

	if not status_response:
		raise HTTPException(status_code=404, detail="Analysis task not found")

	return status_response


@router.get("/analyze-contract/async/{task_id}/result", response_model=AnalysisResponse, tags=["Contract Analysis"])
async def get_async_analysis_result(task_id: str) -> AnalysisResponse:
	"""
	Get the result of a completed asynchronous analysis task.

	Args:
	    task_id: The ID of the analysis task

	Returns:
	    AnalysisResponse: Analysis results

	Raises:
	    HTTPException: If task not found or not completed
	"""
	# Get task status first
	status_response = await workflow_service.get_task_status(task_id)
	if not status_response:
		raise HTTPException(status_code=404, detail="Analysis task not found")

	if status_response.status != "completed":
		raise HTTPException(status_code=400, detail=f"Analysis task is not completed. Current status: {status_response.status}")

	# Get the actual result
	result = await workflow_service.get_task_result(task_id)
	if not result:
		raise HTTPException(status_code=500, detail="Analysis completed but no result available")

	return convert_workflow_result_to_response(result, status_response.processing_duration)


@router.get("/analyze-contract/{thread_id}/status", response_model=AnalysisStatusResponse, tags=["Contract Analysis"])
async def get_analysis_status(thread_id: str) -> AnalysisStatusResponse:
	"""
	Get the current status of a job application tracking workflow by thread ID.

	Args:
	    thread_id: The ID of the workflow thread to check

	Returns:
	    AnalysisStatusResponse: Current workflow status information
	"""
	logger.info(f"Fetching status for workflow thread_id: {thread_id}")

	try:
		status_dict = workflow.get_workflow_status(thread_id=thread_id)

		# Convert dict to AnalysisStatusResponse
		return AnalysisStatusResponse(
			status=status_dict.get("status", "unknown"),
			current_node=status_dict.get("current_node", "unknown"),
			execution_id=status_dict.get("execution_id", "unknown"),
			error_count=status_dict.get("error_count", 0),
			warnings=status_dict.get("warnings", []),
			last_error=status_dict.get("last_error"),
			start_time=status_dict.get("start_time"),
			end_time=status_dict.get("end_time"),
			processing_duration=status_dict.get("processing_duration"),
			risky_clauses_count=status_dict.get("risky_clauses_count", 0),
			redlines_count=status_dict.get("redlines_count", 0),
			overall_risk_score=status_dict.get("overall_risk_score"),
			contract_filename=status_dict.get("contract_filename", "unknown"),
		)

	except Exception as e:
		logger.error(f"Error fetching workflow status: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to fetch workflow status")


@router.get("/contracts/list", response_model=dict, tags=["Contract Upload"])
async def list_uploaded_contracts() -> dict:
	"""
	List all uploaded contract files with their status and metadata.
	
	Returns:
		dict: List of uploaded contracts with metadata
	"""
	try:
		# Get information about all active files
		files_info = temp_file_handler.get_active_files_info()
		
		# Format file information for response
		contracts = []
		for file_path, file_info in temp_file_handler.active_files.items():
			contracts.append({
				"file_id": file_info.get("file_id") or file_info.get("file_hash"),
				"filename": file_info.get("filename"),
				"safe_filename": file_info.get("safe_filename"),
				"file_size": file_info.get("size"),
				"upload_timestamp": datetime.fromtimestamp(file_info["created_at"]).isoformat(),
				"age_seconds": time.time() - file_info["created_at"],
				"encrypted": file_info.get("encrypted", False),
				"status": "uploaded"
			})
		
		# Sort by upload time (newest first)
		contracts.sort(key=lambda x: x["upload_timestamp"], reverse=True)
		
		return {
			"success": True,
			"message": f"Found {len(contracts)} uploaded contracts",
			"data": {
				"contracts": contracts,
				"total_count": len(contracts),
				"total_size_bytes": files_info["total_size_bytes"],
				"total_size_mb": files_info["total_size_mb"]
			}
		}
		
	except Exception as e:
		logger.error(f"Error listing uploaded contracts: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Error listing uploaded contracts")


@router.post("/contracts/cleanup", response_model=dict, tags=["Contract Upload"])
async def cleanup_old_contracts(max_age_hours: Optional[int] = None) -> dict:
	"""
	Clean up old contract files to free storage space.
	
	Args:
		max_age_hours: Maximum age in hours before cleanup (optional)
		
	Returns:
		dict: Cleanup results
	"""
	try:
		# Use default cleanup age if not specified
		if max_age_hours is None:
			max_age_hours = temp_file_handler.settings.temp_file_cleanup_hours
		
		# Perform cleanup
		cleaned_count = temp_file_handler.cleanup_old_files(max_age_hours)
		
		# Log cleanup operation
		log_audit_event(
			"contract_files_cleanup",
			details={
				"cleaned_count": cleaned_count,
				"max_age_hours": max_age_hours
			}
		)
		
		return {
			"success": True,
			"message": f"Cleanup completed successfully",
			"data": {
				"files_cleaned": cleaned_count,
				"max_age_hours": max_age_hours,
				"cleanup_timestamp": datetime.utcnow().isoformat()
			}
		}
		
	except Exception as e:
		logger.error(f"Error during contract cleanup: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Error during contract cleanup")


@router.get("/analyze-contract/tasks/active", response_model=List[AnalysisStatusResponse], tags=["Contract Analysis"])
async def get_active_tasks() -> List[AnalysisStatusResponse]:
	"""
	Get the status of all active analysis tasks with enhanced monitoring.

	Returns:
	    List[AnalysisStatusResponse]: List of active task statuses with progress and resource metrics
	"""
	return await workflow_service.get_active_tasks()


@router.delete("/analyze-contract/async/{task_id}", tags=["Contract Analysis"])
async def cancel_async_analysis(task_id: str) -> dict:
	"""
	Cancel an active asynchronous analysis task.

	Args:
	    task_id: The ID of the analysis task to cancel

	Returns:
	    dict: Cancellation confirmation

	Raises:
	    HTTPException: If task not found or cannot be cancelled
	"""
	success = await workflow_service.cancel_task(task_id)

	if not success:
		raise HTTPException(status_code=404, detail="Analysis task not found or cannot be cancelled")

	logger.info(f"Cancelled analysis task {task_id}")
	return {"message": f"Analysis task {task_id} has been cancelled"}


@router.post("/workflows/create", response_model=dict, tags=["Agent Workflow"])
async def create_agent_workflow(
	request: Request,
	file_id: Optional[str] = None,
	file: Optional[UploadFile] = File(None),
	workflow_config: Optional[dict] = None
) -> dict:
	"""
	Create a new agent workflow for job application tracking.
	
	Args:
		request: FastAPI request object
		file_id: ID of previously uploaded file
		file: New file to upload and analyze
		workflow_config: Workflow configuration options
		
	Returns:
		dict: Workflow creation response with workflow ID
		
	Raises:
		HTTPException: For validation or creation errors
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		# Validate input - either file_id or file must be provided
		if not file_id and not file:
			raise HTTPException(status_code=400, detail="Either file_id or file must be provided")
		
		if file_id and file:
			raise HTTPException(status_code=400, detail="Provide either file_id or file, not both")
		
		# Handle file upload if new file provided
		if file:
			file_validator = FileSecurityValidator()
			file_content, mime_type, validated_filename = await file_validator.validate_upload_file(file)
			
			# Process document
			temp_file_path = temp_file_handler.save_temporary_file(file_content, validated_filename)
			processed_doc = await document_processor.process_document(temp_file_path, validated_filename)
			contract_text = processed_doc.content
			contract_filename = validated_filename
			
			# Generate file ID
			import hashlib
			file_id = hashlib.sha256(file_content).hexdigest()
		else:
			# Use existing file
			if not temp_file_handler.file_exists(file_id):
				raise HTTPException(status_code=404, detail="File not found or expired")
			
			file_info = temp_file_handler.get_file_info(file_id)
			temp_file_path = file_info.get("temp_path")
			contract_filename = file_info.get("filename")
			
			# Re-process document to get text
			processed_doc = await document_processor.process_document(temp_file_path, contract_filename)
			contract_text = processed_doc.content
		
		# Create workflow configuration
		config = workflow_config or {}
		timeout_seconds = config.get("timeout_seconds", 300)
		priority = config.get("priority", "normal")
		enable_progress = config.get("enable_progress_tracking", True)
		
		# Start workflow using orchestration service
		from ...agents.orchestration_service import orchestration_service
		
		workflow_id = await orchestration_service.create_workflow(
			contract_text=contract_text,
			contract_filename=contract_filename,
			file_id=file_id,
			config=config
		)
		
		# Log workflow creation
		user_id = getattr(request.state, "user_id", None)
		log_audit_event(
			"workflow_created",
			details={
				"workflow_id": workflow_id,
				"file_id": file_id,
				"filename": contract_filename,
				"config": config,
				"user_id": user_id
			}
		)
		
		logger.info(f"Agent workflow {workflow_id} created for file {contract_filename}", extra={"request_id": request_id})
		
		return {
			"success": True,
			"message": "Agent workflow created successfully",
			"data": {
				"workflow_id": workflow_id,
				"file_id": file_id,
				"filename": contract_filename,
				"status": "created",
				"created_at": datetime.utcnow().isoformat(),
				"estimated_completion_time": (datetime.utcnow() + timedelta(seconds=timeout_seconds)).isoformat(),
				"status_url": f"/workflows/{workflow_id}/status",
				"config": config
			}
		}
		
	except HTTPException:
		raise
	except (ValidationError, SecurityError, DocumentProcessingError) as e:
		raise e
	except Exception as e:
		logger.error(f"Error creating agent workflow: {e}", exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail="Failed to create agent workflow")


@router.post("/workflows/{workflow_id}/execute", response_model=dict, tags=["Agent Workflow"])
async def execute_agent_workflow(
	workflow_id: str,
	request: Request,
	execution_options: Optional[dict] = None
) -> dict:
	"""
	Execute an agent workflow for job application tracking.
	
	Args:
		workflow_id: ID of the workflow to execute
		request: FastAPI request object
		execution_options: Execution configuration options
		
	Returns:
		dict: Workflow execution response
		
	Raises:
		HTTPException: For execution errors
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		from ...agents.orchestration_service import orchestration_service
		
		# Execute workflow
		execution_id = await orchestration_service.execute_workflow(
			workflow_id=workflow_id,
			options=execution_options or {}
		)
		
		# Log workflow execution
		user_id = getattr(request.state, "user_id", None)
		log_audit_event(
			"workflow_executed",
			details={
				"workflow_id": workflow_id,
				"execution_id": execution_id,
				"options": execution_options
			}
		)
		
		logger.info(f"Agent workflow {workflow_id} execution started: {execution_id}", extra={"request_id": request_id})
		
		return {
			"success": True,
			"message": "Agent workflow execution started",
			"data": {
				"workflow_id": workflow_id,
				"execution_id": execution_id,
				"status": "executing",
				"started_at": datetime.utcnow().isoformat(),
				"progress_url": f"/workflows/{workflow_id}/executions/{execution_id}/progress"
			}
		}
		
	except Exception as e:
		logger.error(f"Error executing workflow {workflow_id}: {e}", exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail="Failed to execute agent workflow")


@router.get("/workflows/{workflow_id}/status", response_model=dict, tags=["Agent Workflow"])
async def get_workflow_status(workflow_id: str) -> dict:
	"""
	Get the status of an agent workflow.
	
	Args:
		workflow_id: ID of the workflow
		
	Returns:
		dict: Workflow status information
		
	Raises:
		HTTPException: If workflow not found
	"""
	try:
		from ...agents.orchestration_service import orchestration_service
		
		status = await orchestration_service.get_workflow_status(workflow_id)
		
		if not status:
			raise HTTPException(status_code=404, detail="Workflow not found")
		
		return {
			"success": True,
			"message": "Workflow status retrieved",
			"data": status
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting workflow status: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to get workflow status")


@router.get("/workflows/{workflow_id}/executions/{execution_id}/progress", response_model=dict, tags=["Agent Workflow"])
async def get_execution_progress(workflow_id: str, execution_id: str) -> dict:
	"""
	Get the progress of a workflow execution.
	
	Args:
		workflow_id: ID of the workflow
		execution_id: ID of the execution
		
	Returns:
		dict: Execution progress information
		
	Raises:
		HTTPException: If execution not found
	"""
	try:
		from ...agents.orchestration_service import orchestration_service
		
		progress = await orchestration_service.get_execution_progress(workflow_id, execution_id)
		
		if not progress:
			raise HTTPException(status_code=404, detail="Execution not found")
		
		return {
			"success": True,
			"message": "Execution progress retrieved",
			"data": progress
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting execution progress: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to get execution progress")


@router.get("/workflows/active", response_model=dict, tags=["Agent Workflow"])
async def get_active_workflows(
	limit: int = 50,
	offset: int = 0,
	status_filter: Optional[str] = None
) -> dict:
	"""
	Get list of active agent workflows.
	
	Args:
		limit: Maximum number of workflows to return
		offset: Number of workflows to skip
		status_filter: Filter by workflow status
		
	Returns:
		dict: List of active workflows
	"""
	try:
		from ...agents.orchestration_service import orchestration_service
		
		workflows = await orchestration_service.get_active_workflows(
			limit=limit,
			offset=offset,
			status_filter=status_filter
		)
		
		return {
			"success": True,
			"message": "Active workflows retrieved",
			"data": {
				"workflows": workflows,
				"total_count": len(workflows),
				"limit": limit,
				"offset": offset
			}
		}
		
	except Exception as e:
		logger.error(f"Error getting active workflows: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to get active workflows")


@router.delete("/workflows/{workflow_id}", response_model=dict, tags=["Agent Workflow"])
async def cancel_workflow(workflow_id: str, request: Request) -> dict:
	"""
	Cancel an agent workflow.
	
	Args:
		workflow_id: ID of the workflow to cancel
		request: FastAPI request object
		
	Returns:
		dict: Cancellation confirmation
		
	Raises:
		HTTPException: If workflow not found or cannot be cancelled
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		from ...agents.orchestration_service import orchestration_service
		
		success = await orchestration_service.cancel_workflow(workflow_id)
		
		if not success:
			raise HTTPException(status_code=404, detail="Workflow not found or cannot be cancelled")
		
		# Log workflow cancellation
		user_id = getattr(request.state, "user_id", None)
		log_audit_event(
			"workflow_cancelled",
			details={"workflow_id": workflow_id, "user_id": user_id}
		)
		
		logger.info(f"Agent workflow {workflow_id} cancelled", extra={"request_id": request_id})
		
		return {
			"success": True,
			"message": "Workflow cancelled successfully",
			"data": {
				"workflow_id": workflow_id,
				"status": "cancelled",
				"cancelled_at": datetime.utcnow().isoformat()
			}
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error cancelling workflow {workflow_id}: {e}", exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail="Failed to cancel workflow")


@router.get("/agents/status", response_model=dict, tags=["Agent Workflow"])
async def get_agents_status() -> dict:
	"""
	Get the status of all available agents.
	
	Returns:
		dict: Status of all agents in the system
	"""
	try:
		from ...agents.orchestration_service import orchestration_service
		
		agents_status = await orchestration_service.get_agents_status()
		
		return {
			"success": True,
			"message": "Agents status retrieved",
			"data": agents_status
		}
		
	except Exception as e:
		logger.error(f"Error getting agents status: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to get agents status")


@router.get("/analyze-contract/service/metrics", tags=["Contract Analysis"])
async def get_service_metrics() -> dict:
	"""
	Get service-level metrics for monitoring and capacity planning.

	Returns:
	    dict: Service metrics including task counts and resource utilization
	"""
	return workflow_service.get_service_metrics()


@router.get("/analysis/{analysis_id}/results", response_model=dict, tags=["Analysis Results"])
async def get_analysis_results(
	analysis_id: str,
	include_details: bool = True,
	format_type: str = "json"
) -> dict:
	"""
	Get comprehensive analysis results for a completed analysis.
	
	Args:
		analysis_id: ID of the analysis (workflow_id or task_id)
		include_details: Whether to include detailed clause analysis
		format_type: Response format (json, summary)
		
	Returns:
		dict: Analysis results with risk assessment and redlines
		
	Raises:
		HTTPException: If analysis not found or not completed
	"""
	try:
		# Try to get results from workflow service first
		result = await workflow_service.get_task_result(analysis_id)
		
		if not result:
			# Try orchestration service
			from ...agents.orchestration_service import orchestration_service
			result = await orchestration_service.get_analysis_results(analysis_id)
		
		if not result:
			raise HTTPException(status_code=404, detail="Analysis results not found")
		
		# Format results based on request
		if format_type == "summary":
			formatted_result = {
				"analysis_id": analysis_id,
				"overall_risk_score": result.get("overall_risk_score", 0.0),
				"risk_level": _get_risk_level(result.get("overall_risk_score", 0.0)),
				"risky_clauses_count": len(result.get("risky_clauses", [])),
				"redlines_count": len(result.get("suggested_redlines", [])),
				"analysis_timestamp": result.get("analysis_timestamp"),
				"status": result.get("status", "completed")
			}
		else:
			formatted_result = result
			
			if include_details:
				# Add detailed clause analysis
				formatted_result["detailed_analysis"] = {
					"clause_breakdown": _analyze_clause_types(result.get("risky_clauses", [])),
					"risk_distribution": _calculate_risk_distribution(result.get("risky_clauses", [])),
					"precedent_matches": result.get("precedent_matches", []),
					"negotiation_recommendations": result.get("negotiation_recommendations", [])
				}
		
		return {
			"success": True,
			"message": "Analysis results retrieved successfully",
			"data": formatted_result
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting analysis results: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to retrieve analysis results")


@router.get("/analysis/{analysis_id}/redlines", response_model=dict, tags=["Analysis Results"])
async def get_redline_suggestions(
	analysis_id: str,
	clause_filter: Optional[str] = None,
	risk_level_filter: Optional[str] = None
) -> dict:
	"""
	Get redline suggestions for a completed analysis.
	
	Args:
		analysis_id: ID of the analysis
		clause_filter: Filter by clause type
		risk_level_filter: Filter by risk level (Low, Medium, High)
		
	Returns:
		dict: Redline suggestions with filtering options
		
	Raises:
		HTTPException: If analysis not found
	"""
	try:
		# Get analysis results
		result = await workflow_service.get_task_result(analysis_id)
		
		if not result:
			from ...agents.orchestration_service import orchestration_service
			result = await orchestration_service.get_analysis_results(analysis_id)
		
		if not result:
			raise HTTPException(status_code=404, detail="Analysis not found")
		
		redlines = result.get("suggested_redlines", [])
		
		# Apply filters
		if clause_filter:
			redlines = [r for r in redlines if clause_filter.lower() in r.get("clause_type", "").lower()]
		
		if risk_level_filter:
			redlines = [r for r in redlines if r.get("risk_level", "").lower() == risk_level_filter.lower()]
		
		# Enhance redlines with additional metadata
		enhanced_redlines = []
		for redline in redlines:
			enhanced_redline = {
				**redline,
				"redline_id": f"{analysis_id}_{len(enhanced_redlines)}",
				"confidence_score": redline.get("confidence_score", 0.8),
				"implementation_difficulty": _assess_implementation_difficulty(redline),
				"legal_precedents": redline.get("precedent_references", []),
				"alternative_approaches": redline.get("alternatives", [])
			}
			enhanced_redlines.append(enhanced_redline)
		
		return {
			"success": True,
			"message": "Redline suggestions retrieved successfully",
			"data": {
				"analysis_id": analysis_id,
				"total_redlines": len(enhanced_redlines),
				"filtered_count": len(enhanced_redlines),
				"redlines": enhanced_redlines,
				"filters_applied": {
					"clause_filter": clause_filter,
					"risk_level_filter": risk_level_filter
				}
			}
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting redline suggestions: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to retrieve redline suggestions")


@router.post("/analysis/{analysis_id}/redlines/{redline_id}/accept", response_model=dict, tags=["Analysis Results"])
async def accept_redline_suggestion(
	analysis_id: str,
	redline_id: str,
	request: Request,
	modifications: Optional[dict] = None
) -> dict:
	"""
	Accept a redline suggestion with optional modifications.
	
	Args:
		analysis_id: ID of the analysis
		redline_id: ID of the redline suggestion
		request: FastAPI request object
		modifications: Optional modifications to the redline
		
	Returns:
		dict: Acceptance confirmation and updated contract
		
	Raises:
		HTTPException: If redline not found
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		# Get the redline suggestion
		result = await workflow_service.get_task_result(analysis_id)
		if not result:
			raise HTTPException(status_code=404, detail="Analysis not found")
		
		redlines = result.get("suggested_redlines", [])
		redline = next((r for r in redlines if f"{analysis_id}_{redlines.index(r)}" == redline_id), None)
		
		if not redline:
			raise HTTPException(status_code=404, detail="Redline suggestion not found")
		
		# Apply modifications if provided
		if modifications:
			redline.update(modifications)
		
		# Generate updated contract text
		updated_contract = _apply_redline_to_contract(
			original_text=result.get("original_contract_text", ""),
			redline=redline
		)
		
		# Log redline acceptance
		user_id = getattr(request.state, "user_id", None)
		log_audit_event(
			"redline_accepted",
			details={
				"analysis_id": analysis_id,
				"redline_id": redline_id,
				"modifications": modifications,
				"user_id": user_id
			}
		)
		
		logger.info(f"Redline {redline_id} accepted for analysis {analysis_id}", extra={"request_id": request_id})
		
		return {
			"success": True,
			"message": "Redline suggestion accepted successfully",
			"data": {
				"analysis_id": analysis_id,
				"redline_id": redline_id,
				"accepted_at": datetime.utcnow().isoformat(),
				"applied_redline": redline,
				"updated_contract_preview": updated_contract[:500] + "..." if len(updated_contract) > 500 else updated_contract,
				"full_contract_url": f"/analysis/{analysis_id}/contract/revised"
			}
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error accepting redline: {e}", exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail="Failed to accept redline suggestion")


@router.post("/analysis/{analysis_id}/contract/generate-revised", response_model=dict, tags=["Analysis Results"])
async def generate_revised_contract(
	analysis_id: str,
	request: Request,
	accepted_redlines: List[str],
	export_format: str = "pdf"
) -> dict:
	"""
	Generate a revised contract with accepted redlines.
	
	Args:
		analysis_id: ID of the analysis
		request: FastAPI request object
		accepted_redlines: List of accepted redline IDs
		export_format: Export format (pdf, docx, txt)
		
	Returns:
		dict: Revised contract generation response
		
	Raises:
		HTTPException: If analysis not found or generation fails
	"""
	request_id = getattr(request.state, "request_id", "unknown")
	
	try:
		# Get analysis results
		result = await workflow_service.get_task_result(analysis_id)
		if not result:
			raise HTTPException(status_code=404, detail="Analysis not found")
		
		# Get original contract text
		original_text = result.get("original_contract_text", "")
		if not original_text:
			raise HTTPException(status_code=400, detail="Original contract text not available")
		
		# Apply accepted redlines
		revised_text = original_text
		applied_redlines = []
		
		redlines = result.get("suggested_redlines", [])
		for redline_id in accepted_redlines:
			# Find the redline by ID
			redline_index = int(redline_id.split("_")[-1]) if "_" in redline_id else -1
			if 0 <= redline_index < len(redlines):
				redline = redlines[redline_index]
				revised_text = _apply_redline_to_contract(revised_text, redline)
				applied_redlines.append(redline)
		
		# Generate document in requested format
		from ...services.document_processor import DocumentProcessingService
		doc_processor = DocumentProcessingService()
		
		output_filename = f"revised_contract_{analysis_id}.{export_format}"
		generated_file_path = await doc_processor.generate_document(
			content=revised_text,
			format=export_format,
			filename=output_filename
		)
		
		# Log contract generation
		user_id = getattr(request.state, "user_id", None)
		log_audit_event(
			"revised_contract_generated",
			details={
				"analysis_id": analysis_id,
				"accepted_redlines_count": len(accepted_redlines),
				"export_format": export_format,
				"output_filename": output_filename,
				"user_id": user_id
			}
		)
		
		logger.info(f"Revised contract generated for analysis {analysis_id}", extra={"request_id": request_id})
		
		return {
			"success": True,
			"message": "Revised contract generated successfully",
			"data": {
				"analysis_id": analysis_id,
				"output_filename": output_filename,
				"export_format": export_format,
				"applied_redlines_count": len(applied_redlines),
				"generated_at": datetime.utcnow().isoformat(),
				"download_url": f"/analysis/{analysis_id}/contract/download/{output_filename}",
				"file_size_bytes": len(revised_text.encode('utf-8')),
				"revision_summary": {
					"total_changes": len(applied_redlines),
					"risk_reduction_estimate": _calculate_risk_reduction(applied_redlines)
				}
			}
		}
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error generating revised contract: {e}", exc_info=True, extra={"request_id": request_id})
		raise HTTPException(status_code=500, detail="Failed to generate revised contract")


@router.get("/analysis/{analysis_id}/contract/download/{filename}", tags=["Analysis Results"])
async def download_revised_contract(analysis_id: str, filename: str):
	"""
	Download a generated revised contract file.
	
	Args:
		analysis_id: ID of the analysis
		filename: Name of the file to download
		
	Returns:
		FileResponse: The requested file
		
	Raises:
		HTTPException: If file not found
	"""
	try:
		from fastapi.responses import FileResponse
		import os
		
		# Construct file path (in a real implementation, this would be in a secure storage location)
		file_path = f"/tmp/contracts/{analysis_id}/{filename}"
		
		if not os.path.exists(file_path):
			raise HTTPException(status_code=404, detail="File not found")
		
		return FileResponse(
			path=file_path,
			filename=filename,
			media_type="application/octet-stream"
		)
		
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error downloading file: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to download file")


@router.get("/analyze-contract/async/{task_id}/progress", tags=["Contract Analysis"])
async def get_task_progress(task_id: str, limit: int = 10) -> List[ProgressUpdate]:
	"""
	Get progress updates for a specific task.

	Args:
	    task_id: The ID of the analysis task
	    limit: Maximum number of progress updates to return

	Returns:
	    List[ProgressUpdate]: Recent progress updates

	Raises:
	    HTTPException: If task not found
	"""
	status_response = await workflow_service.get_task_status(task_id)

	if not status_response:
		raise HTTPException(status_code=404, detail="Analysis task not found")

	return status_response.progress_updates[-limit:] if status_response.progress_updates else []


# Helper functions for analysis results processing
def _get_risk_level(risk_score: float) -> str:
	"""Convert risk score to risk level."""
	if risk_score >= 0.8:
		return "High"
	elif risk_score >= 0.5:
		return "Medium"
	else:
		return "Low"


def _analyze_clause_types(risky_clauses: List[dict]) -> dict:
	"""Analyze clause types distribution."""
	clause_types = {}
	for clause in risky_clauses:
		clause_type = clause.get("clause_type", "Unknown")
		clause_types[clause_type] = clause_types.get(clause_type, 0) + 1
	return clause_types


def _calculate_risk_distribution(risky_clauses: List[dict]) -> dict:
	"""Calculate risk level distribution."""
	distribution = {"High": 0, "Medium": 0, "Low": 0}
	for clause in risky_clauses:
		risk_level = clause.get("risk_level", "Low")
		distribution[risk_level] = distribution.get(risk_level, 0) + 1
	return distribution


def _assess_implementation_difficulty(redline: dict) -> str:
	"""Assess implementation difficulty of a redline."""
	# Simple heuristic based on change complexity
	change_length = len(redline.get("suggested_redline", ""))
	if change_length > 200:
		return "High"
	elif change_length > 50:
		return "Medium"
	else:
		return "Low"


def _apply_redline_to_contract(original_text: str, redline: dict) -> str:
	"""Apply a redline suggestion to contract text."""
	# Simple text replacement (in a real implementation, this would be more sophisticated)
	original_clause = redline.get("original_clause", "")
	suggested_redline = redline.get("suggested_redline", "")
	
	if original_clause and suggested_redline:
		return original_text.replace(original_clause, suggested_redline)
	
	return original_text


def _calculate_risk_reduction(applied_redlines: List[dict]) -> float:
	"""Calculate estimated risk reduction from applied redlines."""
	total_reduction = 0.0
	for redline in applied_redlines:
		# Simple heuristic based on risk level
		risk_level = redline.get("risk_level", "Low")
		if risk_level == "High":
			total_reduction += 0.3
		elif risk_level == "Medium":
			total_reduction += 0.2
		else:
			total_reduction += 0.1
	
	return min(total_reduction, 1.0)  # Cap at 100% reduction
