"""
File Storage API Endpoints

Provides REST API endpoints for file storage operations including
versioning, cleanup, and storage management.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import io

from ...services.file_storage_service import (
    file_storage_service, 
    FileRecord, 
    FileVersion, 
    StorageStats, 
    CleanupPolicy
)
from ...core.exceptions import StorageError, ValidationError
from ...core.logging import get_logger
from ...core.auth import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/file-storage", tags=["File Storage"])


class FileUploadRequest(BaseModel):
    """File upload request model."""
    content: str = Field(description="Base64 encoded file content")
    filename: str = Field(description="Original filename")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    tags: Optional[List[str]] = Field(default=None, description="File tags")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class FileUpdateRequest(BaseModel):
    """File update request model."""
    content: str = Field(description="Base64 encoded file content")
    filename: Optional[str] = Field(default=None, description="New filename")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class FileListResponse(BaseModel):
    """File list response model."""
    files: List[FileRecord] = Field(description="List of files")
    total_count: int = Field(description="Total number of files")
    active_count: int = Field(description="Number of active files")
    deleted_count: int = Field(description="Number of deleted files")


class CleanupRequest(BaseModel):
    """Cleanup request model."""
    policy_name: str = Field(default="default", description="Cleanup policy to use")
    dry_run: bool = Field(default=False, description="Perform dry run without actual cleanup")


@router.get("/", response_model=Dict[str, str])
async def get_file_storage_info():
    """Get file storage service information."""
    try:
        stats = await file_storage_service.get_storage_stats()
        
        return {
            "service": "File Storage Service",
            "version": "1.0.0",
            "storage_backend": stats.storage_backend,
            "status": "operational",
            "endpoints": {
                "upload": "POST /file-storage/upload - Upload a new file",
                "get": "GET /file-storage/{file_id} - Get file content",
                "update": "PUT /file-storage/{file_id} - Update file (creates new version)",
                "delete": "DELETE /file-storage/{file_id} - Delete file",
                "list": "GET /file-storage/list - List all files",
                "info": "GET /file-storage/{file_id}/info - Get file metadata",
                "versions": "GET /file-storage/{file_id}/versions - Get file versions",
                "stats": "GET /file-storage/stats - Get storage statistics",
                "cleanup": "POST /file-storage/cleanup - Clean up old files",
                "policies": "GET /file-storage/policies - Get cleanup policies"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get file storage info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service information")


@router.post("/upload", response_model=FileRecord)
async def upload_file(
    request: FileUploadRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Upload a new file to storage."""
    try:
        # Decode base64 content
        import base64
        try:
            content = base64.b64decode(request.content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {e}")
        
        # Prepare metadata
        metadata = request.metadata or {}
        if request.mime_type:
            metadata['mime_type'] = request.mime_type
        if request.tags:
            metadata['tags'] = request.tags
        if current_user:
            metadata['uploaded_by'] = current_user
        
        # Store file
        file_record = await file_storage_service.store_file(
            content=content,
            filename=request.filename,
            metadata=metadata
        )
        
        logger.info(f"File uploaded successfully: {request.filename} (ID: {file_record.file_id})")
        return file_record
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    version_id: Optional[str] = Query(None, description="Specific version ID"),
    download: bool = Query(False, description="Download as attachment"),
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get file content."""
    try:
        content, version = await file_storage_service.get_file(file_id, version_id)
        
        # Prepare response headers
        headers = {
            "Content-Type": version.mime_type,
            "Content-Length": str(len(content)),
            "X-File-ID": file_id,
            "X-Version-ID": version.version_id,
            "X-File-Hash": version.file_hash
        }
        
        if download:
            headers["Content-Disposition"] = f'attachment; filename="{version.original_filename}"'
        
        # Return file content as streaming response
        return StreamingResponse(
            io.BytesIO(content),
            media_type=version.mime_type,
            headers=headers
        )
    
    except StorageError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file")


@router.put("/{file_id}", response_model=FileVersion)
async def update_file(
    file_id: str,
    request: FileUpdateRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Update an existing file (creates new version)."""
    try:
        # Decode base64 content
        import base64
        try:
            content = base64.b64decode(request.content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {e}")
        
        # Prepare metadata
        metadata = request.metadata or {}
        if request.mime_type:
            metadata['mime_type'] = request.mime_type
        if current_user:
            metadata['updated_by'] = current_user
        
        # Update file
        new_version = await file_storage_service.update_file(
            file_id=file_id,
            content=content,
            filename=request.filename,
            metadata=metadata
        )
        
        logger.info(f"File updated successfully: {file_id} (new version: {new_version.version_id})")
        return new_version
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update file")


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    hard_delete: bool = Query(False, description="Perform hard delete (permanent)"),
    current_user: Optional[str] = Depends(get_current_user)
):
    """Delete a file."""
    try:
        success = await file_storage_service.delete_file(file_id, hard_delete)
        
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        
        delete_type = "hard" if hard_delete else "soft"
        logger.info(f"File {delete_type} deleted successfully: {file_id}")
        
        return {
            "success": True,
            "message": f"File {delete_type} deleted successfully",
            "file_id": file_id,
            "hard_delete": hard_delete
        }
    
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")


@router.get("/list", response_model=FileListResponse)
async def list_files(
    include_deleted: bool = Query(False, description="Include soft-deleted files"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of files to return"),
    offset: int = Query(0, ge=0, description="Number of files to skip"),
    current_user: Optional[str] = Depends(get_current_user)
):
    """List all files with optional filtering."""
    try:
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Get all files
        all_files = await file_storage_service.list_files(
            include_deleted=include_deleted,
            tags=tag_list
        )
        
        # Apply pagination
        total_count = len(all_files)
        files = all_files[offset:offset + limit]
        
        # Count active and deleted files
        active_count = sum(1 for f in all_files if not f.is_deleted)
        deleted_count = total_count - active_count
        
        return FileListResponse(
            files=files,
            total_count=total_count,
            active_count=active_count,
            deleted_count=deleted_count
        )
    
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")


@router.get("/{file_id}/info", response_model=FileRecord)
async def get_file_info(
    file_id: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get file metadata without content."""
    try:
        file_record = await file_storage_service.get_file_info(file_id)
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        return file_record
    
    except Exception as e:
        logger.error(f"Failed to get file info {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file information")


@router.get("/{file_id}/versions", response_model=List[FileVersion])
async def get_file_versions(
    file_id: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get all versions of a file."""
    try:
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
async def get_storage_stats(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get storage statistics."""
    try:
        stats = await file_storage_service.get_storage_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get storage statistics")


@router.post("/cleanup")
async def cleanup_files(
    request: CleanupRequest = Body(...),
    current_user: Optional[str] = Depends(get_current_user)
):
    """Clean up old files according to policy."""
    try:
        if request.dry_run:
            # For dry run, we would need to implement a preview function
            # For now, just return the policy information
            policies = file_storage_service.get_cleanup_policies()
            policy = policies.get(request.policy_name)
            
            if not policy:
                raise HTTPException(status_code=400, detail=f"Unknown cleanup policy: {request.policy_name}")
            
            return {
                "dry_run": True,
                "policy": policy.dict(),
                "message": "Dry run completed - no files were actually deleted"
            }
        else:
            # Perform actual cleanup
            stats = await file_storage_service.cleanup_files(request.policy_name)
            
            logger.info(f"Cleanup completed with policy '{request.policy_name}': {stats}")
            
            return {
                "success": True,
                "policy_name": request.policy_name,
                "cleanup_stats": stats
            }
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cleanup files: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup files")


@router.get("/policies", response_model=Dict[str, CleanupPolicy])
async def get_cleanup_policies(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get all cleanup policies."""
    try:
        policies = file_storage_service.get_cleanup_policies()
        return policies
    
    except Exception as e:
        logger.error(f"Failed to get cleanup policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cleanup policies")


@router.post("/policies", response_model=Dict[str, str])
async def add_cleanup_policy(
    policy: CleanupPolicy,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Add a new cleanup policy."""
    try:
        file_storage_service.add_cleanup_policy(policy)
        
        return {
            "success": True,
            "message": f"Cleanup policy '{policy.name}' added successfully",
            "policy_name": policy.name
        }
    
    except Exception as e:
        logger.error(f"Failed to add cleanup policy: {e}")
        raise HTTPException(status_code=500, detail="Failed to add cleanup policy")


@router.post("/start-background-cleanup")
async def start_background_cleanup(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Start background cleanup task."""
    try:
        await file_storage_service.start_background_cleanup()
        
        return {
            "success": True,
            "message": "Background cleanup task started"
        }
    
    except Exception as e:
        logger.error(f"Failed to start background cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to start background cleanup")


@router.post("/stop-background-cleanup")
async def stop_background_cleanup(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Stop background cleanup task."""
    try:
        await file_storage_service.stop_background_cleanup()
        
        return {
            "success": True,
            "message": "Background cleanup task stopped"
        }
    
    except Exception as e:
        logger.error(f"Failed to stop background cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop background cleanup")