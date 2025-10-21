"""
Secure temporary file management with encryption and automatic cleanup.
"""

import base64
import hashlib
import os
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from uuid import uuid4

from cryptography.fernet import Fernet

from ..core.config import get_settings
from ..core.logging import get_logger
from ..repositories.audit_repository import AuditRepository

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class TempFileInfo:
    """Information about a temporary file."""
    file_id: str
    original_filename: str
    temp_path: str
    encrypted_path: Optional[str]
    file_hash: str
    file_size: int
    created_at: datetime
    expires_at: datetime
    access_count: int
    is_quarantined: bool
    metadata: Dict[str, any]


class TempFileManager:
    """Secure temporary file manager with encryption and cleanup."""
    
    def __init__(self, audit_repository: Optional[AuditRepository] = None):
        """Initialize temporary file manager."""
        self.audit_repository = audit_repository
        self.temp_files: Dict[str, TempFileInfo] = {}
        self.quarantine_files: Dict[str, TempFileInfo] = {}
        self.lock = threading.RLock()
        
        # Initialize encryption
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Create directories
        self.temp_dir = Path(tempfile.gettempdir()) / "contract_analyzer_temp"
        self.quarantine_dir = Path(tempfile.gettempdir()) / "contract_analyzer_quarantine"
        self.encrypted_dir = Path(tempfile.gettempdir()) / "contract_analyzer_encrypted"
        
        self._create_directories()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("Temporary file manager initialized")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key."""
        if hasattr(settings, 'encryption_key') and settings.encryption_key:
            # Use configured key
            key_str = settings.encryption_key.get_secret_value()
            # Ensure key is proper length for Fernet
            key_bytes = key_str.encode('utf-8')
            if len(key_bytes) == 32:
                return base64.urlsafe_b64encode(key_bytes)
            else:
                # Hash to get consistent 32-byte key
                return base64.urlsafe_b64encode(hashlib.sha256(key_bytes).digest())
        else:
            # Generate new key
            return Fernet.generate_key()
    
    def _create_directories(self) -> None:
        """Create necessary directories."""
        for directory in [self.temp_dir, self.quarantine_dir, self.encrypted_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions
            os.chmod(directory, 0o700)
    
    def save_temporary_file(
        self, 
        file_content: bytes, 
        original_filename: str,
        encrypt: bool = True,
        retention_hours: int = 24,
        metadata: Optional[Dict[str, any]] = None
    ) -> str:
        """
        Save file to temporary storage with optional encryption.
        
        Args:
            file_content: File content as bytes
            original_filename: Original filename
            encrypt: Whether to encrypt the file
            retention_hours: Hours to retain the file
            metadata: Additional metadata
            
        Returns:
            File ID for later retrieval
        """
        file_id = str(uuid4())
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        with self.lock:
            try:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    dir=self.temp_dir,
                    prefix=f"temp_{file_id}_",
                    suffix=Path(original_filename).suffix,
                    delete=False
                )
                
                temp_path = temp_file.name
                temp_file.write(file_content)
                temp_file.close()
                
                # Set restrictive permissions
                os.chmod(temp_path, 0o600)
                
                encrypted_path = None
                if encrypt:
                    encrypted_path = self._encrypt_file(temp_path, file_id)
                
                # Create file info
                file_info = TempFileInfo(
                    file_id=file_id,
                    original_filename=original_filename,
                    temp_path=temp_path,
                    encrypted_path=encrypted_path,
                    file_hash=file_hash,
                    file_size=len(file_content),
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=retention_hours),
                    access_count=0,
                    is_quarantined=False,
                    metadata=metadata or {}
                )
                
                self.temp_files[file_id] = file_info
                
                # Audit log
                if self.audit_repository:
                    self.audit_repository.log_event(
                        event_type="temp_file_created",
                        event_data={
                            "file_id": file_id,
                            "original_filename": original_filename,
                            "file_size": len(file_content),
                            "encrypted": encrypt,
                            "retention_hours": retention_hours
                        },
                        action="CREATE",
                        result="SUCCESS"
                    )
                
                logger.info(f"Temporary file saved: {file_id} ({original_filename})")
                return file_id
                
            except Exception as e:
                logger.error(f"Failed to save temporary file: {e}", exc_info=True)
                
                # Audit log
                if self.audit_repository:
                    self.audit_repository.log_event(
                        event_type="temp_file_create_failed",
                        event_data={
                            "original_filename": original_filename,
                            "error": str(e)
                        },
                        action="CREATE",
                        result="FAILURE"
                    )
                
                raise
    
    def get_temporary_file(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve temporary file content.
        
        Args:
            file_id: File ID
            
        Returns:
            File content as bytes or None if not found
        """
        with self.lock:
            file_info = self.temp_files.get(file_id)
            if not file_info:
                return None
            
            # Check if expired
            if datetime.utcnow() > file_info.expires_at:
                logger.warning(f"Attempted to access expired file: {file_id}")
                return None
            
            # Check if quarantined
            if file_info.is_quarantined:
                logger.warning(f"Attempted to access quarantined file: {file_id}")
                return None
            
            try:
                # Update access count
                file_info.access_count += 1
                
                # Read file content
                if file_info.encrypted_path and Path(file_info.encrypted_path).exists():
                    content = self._decrypt_file(file_info.encrypted_path)
                elif Path(file_info.temp_path).exists():
                    with open(file_info.temp_path, 'rb') as f:
                        content = f.read()
                else:
                    logger.error(f"Temporary file not found: {file_id}")
                    return None
                
                # Verify integrity
                content_hash = hashlib.sha256(content).hexdigest()
                if content_hash != file_info.file_hash:
                    logger.error(f"File integrity check failed: {file_id}")
                    self.quarantine_file(file_id, "Integrity check failed")
                    return None
                
                # Audit log
                if self.audit_repository:
                    self.audit_repository.log_event(
                        event_type="temp_file_accessed",
                        event_data={
                            "file_id": file_id,
                            "access_count": file_info.access_count
                        },
                        action="READ",
                        result="SUCCESS"
                    )
                
                return content
                
            except Exception as e:
                logger.error(f"Failed to retrieve temporary file {file_id}: {e}", exc_info=True)
                
                # Audit log
                if self.audit_repository:
                    self.audit_repository.log_event(
                        event_type="temp_file_access_failed",
                        event_data={
                            "file_id": file_id,
                            "error": str(e)
                        },
                        action="READ",
                        result="FAILURE"
                    )
                
                return None
    
    def get_file_info(self, file_id: str) -> Optional[TempFileInfo]:
        """Get information about a temporary file."""
        with self.lock:
            return self.temp_files.get(file_id)
    
    def quarantine_file(self, file_id: str, reason: str) -> bool:
        """
        Quarantine a suspicious file.
        
        Args:
            file_id: File ID
            reason: Reason for quarantine
            
        Returns:
            True if successfully quarantined
        """
        with self.lock:
            file_info = self.temp_files.get(file_id)
            if not file_info:
                return False
            
            try:
                # Mark as quarantined
                file_info.is_quarantined = True
                file_info.metadata["quarantine_reason"] = reason
                file_info.metadata["quarantined_at"] = datetime.utcnow().isoformat()
                
                # Move to quarantine directory
                quarantine_path = self.quarantine_dir / f"quarantine_{file_id}_{Path(file_info.original_filename).name}"
                
                if file_info.encrypted_path and Path(file_info.encrypted_path).exists():
                    shutil.move(file_info.encrypted_path, quarantine_path)
                elif Path(file_info.temp_path).exists():
                    shutil.move(file_info.temp_path, quarantine_path)
                
                # Update paths
                file_info.temp_path = str(quarantine_path)
                file_info.encrypted_path = None
                
                # Move to quarantine tracking
                self.quarantine_files[file_id] = file_info
                
                # Audit log
                if self.audit_repository:
                    self.audit_repository.log_event(
                        event_type="file_quarantined",
                        event_data={
                            "file_id": file_id,
                            "reason": reason,
                            "original_filename": file_info.original_filename
                        },
                        action="QUARANTINE",
                        result="SUCCESS"
                    )
                
                logger.warning(f"File quarantined: {file_id} - {reason}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to quarantine file {file_id}: {e}", exc_info=True)
                return False
    
    def delete_temporary_file(self, file_id: str) -> bool:
        """
        Delete a temporary file.
        
        Args:
            file_id: File ID
            
        Returns:
            True if successfully deleted
        """
        with self.lock:
            file_info = self.temp_files.get(file_id)
            if not file_info:
                return False
            
            try:
                # Delete files
                if file_info.encrypted_path:
                    Path(file_info.encrypted_path).unlink(missing_ok=True)
                
                Path(file_info.temp_path).unlink(missing_ok=True)
                
                # Remove from tracking
                del self.temp_files[file_id]
                
                # Audit log
                if self.audit_repository:
                    self.audit_repository.log_event(
                        event_type="temp_file_deleted",
                        event_data={
                            "file_id": file_id,
                            "original_filename": file_info.original_filename
                        },
                        action="DELETE",
                        result="SUCCESS"
                    )
                
                logger.info(f"Temporary file deleted: {file_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete temporary file {file_id}: {e}", exc_info=True)
                return False
    
    def cleanup_expired_files(self) -> int:
        """Clean up expired temporary files."""
        cleaned_count = 0
        current_time = datetime.utcnow()
        
        with self.lock:
            expired_files = [
                file_id for file_id, file_info in self.temp_files.items()
                if current_time > file_info.expires_at
            ]
            
            for file_id in expired_files:
                if self.delete_temporary_file(file_id):
                    cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired temporary files")
        
        return cleaned_count
    
    def cleanup_all(self) -> int:
        """Clean up all temporary files."""
        cleaned_count = 0
        
        with self.lock:
            file_ids = list(self.temp_files.keys())
            
            for file_id in file_ids:
                if self.delete_temporary_file(file_id):
                    cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} temporary files")
        return cleaned_count
    
    def get_statistics(self) -> Dict[str, any]:
        """Get temporary file statistics."""
        with self.lock:
            current_time = datetime.utcnow()
            
            total_files = len(self.temp_files)
            quarantined_files = len(self.quarantine_files)
            expired_files = sum(
                1 for file_info in self.temp_files.values()
                if current_time > file_info.expires_at
            )
            
            total_size = sum(file_info.file_size for file_info in self.temp_files.values())
            
            return {
                "total_files": total_files,
                "quarantined_files": quarantined_files,
                "expired_files": expired_files,
                "total_size_bytes": total_size,
                "temp_directory": str(self.temp_dir),
                "quarantine_directory": str(self.quarantine_dir)
            }
    
    def _encrypt_file(self, file_path: str, file_id: str) -> str:
        """Encrypt a file and return encrypted file path."""
        try:
            # Read original file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Encrypt content
            encrypted_content = self.cipher.encrypt(content)
            
            # Write encrypted file
            encrypted_path = self.encrypted_dir / f"encrypted_{file_id}.enc"
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_content)
            
            # Set restrictive permissions
            os.chmod(encrypted_path, 0o600)
            
            # Remove original unencrypted file
            Path(file_path).unlink()
            
            return str(encrypted_path)
            
        except Exception as e:
            logger.error(f"Failed to encrypt file {file_path}: {e}")
            raise
    
    def _decrypt_file(self, encrypted_path: str) -> bytes:
        """Decrypt a file and return content."""
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_content = f.read()
            
            return self.cipher.decrypt(encrypted_content)
            
        except Exception as e:
            logger.error(f"Failed to decrypt file {encrypted_path}: {e}")
            raise
    
    def _cleanup_worker(self) -> None:
        """Background worker for cleaning up expired files."""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                self.cleanup_expired_files()
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}", exc_info=True)


# Global instance
temp_file_manager = TempFileManager()


# Convenience functions
def save_temp_file(content: bytes, filename: str, encrypt: bool = True) -> str:
    """Save temporary file."""
    return temp_file_manager.save_temporary_file(content, filename, encrypt=encrypt)


def get_temp_file(file_id: str) -> Optional[bytes]:
    """Get temporary file content."""
    return temp_file_manager.get_temporary_file(file_id)


def delete_temp_file(file_id: str) -> bool:
    """Delete temporary file."""
    return temp_file_manager.delete_temporary_file(file_id)


def quarantine_temp_file(file_id: str, reason: str) -> bool:
    """Quarantine temporary file."""
    return temp_file_manager.quarantine_file(file_id, reason)