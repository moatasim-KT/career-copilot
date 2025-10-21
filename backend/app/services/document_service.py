"""
Document service for Career Co-Pilot system with compression and encryption support
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.document import Document
from app.models.application import JobApplication
from app.models.document_history import DocumentHistory
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentSearchFilters,
    DocumentUsageStats, SUPPORTED_MIME_TYPES, DOCUMENT_TYPES
)
from app.core.config import settings
from app.services.crypto_service import crypto_service
from app.services.compression_service import compression_service, CompressionType


class DocumentService:
    """Service for managing documents"""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_file_checksum(self, file_data: bytes) -> str:
        """Calculate SHA256 checksum for file data"""
        import hashlib
        return hashlib.sha256(file_data).hexdigest()
    
    def create_version_group_id(self) -> str:
        """Generate a new version group ID"""
        return str(uuid.uuid4())
    
    def create_history_entry(
        self,
        document_id: int,
        user_id: int,
        version_number: int,
        action: str,
        changes: Dict[str, Any],
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
        created_by: Optional[int] = None,
        version_metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentHistory:
        """Create a history entry for a document action"""
        
        history_entry = DocumentHistory(
            document_id=document_id,
            user_id=user_id,
            version_number=version_number,
            action=action,
            changes=changes,
            file_path=file_path,
            file_size=file_size,
            checksum=checksum,
            created_by=created_by or user_id,
            version_metadata=version_metadata or {}
        )
        
        self.db.add(history_entry)
        self.db.flush()
        
        return history_entry
    
    def upload_document(
        self, 
        user_id: int, 
        file: UploadFile, 
        document_data: DocumentCreate
    ) -> Document:
        """Upload and store a new document"""
        
        # Validate file type
        if file.content_type not in SUPPORTED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Validate document type
        if document_data.document_type not in DOCUMENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type: {document_data.document_type}"
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create user-specific directory
        user_dir = self.upload_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Read file data
        file.file.seek(0)
        file_data = file.file.read()
        original_size = len(file_data)
        
        # Calculate checksum for integrity verification
        file_checksum = self.calculate_file_checksum(file_data)
        
        # Generate version group ID for new documents
        version_group_id = self.create_version_group_id()
        
        # Initialize compression and encryption metadata
        is_compressed = "false"
        compression_type = None
        compression_ratio = None
        is_encrypted = "false"
        encryption_algorithm = None
        data_hash = None
        
        # Apply compression if enabled and beneficial
        if settings.ENABLE_COMPRESSION and compression_service.should_compress(original_size, file.content_type):
            try:
                if settings.AUTO_SELECT_COMPRESSION:
                    compressed_data, comp_type, stats = compression_service.compress_file_content(
                        file_data, file.content_type, auto_select=True
                    )
                else:
                    compressed_data, comp_type = compression_service.compress_data(file_data)
                    stats = compression_service.get_compression_stats(file_data, compressed_data, comp_type)
                
                if comp_type != CompressionType.NONE:
                    file_data = compressed_data
                    is_compressed = "true"
                    compression_type = comp_type.value
                    compression_ratio = f"{stats.get('compression_ratio', 0):.4f}"
            except Exception as e:
                # If compression fails, continue with original data
                print(f"Compression failed for {file.filename}: {str(e)}")
        
        # Apply encryption if enabled
        if settings.ENCRYPT_FILES:
            try:
                # Create hash before encryption for integrity verification
                data_hash = crypto_service.hash_data(file_data.hex())
                
                # Encrypt file data
                encrypted_data = crypto_service.encrypt_file(file_data)
                file_data = encrypted_data
                is_encrypted = "true"
                encryption_algorithm = "aes256"
            except Exception as e:
                # If encryption fails, continue with original/compressed data
                print(f"Encryption failed for {file.filename}: {str(e)}")
        
        # Save processed file
        file_path = user_dir / unique_filename
        try:
            with open(file_path, "wb") as buffer:
                buffer.write(file_data)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Create document record with compression and encryption metadata
        document = Document(
            user_id=user_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path.relative_to(self.upload_dir)),
            document_type=document_data.document_type,
            mime_type=file.content_type,
            file_size=len(file_data),  # Size after compression/encryption
            original_size=original_size,  # Original file size
            description=document_data.description,
            notes=document_data.notes,
            tags=document_data.tags,
            version=1,
            is_current_version="true",
            version_group_id=version_group_id,
            checksum=file_checksum,
            usage_count=0,
            content_analysis={},
            is_compressed=is_compressed,
            compression_type=compression_type,
            compression_ratio=compression_ratio,
            is_encrypted=is_encrypted,
            encryption_algorithm=encryption_algorithm,
            data_hash=data_hash
        )
        
        self.db.add(document)
        self.db.flush()  # Get the ID
        
        # Create initial history entry
        self.create_history_entry(
            document_id=document.id,
            user_id=user_id,
            version_number=1,
            action="created",
            changes={
                "action": "document_created",
                "document_type": document_data.document_type,
                "file_size": len(file_data),
                "original_filename": file.filename,
                "checksum": file_checksum,
                "compressed": is_compressed == "true",
                "encrypted": is_encrypted == "true"
            },
            file_path=str(file_path.relative_to(self.upload_dir)),
            file_size=len(file_data),
            checksum=file_checksum,
            created_by=user_id
        )
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def get_document(self, document_id: int, user_id: int) -> Optional[Document]:
        """Get a document by ID for a specific user"""
        return self.db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.user_id == user_id
            )
        ).first()
    
    def get_user_documents(
        self, 
        user_id: int, 
        filters: Optional[DocumentSearchFilters] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Document], int]:
        """Get documents for a user with optional filtering"""
        
        query = self.db.query(Document).filter(Document.user_id == user_id)
        
        # Apply filters
        if filters:
            if filters.document_type:
                query = query.filter(Document.document_type == filters.document_type)
            
            if filters.mime_type:
                query = query.filter(Document.mime_type == filters.mime_type)
            
            if filters.created_after:
                query = query.filter(Document.created_at >= filters.created_after)
            
            if filters.created_before:
                query = query.filter(Document.created_at <= filters.created_before)
            
            if filters.tags:
                # Filter documents that have any of the specified tags
                for tag in filters.tags:
                    query = query.filter(Document.tags.contains([tag]))
            
            if filters.search_text:
                # Search in filename, description, and notes
                search_term = f"%{filters.search_text}%"
                query = query.filter(
                    or_(
                        Document.original_filename.ilike(search_term),
                        Document.description.ilike(search_term),
                        Document.notes.ilike(search_term)
                    )
                )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        documents = query.order_by(desc(Document.created_at)).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        return documents, total
    
    def update_document(
        self, 
        document_id: int, 
        user_id: int, 
        update_data: DocumentUpdate
    ) -> Optional[Document]:
        """Update document metadata"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(document, field, value)
        
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def delete_document(self, document_id: int, user_id: int) -> bool:
        """Delete a document and its file"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            return False
        
        # Delete file from filesystem
        file_path = self.upload_dir / document.file_path
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            # Log error but continue with database deletion
            pass
        
        # Delete from database
        self.db.delete(document)
        self.db.commit()
        
        return True
    
    def create_document_version(
        self, 
        document_id: int, 
        user_id: int, 
        file: UploadFile
    ) -> Document:
        """Create a new version of an existing document"""
        
        # Get original document
        original_doc = self.get_document(document_id, user_id)
        if not original_doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Validate file type matches original
        if file.content_type != original_doc.mime_type:
            raise HTTPException(
                status_code=400,
                detail="New version must have the same file type as original"
            )
        
        # Mark current version as not current
        original_doc.is_current_version = "false"
        
        # Create new version
        document_data = DocumentCreate(
            document_type=original_doc.document_type,
            description=original_doc.description,
            notes=original_doc.notes,
            tags=original_doc.tags
        )
        
        new_version = self.upload_document(user_id, file, document_data)
        
        # Set version information
        new_version.version = original_doc.version + 1
        new_version.parent_document_id = original_doc.id
        
        self.db.commit()
        self.db.refresh(new_version)
        
        return new_version
    
    def get_document_versions(self, document_id: int, user_id: int) -> List[Document]:
        """Get all versions of a document"""
        
        # Get the document to verify ownership
        document = self.get_document(document_id, user_id)
        if not document:
            return []
        
        # Find root document
        root_id = document.parent_document_id or document.id
        
        # Get all versions
        versions = self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                or_(
                    Document.id == root_id,
                    Document.parent_document_id == root_id
                )
            )
        ).order_by(Document.version).all()
        
        return versions
    
    def associate_with_application(
        self, 
        application_id: int, 
        document_ids: List[int], 
        user_id: int
    ) -> bool:
        """Associate documents with a job application"""
        
        # Get application
        application = self.db.query(JobApplication).filter(
            and_(
                JobApplication.id == application_id,
                JobApplication.user_id == user_id
            )
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Verify all documents belong to user
        documents = self.db.query(Document).filter(
            and_(
                Document.id.in_(document_ids),
                Document.user_id == user_id
            )
        ).all()
        
        if len(documents) != len(document_ids):
            raise HTTPException(status_code=400, detail="Some documents not found")
        
        # Create document associations
        document_associations = []
        for doc in documents:
            association = {
                "document_id": doc.id,
                "type": doc.document_type,
                "filename": doc.original_filename,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            document_associations.append(association)
            
            # Update document usage
            doc.usage_count += 1
            doc.last_used = datetime.utcnow()
        
        # Update application documents
        application.documents = document_associations
        application.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    def get_document_usage_stats(self, document_id: int, user_id: int) -> Optional[DocumentUsageStats]:
        """Get usage statistics for a document"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            return None
        
        # Find applications that use this document
        applications = self.db.query(JobApplication).filter(
            and_(
                JobApplication.user_id == user_id,
                JobApplication.documents.contains([{"document_id": document_id}])
            )
        ).all()
        
        application_ids = [app.id for app in applications]
        
        return DocumentUsageStats(
            document_id=document_id,
            usage_count=document.usage_count,
            last_used=document.last_used,
            applications_used_in=application_ids
        )
    
    def get_file_path(self, document_id: int, user_id: int) -> Optional[Path]:
        """Get the file system path for a document"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            return None
        
        return self.upload_dir / document.file_path
    
    def get_file_content(self, document_id: int, user_id: int) -> Optional[bytes]:
        """Get decrypted and decompressed file content"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            return None
        
        file_path = self.upload_dir / document.file_path
        if not file_path.exists():
            return None
        
        try:
            # Read file data
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            # Decrypt if encrypted
            if document.is_encrypted == "true":
                try:
                    file_data = crypto_service.decrypt_file(file_data)
                    
                    # Verify data integrity if hash is available
                    if document.data_hash:
                        calculated_hash = crypto_service.hash_data(file_data.hex())
                        if calculated_hash != document.data_hash:
                            raise ValueError("File integrity check failed")
                            
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to decrypt file: {str(e)}"
                    )
            
            # Decompress if compressed
            if document.is_compressed == "true" and document.compression_type:
                try:
                    compression_type = CompressionType(document.compression_type)
                    file_data = compression_service.decompress_data(file_data, compression_type)
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to decompress file: {str(e)}"
                    )
            
            return file_data
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read file: {str(e)}"
            )
    
    def analyze_document_content(self, document_id: int, user_id: int) -> Dict[str, Any]:
        """Analyze document content (placeholder for future ML integration)"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Placeholder analysis - in a real implementation, this would:
        # 1. Extract text from PDF/Word documents
        # 2. Use NLP to identify skills, experience, etc.
        # 3. Calculate ATS compatibility scores
        # 4. Provide optimization suggestions
        
        analysis = {
            "extracted_text": "Document text would be extracted here...",
            "analysis": {
                "skills_mentioned": [],
                "experience_years": 0,
                "education": [],
                "certifications": [],
                "keywords": []
            },
            "optimization_suggestions": [
                "Add more quantified achievements",
                "Include relevant keywords for ATS optimization"
            ],
            "ats_score": 75,
            "readability_score": 85
        }
        
        # Update document with analysis
        document.content_analysis = analysis
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return analysis