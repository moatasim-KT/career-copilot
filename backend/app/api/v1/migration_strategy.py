"""
API endpoints for data migration strategies
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.sharding_migration_strategy_service import (
	ShardingMigrationStrategyService,
	MigrationStrategy,
	MigrationPlan,
)

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter()


# Pydantic models for API
class MigrationStrategyRequest(BaseModel):
	strategy: str = Field(..., description="Migration strategy type")
	config: Dict[str, Any] = Field(default_factory=dict, description="Strategy-specific configuration")


class ShardingConfigRequest(BaseModel):
	num_shards: int = Field(4, ge=2, le=16, description="Number of shards to create")
	shard_key: str = Field("user_id", description="Key to use for sharding")
	capacity_per_shard: int = Field(100000, ge=1000, description="Maximum records per shard")


class EncryptionConfigRequest(BaseModel):
	encryption_algorithm: str = Field("aes256", description="Encryption algorithm to use")
	batch_size: int = Field(100, ge=10, le=1000, description="Batch size for processing")
	include_files: bool = Field(True, description="Whether to encrypt file attachments")


class VersionMigrationConfigRequest(BaseModel):
	source_version: str = Field(..., description="Current schema version")
	target_version: str = Field(..., description="Target schema version")
	migration_scripts: List[str] = Field(..., description="List of migration script paths")


class CombinedMigrationRequest(BaseModel):
	strategies: List[str] = Field(..., description="List of migration strategies to execute")
	strategy_configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Configuration for each strategy")
	execution_order: Optional[List[str]] = Field(None, description="Custom execution order")
	rollback_on_failure: bool = Field(True, description="Whether to rollback on failure")


class MigrationPlanResponse(BaseModel):
	migration_id: str
	strategy: str
	estimated_duration_minutes: int
	phases: List[str]
	source_config: Dict[str, Any]
	target_config: Dict[str, Any]
	rollback_plan: Dict[str, Any]
	validation_criteria: Dict[str, Any]
	created_at: datetime


class MigrationStatusResponse(BaseModel):
	migration_id: str
	status: str
	current_phase: str
	progress_percentage: float
	records_processed: int
	records_total: int
	errors_count: int
	warnings_count: int
	started_at: datetime
	estimated_completion: Optional[datetime]
	last_updated: datetime


class SystemStatsRequest(BaseModel):
	total_records: int = Field(..., ge=0, description="Total number of records")
	data_size_gb: float = Field(..., ge=0, description="Total data size in GB")
	avg_query_time_ms: int = Field(..., ge=0, description="Average query time in milliseconds")
	concurrent_users: int = Field(..., ge=0, description="Number of concurrent users")
	has_sensitive_data: bool = Field(False, description="Whether system contains sensitive data")
	schema_version: str = Field("1.0.0", description="Current schema version")


@router.get("/strategies", response_model=List[Dict[str, Any]])
async def list_migration_strategies(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""List all available migration strategies"""

	service = ShardingMigrationStrategyService(db)
	strategies = service.list_available_strategies()

	return strategies


