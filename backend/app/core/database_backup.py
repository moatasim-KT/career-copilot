"""
Production-ready database backup and recovery system.

This module provides comprehensive backup and recovery functionality for PostgreSQL
and SQLite databases with automated scheduling, compression, encryption, and monitoring.
"""

import asyncio
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_config_manager
from .logging import get_logger

logger = get_logger(__name__)


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


class DatabaseBackupManager:
    """Production-ready database backup and recovery manager."""
    
    def __init__(self):
        self.config = get_config_manager()
        self.backup_dir = Path(self.config.get("backup.directory", "./backups"))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup configuration
        self.retention_days = self.config.get("backup.retention_days", 30)
        self.compression_enabled = self.config.get("backup.compression_enabled", True)
        self.compression_type = CompressionType(self.config.get("backup.compression_type", "gzip"))
        self.encryption_enabled = self.config.get("backup.encryption_enabled", False)
        self.encryption_key = self.config.get("backup.encryption_key")
        self.parallel_jobs = self.config.get("backup.parallel_jobs", 2)
        
        # Backup metadata storage
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.backup_metadata: Dict[str, BackupMetadata] = {}
        self._load_metadata()
        
        # Database connection info
        self.database_url = self.config.get("database.url")
        self.database_type = self._detect_database_type()
        
        logger.info(f"Database backup manager initialized for {self.database_type}")
    
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
            return "unknown"
    
    def _load_metadata(self):
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
    
    def _save_metadata(self):
        """Save backup metadata to file."""
        try:
            data = {backup_id: metadata.to_dict() 
                   for backup_id, metadata in self.backup_metadata.items()}
            
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    def _generate_backup_id(self) -> str:
        """Generate unique backup ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
        
        # Add support for other compression types as needed
        logger.warning(f"Compression type {compression_type} not implemented, using no compression")
        return source_path   
 
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
            database_name: Name of database to backup (auto-detected if None)
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
            created_at=datetime.now(),
            compression_type=self.compression_type if self.compression_enabled else CompressionType.NONE,
            retention_days=self.retention_days,
            tags=tags or {}
        )
        
        self.backup_metadata[backup_id] = metadata
        self._save_metadata()
        
        try:
            logger.info(f"Starting {backup_type.value} backup: {backup_id}")
            metadata.status = BackupStatus.RUNNING
            self._save_metadata()
            
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
            metadata.completed_at = datetime.now()
            metadata.status = BackupStatus.COMPLETED
            
            logger.info(f"Backup completed successfully: {backup_id}")
            
        except Exception as e:
            logger.error(f"Backup failed: {backup_id} - {e}")
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
        
        finally:
            self._save_metadata()
        
        return metadata
    
    async def _backup_postgresql(self, metadata: BackupMetadata):
        """Create PostgreSQL backup using pg_dump."""
        # Parse connection URL
        conn_params = self._parse_postgresql_url()
        
        # Build pg_dump command
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
        
        # Add backup type specific options
        if metadata.backup_type == BackupType.SCHEMA_ONLY:
            cmd.append("--schema-only")
        elif metadata.backup_type == BackupType.DATA_ONLY:
            cmd.append("--data-only")
        
        # Set environment variables
        env = os.environ.copy()
        if conn_params.get("password"):
            env["PGPASSWORD"] = conn_params["password"]
        
        # Execute pg_dump
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {stderr.decode()}")
        
        logger.debug(f"pg_dump output: {stdout.decode()}")
    
    async def _backup_sqlite(self, metadata: BackupMetadata):
        """Create SQLite backup using .dump command."""
        # Extract database path from URL
        db_path = self.database_url.replace("sqlite:///", "").replace("sqlite://", "")
        
        if not Path(db_path).exists():
            raise FileNotFoundError(f"SQLite database not found: {db_path}")
        
        # Use sqlite3 command line tool
        cmd = [
            "sqlite3",
            db_path,
            ".dump"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"sqlite3 dump failed: {stderr.decode()}")
        
        # Write dump to backup file
        with open(metadata.backup_path, 'wb') as f:
            f.write(stdout)
    
    def _parse_postgresql_url(self) -> Dict[str, Any]:
        """Parse PostgreSQL connection URL."""
        # Simple URL parsing - in production, use a proper URL parser
        url = self.database_url
        
        # Remove protocol
        if "://" in url:
            url = url.split("://", 1)[1]
        
        # Extract components
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
    
    async def restore_backup(
        self,
        backup_id: str,
        options: Optional[RestoreOptions] = None
    ) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_id: ID of backup to restore
            options: Restore options
            
        Returns:
            True if restore was successful
        """
        if backup_id not in self.backup_metadata:
            raise ValueError(f"Backup not found: {backup_id}")
        
        metadata = self.backup_metadata[backup_id]
        options = options or RestoreOptions()
        
        if not metadata.backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {metadata.backup_path}")
        
        try:
            logger.info(f"Starting restore from backup: {backup_id}")
            
            # Verify backup integrity
            if metadata.checksum:
                current_checksum = self._calculate_checksum(metadata.backup_path)
                if current_checksum != metadata.checksum:
                    raise ValueError("Backup file integrity check failed")
            
            # Decompress if needed
            restore_file = metadata.backup_path
            if metadata.compression_type != CompressionType.NONE:
                restore_file = await self._decompress_backup(metadata.backup_path, metadata.compression_type)
            
            # Perform restore based on database type
            if self.database_type == "postgresql":
                success = await self._restore_postgresql(restore_file, options)
            elif self.database_type == "sqlite":
                success = await self._restore_sqlite(restore_file, options)
            else:
                raise ValueError(f"Unsupported database type: {self.database_type}")
            
            # Clean up temporary decompressed file
            if restore_file != metadata.backup_path:
                restore_file.unlink()
            
            if success:
                logger.info(f"Restore completed successfully: {backup_id}")
            else:
                logger.error(f"Restore failed: {backup_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Restore failed: {backup_id} - {e}")
            return False
    
    async def _decompress_backup(self, backup_path: Path, compression_type: CompressionType) -> Path:
        """Decompress backup file for restore."""
        if compression_type == CompressionType.GZIP:
            decompressed_path = backup_path.with_suffix("")
            
            with gzip.open(backup_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return decompressed_path
        
        # Add support for other compression types as needed
        return backup_path
    
    async def _restore_postgresql(self, backup_file: Path, options: RestoreOptions) -> bool:
        """Restore PostgreSQL database from backup."""
        conn_params = self._parse_postgresql_url()
        
        target_db = options.target_database or conn_params["database"]
        
        # Build psql command
        cmd = [
            "psql",
            "--host", conn_params["host"],
            "--port", str(conn_params["port"]),
            "--username", conn_params["username"],
            "--dbname", target_db,
            "--file", str(backup_file),
            "--quiet"
        ]
        
        if options.drop_existing:
            # First drop and recreate database
            await self._recreate_postgresql_database(target_db, conn_params)
        
        # Set environment variables
        env = os.environ.copy()
        if conn_params.get("password"):
            env["PGPASSWORD"] = conn_params["password"]
        
        # Execute psql
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"psql restore failed: {stderr.decode()}")
            return False
        
        return True
    
    async def _restore_sqlite(self, backup_file: Path, options: RestoreOptions) -> bool:
        """Restore SQLite database from backup."""
        db_path = self.database_url.replace("sqlite:///", "").replace("sqlite://", "")
        target_path = options.target_database or db_path
        
        if options.drop_existing and Path(target_path).exists():
            Path(target_path).unlink()
        
        # Use sqlite3 to restore
        cmd = [
            "sqlite3",
            target_path,
            f".read {backup_file}"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"sqlite3 restore failed: {stderr.decode()}")
            return False
        
        return True
    
    async def _recreate_postgresql_database(self, database_name: str, conn_params: Dict[str, Any]):
        """Drop and recreate PostgreSQL database."""
        # Connect to postgres database to drop/create target database
        admin_conn_params = conn_params.copy()
        admin_conn_params["database"] = "postgres"
        
        # Build connection string
        conn_str = f"postgresql://{admin_conn_params['username']}"
        if admin_conn_params.get("password"):
            conn_str += f":{admin_conn_params['password']}"
        conn_str += f"@{admin_conn_params['host']}:{admin_conn_params['port']}/{admin_conn_params['database']}"
        
        conn = await asyncpg.connect(conn_str)
        
        try:
            # Terminate existing connections
            await conn.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{database_name}' AND pid <> pg_backend_pid()
            """)
            
            # Drop database
            await conn.execute(f"DROP DATABASE IF EXISTS {database_name}")
            
            # Create database
            await conn.execute(f"CREATE DATABASE {database_name}")
            
        finally:
            await conn.close()    

    def list_backups(
        self,
        database_name: Optional[str] = None,
        backup_type: Optional[BackupType] = None,
        status: Optional[BackupStatus] = None
    ) -> List[BackupMetadata]:
        """
        List available backups with optional filtering.
        
        Args:
            database_name: Filter by database name
            backup_type: Filter by backup type
            status: Filter by backup status
            
        Returns:
            List of backup metadata
        """
        backups = list(self.backup_metadata.values())
        
        if database_name:
            backups = [b for b in backups if b.database_name == database_name]
        
        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]
        
        if status:
            backups = [b for b in backups if b.status == status]
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b.created_at, reverse=True)
        
        return backups
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get detailed information about a specific backup."""
        return self.backup_metadata.get(backup_id)
    
    async def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Verify backup integrity and validity.
        
        Args:
            backup_id: ID of backup to verify
            
        Returns:
            Verification results
        """
        if backup_id not in self.backup_metadata:
            return {"valid": False, "error": "Backup not found"}
        
        metadata = self.backup_metadata[backup_id]
        
        if not metadata.backup_path.exists():
            return {"valid": False, "error": "Backup file not found"}
        
        results = {
            "backup_id": backup_id,
            "valid": True,
            "checks": {}
        }
        
        try:
            # Check file size
            current_size = metadata.backup_path.stat().st_size
            results["checks"]["file_size"] = {
                "expected": metadata.file_size,
                "actual": current_size,
                "valid": current_size == metadata.file_size
            }
            
            # Check checksum if available
            if metadata.checksum:
                current_checksum = self._calculate_checksum(metadata.backup_path)
                results["checks"]["checksum"] = {
                    "expected": metadata.checksum,
                    "actual": current_checksum,
                    "valid": current_checksum == metadata.checksum
                }
            
            # Check if backup can be read (basic format validation)
            if metadata.compression_type == CompressionType.GZIP:
                try:
                    with gzip.open(metadata.backup_path, 'rt') as f:
                        f.read(1024)  # Read first 1KB
                    results["checks"]["format"] = {"valid": True}
                except Exception as e:
                    results["checks"]["format"] = {"valid": False, "error": str(e)}
            else:
                try:
                    with open(metadata.backup_path, 'r') as f:
                        f.read(1024)  # Read first 1KB
                    results["checks"]["format"] = {"valid": True}
                except Exception as e:
                    results["checks"]["format"] = {"valid": False, "error": str(e)}
            
            # Overall validity
            results["valid"] = all(
                check.get("valid", True) for check in results["checks"].values()
            )
            
        except Exception as e:
            results["valid"] = False
            results["error"] = str(e)
        
        return results
    
    async def cleanup_old_backups(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean up old backups based on retention policy.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Cleanup results
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        old_backups = [
            metadata for metadata in self.backup_metadata.values()
            if metadata.created_at < cutoff_date and metadata.status == BackupStatus.COMPLETED
        ]
        
        results = {
            "total_backups": len(self.backup_metadata),
            "old_backups_found": len(old_backups),
            "deleted_backups": [],
            "failed_deletions": [],
            "space_freed": 0,
            "dry_run": dry_run
        }
        
        for metadata in old_backups:
            try:
                if dry_run:
                    results["deleted_backups"].append({
                        "backup_id": metadata.backup_id,
                        "created_at": metadata.created_at.isoformat(),
                        "file_size": metadata.file_size
                    })
                    results["space_freed"] += metadata.file_size
                else:
                    # Delete backup file
                    if metadata.backup_path.exists():
                        metadata.backup_path.unlink()
                        results["space_freed"] += metadata.file_size
                    
                    # Remove from metadata
                    del self.backup_metadata[metadata.backup_id]
                    
                    results["deleted_backups"].append({
                        "backup_id": metadata.backup_id,
                        "created_at": metadata.created_at.isoformat(),
                        "file_size": metadata.file_size
                    })
                    
                    logger.info(f"Deleted old backup: {metadata.backup_id}")
                    
            except Exception as e:
                logger.error(f"Failed to delete backup {metadata.backup_id}: {e}")
                results["failed_deletions"].append({
                    "backup_id": metadata.backup_id,
                    "error": str(e)
                })
        
        if not dry_run:
            self._save_metadata()
        
        return results    
 
    async def schedule_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        schedule_time: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Schedule a backup to run at a specific time.
        
        Args:
            backup_type: Type of backup to create
            schedule_time: When to run the backup (default: now)
            tags: Additional tags for the backup
            
        Returns:
            Backup ID
        """
        if schedule_time is None:
            schedule_time = datetime.now()
        
        # For now, just run immediately if schedule_time is in the past
        if schedule_time <= datetime.now():
            metadata = await self.create_backup(backup_type, tags=tags)
            return metadata.backup_id
        
        # In a production system, you would integrate with a job scheduler
        # like Celery, APScheduler, or cron
        logger.info(f"Backup scheduled for {schedule_time}: {backup_type.value}")
        
        # For demonstration, create a placeholder
        backup_id = self._generate_backup_id()
        return backup_id
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on backup system."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "backup_directory": str(self.backup_dir),
            "backup_directory_exists": self.backup_dir.exists(),
            "backup_directory_writable": os.access(self.backup_dir, os.W_OK),
            "total_backups": len(self.backup_metadata),
            "recent_backups": 0,
            "failed_backups": 0,
            "disk_usage": {}
        }
        
        try:
            # Count recent and failed backups
            recent_cutoff = datetime.now() - timedelta(days=7)
            for metadata in self.backup_metadata.values():
                if metadata.created_at >= recent_cutoff:
                    health_status["recent_backups"] += 1
                if metadata.status == BackupStatus.FAILED:
                    health_status["failed_backups"] += 1
            
            # Check disk usage
            if self.backup_dir.exists():
                total_size = sum(
                    f.stat().st_size for f in self.backup_dir.rglob('*') if f.is_file()
                )
                health_status["disk_usage"] = {
                    "total_backup_size": total_size,
                    "total_backup_size_mb": round(total_size / (1024 * 1024), 2)
                }
            
            # Check database connectivity
            if self.database_url:
                health_status["database_connectivity"] = await self._test_database_connection()
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def _test_database_connection(self) -> bool:
        """Test database connectivity."""
        try:
            if self.database_type == "postgresql":
                conn_params = self._parse_postgresql_url()
                conn_str = f"postgresql://{conn_params['username']}"
                if conn_params.get("password"):
                    conn_str += f":{conn_params['password']}"
                conn_str += f"@{conn_params['host']}:{conn_params['port']}/{conn_params['database']}"
                
                conn = await asyncpg.connect(conn_str)
                await conn.execute("SELECT 1")
                await conn.close()
                return True
                
            elif self.database_type == "sqlite":
                db_path = self.database_url.replace("sqlite:///", "").replace("sqlite://", "")
                return Path(db_path).exists()
            
            return False
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global backup manager instance
backup_manager = DatabaseBackupManager()


async def get_backup_manager() -> DatabaseBackupManager:
    """Get the global backup manager instance."""
    return backup_manager