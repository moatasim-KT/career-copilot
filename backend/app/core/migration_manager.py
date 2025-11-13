"""
Enhanced migration management system with rollback capabilities and comprehensive monitoring.
"""

import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import StaticPool

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class MigrationStatus(str, Enum):
	"""Migration status enumeration."""

	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"
	ROLLED_BACK = "rolled_back"
	SKIPPED = "skipped"


@dataclass
class MigrationInfo:
	"""Information about a database migration."""

	revision: str
	description: str
	status: MigrationStatus
	applied_at: Optional[datetime] = None
	execution_time: Optional[float] = None
	error_message: Optional[str] = None
	rollback_available: bool = True
	dependencies: List[str] = None

	def __post_init__(self):
		if self.dependencies is None:
			self.dependencies = []


@dataclass
class MigrationPlan:
	"""Migration execution plan."""

	migrations: List[MigrationInfo]
	total_count: int
	estimated_time: float
	rollback_plan: List[str]
	risks: List[str]

	def __post_init__(self):
		if not self.risks:
			self.risks = []


class MigrationManager:
	"""Enhanced migration manager with rollback capabilities and monitoring."""

	def __init__(self):
		self.settings = get_settings()
		self.alembic_cfg = None
		self.engine: Optional[AsyncEngine] = None
		self.migration_history: List[MigrationInfo] = []
		self.rollback_history: List[Dict[str, Any]] = []
		self._setup_alembic_config()
		self._setup_engine()

	def _setup_alembic_config(self):
		"""Setup Alembic configuration with enhanced settings."""
		backend_dir = Path(__file__).parent.parent.parent
		alembic_ini_path = backend_dir / "alembic.ini"

		if not alembic_ini_path.exists():
			logger.warning(f"Alembic configuration not found at {alembic_ini_path}")
			self.alembic_cfg = None
			return

		self.alembic_cfg = Config(str(alembic_ini_path))

		# Set the script location to the correct migrations directory
		migrations_dir = backend_dir / "migrations"
		if migrations_dir.exists():
			self.alembic_cfg.set_main_option("script_location", str(migrations_dir))
		else:
			logger.warning(f"Migrations directory not found at {migrations_dir}")

		# Set the database URL in the config
		if hasattr(self.settings, "database_url") and self.settings.database_url:
			self.alembic_cfg.set_main_option("sqlalchemy.url", self.settings.database_url)
		else:
			logger.warning("No database URL configured")

	def _setup_engine(self):
		"""Setup database engine with optimized connection pooling."""
		if not hasattr(self.settings, "database_url") or not self.settings.database_url:
			logger.warning("No database URL configured, skipping engine setup")
			return

		database_url = self.settings.database_url

		# Configure engine based on database type
		if database_url.startswith(("postgresql", "postgres")):
			# PostgreSQL-specific configuration
			self.engine = create_async_engine(
				database_url,
				pool_size=10,
				max_overflow=20,
				pool_pre_ping=True,
				pool_recycle=3600,
				pool_timeout=30,
				echo=getattr(self.settings, "api_debug", False),
			)


	async def check_database_connection(self) -> Dict[str, Any]:
		"""Check database connection with detailed diagnostics."""
		connection_info = {
			"connected": False,
			"database_type": "unknown",
			"database_version": None,
			"connection_time": None,
			"error": None,
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

		if not hasattr(self.settings, "database_url") or not self.settings.database_url:
			connection_info["error"] = "No database URL configured"
			return connection_info

		start_time = time.time()

		try:
			if not self.engine:
				self._setup_engine()

			async with self.engine.connect() as conn:
				# Test basic connectivity
				await conn.execute(text("SELECT 1"))

				# Get database information
				if self.settings.database_url.startswith(("postgresql", "postgres")):
					connection_info["database_type"] = "postgresql"
					result = await conn.execute(text("SELECT version()"))
					version_info = result.scalar()
					connection_info["database_version"] = version_info


				connection_info["connected"] = True
				connection_info["connection_time"] = time.time() - start_time

				logger.info(f"Database connection successful ({connection_info['connection_time']:.3f}s)")

		except Exception as e:
			connection_info["error"] = str(e)
			connection_info["connection_time"] = time.time() - start_time
			logger.error(f"Database connection failed: {e}")

		return connection_info

	async def get_current_revision(self) -> Optional[str]:
		"""Get current database revision from the database."""
		if not self.engine:
			logger.error("Database engine not initialized")
			return None

		try:
			async with self.engine.connect() as conn:
				# Create migration context to get current revision
				def get_revision_sync(connection):
					migration_context = MigrationContext.configure(connection)
					return migration_context.get_current_revision()

				current_rev = await conn.run_sync(get_revision_sync)
				return current_rev
		except Exception as e:
			logger.error(f"Failed to get current revision: {e}")
			return None

	async def get_migration_history(self) -> List[MigrationInfo]:
		"""Get complete migration history from the database."""
		if not self.alembic_cfg:
			return []

		try:
			script = ScriptDirectory.from_config(self.alembic_cfg)
			current_rev = await self.get_current_revision()

			migration_history = []

			# Get all revisions in the script directory
			for revision in script.walk_revisions():
				migration_info = MigrationInfo(
					revision=revision.revision,
					description=revision.doc or "No description",
					status=MigrationStatus.COMPLETED if revision.revision == current_rev else MigrationStatus.PENDING,
					dependencies=list(revision.dependencies) if revision.dependencies else [],
				)
				migration_history.append(migration_info)

			return migration_history
		except Exception as e:
			logger.error(f"Failed to get migration history: {e}")
			return []

	async def get_pending_migrations(self) -> List[str]:
		"""Get list of pending migrations that need to be applied."""
		if not self.alembic_cfg:
			return []

		try:
			script = ScriptDirectory.from_config(self.alembic_cfg)
			current_rev = await self.get_current_revision()

			# Get all revisions from current to head
			pending_revisions = []
			for revision in script.walk_revisions("head", current_rev):
				if revision.revision != current_rev:
					pending_revisions.append(revision.revision)

			return pending_revisions
		except Exception as e:
			logger.error(f"Failed to get pending migrations: {e}")
			return []

	async def create_migration_plan(self, target_revision: str = "head") -> MigrationPlan:
		"""Create a detailed migration execution plan."""
		pending_migrations = await self.get_pending_migrations()
		migration_history = await self.get_migration_history()

		# Filter migrations that need to be applied
		migrations_to_apply = []
		for migration in migration_history:
			if migration.revision in pending_migrations:
				migrations_to_apply.append(migration)

		# Estimate execution time (rough estimate: 30 seconds per migration)
		estimated_time = len(migrations_to_apply) * 30.0

		# Create rollback plan (reverse order)
		rollback_plan = [m.revision for m in reversed(migrations_to_apply)]

		# Identify potential risks
		risks = []
		if len(migrations_to_apply) > 5:
			risks.append("Large number of migrations - consider backup before proceeding")

		# Check for data migrations (heuristic: look for 'data' in description)
		data_migrations = [m for m in migrations_to_apply if "data" in m.description.lower()]
		if data_migrations:
			risks.append("Data migrations detected - ensure data backup is available")

		return MigrationPlan(
			migrations=migrations_to_apply,
			total_count=len(migrations_to_apply),
			estimated_time=estimated_time,
			rollback_plan=rollback_plan,
			risks=risks,
		)

	async def run_migrations(self, revision: str = "head", dry_run: bool = False) -> bool:
		"""Run database migrations to specified revision with enhanced monitoring."""
		if not self.alembic_cfg:
			logger.error("Alembic configuration not initialized")
			return False

		# Create migration plan
		plan = await self.create_migration_plan(revision)

		if not plan.migrations:
			logger.info("No pending migrations to apply")
			return True

		logger.info(f"Migration plan: {plan.total_count} migrations, estimated time: {plan.estimated_time:.1f}s")

		if dry_run:
			logger.info("DRY RUN - Would apply the following migrations:")
			for migration in plan.migrations:
				logger.info(f"  - {migration.revision}: {migration.description}")
			return True

		# Display risks
		if plan.risks:
			logger.warning("Migration risks identified:")
			for risk in plan.risks:
				logger.warning(f"  - {risk}")

		migration_info = MigrationInfo(revision=revision, description=f"Migration to {revision}", status=MigrationStatus.PENDING)

		start_time = time.time()

		try:
			logger.info(f"Starting migration to revision: {revision}")
			migration_info.status = MigrationStatus.RUNNING

			# Check current revision before migration
			current_revision = await self.get_current_revision()
			logger.info(f"Current database revision: {current_revision}")

			# Ensure database connection is available before migration
			connection_info = await self.check_database_connection()
			if not connection_info["connected"]:
				logger.error("Cannot run migrations: database connection failed")
				migration_info.status = MigrationStatus.FAILED
				migration_info.error_message = "Database connection failed"
				self.migration_history.append(migration_info)
				return False

			# Run the migration in a loop to handle async context
			def run_sync_migration():
				command.upgrade(self.alembic_cfg, revision)

			# Execute migration synchronously
			await asyncio.get_event_loop().run_in_executor(None, run_sync_migration)

			# Verify migration completed
			new_revision = await self.get_current_revision()

			migration_info.status = MigrationStatus.COMPLETED
			migration_info.applied_at = datetime.now(timezone.utc)
			migration_info.execution_time = time.time() - start_time

			logger.info(f"Migration completed successfully in {migration_info.execution_time:.2f}s")
			logger.info(f"Database revision updated: {current_revision} -> {new_revision}")

			self.migration_history.append(migration_info)
			return True

		except Exception as e:
			migration_info.status = MigrationStatus.FAILED
			migration_info.error_message = str(e)
			migration_info.execution_time = time.time() - start_time

			self.migration_history.append(migration_info)
			logger.error(f"Migration failed after {migration_info.execution_time:.2f}s: {e}")
			return False

	async def rollback_migration(self, revision: str, confirm: bool = False) -> bool:
		"""Rollback to a specific revision with enhanced safety checks."""
		if not self.alembic_cfg:
			logger.error("Alembic configuration not initialized")
			return False

		if not confirm:
			logger.error("Rollback requires explicit confirmation (confirm=True)")
			return False

		# Get current revision
		current_revision = await self.get_current_revision()
		if not current_revision:
			logger.error("Cannot determine current revision for rollback")
			return False

		# Validate rollback target
		if revision == current_revision:
			logger.info("Already at target revision, no rollback needed")
			return True

		rollback_info = {"from_revision": current_revision, "to_revision": revision, "timestamp": datetime.now(timezone.utc), "status": "pending"}

		start_time = time.time()

		try:
			logger.warning(f"ROLLBACK: Rolling back from {current_revision} to {revision}")
			rollback_info["status"] = "running"

			# Perform rollback
			def run_sync_rollback():
				command.downgrade(self.alembic_cfg, revision)

			await asyncio.get_event_loop().run_in_executor(None, run_sync_rollback)

			# Verify rollback completed
			new_revision = await self.get_current_revision()

			rollback_info["status"] = "completed"
			rollback_info["execution_time"] = time.time() - start_time
			rollback_info["actual_revision"] = new_revision

			logger.warning(f"ROLLBACK completed in {rollback_info['execution_time']:.2f}s")
			logger.warning(f"Database revision rolled back: {current_revision} -> {new_revision}")

			self.rollback_history.append(rollback_info)
			return True

		except Exception as e:
			rollback_info["status"] = "failed"
			rollback_info["error"] = str(e)
			rollback_info["execution_time"] = time.time() - start_time

			self.rollback_history.append(rollback_info)
			logger.error(f"ROLLBACK failed after {rollback_info['execution_time']:.2f}s: {e}")
			return False

	def create_migration(self, message: str, autogenerate: bool = True) -> bool:
		"""Create a new migration file with enhanced validation."""
		if not self.alembic_cfg:
			logger.error("Alembic configuration not initialized")
			return False

		try:
			logger.info(f"Creating migration: {message}")

			command.revision(self.alembic_cfg, message=message, autogenerate=autogenerate)
			logger.info("Migration file created successfully")
			return True
		except Exception as e:
			logger.error(f"Failed to create migration: {e}")
			return False

	async def get_migration_status(self) -> Dict[str, Any]:
		"""Get comprehensive migration status information."""
		status = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"database_connected": False,
			"current_revision": None,
			"pending_migrations": [],
			"migration_history": [],
			"rollback_history": self.rollback_history,
			"health": "unknown",
		}

		try:
			# Check database connection
			connection_info = await self.check_database_connection()
			status["database_connected"] = connection_info["connected"]
			status["database_type"] = connection_info.get("database_type", "unknown")

			if connection_info["connected"]:
				# Get current revision
				current_revision = await self.get_current_revision()
				status["current_revision"] = current_revision

				# Get pending migrations
				pending_migrations = await self.get_pending_migrations()
				status["pending_migrations"] = pending_migrations

				# Get migration history
				migration_history = await self.get_migration_history()
				status["migration_history"] = [
					{
						"revision": m.revision,
						"description": m.description,
						"status": m.status.value,
						"applied_at": m.applied_at.isoformat() if m.applied_at else None,
					}
					for m in migration_history
				]

				# Determine overall health
				if not pending_migrations:
					status["health"] = "up_to_date"
				elif len(pending_migrations) <= 3:
					status["health"] = "needs_migration"
				else:
					status["health"] = "major_migration_needed"
			else:
				status["health"] = "database_unavailable"
				status["error"] = connection_info.get("error", "Unknown connection error")

		except Exception as e:
			status["health"] = "error"
			status["error"] = str(e)
			logger.error(f"Failed to get migration status: {e}")

		return status

	async def validate_migration_integrity(self) -> Dict[str, Any]:
		"""Validate migration integrity and detect issues."""
		validation_result = {"valid": True, "issues": [], "warnings": [], "recommendations": []}

		try:
			if not self.alembic_cfg:
				validation_result["valid"] = False
				validation_result["issues"].append("Alembic configuration not found")
				return validation_result

			# Check script directory
			script = ScriptDirectory.from_config(self.alembic_cfg)

			# Check for multiple heads
			heads = script.get_heads()
			if len(heads) > 1:
				validation_result["issues"].append(f"Multiple migration heads detected: {heads}")
				validation_result["recommendations"].append("Merge migration branches using 'alembic merge'")

			# Check for missing dependencies
			for revision in script.walk_revisions():
				if revision.dependencies:
					for dep in revision.dependencies:
						if not script.get_revision(dep):
							validation_result["issues"].append(f"Missing dependency {dep} for revision {revision.revision}")

			# Check database connection
			connection_info = await self.check_database_connection()
			if not connection_info["connected"]:
				validation_result["warnings"].append("Database connection not available for validation")

		except Exception as e:
			validation_result["valid"] = False
			validation_result["issues"].append(f"Validation error: {e}")

		return validation_result

	async def get_connection_pool_stats(self) -> Optional[Dict[str, Any]]:
		"""Get connection pool statistics."""
		if not self.engine or not hasattr(self.engine, "pool"):
			return None

		pool = self.engine.pool
		pool_type = type(pool).__name__

		try:

				# QueuePool and other pool types
				return {
					"pool_size": pool.size(),
					"active_connections": pool.checkedout(),
					"idle_connections": pool.checkedin(),
					"pool_type": pool_type,
				}
			else:
				return {"pool_type": pool_type, "pool_size": "unknown"}
		except Exception as e:
			return {"pool_type": pool_type, "error": str(e)}

	async def cleanup_connections(self):
		"""Clean up database connections and dispose of engine."""
		if self.engine:
			await self.engine.dispose()
			logger.info("Migration manager database connections cleaned up")


# Global migration manager instance
migration_manager = MigrationManager()


async def get_migration_manager() -> MigrationManager:
	"""Get the global migration manager instance."""
	return migration_manager


async def run_migrations(revision: str = "head", dry_run: bool = False) -> bool:
	"""Run database migrations."""
	return await migration_manager.run_migrations(revision, dry_run)


async def rollback_migration(revision: str, confirm: bool = False) -> bool:
	"""Rollback to a specific revision."""
	return await migration_manager.rollback_migration(revision, confirm)


def create_migration(message: str, autogenerate: bool = True) -> bool:
	"""Create a new migration file."""
	return migration_manager.create_migration(message, autogenerate)


async def get_migration_status() -> Dict[str, Any]:
	"""Get migration status information."""
	return await migration_manager.get_migration_status()


async def validate_migration_integrity() -> Dict[str, Any]:
	"""Validate migration integrity."""
	return await migration_manager.validate_migration_integrity()
