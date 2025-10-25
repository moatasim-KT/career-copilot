"""
Consolidated database optimization service.

This module provides comprehensive database optimization functionality including:
- Performance monitoring and optimization
- Backup and recovery management
- Migration system
- Connection pool optimization
- Query analysis and recommendations
"""

import asyncio
import gzip
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, AsyncGenerator

import asyncpg
from sqlalchemy import text, event, MetaData, Table, Column, String, DateTime, Integer, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ============================================================================
# BACKUP SYSTEM
# ============================================================================

class BackupType(str, Enum):
    """Types of database backups."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"


class BackupStatus(str, Enum):
    """Backup operation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CompressionType(str, Enum):
    """Compression types for backups."""
    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    XZ = "xz"


@dataclass
class BackupMetadata:
    """Metadata for a database backup."""
    backup_id: str
    backup_type: BackupType
    database_name: str
    backup_path: Path
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_size: int = 0
    compressed_size: int = 0
    compression_type: CompressionType = CompressionType.GZIP
    checksum: Optional[str] = None
    status: BackupStatus = BackupStatus.PENDING
    error_message: Optional[str] = None
    retention_days: int = 30
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "database_name": self.database_name,
            "backup_path": str(self.backup_path),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "file_size": self.file_size,
            "compressed_size": self.compressed_size,
            "compression_type": self.compression_type.value,
            "checksum": self.checksum,
            "status": self.status.value,
            "error_message": self.error_message,
            "retention_days": self.retention_days,
            "tags": self.tags
        }


@dataclass
class RestoreOptions:
    """Options for database restore operations."""
    target_database: Optional[str] = None
    restore_schema: bool = True
    restore_data: bool = True
    drop_existing: bool = False
    parallel_jobs: int = 1
    verify_restore: bool = True
    restore_point: Optional[datetime] = None

# ==
==========================================================================
# MIGRATION SYSTEM
# ============================================================================

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


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

@dataclass
class QueryPerformanceMetric:
    """Query performance metric data."""
    query_hash: str
    query_text: str
    execution_time: float
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    parameters: Optional[Dict] = None
    row_count: Optional[int] = None
    connection_id: Optional[str] = None


