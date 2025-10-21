"""
Backup and recovery API endpoints
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from app.services.backup_service import backup_service
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class BackupRequest(BaseModel):
    """Request model for creating backups"""
    include_files: bool = True
    compress: bool = True
    description: str = None


class RestoreRequest(BaseModel):
    """Request model for restoring from backup"""
    backup_name: str
    restore_database: bool = True
    restore_files: bool = True
    confirm: bool = False  # Safety flag


@router.post("/create")
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Create a new system backup
    
    This endpoint creates a comprehensive backup including:
    - Database dump (PostgreSQL)
    - Configuration files
    - Uploaded files (optional)
    - Application logs
    """
    try:
        logger.info(f"Creating backup with options: {request.dict()}")
        
        # For large backups, run in background
        if request.include_files:
            background_tasks.add_task(
                _create_backup_task,
                request.include_files,
                request.compress,
                request.description
            )
            
            return {
                "message": "Backup creation started in background",
                "status": "started",
                "include_files": request.include_files,
                "compress": request.compress
            }
        else:
            # Small backup, run synchronously
            backup_info = backup_service.create_full_backup(
                include_files=request.include_files,
                compress=request.compress
            )
            
            if request.description:
                backup_info["description"] = request.description
            
            return backup_info
            
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")


@router.get("/list")
async def list_backups() -> Dict[str, Any]:
    """
    List all available backups
    
    Returns information about all backups including:
    - Backup name and creation date
    - Size and type (compressed/directory)
    - Manifest information if available
    """
    try:
        backups = backup_service.list_backups()
        
        return {
            "backups": backups,
            "total_count": len(backups),
            "timestamp": backup_service._get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Failed to list backups: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.get("/info/{backup_name}")
async def get_backup_info(backup_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific backup
    """
    try:
        backups = backup_service.list_backups()
        backup_info = next((b for b in backups if b["name"] == backup_name), None)
        
        if not backup_info:
            raise HTTPException(status_code=404, detail=f"Backup not found: {backup_name}")
        
        return backup_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backup info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get backup info: {str(e)}")


@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Restore system from backup
    
    WARNING: This operation will overwrite existing data!
    Set confirm=true to proceed with restore.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Restore operation requires confirmation. Set 'confirm' to true."
        )
    
    try:
        logger.warning(f"Starting restore from backup: {request.backup_name}")
        
        # Run restore in background for safety
        background_tasks.add_task(
            _restore_backup_task,
            request.backup_name,
            request.restore_database,
            request.restore_files
        )
        
        return {
            "message": "Restore operation started in background",
            "backup_name": request.backup_name,
            "restore_database": request.restore_database,
            "restore_files": request.restore_files,
            "status": "started",
            "warning": "Monitor logs for restore progress and completion"
        }
        
    except Exception as e:
        logger.error(f"Failed to start restore: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_backups(
    keep_days: int = Query(30, ge=1, le=365, description="Number of days to keep backups")
) -> Dict[str, Any]:
    """
    Clean up old backups
    
    Removes backups older than the specified number of days.
    Default is 30 days.
    """
    try:
        cleanup_info = backup_service.cleanup_old_backups(keep_days=keep_days)
        
        logger.info(f"Cleaned up {cleanup_info['deleted_count']} old backups")
        
        return cleanup_info
        
    except Exception as e:
        logger.error(f"Failed to cleanup backups: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.delete("/{backup_name}")
async def delete_backup(backup_name: str) -> Dict[str, Any]:
    """
    Delete a specific backup
    """
    try:
        import shutil
        from pathlib import Path
        
        backup_dir = Path("backups")
        backup_path = backup_dir / backup_name
        
        # Try both directory and compressed file
        deleted = False
        if backup_path.exists():
            if backup_path.is_dir():
                shutil.rmtree(backup_path)
            else:
                backup_path.unlink()
            deleted = True
        
        # Try compressed version
        compressed_path = backup_dir / f"{backup_name}.tar.gz"
        if compressed_path.exists():
            compressed_path.unlink()
            deleted = True
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Backup not found: {backup_name}")
        
        logger.info(f"Deleted backup: {backup_name}")
        
        return {
            "message": f"Backup deleted successfully: {backup_name}",
            "backup_name": backup_name,
            "timestamp": backup_service._get_current_timestamp()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")


@router.get("/export/database")
async def export_database_json() -> Dict[str, Any]:
    """
    Export database as JSON for manual backup/migration
    
    This creates a portable JSON export of all database data
    that can be used for migration or manual backup purposes.
    """
    try:
        from pathlib import Path
        import tempfile
        
        # Create temporary export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        backup_service._export_data_as_json(temp_path)
        
        # Read the file size
        file_size = temp_path.stat().st_size
        
        return {
            "message": "Database exported successfully",
            "export_path": str(temp_path),
            "size_mb": round(file_size / 1024 / 1024, 2),
            "timestamp": backup_service._get_current_timestamp(),
            "note": "Export file is temporary and should be downloaded immediately"
        }
        
    except Exception as e:
        logger.error(f"Failed to export database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database export failed: {str(e)}")


async def _create_backup_task(include_files: bool, compress: bool, description: str = None):
    """Background task for creating backups"""
    try:
        backup_info = backup_service.create_full_backup(
            include_files=include_files,
            compress=compress
        )
        
        if description:
            backup_info["description"] = description
        
        logger.info(f"Background backup completed: {backup_info.get('backup_id')}")
        
    except Exception as e:
        logger.error(f"Background backup failed: {str(e)}")


async def _restore_backup_task(backup_name: str, restore_database: bool, restore_files: bool):
    """Background task for restoring backups"""
    try:
        restore_info = backup_service.restore_from_backup(
            backup_name=backup_name,
            restore_database=restore_database,
            restore_files=restore_files
        )
        
        logger.info(f"Background restore completed: {backup_name}")
        
    except Exception as e:
        logger.error(f"Background restore failed: {str(e)}")


# Add helper method to backup service
def _get_current_timestamp():
    """Helper to get current timestamp"""
    from datetime import datetime
    return datetime.utcnow().isoformat()

# Monkey patch the method
backup_service._get_current_timestamp = _get_current_timestamp