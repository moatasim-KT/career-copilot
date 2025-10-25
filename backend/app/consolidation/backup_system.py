"""
Backup system for original files before consolidation.

This module provides functionality to create backups of original files
before they are consolidated, enabling rollback capabilities.
"""

import os
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup operation."""
    backup_id: str
    timestamp: datetime
    original_path: str
    backup_path: str
    file_hash: str
    file_size: int
    consolidation_phase: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BackupMetadata':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class BackupSystem:
    """System for backing up files before consolidation."""
    
    def __init__(self, backup_root: str = "data/consolidation_backups"):
        """
        Initialize backup system.
        
        Args:
            backup_root: Root directory for storing backups
        """
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        # Metadata file to track all backups
        self.metadata_file = self.backup_root / "backup_metadata.json"
        self.backups: Dict[str, BackupMetadata] = {}
        
        # Load existing metadata
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load backup metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.backups = {
                        backup_id: BackupMetadata.from_dict(backup_data)
                        for backup_id, backup_data in data.items()
                    }
                logger.info(f"Loaded {len(self.backups)} backup records")
            except Exception as e:
                logger.error(f"Failed to load backup metadata: {e}")
                self.backups = {}
    
    def _save_metadata(self) -> None:
        """Save backup metadata to file."""
        try:
            data = {
                backup_id: backup.to_dict()
                for backup_id, backup in self.backups.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Saved backup metadata")
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def create_backup(
        self, 
        file_path: str, 
        consolidation_phase: str = "unknown"
    ) -> Optional[str]:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            consolidation_phase: Phase of consolidation this backup is for
            
        Returns:
            Backup ID if successful, None otherwise
        """
        source_path = Path(file_path)
        
        if not source_path.exists():
            logger.error(f"Source file does not exist: {file_path}")
            return None
        
        if not source_path.is_file():
            logger.error(f"Source path is not a file: {file_path}")
            return None
        
        # Generate backup ID
        timestamp = datetime.now()
        backup_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{source_path.name}_{hashlib.md5(str(source_path).encode()).hexdigest()[:8]}"
        
        # Create backup directory structure
        backup_dir = self.backup_root / consolidation_phase / timestamp.strftime('%Y-%m-%d')
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup file path
        backup_path = backup_dir / f"{backup_id}_{source_path.name}"
        
        try:
            # Copy file to backup location
            shutil.copy2(source_path, backup_path)
            
            # Calculate file hash and size
            file_hash = self._calculate_file_hash(source_path)
            file_size = source_path.stat().st_size
            
            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=timestamp,
                original_path=str(source_path.resolve()),
                backup_path=str(backup_path.resolve()),
                file_hash=file_hash,
                file_size=file_size,
                consolidation_phase=consolidation_phase
            )
            
            # Store metadata
            self.backups[backup_id] = metadata
            self._save_metadata()
            
            logger.info(f"Created backup {backup_id} for {file_path}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def create_batch_backup(
        self, 
        file_paths: List[str], 
        consolidation_phase: str = "unknown"
    ) -> Dict[str, Optional[str]]:
        """
        Create backups for multiple files.
        
        Args:
            file_paths: List of file paths to backup
            consolidation_phase: Phase of consolidation
            
        Returns:
            Dictionary mapping file paths to backup IDs (None if failed)
        """
        results = {}
        
        for file_path in file_paths:
            backup_id = self.create_backup(file_path, consolidation_phase)
            results[file_path] = backup_id
        
        logger.info(f"Created {sum(1 for v in results.values() if v is not None)} backups out of {len(file_paths)} files")
        return results
    
    def restore_backup(self, backup_id: str) -> bool:
        """
        Restore a file from backup.
        
        Args:
            backup_id: ID of the backup to restore
            
        Returns:
            True if successful, False otherwise
        """
        if backup_id not in self.backups:
            logger.error(f"Backup ID not found: {backup_id}")
            return False
        
        metadata = self.backups[backup_id]
        backup_path = Path(metadata.backup_path)
        original_path = Path(metadata.original_path)
        
        if not backup_path.exists():
            logger.error(f"Backup file does not exist: {backup_path}")
            return False
        
        try:
            # Create parent directories if they don't exist
            original_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Restore file
            shutil.copy2(backup_path, original_path)
            
            # Verify restoration
            restored_hash = self._calculate_file_hash(original_path)
            if restored_hash != metadata.file_hash:
                logger.warning(f"Hash mismatch after restoration for {backup_id}")
            
            logger.info(f"Restored backup {backup_id} to {original_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_id}: {e}")
            return False
    
    def restore_phase_backups(self, consolidation_phase: str) -> Dict[str, bool]:
        """
        Restore all backups from a specific consolidation phase.
        
        Args:
            consolidation_phase: Phase to restore backups from
            
        Returns:
            Dictionary mapping backup IDs to restoration success
        """
        phase_backups = {
            backup_id: metadata
            for backup_id, metadata in self.backups.items()
            if metadata.consolidation_phase == consolidation_phase
        }
        
        results = {}
        for backup_id in phase_backups:
            results[backup_id] = self.restore_backup(backup_id)
        
        logger.info(f"Restored {sum(results.values())} out of {len(results)} backups for phase {consolidation_phase}")
        return results
    
    def list_backups(self, consolidation_phase: Optional[str] = None) -> List[BackupMetadata]:
        """
        List all backups, optionally filtered by phase.
        
        Args:
            consolidation_phase: Optional phase filter
            
        Returns:
            List of backup metadata
        """
        backups = list(self.backups.values())
        
        if consolidation_phase:
            backups = [b for b in backups if b.consolidation_phase == consolidation_phase]
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        return backups
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupMetadata]:
        """
        Get information about a specific backup.
        
        Args:
            backup_id: ID of the backup
            
        Returns:
            Backup metadata if found, None otherwise
        """
        return self.backups.get(backup_id)
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup (use with caution).
        
        Args:
            backup_id: ID of the backup to delete
            
        Returns:
            True if successful, False otherwise
        """
        if backup_id not in self.backups:
            logger.error(f"Backup ID not found: {backup_id}")
            return False
        
        metadata = self.backups[backup_id]
        backup_path = Path(metadata.backup_path)
        
        try:
            if backup_path.exists():
                backup_path.unlink()
            
            # Remove from metadata
            del self.backups[backup_id]
            self._save_metadata()
            
            logger.info(f"Deleted backup {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """
        Clean up backups older than specified days.
        
        Args:
            days_to_keep: Number of days to keep backups
            
        Returns:
            Number of backups deleted
        """
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
        
        old_backups = [
            backup_id for backup_id, metadata in self.backups.items()
            if metadata.timestamp < cutoff_date
        ]
        
        deleted_count = 0
        for backup_id in old_backups:
            if self.delete_backup(backup_id):
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count
    
    def get_backup_statistics(self) -> Dict:
        """
        Get statistics about backups.
        
        Returns:
            Dictionary with backup statistics
        """
        if not self.backups:
            return {
                "total_backups": 0,
                "total_size_bytes": 0,
                "phases": {},
                "oldest_backup": None,
                "newest_backup": None
            }
        
        total_size = sum(metadata.file_size for metadata in self.backups.values())
        phases = {}
        
        for metadata in self.backups.values():
            phase = metadata.consolidation_phase
            if phase not in phases:
                phases[phase] = {"count": 0, "size_bytes": 0}
            phases[phase]["count"] += 1
            phases[phase]["size_bytes"] += metadata.file_size
        
        timestamps = [metadata.timestamp for metadata in self.backups.values()]
        
        return {
            "total_backups": len(self.backups),
            "total_size_bytes": total_size,
            "phases": phases,
            "oldest_backup": min(timestamps).isoformat() if timestamps else None,
            "newest_backup": max(timestamps).isoformat() if timestamps else None
        }