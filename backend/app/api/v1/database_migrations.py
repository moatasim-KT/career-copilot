"""
Database migration management API endpoints.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.database_migrations import get_migration_manager, DatabaseMigrationManager
from ...core.auth import get_current_user
from ...models.database_models import User
from ...models.api_models import BaseResponse

router = APIRouter(prefix="/database-migrations", tags=["Database Migrations"])


class CreateMigrationRequest(BaseModel):
    """Request model for creating a migration."""
    name: str
    description: str = ""
    up_sql: str = ""
    down_sql: str = ""
    dependencies: Optional[List[str]] = None


@router.get("/status", response_model=BaseResponse)
async def get_migration_status(
    current_user: User = Depends(get_current_user),
    migration_manager: DatabaseMigrationManager = Depends(get_migration_manager)
):
    """
    Get current database migration status.
    
    Args:
        current_user: Current authenticated user
        migration_manager: Database migration manager instance
        
    Returns:
        Current migration status
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        status = await migration_manager.get_migration_status()
        
        return BaseResponse(
            success=True,
            message="Migration status retrieved",
            data=status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get migration status: {str(e)}")


@router.post("/run", response_model=BaseResponse)
async def run_migrations(
    target_version: Optional[str] = Query(None, description="Target version to migrate to"),
    current_user: User = Depends(get_current_user),
    migration_manager: DatabaseMigrationManager = Depends(get_migration_manager)
):
    """
    Run pending database migrations.
    
    Args:
        target_version: Target version to migrate to (latest if None)
        current_user: Current authenticated user
        migration_manager: Database migration manager instance
        
    Returns:
        Migration execution results
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        results = await migration_manager.run_migrations(target_version=target_version)
        
        return BaseResponse(
            success=results["success"],
            message=results.get("message", "Migrations completed"),
            data=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run migrations: {str(e)}")


@router.post("/rollback", response_model=BaseResponse)
async def rollback_migrations(
    target_version: str = Query(..., description="Version to rollback to"),
    current_user: User = Depends(get_current_user),
    migration_manager: DatabaseMigrationManager = Depends(get_migration_manager)
):
    """
    Rollback database migrations to target version.
    
    Args:
        target_version: Version to rollback to
        current_user: Current authenticated user
        migration_manager: Database migration manager instance
        
    Returns:
        Rollback execution results
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        results = await migration_manager.rollback_migration(target_version)
        
        return BaseResponse(
            success=results["success"],
            message=results.get("message", "Rollback completed"),
            data=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rollback migrations: {str(e)}")


@router.post("/create", response_model=BaseResponse)
async def create_migration(
    request: CreateMigrationRequest,
    current_user: User = Depends(get_current_user),
    migration_manager: DatabaseMigrationManager = Depends(get_migration_manager)
):
    """
    Create a new database migration.
    
    Args:
        request: Migration creation request
        current_user: Current authenticated user
        migration_manager: Database migration manager instance
        
    Returns:
        Created migration information
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        version = await migration_manager.create_migration(
            name=request.name,
            description=request.description,
            up_sql=request.up_sql,
            down_sql=request.down_sql,
            dependencies=request.dependencies
        )
        
        return BaseResponse(
            success=True,
            message=f"Migration created successfully: {version}",
            data={
                "version": version,
                "name": request.name,
                "description": request.description
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create migration: {str(e)}")


@router.get("/validate", response_model=BaseResponse)
async def validate_migrations(
    current_user: User = Depends(get_current_user),
    migration_manager: DatabaseMigrationManager = Depends(get_migration_manager)
):
    """
    Validate all migrations for consistency and integrity.
    
    Args:
        current_user: Current authenticated user
        migration_manager: Database migration manager instance
        
    Returns:
        Migration validation results
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        validation_results = await migration_manager.validate_migrations()
        
        return BaseResponse(
            success=validation_results["valid"],
            message="Migration validation completed" if validation_results["valid"] else "Migration validation failed",
            data=validation_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate migrations: {str(e)}")


@router.get("/history", response_model=BaseResponse)
async def get_migration_history(
    current_user: User = Depends(get_current_user),
    migration_manager: DatabaseMigrationManager = Depends(get_migration_manager)
):
    """
    Get complete migration execution history.
    
    Args:
        current_user: Current authenticated user
        migration_manager: Database migration manager instance
        
    Returns:
        Migration execution history
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        history = await migration_manager.get_migration_history()
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(history)} migration records",
            data={
                "history": history,
                "total_count": len(history)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get migration history: {str(e)}")