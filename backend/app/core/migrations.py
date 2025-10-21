"""
Enhanced database migration utilities for the Career Copilot application.
Provides automatic migration management, connection pooling, and health monitoring.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text, inspect, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.pool import Pool
from sqlalchemy import event
import asyncpg

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)


class MigrationStatus(str, Enum):
    """Migration status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationInfo:
    """Information about a database migration."""
    revision: str
    description: str
    status: MigrationStatus
    applied_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class ConnectionPoolStats:
    """Connection pool statistics."""
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: int
    total_connections: int
    active_connections: int
    idle_connections: int
    pool_timeout: float
    max_overflow: int


class EnhancedDatabaseMigrator:
    """Enhanced database migration manager with connection pooling and monitoring."""
    
    def __init__(self):
        self.settings = get_settings()
        self.alembic_cfg = None
        self.engine: Optional[AsyncEngine] = None
        self.migration_history: List[MigrationInfo] = []
        self.connection_stats = {
            "total_connections": 0,
            "failed_connections": 0,
            "successful_connections": 0,
            "avg_connection_time": 0.0,
            "last_connection_check": None
        }
        self._setup_alembic_config()
        self._setup_engine()
    
    def _setup_alembic_config(self):
        """Setup Alembic configuration with enhanced settings."""
        # Get the backend directory path
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
        if hasattr(self.settings, 'database_url') and self.settings.database_url:
            self.alembic_cfg.set_main_option("sqlalchemy.url", self.settings.database_url)
        else:
            logger.warning("No database URL configured")
    
    def _setup_engine(self):
        """Setup database engine with optimized connection pooling."""
        if not hasattr(self.settings, 'database_url') or not self.settings.database_url:
            logger.warning("No database URL configured, skipping engine setup")
            return
        
        database_url = self.settings.database_url
        
        # Determine optimal pool settings based on database type and system resources
        try:
            import psutil
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            # Calculate optimal pool size based on system resources
            base_pool_size = max(5, min(20, cpu_count * 2))
            max_overflow = min(30, base_pool_size * 2)
            
            # Adjust for available memory
            if memory_gb < 4:
                base_pool_size = max(3, base_pool_size // 2)
                max_overflow = max(5, max_overflow // 2)
            
        except ImportError:
            # Fallback if psutil is not available
            base_pool_size = 10
            max_overflow = 20
        
        # Configure engine based on database type
        if database_url.startswith(("postgresql", "postgres")):
            # PostgreSQL-specific configuration
            self.engine = create_async_engine(
                database_url,
                pool_size=base_pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections every hour
                pool_timeout=30,
                pool_reset_on_return='commit',
                echo=getattr(self.settings, 'api_debug', False),
                connect_args={
                    "command_timeout": 60,
                    "server_settings": {
                        "application_name": "contract_analyzer_migrator",
                        "jit": "off",
                    }
                }
            )
        else:
            # SQLite or other database configuration
            self.engine = create_async_engine(
                database_url,
                echo=getattr(self.settings, 'api_debug', False),
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 60
                }
            )
        
        # Set up connection pool monitoring
        self._setup_pool_monitoring()
    
    def _setup_pool_monitoring(self):
        """Setup connection pool event monitoring."""
        if not self.engine:
            return
        
        @event.listens_for(Pool, "connect")
        def on_connect(dbapi_conn, connection_record):
            self.connection_stats["total_connections"] += 1
            self.connection_stats["successful_connections"] += 1
            connection_record.info['connect_time'] = time.time()
        
        @event.listens_for(Pool, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            if 'connect_time' in connection_record.info:
                connect_time = time.time() - connection_record.info['connect_time']
                # Update average connection time
                current_avg = self.connection_stats["avg_connection_time"]
                total_conns = self.connection_stats["successful_connections"]
                if total_conns > 0:
                    self.connection_stats["avg_connection_time"] = (
                        (current_avg * (total_conns - 1) + connect_time) / total_conns
                    )
    
    async def check_database_connection(self) -> Dict[str, Any]:
        """Check database connection with detailed diagnostics."""
        connection_info = {
            "connected": False,
            "database_type": "unknown",
            "database_version": None,
            "connection_time": None,
            "error": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if not hasattr(self.settings, 'database_url') or not self.settings.database_url:
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
                elif "sqlite" in self.settings.database_url:
                    connection_info["database_type"] = "sqlite"
                    result = await conn.execute(text("SELECT sqlite_version()"))
                    version_info = result.scalar()
                    connection_info["database_version"] = version_info
                
                connection_info["connected"] = True
                connection_info["connection_time"] = time.time() - start_time
                
                # Update connection stats
                self.connection_stats["last_connection_check"] = datetime.utcnow()
                
                logger.info(f"Database connection successful ({connection_info['connection_time']:.3f}s)")
                
        except Exception as e:
            connection_info["error"] = str(e)
            connection_info["connection_time"] = time.time() - start_time
            self.connection_stats["failed_connections"] += 1
            logger.error(f"Database connection failed: {e}")
        
        return connection_info
    
    async def create_database_if_not_exists(self) -> bool:
        """Create database if it doesn't exist (PostgreSQL only)."""
        if not hasattr(self.settings, 'database_url') or not self.settings.database_url:
            logger.error("No database URL configured")
            return False
        
        # Only applicable for PostgreSQL
        if not self.settings.database_url.startswith(("postgresql", "postgres")):
            logger.info("Database creation not needed for non-PostgreSQL databases")
            return True
        
        try:
            # Parse database URL to get database name
            from urllib.parse import urlparse
            parsed = urlparse(self.settings.database_url)
            db_name = parsed.path.lstrip('/')
            
            # Create connection to postgres database (not the target database)
            postgres_url = self.settings.database_url.replace(f"/{db_name}", "/postgres")
            engine = create_async_engine(postgres_url, isolation_level="AUTOCOMMIT")
            
            async with engine.connect() as conn:
                # Check if database exists
                result = await conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": db_name}
                )
                
                if not result.fetchone():
                    # Create database
                    await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                    logger.info(f"Created database: {db_name}")
                else:
                    logger.info(f"Database already exists: {db_name}")
            
            await engine.dispose()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False
    
    async def run_migrations(self, revision: str = "head") -> bool:
        """Run database migrations to specified revision with enhanced monitoring."""
        if not self.alembic_cfg:
            logger.error("Alembic configuration not initialized")
            return False
        
        migration_info = MigrationInfo(
            revision=revision,
            description=f"Migration to {revision}",
            status=MigrationStatus.PENDING
        )
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting migration to revision: {revision}")
            migration_info.status = MigrationStatus.RUNNING
            
            # Check current revision before migration
            current_revision = await self.get_current_revision()
            logger.info(f"Current database revision: {current_revision}")
            
            # Check if migration is needed
            pending_migrations = await self.get_pending_migrations()
            if not pending_migrations and current_revision is not None:
                logger.info("No pending migrations, database is up to date")
                migration_info.status = MigrationStatus.COMPLETED
                migration_info.applied_at = datetime.utcnow()
                migration_info.execution_time = time.time() - start_time
                self.migration_history.append(migration_info)
                return True
            
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
            migration_info.applied_at = datetime.utcnow()
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
    
    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """Create a new migration file with enhanced validation."""
        if not self.alembic_cfg:
            logger.error("Alembic configuration not initialized")
            return False
        
        try:
            logger.info(f"Creating migration: {message}")
            
            # Validate database connection before creating migration
            connection_info = asyncio.run(self.check_database_connection())
            if not connection_info["connected"]:
                logger.error("Cannot create migration: database connection failed")
                return False
            
            command.revision(
                self.alembic_cfg, 
                message=message, 
                autogenerate=autogenerate
            )
            logger.info("Migration file created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return False
    
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
    
    async def rollback_migration(self, revision: str) -> bool:
        """Rollback to a specific revision with enhanced monitoring."""
        if not self.alembic_cfg:
            logger.error("Alembic configuration not initialized")
            return False
        
        migration_info = MigrationInfo(
            revision=revision,
            description=f"Rollback to {revision}",
            status=MigrationStatus.PENDING
        )
        
        start_time = time.time()
        
        try:
            logger.info(f"Rolling back to revision: {revision}")
            migration_info.status = MigrationStatus.RUNNING
            
            # Get current revision before rollback
            current_revision = await self.get_current_revision()
            logger.info(f"Current database revision: {current_revision}")
            
            # Perform rollback
            command.downgrade(self.alembic_cfg, revision)
            
            # Verify rollback completed
            new_revision = await self.get_current_revision()
            
            migration_info.status = MigrationStatus.ROLLED_BACK
            migration_info.applied_at = datetime.utcnow()
            migration_info.execution_time = time.time() - start_time
            
            logger.info(f"Rollback completed successfully in {migration_info.execution_time:.2f}s")
            logger.info(f"Database revision rolled back: {current_revision} -> {new_revision}")
            
            self.migration_history.append(migration_info)
            return True
            
        except Exception as e:
            migration_info.status = MigrationStatus.FAILED
            migration_info.error_message = str(e)
            migration_info.execution_time = time.time() - start_time
            
            self.migration_history.append(migration_info)
            logger.error(f"Rollback failed after {migration_info.execution_time:.2f}s: {e}")
            return False
    
    async def initialize_database(self) -> bool:
        """Initialize database with schema and migrations with comprehensive checks."""
        logger.info("Starting comprehensive database initialization...")
        
        # Step 1: Check database connection
        logger.info("Step 1: Checking database connection...")
        connection_info = await self.check_database_connection()
        
        if not connection_info["connected"]:
            logger.info("Database connection failed, attempting to create database...")
            
            # Try to create database if it doesn't exist (PostgreSQL only)
            if not await self.create_database_if_not_exists():
                logger.error("Failed to create database")
                return False
            
            # Check connection again
            connection_info = await self.check_database_connection()
            if not connection_info["connected"]:
                logger.error("Failed to establish database connection after creation")
                return False
        
        logger.info(f"✅ Database connection successful ({connection_info['database_type']})")
        
        # Step 2: Check current migration status
        logger.info("Step 2: Checking migration status...")
        current_revision = await self.get_current_revision()
        pending_migrations = await self.get_pending_migrations()
        
        logger.info(f"Current revision: {current_revision or 'None (fresh database)'}")
        logger.info(f"Pending migrations: {len(pending_migrations)}")
        
        # Step 3: Run migrations if needed
        if pending_migrations or current_revision is None:
            logger.info("Step 3: Running database migrations...")
            if not await self.run_migrations():
                logger.error("Failed to run database migrations")
                return False
        else:
            logger.info("Step 3: Database is up to date, no migrations needed")
        
        # Step 4: Verify database health
        logger.info("Step 4: Verifying database health...")
        health_status = await self.get_database_health()
        
        if not health_status["healthy"]:
            logger.error("Database health check failed")
            return False
        
        logger.info("✅ Database initialization completed successfully")
        return True
    
    async def auto_migrate_on_startup(self) -> bool:
        """Automatically run migrations on application startup."""
        try:
            logger.info("🔄 Checking for pending migrations on startup...")
            
            # Check if database connection is available
            connection_info = await self.check_database_connection()
            if not connection_info["connected"]:
                logger.warning("Database not available for auto-migration")
                return False
            
            # Check for pending migrations
            pending_migrations = await self.get_pending_migrations()
            
            if not pending_migrations:
                logger.info("✅ No pending migrations, database is up to date")
                return True
            
            logger.info(f"🔄 Found {len(pending_migrations)} pending migrations, applying automatically...")
            
            # Run migrations
            success = await self.run_migrations()
            
            if success:
                logger.info("✅ Auto-migration completed successfully")
            else:
                logger.error("❌ Auto-migration failed")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Auto-migration error: {e}")
            return False


    
    async def get_connection_pool_stats(self) -> Optional[ConnectionPoolStats]:
        """Get detailed connection pool statistics."""
        if not self.engine or not hasattr(self.engine, 'pool'):
            return None
        
        pool = self.engine.pool
        pool_type = type(pool).__name__
        
        if pool_type == "StaticPool":
            # StaticPool (SQLite) - single connection
            return ConnectionPoolStats(
                pool_size=1,
                checked_in=0,
                checked_out=1 if self.connection_stats["successful_connections"] > 0 else 0,
                overflow=0,
                invalid=0,
                total_connections=self.connection_stats["total_connections"],
                active_connections=1 if self.connection_stats["successful_connections"] > 0 else 0,
                idle_connections=0,
                pool_timeout=30,
                max_overflow=0
            )
        elif hasattr(pool, 'size'):
            # QueuePool and other pool types
            return ConnectionPoolStats(
                pool_size=pool.size(),
                checked_in=pool.checkedin(),
                checked_out=pool.checkedout(),
                overflow=pool.overflow(),
                invalid=pool.invalid(),
                total_connections=self.connection_stats["total_connections"],
                active_connections=pool.checkedout(),
                idle_connections=pool.checkedin(),
                pool_timeout=getattr(pool, '_timeout', 30),
                max_overflow=getattr(pool, '_max_overflow', 0)
            )
        else:
            # Unknown pool type - return None
            return None
    
    async def get_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health check."""
        health_status = {
            "healthy": False,
            "timestamp": datetime.utcnow().isoformat(),
            "connection": {},
            "migrations": {},
            "pool": {},
            "performance": {}
        }
        
        try:
            # Check connection
            connection_info = await self.check_database_connection()
            health_status["connection"] = connection_info
            
            if connection_info["connected"]:
                # Check migration status
                current_revision = await self.get_current_revision()
                pending_migrations = await self.get_pending_migrations()
                
                health_status["migrations"] = {
                    "current_revision": current_revision,
                    "pending_count": len(pending_migrations),
                    "pending_migrations": pending_migrations,
                    "up_to_date": len(pending_migrations) == 0
                }
                
                # Check connection pool
                pool_stats = await self.get_connection_pool_stats()
                if pool_stats:
                    health_status["pool"] = {
                        "pool_size": pool_stats.pool_size,
                        "active_connections": pool_stats.active_connections,
                        "idle_connections": pool_stats.idle_connections,
                        "pool_utilization": (pool_stats.active_connections / pool_stats.pool_size) * 100 if pool_stats.pool_size > 0 else 0
                    }
                
                # Performance metrics
                health_status["performance"] = {
                    "avg_connection_time": self.connection_stats["avg_connection_time"],
                    "total_connections": self.connection_stats["total_connections"],
                    "failed_connections": self.connection_stats["failed_connections"],
                    "success_rate": (
                        (self.connection_stats["successful_connections"] / self.connection_stats["total_connections"]) * 100
                        if self.connection_stats["total_connections"] > 0 else 0
                    )
                }
                
                # Overall health determination
                health_status["healthy"] = (
                    connection_info["connected"] and
                    len(pending_migrations) == 0 and
                    self.connection_stats["failed_connections"] == 0
                )
            
        except Exception as e:
            health_status["error"] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        return health_status
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Perform database optimization tasks."""
        optimization_results = {
            "optimizations_performed": [],
            "recommendations": [],
            "performance_impact": {}
        }
        
        if not self.engine:
            optimization_results["error"] = "Database engine not initialized"
            return optimization_results
        
        try:
            async with self.engine.connect() as conn:
                # Analyze table statistics (PostgreSQL specific)
                if self.settings.database_url.startswith(("postgresql", "postgres")):
                    await conn.execute(text("ANALYZE"))
                    optimization_results["optimizations_performed"].append("Table statistics updated")
                
                # Check for missing indexes
                # This is a simplified check - in production, you'd want more sophisticated analysis
                optimization_results["recommendations"].append("Consider adding indexes for frequently queried columns")
                
        except Exception as e:
            optimization_results["error"] = str(e)
            logger.error(f"Database optimization failed: {e}")
        
        return optimization_results
    
    async def cleanup_connections(self):
        """Clean up database connections and dispose of engine."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections cleaned up")


# Global migrator instance
migrator = EnhancedDatabaseMigrator()


async def get_database_migrator() -> EnhancedDatabaseMigrator:
    """Get the global database migrator instance."""
    return migrator


async def initialize_database() -> bool:
    """Initialize database with proper schema."""
    return await migrator.initialize_database()


async def run_migrations(revision: str = "head") -> bool:
    """Run database migrations."""
    return await migrator.run_migrations(revision)


def create_migration(message: str, autogenerate: bool = True) -> bool:
    """Create a new migration file."""
    return migrator.create_migration(message, autogenerate)


async def check_database_health() -> Dict[str, Any]:
    """Check database health and migration status."""
    return await migrator.get_database_health()


async def get_connection_pool_stats() -> Optional[ConnectionPoolStats]:
    """Get connection pool statistics."""
    return await migrator.get_connection_pool_stats()


async def optimize_database() -> Dict[str, Any]:
    """Optimize database performance."""
    return await migrator.optimize_database()


async def auto_migrate_on_startup() -> bool:
    """Automatically run migrations on application startup."""
    try:
        logger.info("🔄 Checking for pending migrations on startup...")
        
        # Use the new migration manager
        from .migration_manager import get_migration_manager
        migration_mgr = await get_migration_manager()
        
        # Check if database connection is available
        connection_info = await migration_mgr.check_database_connection()
        if not connection_info["connected"]:
            logger.warning("Database not available for auto-migration")
            return False
        
        # Check for pending migrations
        pending_migrations = await migration_mgr.get_pending_migrations()
        
        if not pending_migrations:
            logger.info("✅ No pending migrations, database is up to date")
            return True
        
        logger.info(f"🔄 Found {len(pending_migrations)} pending migrations, applying automatically...")
        
        # Run migrations
        success = await migration_mgr.run_migrations()
        
        if success:
            logger.info("✅ Auto-migration completed successfully")
        else:
            logger.error("❌ Auto-migration failed")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Auto-migration error: {e}")
        return False


if __name__ == "__main__":
    """CLI interface for database operations."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations.py <command> [args]")
        print("Commands:")
        print("  init - Initialize database")
        print("  migrate [revision] - Run migrations")
        print("  create <message> - Create new migration")
        print("  rollback <revision> - Rollback to revision")
        print("  health - Check database health")
        sys.exit(1)
    
    command_name = sys.argv[1]
    
    if command_name == "init":
        success = asyncio.run(initialize_database())
        sys.exit(0 if success else 1)
    
    elif command_name == "migrate":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        success = run_migrations(revision)
        sys.exit(0 if success else 1)
    
    elif command_name == "create":
        if len(sys.argv) < 3:
            print("Error: Migration message required")
            sys.exit(1)
        message = sys.argv[2]
        success = create_migration(message)
        sys.exit(0 if success else 1)
    
    elif command_name == "rollback":
        if len(sys.argv) < 3:
            print("Error: Revision required")
            sys.exit(1)
        revision = sys.argv[2]
        success = migrator.rollback_migration(revision)
        sys.exit(0 if success else 1)
    
    elif command_name == "health":
        health = asyncio.run(check_database_health())
        import json
        print(json.dumps(health, indent=2))
        sys.exit(0)
    
    else:
        print(f"Unknown command: {command_name}")
        sys.exit(1)