@router.post("/validate-prerequisites")
async def validate_migration_prerequisites(strategy: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Validate prerequisites for a migration strategy"""

	try:
		migration_strategy = MigrationStrategy(strategy)
	except ValueError:
		raise HTTPException(status_code=400, detail=f"Invalid migration strategy: {strategy}")

	service = ShardingMigrationStrategyService(db)
	validation_result = service.validate_migration_prerequisites(migration_strategy)

	return validation_result


@router.post("/plan/sharding", response_model=MigrationPlanResponse)
async def create_sharding_migration_plan(
	config: ShardingConfigRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Create a sharding migration plan"""

	service = ShardingMigrationStrategyService(db)

	try:
		plan = service.create_migration_plan(
			MigrationStrategy.SHARDING, num_shards=config.num_shards, shard_key=config.shard_key, capacity_per_shard=config.capacity_per_shard
		)

		return MigrationPlanResponse(
			migration_id=plan.migration_id,
			strategy=plan.strategy.value,
			estimated_duration_minutes=int(plan.estimated_duration.total_seconds() / 60),
			phases=[phase.value for phase in plan.phases],
			source_config=plan.source_config,
			target_config=plan.target_config,
			rollback_plan=plan.rollback_plan,
			validation_criteria=plan.validation_criteria,
			created_at=plan.created_at,
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to create sharding plan: {e!s}")


@router.post("/plan/encryption", response_model=MigrationPlanResponse)
async def create_encryption_migration_plan(
	config: EncryptionConfigRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Create an encryption migration plan"""

	service = ShardingMigrationStrategyService(db)

	try:
		plan = service.create_migration_plan(
			MigrationStrategy.ENCRYPTION,
			encryption_algorithm=config.encryption_algorithm,
			batch_size=config.batch_size,
			include_files=config.include_files,
		)

		return MigrationPlanResponse(
			migration_id=plan.migration_id,
			strategy=plan.strategy.value,
			estimated_duration_minutes=int(plan.estimated_duration.total_seconds() / 60),
			phases=[phase.value for phase in plan.phases],
			source_config=plan.source_config,
			target_config=plan.target_config,
			rollback_plan=plan.rollback_plan,
			validation_criteria=plan.validation_criteria,
			created_at=plan.created_at,
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to create encryption plan: {e!s}")


@router.post("/plan/version", response_model=MigrationPlanResponse)
async def create_version_migration_plan(
	config: VersionMigrationConfigRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Create a version migration plan"""

	service = ShardingMigrationStrategyService(db)

	try:
		plan = service.create_migration_plan(
			MigrationStrategy.VERSION,
			source_version=config.source_version,
			target_version=config.target_version,
			migration_scripts=config.migration_scripts,
		)

		return MigrationPlanResponse(
			migration_id=plan.migration_id,
			strategy=plan.strategy.value,
			estimated_duration_minutes=int(plan.estimated_duration.total_seconds() / 60),
			phases=[phase.value for phase in plan.phases],
			source_config=plan.source_config,
			target_config=plan.target_config,
			rollback_plan=plan.rollback_plan,
			validation_criteria=plan.validation_criteria,
			created_at=plan.created_at,
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to create version plan: {e!s}")


@router.post("/plan/combined", response_model=MigrationPlanResponse)
async def create_combined_migration_plan(
	config: CombinedMigrationRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Create a combined migration plan"""

	service = ShardingMigrationStrategyService(db)

	try:
		# Convert string strategies to enum
		strategies = []
		for strategy_str in config.strategies:
			try:
				strategies.append(MigrationStrategy(strategy_str))
			except ValueError:
				raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy_str}")

		# Convert strategy configs
		strategy_configs = {}
		for strategy_str, strategy_config in config.strategy_configs.items():
			try:
				strategy_enum = MigrationStrategy(strategy_str)
				strategy_configs[strategy_enum] = strategy_config
			except ValueError:
				raise HTTPException(status_code=400, detail=f"Invalid strategy in config: {strategy_str}")

		plan = service.create_combined_migration_plan(strategies, strategy_configs)

		return MigrationPlanResponse(
			migration_id=plan.migration_id,
			strategy=plan.strategy.value,
			estimated_duration_minutes=int(plan.estimated_duration.total_seconds() / 60),
			phases=[phase.value for phase in plan.phases],
			source_config=plan.source_config,
			target_config=plan.target_config,
			rollback_plan=plan.rollback_plan,
			validation_criteria=plan.validation_criteria,
			created_at=plan.created_at,
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to create combined plan: {e!s}")


@router.post("/execute/{migration_id}")
async def execute_migration(
	migration_id: str, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Execute a migration plan"""

	service = ShardingMigrationStrategyService(db)

	# Get the migration plan from cache or database
	# For now, we'll assume the plan is stored in cache
	from app.services.cache_service import cache_service

	plan_data = cache_service.get(f"migration_plan:{migration_id}")

	if not plan_data:
		raise HTTPException(status_code=404, detail="Migration plan not found")

	try:
		# Reconstruct the migration plan
		plan = MigrationPlan(**plan_data)

		# Execute migration in background
		def execute_migration_task():
			try:
				result = service.execute_migration(plan)
				# Store result in cache
				cache_service.set(f"migration_result:{migration_id}", result, ttl=86400)
				cache_service.set(f"migration_status:{migration_id}", result.get("progress", {}), ttl=86400)
			except Exception as e:
				error_result = {"status": "failed", "migration_id": migration_id, "error": str(e)}
				cache_service.set(f"migration_result:{migration_id}", error_result, ttl=86400)

		background_tasks.add_task(execute_migration_task)

		return {"message": "Migration started", "migration_id": migration_id, "status": "in_progress"}

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to start migration: {e!s}")


@router.get("/status/{migration_id}", response_model=Dict[str, Any])
async def get_migration_status(migration_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get the status of a migration"""

	service = ShardingMigrationStrategyService(db)
	status = service.get_migration_status(migration_id)

	if not status:
		raise HTTPException(status_code=404, detail="Migration status not found")

	return status


@router.get("/result/{migration_id}")
async def get_migration_result(migration_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get the result of a completed migration"""

	from app.services.cache_service import cache_service

	result = cache_service.get(f"migration_result:{migration_id}")

	if not result:
		raise HTTPException(status_code=404, detail="Migration result not found")

	return result


@router.post("/recommendations")
async def get_migration_recommendations(
	system_stats: SystemStatsRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Get migration strategy recommendations based on current system stats"""

	service = ShardingMigrationStrategyService(db)

	current_system_stats = {
		"total_records": system_stats.total_records,
		"data_size_gb": system_stats.data_size_gb,
		"avg_query_time_ms": system_stats.avg_query_time_ms,
		"concurrent_users": system_stats.concurrent_users,
		"has_sensitive_data": system_stats.has_sensitive_data,
		"schema_version": system_stats.schema_version,
	}

	recommendations = service.get_migration_recommendations(current_system_stats)

	return recommendations


@router.delete("/cancel/{migration_id}")
async def cancel_migration(migration_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Cancel an ongoing migration"""

	from app.services.cache_service import cache_service

	# Check if migration exists
	status = cache_service.get(f"migration_status:{migration_id}")
	if not status:
		raise HTTPException(status_code=404, detail="Migration not found")

	# Check if migration is still running
	if status.get("status") not in ["in_progress", "running"]:
		raise HTTPException(status_code=400, detail="Migration is not running")

	# Mark migration as cancelled
	# In a real implementation, this would signal the background task to stop
	cancelled_status = {**status, "status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}

	cache_service.set(f"migration_status:{migration_id}", cancelled_status, ttl=86400)

	return {"message": "Migration cancellation requested", "migration_id": migration_id, "status": "cancelled"}


@router.post("/rollback/{migration_id}")
async def rollback_migration(
	migration_id: str, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Rollback a completed migration"""

	from app.services.cache_service import cache_service

	# Get migration result
	result = cache_service.get(f"migration_result:{migration_id}")
	if not result:
		raise HTTPException(status_code=404, detail="Migration result not found")

	# Check if migration was successful (can only rollback successful migrations)
	if result.get("status") != "success":
		raise HTTPException(status_code=400, detail="Can only rollback successful migrations")

	# Get original plan
	plan_data = cache_service.get(f"migration_plan:{migration_id}")
	if not plan_data:
		raise HTTPException(status_code=404, detail="Migration plan not found")

	try:
		plan = MigrationPlan(**plan_data)
		service = ShardingMigrationStrategyService(db)

		# Execute rollback in background
		def execute_rollback_task():
			try:
				# Create a rollback progress tracker
				from app.services.sharding_migration_strategy_service import MigrationProgress, MigrationPhase

				rollback_progress = MigrationProgress(
					migration_id=f"rollback_{migration_id}",
					current_phase=MigrationPhase.ROLLBACK,
					progress_percentage=0.0,
					records_processed=0,
					records_total=0,
					errors_count=0,
					warnings_count=0,
					started_at=datetime.now(timezone.utc),
				)

				# Execute rollback based on strategy
				if plan.strategy == MigrationStrategy.SHARDING:
					rollback_result = service.sharding_strategy._rollback_sharding_migration(plan, rollback_progress)
				elif plan.strategy == MigrationStrategy.ENCRYPTION:
					rollback_result = service.encryption_strategy._rollback_encryption_migration(plan, rollback_progress)
				elif plan.strategy == MigrationStrategy.VERSION:
					rollback_result = service.version_strategy._rollback_version_migration(plan, rollback_progress)
				else:
					rollback_result = {"status": "failed", "error": "Unsupported strategy for rollback"}

				# Store rollback result
				cache_service.set(f"rollback_result:{migration_id}", rollback_result, ttl=86400)

			except Exception as e:
				error_result = {"status": "failed", "migration_id": migration_id, "error": str(e)}
				cache_service.set(f"rollback_result:{migration_id}", error_result, ttl=86400)

		background_tasks.add_task(execute_rollback_task)

		return {"message": "Rollback started", "migration_id": migration_id, "rollback_id": f"rollback_{migration_id}", "status": "in_progress"}

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to start rollback: {e!s}")


@router.get("/rollback-status/{migration_id}")
async def get_rollback_status(migration_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get the status of a migration rollback"""

	from app.services.cache_service import cache_service

	rollback_result = cache_service.get(f"rollback_result:{migration_id}")

	if not rollback_result:
		raise HTTPException(status_code=404, detail="Rollback status not found")

	return rollback_result
