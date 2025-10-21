"""
Database migration system for production-ready schema management.

This module provides comprehensive database migration functionality with
version control, rollback capabilities, and automated migration execution.
"""

import asyncio
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import text, MetaData, Table, Column, String, DateTime, Integer, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from .config_manager import get_config_manager
from .database import get_db_session
from .logging import get_logger

logger = get_logger(__name__)


class MigrationStatus(str, Enum):
    """Migration execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Database migration definition."""
    version: str
    name: str
    description: str
    up_sql: str
    down_sql: str
    checksum: str
    created_at: datetime
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class MigrationExecution:
    """Migration execution record."""
    version: str
    name: str
    status: MigrationStatus
    executed_at: datetime
    execution_time: float
    checksum: str
    error_message: Optional[str] = None


class DatabaseMigrationManager:
    """Production-ready database migration manager."""
    
    def __init__(self):
        self.config = get_config_manager()
        self.migrations_dir = Path(self.config.get("migrations.directory", "./migrations"))
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Migration configuration
        self.migration_table = self.config.get("migrations.table_name", "schema_migrations")
        self.auto_create_table = self.config.get("migrations.auto_create_table", True)
        self.validate_checksums = self.config.get("migrations.validate_checksums", True)
        
        # Migration cache
        self._migrations_cache: Dict[str, Migration] = {}
        self._cache_loaded = False
        
        logger.info("Database migration manager initialized")
    
    async def initialize(self):
        """Initialize migration system and create migration table if needed."""
        if self.auto_create_table:
            await self._create_migration_table()
        
        # Load migrations from directory
        await self._load_migrations()
        
        logger.info("Migration system initialized")
    
    async def _create_migration_table(self):
        """Create migration tracking table if it doesn't exist."""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.migration_table} (
            version VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            checksum VARCHAR(64) NOT NULL,
            executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            execution_time FLOAT NOT NULL DEFAULT 0,
            status VARCHAR(20) NOT NULL DEFAULT 'completed',
            error_message TEXT
        )
        """
        
        try:
            async with get_db_session() as session:
                await session.execute(text(create_table_sql))
                await session.commit()
            
            logger.info(f"Migration table '{self.migration_table}' created/verified")
            
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise
    
    async def _load_migrations(self):
        """Load migration files from directory."""
        self._migrations_cache.clear()
        
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return
        
        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        
        for migration_file in migration_files:
            try:
                migration = await self._parse_migration_file(migration_file)
                self._migrations_cache[migration.version] = migration
                
            except Exception as e:
                logger.error(f"Failed to parse migration file {migration_file}: {e}")
        
        self._cache_loaded = True
        logger.info(f"Loaded {len(self._migrations_cache)} migrations")
    
    async def _parse_migration_file(self, file_path: Path) -> Migration:
        """Parse a migration file and extract metadata."""
        content = file_path.read_text(encoding='utf-8')
        
        # Extract version from filename (e.g., 001_create_users_table.sql)
        version_match = re.match(r'^(\d+)_(.+)\.sql$', file_path.name)
        if not version_match:
            raise ValueError(f"Invalid migration filename format: {file_path.name}")
        
        version = version_match.group(1)
        name = version_match.group(2).replace('_', ' ').title()
        
        # Parse migration content
        sections = self._parse_migration_content(content)
        
        # Calculate checksum
        checksum = hashlib.sha256(content.encode()).hexdigest()
        
        return Migration(
            version=version,
            name=name,
            description=sections.get('description', ''),
            up_sql=sections.get('up', ''),
            down_sql=sections.get('down', ''),
            checksum=checksum,
            created_at=datetime.fromtimestamp(file_path.stat().st_mtime),
            dependencies=sections.get('dependencies', [])
        )
    
    def _parse_migration_content(self, content: str) -> Dict[str, Any]:
        """Parse migration file content and extract sections."""
        sections = {
            'description': '',
            'up': '',
            'down': '',
            'dependencies': []
        }
        
        current_section = None
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for section markers
            if line.startswith('-- Description:'):
                current_section = 'description'
                sections['description'] = line[15:].strip()
                continue
            elif line.startswith('-- Dependencies:'):
                current_section = 'dependencies'
                deps = line[16:].strip()
                if deps:
                    sections['dependencies'] = [d.strip() for d in deps.split(',')]
                continue
            elif line.startswith('-- Up:') or line == '-- Up':
                current_section = 'up'
                continue
            elif line.startswith('-- Down:') or line == '-- Down':
                current_section = 'down'
                continue
            elif line.startswith('--'):
                # Skip other comments
                continue
            
            # Add content to current section
            if current_section in ['up', 'down']:
                if sections[current_section]:
                    sections[current_section] += '\n'
                sections[current_section] += line
        
        return sections
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        if not self._cache_loaded:
            await self._load_migrations()
        
        # Get executed migrations
        executed_migrations = await self._get_executed_migrations()
        executed_versions = {m.version for m in executed_migrations}
        
        # Get available migrations
        available_versions = set(self._migrations_cache.keys())
        
        # Calculate status
        pending_migrations = available_versions - executed_versions
        
        # Get current version (highest executed version)
        current_version = "000"
        if executed_versions:
            current_version = max(executed_versions)
        
        # Check for missing migrations
        missing_migrations = executed_versions - available_versions
        
        return {
            "current_version": current_version,
            "available_migrations": len(available_versions),
            "executed_migrations": len(executed_versions),
            "pending_migrations": sorted(list(pending_migrations)),
            "missing_migrations": sorted(list(missing_migrations)),
            "is_up_to_date": len(pending_migrations) == 0,
            "has_missing_migrations": len(missing_migrations) > 0
        }
    
    async def _get_executed_migrations(self) -> List[MigrationExecution]:
        """Get list of executed migrations from database."""
        try:
            async with get_db_session() as session:
                query = text(f"""
                    SELECT version, name, status, executed_at, execution_time, checksum, error_message
                    FROM {self.migration_table}
                    ORDER BY version
                """)
                
                result = await session.execute(query)
                rows = result.fetchall()
                
                executions = []
                for row in rows:
                    executions.append(MigrationExecution(
                        version=row.version,
                        name=row.name,
                        status=MigrationStatus(row.status),
                        executed_at=row.executed_at,
                        execution_time=row.execution_time,
                        checksum=row.checksum,
                        error_message=row.error_message
                    ))
                
                return executions
                
        except Exception as e:
            logger.error(f"Failed to get executed migrations: {e}")
            return []
    
    async def run_migrations(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Run pending migrations up to target version.
        
        Args:
            target_version: Target version to migrate to (latest if None)
            
        Returns:
            Migration execution results
        """
        if not self._cache_loaded:
            await self._load_migrations()
        
        # Get current status
        status = await self.get_migration_status()
        
        if status["is_up_to_date"] and target_version is None:
            return {
                "success": True,
                "message": "Database is already up to date",
                "migrations_run": 0,
                "current_version": status["current_version"]
            }
        
        # Determine migrations to run
        pending_migrations = status["pending_migrations"]
        
        if target_version:
            # Filter to only migrations up to target version
            pending_migrations = [v for v in pending_migrations if v <= target_version]
        
        if not pending_migrations:
            return {
                "success": True,
                "message": "No migrations to run",
                "migrations_run": 0,
                "current_version": status["current_version"]
            }
        
        # Validate dependencies
        dependency_errors = await self._validate_dependencies(pending_migrations)
        if dependency_errors:
            return {
                "success": False,
                "message": "Dependency validation failed",
                "errors": dependency_errors,
                "migrations_run": 0
            }
        
        # Run migrations
        results = {
            "success": True,
            "migrations_run": 0,
            "executed_migrations": [],
            "failed_migrations": [],
            "current_version": status["current_version"]
        }
        
        for version in sorted(pending_migrations):
            migration = self._migrations_cache[version]
            
            try:
                logger.info(f"Running migration {version}: {migration.name}")
                
                execution_result = await self._execute_migration(migration)
                
                if execution_result["success"]:
                    results["migrations_run"] += 1
                    results["executed_migrations"].append({
                        "version": version,
                        "name": migration.name,
                        "execution_time": execution_result["execution_time"]
                    })
                    results["current_version"] = version
                else:
                    results["success"] = False
                    results["failed_migrations"].append({
                        "version": version,
                        "name": migration.name,
                        "error": execution_result["error"]
                    })
                    break  # Stop on first failure
                    
            except Exception as e:
                logger.error(f"Migration {version} failed: {e}")
                results["success"] = False
                results["failed_migrations"].append({
                    "version": version,
                    "name": migration.name,
                    "error": str(e)
                })
                break
        
        return results
    
    async def _validate_dependencies(self, migration_versions: List[str]) -> List[str]:
        """Validate migration dependencies."""
        errors = []
        executed_migrations = await self._get_executed_migrations()
        executed_versions = {m.version for m in executed_migrations}
        
        for version in migration_versions:
            migration = self._migrations_cache[version]
            
            for dependency in migration.dependencies:
                if dependency not in executed_versions and dependency not in migration_versions:
                    errors.append(f"Migration {version} depends on {dependency} which is not executed or pending")
        
        return errors
    
    async def _execute_migration(self, migration: Migration) -> Dict[str, Any]:
        """Execute a single migration."""
        start_time = datetime.now()
        
        try:
            async with get_db_session() as session:
                # Execute migration SQL
                if migration.up_sql.strip():
                    # Split SQL into individual statements
                    statements = self._split_sql_statements(migration.up_sql)
                    
                    for statement in statements:
                        if statement.strip():
                            await session.execute(text(statement))
                
                # Record migration execution
                execution_time = (datetime.now() - start_time).total_seconds()
                
                await self._record_migration_execution(
                    session,
                    migration,
                    MigrationStatus.COMPLETED,
                    execution_time
                )
                
                await session.commit()
                
                logger.info(f"Migration {migration.version} completed in {execution_time:.2f}s")
                
                return {
                    "success": True,
                    "execution_time": execution_time
                }
                
        except Exception as e:
            # Record failed migration
            execution_time = (datetime.now() - start_time).total_seconds()
            
            try:
                async with get_db_session() as session:
                    await self._record_migration_execution(
                        session,
                        migration,
                        MigrationStatus.FAILED,
                        execution_time,
                        str(e)
                    )
                    await session.commit()
            except:
                pass  # Don't fail if we can't record the failure
            
            logger.error(f"Migration {migration.version} failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
    
    def _split_sql_statements(self, sql: str) -> List[str]:
        """Split SQL into individual statements."""
        # Simple statement splitting - in production, use a proper SQL parser
        statements = []
        current_statement = ""
        
        for line in sql.split('\n'):
            line = line.strip()
            
            if not line or line.startswith('--'):
                continue
            
            current_statement += line + '\n'
            
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements
    
    async def _record_migration_execution(
        self,
        session: AsyncSession,
        migration: Migration,
        status: MigrationStatus,
        execution_time: float,
        error_message: Optional[str] = None
    ):
        """Record migration execution in database."""
        insert_sql = text(f"""
            INSERT INTO {self.migration_table} 
            (version, name, description, checksum, executed_at, execution_time, status, error_message)
            VALUES (:version, :name, :description, :checksum, :executed_at, :execution_time, :status, :error_message)
            ON CONFLICT (version) DO UPDATE SET
                status = :status,
                execution_time = :execution_time,
                error_message = :error_message,
                executed_at = :executed_at
        """)
        
        await session.execute(insert_sql, {
            "version": migration.version,
            "name": migration.name,
            "description": migration.description,
            "checksum": migration.checksum,
            "executed_at": datetime.now(),
            "execution_time": execution_time,
            "status": status.value,
            "error_message": error_message
        })
    
    async def rollback_migration(self, target_version: str) -> Dict[str, Any]:
        """
        Rollback migrations to target version.
        
        Args:
            target_version: Version to rollback to
            
        Returns:
            Rollback execution results
        """
        if not self._cache_loaded:
            await self._load_migrations()
        
        # Get executed migrations
        executed_migrations = await self._get_executed_migrations()
        executed_versions = [m.version for m in executed_migrations if m.status == MigrationStatus.COMPLETED]
        executed_versions.sort(reverse=True)  # Rollback in reverse order
        
        # Find migrations to rollback
        rollback_versions = []
        for version in executed_versions:
            if version > target_version:
                rollback_versions.append(version)
        
        if not rollback_versions:
            return {
                "success": True,
                "message": f"Already at or below version {target_version}",
                "migrations_rolled_back": 0
            }
        
        # Execute rollbacks
        results = {
            "success": True,
            "migrations_rolled_back": 0,
            "rolled_back_migrations": [],
            "failed_rollbacks": []
        }
        
        for version in rollback_versions:
            if version not in self._migrations_cache:
                results["failed_rollbacks"].append({
                    "version": version,
                    "error": "Migration file not found"
                })
                results["success"] = False
                break
            
            migration = self._migrations_cache[version]
            
            try:
                logger.info(f"Rolling back migration {version}: {migration.name}")
                
                rollback_result = await self._rollback_migration(migration)
                
                if rollback_result["success"]:
                    results["migrations_rolled_back"] += 1
                    results["rolled_back_migrations"].append({
                        "version": version,
                        "name": migration.name,
                        "execution_time": rollback_result["execution_time"]
                    })
                else:
                    results["success"] = False
                    results["failed_rollbacks"].append({
                        "version": version,
                        "name": migration.name,
                        "error": rollback_result["error"]
                    })
                    break
                    
            except Exception as e:
                logger.error(f"Rollback of migration {version} failed: {e}")
                results["success"] = False
                results["failed_rollbacks"].append({
                    "version": version,
                    "name": migration.name,
                    "error": str(e)
                })
                break
        
        return results
    
    async def _rollback_migration(self, migration: Migration) -> Dict[str, Any]:
        """Rollback a single migration."""
        start_time = datetime.now()
        
        try:
            async with get_db_session() as session:
                # Execute rollback SQL
                if migration.down_sql.strip():
                    statements = self._split_sql_statements(migration.down_sql)
                    
                    for statement in statements:
                        if statement.strip():
                            await session.execute(text(statement))
                
                # Update migration record
                execution_time = (datetime.now() - start_time).total_seconds()
                
                update_sql = text(f"""
                    UPDATE {self.migration_table}
                    SET status = :status, executed_at = :executed_at, execution_time = :execution_time
                    WHERE version = :version
                """)
                
                await session.execute(update_sql, {
                    "status": MigrationStatus.ROLLED_BACK.value,
                    "executed_at": datetime.now(),
                    "execution_time": execution_time,
                    "version": migration.version
                })
                
                await session.commit()
                
                logger.info(f"Migration {migration.version} rolled back in {execution_time:.2f}s")
                
                return {
                    "success": True,
                    "execution_time": execution_time
                }
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Rollback of migration {migration.version} failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
    
    async def create_migration(
        self,
        name: str,
        description: str = "",
        up_sql: str = "",
        down_sql: str = "",
        dependencies: List[str] = None
    ) -> str:
        """
        Create a new migration file.
        
        Args:
            name: Migration name
            description: Migration description
            up_sql: SQL for applying migration
            down_sql: SQL for rolling back migration
            dependencies: List of dependency versions
            
        Returns:
            Created migration version
        """
        # Generate version number
        existing_versions = list(self._migrations_cache.keys()) if self._cache_loaded else []
        if existing_versions:
            latest_version = max(existing_versions)
            next_version = f"{int(latest_version) + 1:03d}"
        else:
            next_version = "001"
        
        # Create filename
        filename = f"{next_version}_{name.lower().replace(' ', '_')}.sql"
        file_path = self.migrations_dir / filename
        
        # Create migration content
        content = f"""-- Description: {description}
"""
        
        if dependencies:
            content += f"-- Dependencies: {', '.join(dependencies)}\n"
        
        content += f"""
-- Up
{up_sql}

-- Down
{down_sql}
"""
        
        # Write migration file
        file_path.write_text(content, encoding='utf-8')
        
        # Reload migrations cache
        await self._load_migrations()
        
        logger.info(f"Created migration {next_version}: {name}")
        
        return next_version
    
    async def validate_migrations(self) -> Dict[str, Any]:
        """Validate all migrations for consistency and integrity."""
        if not self._cache_loaded:
            await self._load_migrations()
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checked_migrations": len(self._migrations_cache)
        }
        
        # Check for duplicate versions
        versions = list(self._migrations_cache.keys())
        if len(versions) != len(set(versions)):
            validation_results["valid"] = False
            validation_results["errors"].append("Duplicate migration versions found")
        
        # Check for gaps in version sequence
        if versions:
            sorted_versions = sorted([int(v) for v in versions])
            expected_versions = list(range(1, max(sorted_versions) + 1))
            missing_versions = set(expected_versions) - set(sorted_versions)
            
            if missing_versions:
                validation_results["warnings"].append(
                    f"Missing migration versions: {sorted(missing_versions)}"
                )
        
        # Validate each migration
        for version, migration in self._migrations_cache.items():
            # Check for empty up SQL
            if not migration.up_sql.strip():
                validation_results["warnings"].append(
                    f"Migration {version} has empty up SQL"
                )
            
            # Check for missing down SQL
            if not migration.down_sql.strip():
                validation_results["warnings"].append(
                    f"Migration {version} has empty down SQL (rollback not possible)"
                )
            
            # Validate dependencies
            for dep in migration.dependencies:
                if dep not in self._migrations_cache:
                    validation_results["valid"] = False
                    validation_results["errors"].append(
                        f"Migration {version} depends on non-existent migration {dep}"
                    )
        
        # Check executed migrations against files
        if self.validate_checksums:
            executed_migrations = await self._get_executed_migrations()
            
            for execution in executed_migrations:
                if execution.version in self._migrations_cache:
                    file_migration = self._migrations_cache[execution.version]
                    if execution.checksum != file_migration.checksum:
                        validation_results["valid"] = False
                        validation_results["errors"].append(
                            f"Migration {execution.version} checksum mismatch - file may have been modified"
                        )
        
        return validation_results
    
    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get complete migration execution history."""
        executed_migrations = await self._get_executed_migrations()
        
        history = []
        for execution in executed_migrations:
            history.append({
                "version": execution.version,
                "name": execution.name,
                "status": execution.status.value,
                "executed_at": execution.executed_at.isoformat(),
                "execution_time": execution.execution_time,
                "checksum": execution.checksum,
                "error_message": execution.error_message
            })
        
        return history


# Global migration manager instance
migration_manager = DatabaseMigrationManager()


async def get_migration_manager() -> DatabaseMigrationManager:
    """Get the global migration manager instance."""
    if not migration_manager._cache_loaded:
        await migration_manager.initialize()
    return migration_manager