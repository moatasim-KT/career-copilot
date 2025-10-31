"""
Migration management API endpoints.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from ...core.migration_manager import get_migration_manager, MigrationManager
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/migrations", tags=["migrations"])


class MigrationStatusResponse(BaseModel):
	"""Migration status response model."""

	timestamp: str
	database_connected: bool
	database_type: str
	current_revision: Optional[str]
	pending_migrations: List[str]
	health: str
	error: Optional[str] = None


class MigrationPlanResponse(BaseModel):
	"""Migration plan response model."""

	total_count: int
	estimated_time: float
	risks: List[str]
	migrations: List[Dict[str, Any]]
	rollback_plan: List[str]


class MigrationValidationResponse(BaseModel):
	"""Migration validation response model."""

	valid: bool
	issues: List[str]
	warnings: List[str]
	recommendations: List[str]


class MigrationHistoryResponse(BaseModel):
	"""Migration history response model."""

	migrations: List[Dict[str, Any]]
	rollback_history: List[Dict[str, Any]]


@router.get("/status", response_model=MigrationStatusResponse)
async def get_migration_status(migration_mgr: MigrationManager = Depends(get_migration_manager)) -> MigrationStatusResponse:
	"""Get current migration status."""
	try:
		status = await migration_mgr.get_migration_status()
		return MigrationStatusResponse(**status)
	except Exception as e:
		logger.error(f"Failed to get migration status: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get migration status: {e}")


@router.get("/plan", response_model=MigrationPlanResponse)
async def get_migration_plan(
	revision: str = Query(default="head", description="Target revision"), migration_mgr: MigrationManager = Depends(get_migration_manager)
) -> MigrationPlanResponse:
	"""Get migration execution plan."""
	try:
		plan = await migration_mgr.create_migration_plan(revision)

		# Convert migrations to dict format
		migrations_dict = []
		for migration in plan.migrations:
			migrations_dict.append(
				{
					"revision": migration.revision,
					"description": migration.description,
					"status": migration.status.value,
					"dependencies": migration.dependencies,
					"rollback_available": migration.rollback_available,
				}
			)

		return MigrationPlanResponse(
			total_count=plan.total_count,
			estimated_time=plan.estimated_time,
			risks=plan.risks,
			migrations=migrations_dict,
			rollback_plan=plan.rollback_plan,
		)
	except Exception as e:
		logger.error(f"Failed to create migration plan: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to create migration plan: {e}")


@router.get("/validate", response_model=MigrationValidationResponse)
async def validate_migrations(migration_mgr: MigrationManager = Depends(get_migration_manager)) -> MigrationValidationResponse:
	"""Validate migration integrity."""
	try:
		validation = await migration_mgr.validate_migration_integrity()
		return MigrationValidationResponse(**validation)
	except Exception as e:
		logger.error(f"Failed to validate migrations: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to validate migrations: {e}")


@router.get("/history", response_model=MigrationHistoryResponse)
async def get_migration_history(migration_mgr: MigrationManager = Depends(get_migration_manager)) -> MigrationHistoryResponse:
	"""Get migration history."""
	try:
		history = await migration_mgr.get_migration_history()

		# Convert migrations to dict format
		migrations_dict = []
		for migration in history:
			migrations_dict.append(
				{
					"revision": migration.revision,
					"description": migration.description,
					"status": migration.status.value,
					"applied_at": migration.applied_at.isoformat() if migration.applied_at else None,
					"execution_time": migration.execution_time,
					"error_message": migration.error_message,
					"dependencies": migration.dependencies,
					"rollback_available": migration.rollback_available,
				}
			)

		return MigrationHistoryResponse(migrations=migrations_dict, rollback_history=migration_mgr.rollback_history)
	except Exception as e:
		logger.error(f"Failed to get migration history: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get migration history: {e}")


@router.post("/migrate")
async def run_migrations(
	revision: str = Query(default="head", description="Target revision"),
	dry_run: bool = Query(default=False, description="Perform dry run"),
	migration_mgr: MigrationManager = Depends(get_migration_manager),
) -> Dict[str, Any]:
	"""Run database migrations."""
	try:
		logger.info(f"Running migrations to {revision} (dry_run={dry_run})")

		success = await migration_mgr.run_migrations(revision, dry_run)

		if success:
			message = f"Migrations {'planned' if dry_run else 'completed'} successfully"
			logger.info(message)
			return {"success": True, "message": message, "revision": revision, "dry_run": dry_run}
		else:
			message = f"Migration {'planning' if dry_run else 'execution'} failed"
			logger.error(message)
			raise HTTPException(status_code=500, detail=message)

	except Exception as e:
		logger.error(f"Failed to run migrations: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to run migrations: {e}")


@router.post("/rollback")
async def rollback_migrations(
	revision: str = Query(..., description="Target revision to rollback to"),
	confirm: bool = Query(default=False, description="Confirmation required for rollback"),
	migration_mgr: MigrationManager = Depends(get_migration_manager),
) -> Dict[str, Any]:
	"""Rollback database migrations."""
	try:
		if not confirm:
			raise HTTPException(status_code=400, detail="Rollback requires explicit confirmation (confirm=true)")

		logger.warning(f"Rolling back migrations to {revision}")

		success = await migration_mgr.rollback_migration(revision, confirm=True)

		if success:
			message = f"Rollback to {revision} completed successfully"
			logger.warning(message)
			return {"success": True, "message": message, "revision": revision}
		else:
			message = f"Rollback to {revision} failed"
			logger.error(message)
			raise HTTPException(status_code=500, detail=message)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to rollback migrations: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to rollback migrations: {e}")


@router.get("/health")
async def get_migration_health(migration_mgr: MigrationManager = Depends(get_migration_manager)) -> Dict[str, Any]:
	"""Get comprehensive migration health status."""
	try:
		# Get migration status
		status = await migration_mgr.get_migration_status()

		# Get validation results
		validation = await migration_mgr.validate_migration_integrity()

		# Determine overall health
		overall_health = "healthy"
		if not status["database_connected"]:
			overall_health = "database_unavailable"
		elif not validation["valid"]:
			overall_health = "validation_failed"
		elif status["pending_migrations"]:
			overall_health = "migrations_pending"
		elif validation["issues"]:
			overall_health = "issues_detected"

		return {"overall_health": overall_health, "status": status, "validation": validation, "timestamp": status["timestamp"]}

	except Exception as e:
		logger.error(f"Failed to get migration health: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get migration health: {e}")
