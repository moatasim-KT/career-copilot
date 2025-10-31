"""
Consolidated Database Optimization and Maintenance Service.

This module provides high-level services for database maintenance tasks,
relying on the core DatabaseManager for connection and session handling.
Services include:
- Backup and recovery management
- Database migration system
- Performance analysis and recommendations
"""

import asyncio
import gzip
import hashlib
import json
import os
import re
import shutil
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from .config import settings
from .database import get_db_manager
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

class BackupType(str, Enum):
    FULL = "full"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"

class BackupStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BackupMetadata:
    backup_id: str
    backup_type: BackupType
    database_name: str
    backup_path: Path
    created_at: datetime
    status: BackupStatus = BackupStatus.PENDING
    file_size: int = 0
    checksum: Optional[str] = None
    error_message: Optional[str] = None

class DatabaseOptimizationService:
    """High-level service for database optimization and maintenance."""

    def __init__(self):
        self.settings = get_settings()
        self.db_manager = get_db_manager()
        self.backup_dir = Path(getattr(self.settings, 'backup_directory', './data/backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.backup_metadata: Dict[str, BackupMetadata] = self._load_backup_metadata()

    def _load_backup_metadata(self) -> Dict[str, BackupMetadata]:
        if not self.metadata_file.exists():
            return {}
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
            return {k: BackupMetadata(**v) for k, v in data.items()}
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to load backup metadata: {e}")
            return {}

    def _save_backup_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump({k: v.__dict__ for k, v in self.backup_metadata.items()}, f, indent=2, default=str)

    async def create_backup(self, backup_type: BackupType = BackupType.FULL) -> BackupMetadata:
        backup_id = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        db_name = self.db_manager.database_url.split('/')[-1]
        backup_path = self.backup_dir / f"{backup_id}.sql.gz"

        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            database_name=db_name,
            backup_path=backup_path,
            created_at=datetime.now(timezone.utc)
        )
        self.backup_metadata[backup_id] = metadata

        try:
            logger.info(f"Starting {backup_type.value} backup: {backup_id}")
            metadata.status = BackupStatus.RUNNING
            self._save_backup_metadata()

            db_type = self.db_manager.database_url.split('://')[0]
            if "postgresql" in db_type:
                await self._backup_postgresql(metadata)
            elif "sqlite" in db_type:
                await self._backup_sqlite(metadata)
            else:
                raise NotImplementedError(f"Backup not supported for db type: {db_type}")

            metadata.file_size = metadata.backup_path.stat().st_size
            metadata.checksum = self._calculate_checksum(metadata.backup_path)
            metadata.status = BackupStatus.COMPLETED
            logger.info(f"Backup completed successfully: {backup_id}")

        except Exception as e:
            logger.error(f"Backup failed: {backup_id} - {e}")
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
        finally:
            self._save_backup_metadata()

        return metadata

    async def _backup_postgresql(self, metadata: BackupMetadata):
        # This is a simplified example. In a real-world scenario, you would use
        # pg_dump with asyncio.create_subprocess_exec.
        logger.warning("PostgreSQL backup simulation. Not a real backup.")
        async with self.db_manager.get_session() as session:
            result = await session.execute(text("SELECT 'PostgreSQL backup simulation'"))
            simulated_content = result.scalar_one()

        with gzip.open(metadata.backup_path, 'wt') as f_out:
            f_out.write(simulated_content)

    async def _backup_sqlite(self, metadata: BackupMetadata):
        db_path = self.db_manager.database_url.replace("sqlite:///", "")
        if not Path(db_path).exists():
            raise FileNotFoundError(f"SQLite database not found: {db_path}")

        # Use the .iterdump() method for a memory-efficient backup
        with self.db_manager.get_sync_session() as session:
            with gzip.open(metadata.backup_path, "wt", encoding="utf-8") as f_out:
                for line in session.connection().connection.iterdump():
                    f_out.write(f'{line}\n')

    def _calculate_checksum(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

_optimization_service: Optional[DatabaseOptimizationService] = None

def get_optimization_service() -> DatabaseOptimizationService:
    global _optimization_service
    if _optimization_service is None:
        _optimization_service = DatabaseOptimizationService()
    return _optimization_service
