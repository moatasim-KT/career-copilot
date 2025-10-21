"""
Document migration strategy service for Career Co-Pilot system
"""

import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.document import Document
from app.models.document_history import DocumentVersionMigration
from app.services.document_versioning_service import DocumentVersioningService
from app.services.crypto_service import crypto_service
from app.services.compression_service import compression_service, CompressionType
from app.core.config import settings


class DocumentMigrationStrategyService:
    """Service for handling document migration strategies"""
    
    def __init__(self, db: Session):
        self.db = db
        self.versioning_service = DocumentVersioningService(db)
        self.upload_dir = Path(settings.UPLOAD_DIR)
    
    async def execute_migration(self, migration_id: str) -> bool:
        """Execute a document migration based on its type"""
        
        migration = self.versioning_service.get_migration_status(migration_id)
        if not migration:
            return False
        
        try:
            # Update migration status to running
            self.versioning_service.update_migration_progress(
                migration_id=migration_id,
                progress=0,
                status="running",
                log_entry={"action": "migration_started", "message": "Migration execution started"}
            )
            
            # Execute migration based on type
            if migration.migration_type == "version_upgrade":
                success = await self._execute_version_upgrade_migration(migration)
            elif migration.migration_type == "compression_migration":
                success = await self._execute_compression_migration(migration)
            elif migration.migration_type == "encryption_migration":
                success = await self._execute_encryption_migration(migration)
            elif migration.migration_type == "storage_migration":
                success = await self._execute_storage_migration(migration)
            elif migration.migration_type == "format_migration":
                success = await self._execute_format_migration(migration)
            elif migration.migration_type == "cleanup_migration":
                success = await self._execute_cleanup_migration(migration)
            else:
                raise ValueError(f"Unknown migration type: {migration.migration_type}")
            
            # Update final status
            final_status = "completed" if success else "failed"
            self.versioning_service.update_migration_progress(
                migration_id=migration_id,
                progress=100,
                status=final_status,
                log_entry={
                    "action": "migration_completed" if success else "migration_failed",
                    "message": f"Migration {final_status}"
                }
            )
            
            return success
            
        except Exception as e:
            # Update migration status to failed
            self.versioning_service.update_migration_progress(
                migration_id=migration_id,
                progress=0,
                status="failed",
                error_message=str(e),
                log_entry={"action": "migration_error", "message": f"Migration failed: {str(e)}"}
            )
            return False
    
    async def _execute_version_upgrade_migration(self, migration: DocumentVersionMigration) -> bool:
        """Execute version upgrade migration"""
        
        # Get all documents for the user
        documents = self.db.query(Document).filter(
            Document.user_id == migration.user_id
        ).all()
        
        total_documents = len(documents)
        processed = 0
        
        for document in documents:
            try:
                # Upgrade document version schema if needed
                if not document.version_group_id:
                    document.version_group_id = self.versioning_service.create_version_group_id()
                
                if not document.checksum:
                    # Calculate checksum for existing documents
                    file_path = self.upload_dir / document.file_path
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                        document.checksum = self.versioning_service.calculate_file_checksum(file_data)
                
                # Create history entry for upgrade
                self.versioning_service.create_history_entry(
                    document_id=document.id,
                    user_id=migration.user_id,
                    version_number=document.version,
                    action="migrated",
                    changes={
                        "action": "version_upgrade",
                        "migration_id": migration.migration_id,
                        "upgraded_fields": ["version_group_id", "checksum"]
                    },
                    created_by=migration.user_id
                )
                
                processed += 1
                progress = int((processed / total_documents) * 100)
                
                # Update progress every 10 documents
                if processed % 10 == 0:
                    self.versioning_service.update_migration_progress(
                        migration_id=migration.migration_id,
                        progress=progress,
                        log_entry={
                            "action": "progress_update",
                            "message": f"Processed {processed}/{total_documents} documents"
                        }
                    )
                
            except Exception as e:
                self.versioning_service.update_migration_progress(
                    migration_id=migration.migration_id,
                    progress=progress,
                    log_entry={
                        "action": "document_error",
                        "message": f"Error processing document {document.id}: {str(e)}"
                    }
                )
                continue
        
        # Update migration stats
        migration.documents_affected = processed
        self.db.commit()
        
        return True
    
    async def _execute_compression_migration(self, migration: DocumentVersionMigration) -> bool:
        """Execute compression migration"""
        
        # Get all uncompressed documents for the user
        documents = self.db.query(Document).filter(
            and_(
                Document.user_id == migration.user_id,
                Document.is_compressed == "false",
                Document.is_archived == "false"
            )
        ).all()
        
        total_documents = len(documents)
        processed = 0
        space_saved = 0
        
        for document in documents:
            try:
                file_path = self.upload_dir / document.file_path
                if not file_path.exists():
                    continue
                
                # Read original file
                with open(file_path, "rb") as f:
                    original_data = f.read()
                
                original_size = len(original_data)
                
                # Skip if file is too small to benefit from compression
                if not compression_service.should_compress(original_size, document.mime_type):
                    continue
                
                # Compress the file
                compressed_data, comp_type, stats = compression_service.compress_file_content(
                    original_data, document.mime_type, auto_select=True
                )
                
                if comp_type != CompressionType.NONE:
                    # Create backup of original
                    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                    shutil.copy2(file_path, backup_path)
                    
                    # Write compressed data
                    with open(file_path, "wb") as f:
                        f.write(compressed_data)
                    
                    # Update document metadata
                    document.is_compressed = "true"
                    document.compression_type = comp_type.value
                    document.compression_ratio = f"{stats.get('compression_ratio', 0):.4f}"
                    document.file_size = len(compressed_data)
                    document.updated_at = datetime.utcnow()
                    
                    space_saved += original_size - len(compressed_data)
                    
                    # Create history entry
                    self.versioning_service.create_history_entry(
                        document_id=document.id,
                        user_id=migration.user_id,
                        version_number=document.version,
                        action="compressed",
                        changes={
                            "action": "compression_applied",
                            "migration_id": migration.migration_id,
                            "compression_type": comp_type.value,
                            "original_size": original_size,
                            "compressed_size": len(compressed_data),
                            "space_saved": original_size - len(compressed_data),
                            "compression_ratio": stats.get('compression_ratio', 0)
                        },
                        created_by=migration.user_id
                    )
                
                processed += 1
                progress = int((processed / total_documents) * 100)
                
                # Update progress every 5 documents
                if processed % 5 == 0:
                    self.versioning_service.update_migration_progress(
                        migration_id=migration.migration_id,
                        progress=progress,
                        log_entry={
                            "action": "progress_update",
                            "message": f"Compressed {processed}/{total_documents} documents, saved {space_saved} bytes"
                        }
                    )
                
            except Exception as e:
                self.versioning_service.update_migration_progress(
                    migration_id=migration.migration_id,
                    progress=progress,
                    log_entry={
                        "action": "document_error",
                        "message": f"Error compressing document {document.id}: {str(e)}"
                    }
                )
                continue
        
        # Update migration stats
        migration.documents_affected = processed
        self.db.commit()
        
        return True
    
    async def _execute_encryption_migration(self, migration: DocumentVersionMigration) -> bool:
        """Execute encryption migration"""
        
        # Get all unencrypted documents for the user
        documents = self.db.query(Document).filter(
            and_(
                Document.user_id == migration.user_id,
                Document.is_encrypted == "false",
                Document.is_archived == "false"
            )
        ).all()
        
        total_documents = len(documents)
        processed = 0
        
        for document in documents:
            try:
                file_path = self.upload_dir / document.file_path
                if not file_path.exists():
                    continue
                
                # Read original file
                with open(file_path, "rb") as f:
                    original_data = f.read()
                
                # Create hash before encryption
                data_hash = crypto_service.hash_data(original_data.hex())
                
                # Encrypt the file
                encrypted_data = crypto_service.encrypt_file(original_data)
                
                # Create backup of original
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                shutil.copy2(file_path, backup_path)
                
                # Write encrypted data
                with open(file_path, "wb") as f:
                    f.write(encrypted_data)
                
                # Update document metadata
                document.is_encrypted = "true"
                document.encryption_algorithm = "aes256"
                document.data_hash = data_hash
                document.file_size = len(encrypted_data)
                document.updated_at = datetime.utcnow()
                
                # Create history entry
                self.versioning_service.create_history_entry(
                    document_id=document.id,
                    user_id=migration.user_id,
                    version_number=document.version,
                    action="encrypted",
                    changes={
                        "action": "encryption_applied",
                        "migration_id": migration.migration_id,
                        "encryption_algorithm": "aes256",
                        "original_size": len(original_data),
                        "encrypted_size": len(encrypted_data)
                    },
                    created_by=migration.user_id
                )
                
                processed += 1
                progress = int((processed / total_documents) * 100)
                
                # Update progress every 5 documents
                if processed % 5 == 0:
                    self.versioning_service.update_migration_progress(
                        migration_id=migration.migration_id,
                        progress=progress,
                        log_entry={
                            "action": "progress_update",
                            "message": f"Encrypted {processed}/{total_documents} documents"
                        }
                    )
                
            except Exception as e:
                self.versioning_service.update_migration_progress(
                    migration_id=migration.migration_id,
                    progress=progress,
                    log_entry={
                        "action": "document_error",
                        "message": f"Error encrypting document {document.id}: {str(e)}"
                    }
                )
                continue
        
        # Update migration stats
        migration.documents_affected = processed
        self.db.commit()
        
        return True
    
    async def _execute_storage_migration(self, migration: DocumentVersionMigration) -> bool:
        """Execute storage migration (move files to new storage structure)"""
        
        # Get all documents for the user
        documents = self.db.query(Document).filter(
            Document.user_id == migration.user_id
        ).all()
        
        total_documents = len(documents)
        processed = 0
        
        # Create new storage structure
        new_storage_dir = self.upload_dir / "v2" / str(migration.user_id)
        new_storage_dir.mkdir(parents=True, exist_ok=True)
        
        for document in documents:
            try:
                old_file_path = self.upload_dir / document.file_path
                if not old_file_path.exists():
                    continue
                
                # Create new file path with better organization
                new_filename = f"{document.version_group_id or document.id}_{document.version}_{document.filename}"
                new_file_path = new_storage_dir / document.document_type / new_filename
                new_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file to new location
                shutil.move(str(old_file_path), str(new_file_path))
                
                # Update document file path
                document.file_path = str(new_file_path.relative_to(self.upload_dir))
                document.updated_at = datetime.utcnow()
                
                # Create history entry
                self.versioning_service.create_history_entry(
                    document_id=document.id,
                    user_id=migration.user_id,
                    version_number=document.version,
                    action="migrated",
                    changes={
                        "action": "storage_migrated",
                        "migration_id": migration.migration_id,
                        "old_path": str(old_file_path.relative_to(self.upload_dir)),
                        "new_path": document.file_path
                    },
                    created_by=migration.user_id
                )
                
                processed += 1
                progress = int((processed / total_documents) * 100)
                
                # Update progress every 10 documents
                if processed % 10 == 0:
                    self.versioning_service.update_migration_progress(
                        migration_id=migration.migration_id,
                        progress=progress,
                        log_entry={
                            "action": "progress_update",
                            "message": f"Migrated {processed}/{total_documents} documents to new storage"
                        }
                    )
                
            except Exception as e:
                self.versioning_service.update_migration_progress(
                    migration_id=migration.migration_id,
                    progress=progress,
                    log_entry={
                        "action": "document_error",
                        "message": f"Error migrating document {document.id}: {str(e)}"
                    }
                )
                continue
        
        # Update migration stats
        migration.documents_affected = processed
        self.db.commit()
        
        return True
    
    async def _execute_format_migration(self, migration: DocumentVersionMigration) -> bool:
        """Execute format migration (placeholder for future format conversions)"""
        
        # This would handle format conversions like:
        # - Converting old Word formats to newer ones
        # - Converting images to more efficient formats
        # - Standardizing document formats
        
        self.versioning_service.update_migration_progress(
            migration_id=migration.migration_id,
            progress=100,
            log_entry={
                "action": "format_migration_skipped",
                "message": "Format migration not implemented yet"
            }
        )
        
        return True
    
    async def _execute_cleanup_migration(self, migration: DocumentVersionMigration) -> bool:
        """Execute cleanup migration"""
        
        # Clean up old versions using the versioning service
        cleanup_stats = self.versioning_service.cleanup_old_versions(
            user_id=migration.user_id,
            keep_versions=10,  # Keep 10 most recent versions
            created_by=migration.user_id
        )
        
        # Update migration stats
        migration.documents_affected = cleanup_stats["versions_archived"]
        
        self.versioning_service.update_migration_progress(
            migration_id=migration.migration_id,
            progress=100,
            log_entry={
                "action": "cleanup_completed",
                "message": f"Archived {cleanup_stats['versions_archived']} old versions, freed {cleanup_stats['space_freed']} bytes"
            }
        )
        
        self.db.commit()
        
        return True
    
    def get_migration_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get migration recommendations for a user"""
        
        recommendations = []
        
        # Check for documents without version group IDs
        documents_without_group = self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.version_group_id.is_(None)
            )
        ).count()
        
        if documents_without_group > 0:
            recommendations.append({
                "type": "version_upgrade",
                "priority": "high",
                "description": f"{documents_without_group} documents need version schema upgrade",
                "estimated_time": f"{documents_without_group * 2} seconds"
            })
        
        # Check for uncompressed large files
        large_uncompressed = self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.is_compressed == "false",
                Document.file_size > 1024 * 1024,  # > 1MB
                Document.is_archived == "false"
            )
        ).count()
        
        if large_uncompressed > 0:
            recommendations.append({
                "type": "compression_migration",
                "priority": "medium",
                "description": f"{large_uncompressed} large files could benefit from compression",
                "estimated_time": f"{large_uncompressed * 5} seconds"
            })
        
        # Check for unencrypted files
        unencrypted = self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.is_encrypted == "false",
                Document.is_archived == "false"
            )
        ).count()
        
        if unencrypted > 0:
            recommendations.append({
                "type": "encryption_migration",
                "priority": "high",
                "description": f"{unencrypted} documents are not encrypted",
                "estimated_time": f"{unencrypted * 3} seconds"
            })
        
        # Check for old versions that can be cleaned up
        old_versions = self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.is_current_version == "false",
                Document.is_archived == "false"
            )
        ).count()
        
        if old_versions > 50:  # Only recommend if there are many old versions
            recommendations.append({
                "type": "cleanup_migration",
                "priority": "low",
                "description": f"{old_versions} old document versions can be archived",
                "estimated_time": f"{old_versions} seconds"
            })
        
        return recommendations