@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics."""
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: int
    total_connections: int
    active_connections: int
    idle_connections: int
    avg_connection_time: float
    max_connection_time: float
    connection_errors: int


@dataclass
class SlowQueryAnalysis:
    """Slow query analysis result."""
    query_pattern: str
    avg_execution_time: float
    max_execution_time: float
    min_execution_time: float
    execution_count: int
    total_time: float
    suggestions: List[str] = field(default_factory=list)
    affected_tables: List[str] = field(default_factory=list)
# ==
==========================================================================
# MAIN OPTIMIZATION SERVICE
# ============================================================================

class DatabaseOptimizationService:
    """
    Comprehensive database optimization service.
    
    Provides backup management, migration system, performance monitoring,
    and optimization recommendations.
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Backup configuration
        self.backup_dir = Path(getattr(self.settings, 'backup_directory', './backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = getattr(self.settings, 'backup_retention_days', 30)
        self.compression_enabled = getattr(self.settings, 'backup_compression_enabled', True)
        self.compression_type = CompressionType(getattr(self.settings, 'backup_compression_type', 'gzip'))
        
        # Migration configuration
        self.migrations_dir = Path(getattr(self.settings, 'migrations_directory', './migrations'))
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self.migration_table = getattr(self.settings, 'migration_table_name', 'schema_migrations')
        
        # Performance monitoring
        self.query_metrics: List[QueryPerformanceMetric] = []
        self.slow_query_threshold = 1.0  # seconds
        self.max_metrics_history = 10000
        self.query_patterns = defaultdict(list)
        
        # Metadata storage
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.backup_metadata: Dict[str, BackupMetadata] = {}
        self.migrations_cache: Dict[str, Migration] = {}
        
        # Database info
        self.database_url = getattr(self.settings, 'database_url', '')
        self.database_type = self._detect_database_type()
        
        # Load existing metadata
        self._load_backup_metadata()
        
        logger.info(f"Database optimization service initialized for {self.database_type}")
    
    def _detect_database_type(self) -> str:
        """Detect database type from connection URL."""
        if not self.database_url:
            return "unknown"
        
        if "postgresql" in self.database_url or "postgres" in self.database_url:
            return "postgresql"
        elif "sqlite" in self.database_url:
            return "sqlite"
        elif "mysql" in self.database_url:
            return "mysql"
        else:
            return "unknown"    # =
=======================================================================
    # PERFORMANCE OPTIMIZATION
    # ========================================================================
    
    def optimize_performance(self) -> Dict[str, Any]:
        """
        Perform comprehensive database performance optimization.
        
        Returns:
            Optimization results and recommendations
        """
        optimization_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "database_type": self.database_type,
            "optimizations_applied": [],
            "recommendations": [],
            "performance_metrics": {}
        }
        
        try:
            # Analyze query performance
            query_analysis = self._analyze_query_performance()
            optimization_results["performance_metrics"]["query_analysis"] = query_analysis
            
            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(query_analysis)
            optimization_results["recommendations"] = recommendations
            
            # Apply automatic optimizations based on database type
            if self.database_type == "postgresql":
                pg_optimizations = self._optimize_postgresql()
                optimization_results["optimizations_applied"].extend(pg_optimizations)
            elif self.database_type == "sqlite":
                sqlite_optimizations = self._optimize_sqlite()
                optimization_results["optimizations_applied"].extend(sqlite_optimizations)
            
            # Connection pool optimization
            pool_optimization = self._optimize_connection_pool()
            optimization_results["optimizations_applied"].append(pool_optimization)
            
            logger.info("Database performance optimization completed")
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            optimization_results["error"] = str(e)
        
        return optimization_results
    
    def _analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze query performance metrics."""
        if not self.query_metrics:
            return {"status": "no_data", "message": "No query metrics available"}
        
        # Calculate basic statistics
        execution_times = [m.execution_time for m in self.query_metrics if m.success]
        
        if not execution_times:
            return {"status": "no_successful_queries"}
        
        analysis = {
            "total_queries": len(self.query_metrics),
            "successful_queries": len(execution_times),
            "failed_queries": len(self.query_metrics) - len(execution_times),
            "avg_execution_time": statistics.mean(execution_times),
            "median_execution_time": statistics.median(execution_times),
            "max_execution_time": max(execution_times),
            "min_execution_time": min(execution_times),
            "slow_queries": len([t for t in execution_times if t > self.slow_query_threshold]),
            "slow_query_patterns": []
        }
        
        # Analyze slow query patterns
        for pattern_hash, metrics in self.query_patterns.items():
            pattern_times = [m.execution_time for m in metrics if m.success]
            if pattern_times and statistics.mean(pattern_times) > self.slow_query_threshold:
                analysis["slow_query_patterns"].append({
                    "pattern": metrics[0].query_text[:100] + "...",
                    "avg_time": statistics.mean(pattern_times),
                    "count": len(pattern_times)
                })
        
        return analysis 
   def _generate_optimization_recommendations(self, query_analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        if query_analysis.get("slow_queries", 0) > 0:
            recommendations.append("Consider adding indexes for slow queries")
            recommendations.append("Review query execution plans for optimization opportunities")
        
        if query_analysis.get("avg_execution_time", 0) > 0.5:
            recommendations.append("Average query time is high - consider query optimization")
        
        if query_analysis.get("failed_queries", 0) > query_analysis.get("total_queries", 1) * 0.05:
            recommendations.append("High query failure rate detected - review error logs")
        
        # Database-specific recommendations
        if self.database_type == "postgresql":
            recommendations.extend([
                "Consider running ANALYZE to update table statistics",
                "Review pg_stat_statements for query optimization",
                "Consider connection pooling with pgbouncer"
            ])
        elif self.database_type == "sqlite":
            recommendations.extend([
                "Consider enabling WAL mode for better concurrency",
                "Review PRAGMA settings for optimization",
                "Consider VACUUM for database maintenance"
            ])
        
        return recommendations
    
    def _optimize_postgresql(self) -> List[str]:
        """Apply PostgreSQL-specific optimizations."""
        optimizations = []
        
        try:
            from .database import get_database_manager
            db_manager = get_database_manager()
            
            with db_manager.get_session() as session:
                # Update table statistics
                session.execute(text("ANALYZE"))
                optimizations.append("Updated table statistics with ANALYZE")
                
                # Check for unused indexes
                unused_indexes_query = text("""
                    SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE idx_tup_read = 0 AND idx_tup_fetch = 0
                """)
                
                result = session.execute(unused_indexes_query)
                unused_indexes = result.fetchall()
                
                if unused_indexes:
                    optimizations.append(f"Found {len(unused_indexes)} potentially unused indexes")
                
        except Exception as e:
            logger.error(f"PostgreSQL optimization failed: {e}")
            optimizations.append(f"PostgreSQL optimization failed: {e}")
        
        return optimizations
    
    def _optimize_sqlite(self) -> List[str]:
        """Apply SQLite-specific optimizations."""
        optimizations = []
        
        try:
            from .database import get_database_manager
            db_manager = get_database_manager()
            
            with db_manager.get_session() as session:
                # Run PRAGMA optimize
                session.execute(text("PRAGMA optimize"))
                optimizations.append("Ran PRAGMA optimize")
                
                # Check WAL checkpoint
                session.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
                optimizations.append("Performed WAL checkpoint")
                
                # Get database size info
                result = session.execute(text("PRAGMA page_count"))
                page_count = result.scalar()
                
                result = session.execute(text("PRAGMA page_size"))
                page_size = result.scalar()
                
                if page_count and page_size:
                    db_size_mb = (page_count * page_size) / (1024 * 1024)
                    optimizations.append(f"Database size: {db_size_mb:.2f} MB")
                
        except Exception as e:
            logger.error(f"SQLite optimization failed: {e}")
            optimizations.append(f"SQLite optimization failed: {e}")
        
        return optimizations
    
    def _optimize_connection_pool(self) -> str:
        """Optimize connection pool settings."""
        try:
            # Get system resources
            try:
                import psutil
                cpu_count = psutil.cpu_count()
                memory_gb = psutil.virtual_memory().total / (1024**3)
                
                # Calculate optimal pool size
                optimal_pool_size = max(5, min(20, cpu_count * 2))
                
                return f"Recommended pool size: {optimal_pool_size} (CPU cores: {cpu_count}, Memory: {memory_gb:.1f}GB)"
                
            except ImportError:
                return "Install psutil for automatic pool size optimization"
                
        except Exception as e:
            return f"Connection pool optimization failed: {e}"    # =====
===================================================================
    # BACKUP MANAGEMENT
    # ========================================================================
    
    def _load_backup_metadata(self):
        """Load backup metadata from file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    
                for backup_id, metadata_dict in data.items():
                    metadata = BackupMetadata(
                        backup_id=metadata_dict["backup_id"],
                        backup_type=BackupType(metadata_dict["backup_type"]),
                        database_name=metadata_dict["database_name"],
                        backup_path=Path(metadata_dict["backup_path"]),
                        created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                        completed_at=datetime.fromisoformat(metadata_dict["completed_at"]) if metadata_dict.get("completed_at") else None,
                        file_size=metadata_dict.get("file_size", 0),
                        compressed_size=metadata_dict.get("compressed_size", 0),
                        compression_type=CompressionType(metadata_dict.get("compression_type", "gzip")),
                        checksum=metadata_dict.get("checksum"),
                        status=BackupStatus(metadata_dict.get("status", "pending")),
                        error_message=metadata_dict.get("error_message"),
                        retention_days=metadata_dict.get("retention_days", 30),
                        tags=metadata_dict.get("tags", {})
                    )
                    self.backup_metadata[backup_id] = metadata
                    
        except Exception as e:
            logger.error(f"Failed to load backup metadata: {e}")
    
    def _save_backup_metadata(self):
        """Save backup metadata to file."""
        try:
            data = {backup_id: metadata.to_dict() 
                   for backup_id, metadata in self.backup_metadata.items()}
            
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    async def create_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        database_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> BackupMetadata:
        """
        Create a database backup.
        
        Args:
            backup_type: Type of backup to create
            database_name: Name of database to backup
            tags: Additional tags for the backup
            
        Returns:
            Backup metadata
        """
        backup_id = self._generate_backup_id()
        
        if not database_name:
            database_name = self._extract_database_name()
        
        # Create backup metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            database_name=database_name,
            backup_path=self.backup_dir / f"{backup_id}.sql",
            created_at=datetime.utcnow(),
            compression_type=self.compression_type if self.compression_enabled else CompressionType.NONE,
            retention_days=self.retention_days,
            tags=tags or {}
        )
        
        self.backup_metadata[backup_id] = metadata
        self._save_backup_metadata()
        
        try:
            logger.info(f"Starting {backup_type.value} backup: {backup_id}")
            metadata.status = BackupStatus.RUNNING
            self._save_backup_metadata()
            
            # Perform backup based on database type
            if self.database_type == "postgresql":
                await self._backup_postgresql(metadata)
            elif self.database_type == "sqlite":
                await self._backup_sqlite(metadata)
            else:
                raise ValueError(f"Unsupported database type: {self.database_type}")
            
            # Compress backup if enabled
            if self.compression_enabled:
                compressed_path = self._compress_file(metadata.backup_path, self.compression_type)
                metadata.backup_path = compressed_path
                metadata.compressed_size = compressed_path.stat().st_size
            
            # Calculate checksum
            metadata.checksum = self._calculate_checksum(metadata.backup_path)
            metadata.file_size = metadata.backup_path.stat().st_size
            metadata.completed_at = datetime.utcnow()
            metadata.status = BackupStatus.COMPLETED
            
            logger.info(f"Backup completed successfully: {backup_id}")
            
        except Exception as e:
            logger.error(f"Backup failed: {backup_id} - {e}")
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
        
        finally:
            self._save_backup_metadata()
        
        return metadata  
  def _generate_backup_id(self) -> str:
        """Generate unique backup ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}_{int(time.time())}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _compress_file(self, source_path: Path, compression_type: CompressionType) -> Path:
        """Compress backup file."""
        if compression_type == CompressionType.NONE:
            return source_path
        
        if compression_type == CompressionType.GZIP:
            compressed_path = source_path.with_suffix(source_path.suffix + ".gz")
            
            with open(source_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            source_path.unlink()
            return compressed_path
        
        logger.warning(f"Compression type {compression_type} not implemented")
        return source_path
    
    async def _backup_postgresql(self, metadata: BackupMetadata):
        """Create PostgreSQL backup using pg_dump."""
        conn_params = self._parse_postgresql_url()
        
        cmd = [
            "pg_dump",
            "--host", conn_params["host"],
            "--port", str(conn_params["port"]),
            "--username", conn_params["username"],
            "--dbname", conn_params["database"],
            "--verbose",
            "--no-password",
            "--file", str(metadata.backup_path)
        ]
        
        if metadata.backup_type == BackupType.SCHEMA_ONLY:
            cmd.append("--schema-only")
        elif metadata.backup_type == BackupType.DATA_ONLY:
            cmd.append("--data-only")
        
        env = os.environ.copy()
        if conn_params.get("password"):
            env["PGPASSWORD"] = conn_params["password"]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {stderr.decode()}")
    
    async def _backup_sqlite(self, metadata: BackupMetadata):
        """Create SQLite backup using .dump command."""
        db_path = self.database_url.replace("sqlite:///", "").replace("sqlite://", "")
        
        if not Path(db_path).exists():
            raise FileNotFoundError(f"SQLite database not found: {db_path}")
        
        cmd = ["sqlite3", db_path, ".dump"]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"sqlite3 dump failed: {stderr.decode()}")
        
        with open(metadata.backup_path, 'wb') as f:
            f.write(stdout)    
def _parse_postgresql_url(self) -> Dict[str, Any]:
        """Parse PostgreSQL connection URL."""
        url = self.database_url
        
        if "://" in url:
            url = url.split("://", 1)[1]
        
        if "@" in url:
            auth, host_db = url.split("@", 1)
            if ":" in auth:
                username, password = auth.split(":", 1)
            else:
                username, password = auth, None
        else:
            username, password = None, None
            host_db = url
        
        if "/" in host_db:
            host_port, database = host_db.split("/", 1)
        else:
            host_port, database = host_db, "postgres"
        
        if ":" in host_port:
            host, port = host_port.split(":", 1)
            port = int(port)
        else:
            host, port = host_port, 5432
        
        return {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database
        }
    
    def _extract_database_name(self) -> str:
        """Extract database name from connection URL."""
        if self.database_type == "postgresql":
            return self._parse_postgresql_url()["database"]
        elif self.database_type == "sqlite":
            db_path = self.database_url.replace("sqlite:///", "").replace("sqlite://", "")
            return Path(db_path).stem
        else:
            return "unknown"
    
    # ========================================================================
    # MIGRATION MANAGEMENT
    # ========================================================================
    
    async def run_migration(self, migration_version: str) -> Dict[str, Any]:
        """
        Run a specific database migration.
        
        Args:
            migration_version: Version of migration to run
            
        Returns:
            Migration execution result
        """
        try:
            # Load migrations if not cached
            if not self.migrations_cache:
                await self._load_migrations()
            
            if migration_version not in self.migrations_cache:
                return {
                    "success": False,
                    "error": f"Migration {migration_version} not found"
                }
            
            migration = self.migrations_cache[migration_version]
            
            # Execute migration
            start_time = datetime.utcnow()
            
            from .database import get_database_manager
            db_manager = get_database_manager()
            
            async with db_manager.get_async_session() as session:
                # Execute migration SQL
                if migration.up_sql.strip():
                    statements = self._split_sql_statements(migration.up_sql)
                    
                    for statement in statements:
                        if statement.strip():
                            await session.execute(text(statement))
                
                # Record migration execution
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                await self._record_migration_execution(
                    session,
                    migration,
                    MigrationStatus.COMPLETED,
                    execution_time
                )
                
                await session.commit()
            
            logger.info(f"Migration {migration_version} completed successfully")
            
            return {
                "success": True,
                "migration_version": migration_version,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Migration {migration_version} failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "migration_version": migration_version
            }   
 async def _load_migrations(self):
        """Load migration files from directory."""
        self.migrations_cache.clear()
        
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return
        
        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        
        for migration_file in migration_files:
            try:
                migration = await self._parse_migration_file(migration_file)
                self.migrations_cache[migration.version] = migration
                
            except Exception as e:
                logger.error(f"Failed to parse migration file {migration_file}: {e}")
        
        logger.info(f"Loaded {len(self.migrations_cache)} migrations")
    
    async def _parse_migration_file(self, file_path: Path) -> Migration:
        """Parse a migration file and extract metadata."""
        content = file_path.read_text(encoding='utf-8')
        
        # Extract version from filename
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
                continue
            
            if current_section in ['up', 'down']:
                if sections[current_section]:
                    sections[current_section] += '\n'
                sections[current_section] += line
        
        return sections
    
    def _split_sql_statements(self, sql: str) -> List[str]:
        """Split SQL into individual statements."""
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
        
        return statements    a
sync def _record_migration_execution(
        self,
        session: AsyncSession,
        migration: Migration,
        status: MigrationStatus,
        execution_time: float,
        error_message: Optional[str] = None
    ):
        """Record migration execution in database."""
        # Create migration table if it doesn't exist
        create_table_sql = text(f"""
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
        """)
        
        await session.execute(create_table_sql)
        
        # Insert migration record
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
            "executed_at": datetime.utcnow(),
            "execution_time": execution_time,
            "status": status.value,
            "error_message": error_message
        })


# Global optimization service instance
_optimization_service = None


def get_optimization_service() -> DatabaseOptimizationService:
    """
    Get the global database optimization service instance.
    
    Returns:
        DatabaseOptimizationService instance
    """
    global _optimization_service
    if _optimization_service is None:
        _optimization_service = DatabaseOptimizationService()
    return _optimization_service


async def get_optimization_service_async() -> DatabaseOptimizationService:
    """
    Get the global database optimization service instance (async version).
    
    Returns:
        DatabaseOptimizationService instance
    """
    return get_optimization_service()


# Convenience functions for backward compatibility
def optimize_performance() -> Dict[str, Any]:
    """Perform database performance optimization."""
    service = get_optimization_service()
    return service.optimize_performance()


async def create_backup(
    backup_type: BackupType = BackupType.FULL,
    database_name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None
) -> BackupMetadata:
    """Create a database backup."""
    service = get_optimization_service()
    return await service.create_backup(backup_type, database_name, tags)


async def run_migration(migration_version: str) -> Dict[str, Any]:
    """Run a database migration."""
    service = get_optimization_service()
    return await service.run_migration(migration_version)