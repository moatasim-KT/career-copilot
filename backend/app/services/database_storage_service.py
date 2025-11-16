"""
ChromaDB Storage Service

Provides ChromaDB-based storage for files with vector search capabilities.
PostgreSQL is used for structured metadata only.
"""

import base64
import uuid
from typing import Dict, List, Optional

from chromadb.api.models.Collection import Collection

from ..core.database import get_db
from ..core.exceptions import StorageError
from ..core.logging import get_logger
from ..models.document import Document
from .chroma_client import get_chroma_client

logger = get_logger(__name__)


class ChromaStorageService:
	"""ChromaDB-based storage service for files with AI search capabilities."""

	def __init__(self):
		"""Initialize ChromaDB storage service."""
		self.chroma_client = None
		self.collection_name = "user_documents"

	async def _ensure_client(self):
		"""Ensure ChromaDB client is initialized."""
		if self.chroma_client is None:
			from .chroma_client import get_chroma_client

			self.chroma_client = await get_chroma_client()

	async def _get_collection(self) -> Collection:
		"""Get or create the documents collection."""
		await self._ensure_client()
		return await self.chroma_client.get_or_create_collection(
			name=self.collection_name, metadata={"description": "User uploaded documents for AI search"}
		)

	async def store_file(self, user_id: int, file_content: bytes, original_filename: str, document_type: str, mime_type: Optional[str] = None) -> str:
		"""Store a file in ChromaDB.

		Args:
			user_id: User ID
			file_content: File content as bytes
			original_filename: Original filename
			document_type: Type of document (resume, cover_letter, etc.)
			mime_type: MIME type of the file

		Returns:
			Stored filename (UUID-based)
		"""
		try:
			# Get database session for metadata
			db_session = next(get_db())

			# Generate unique filename
			file_extension = original_filename.split(".")[-1] if "." in original_filename else "bin"
			stored_filename = f"{uuid.uuid4()}.{file_extension}"

			# Convert binary content to base64 for ChromaDB storage
			content_b64 = base64.b64encode(file_content).decode("utf-8")

			# Create document record in PostgreSQL (metadata only)
			document = Document(
				user_id=user_id,
				original_filename=original_filename,
				stored_filename=stored_filename,
				document_type=document_type,
				file_size=len(file_content),
				mime_type=mime_type,
				content=file_content,  # Keep in PostgreSQL for direct access
			)

			db_session.add(document)
			db_session.commit()
			db_session.refresh(document)

			# Store document content in ChromaDB for AI search
			collection = await self._get_collection()

			# Try to extract text content for search (simple approach)
			text_content = self._extract_text_content(file_content, mime_type or "")

			await collection.add(
				ids=[stored_filename],
				documents=[text_content or f"Document: {original_filename}"],
				metadatas=[
					{
						"user_id": str(user_id),
						"original_filename": original_filename,
						"document_type": document_type,
						"mime_type": mime_type or "",
						"file_size": len(file_content),
						"stored_filename": stored_filename,
					}
				],
			)

			logger.info(f"Stored file {stored_filename} for user {user_id} in ChromaDB")
			return stored_filename

		except Exception as e:
			logger.error(f"Failed to store file: {e}")
			if "db_session" in locals():
				db_session.rollback()
			raise StorageError(f"Failed to store file: {e!s}")

	def _extract_text_content(self, file_content: bytes, mime_type: str) -> Optional[str]:
		"""Extract text content from file for ChromaDB indexing."""
		try:
			if mime_type.startswith("text/"):
				return file_content.decode("utf-8", errors="ignore")
			elif mime_type == "application/pdf":
				# Simple PDF text extraction (basic implementation)
				# In production, you'd want proper PDF parsing
				return file_content.decode("utf-8", errors="ignore")[:1000]
			else:
				# For binary files, return None (ChromaDB will use filename)
				return None
		except Exception:
			return None

	async def get_file(self, stored_filename: str) -> Optional[bytes]:
		"""Retrieve file content from PostgreSQL.

		Args:
			stored_filename: Stored filename

		Returns:
			File content as bytes, or None if not found
		"""
		try:
			db_session = next(get_db())
			document = db_session.query(Document).filter_by(stored_filename=stored_filename).first()
			if document:
				# Update usage tracking
				document.usage_count += 1
				from datetime import datetime, timezone

				document.last_used = datetime.now(timezone.utc)
				db_session.commit()
				return document.content
			return None

		except Exception as e:
			logger.error(f"Failed to retrieve file {stored_filename}: {e}")
			return None

	async def delete_file(self, stored_filename: str) -> bool:
		"""Delete a file from both PostgreSQL and ChromaDB.

		Args:
			stored_filename: Stored filename

		Returns:
			True if deleted, False if not found
		"""
		try:
			db_session = next(get_db())
			document = db_session.query(Document).filter_by(stored_filename=stored_filename).first()

			if document:
				# Delete from PostgreSQL
				db_session.delete(document)
				db_session.commit()

				# Delete from ChromaDB
				try:
					collection = await self._get_collection()
					await collection.delete(ids=[stored_filename])  # nosec B608 - ChromaDB deletion API, not SQL
				except Exception as e:
					logger.warning(f"Failed to remove ChromaDB document: {e}")

				logger.info(f"Deleted file {stored_filename}")
				return True
			return False

		except Exception as e:
			logger.error(f"Failed to delete file {stored_filename}: {e}")
			if "db_session" in locals():
				db_session.rollback()
			return False

	async def list_user_files(self, user_id: int, document_type: Optional[str] = None) -> List[Dict]:
		"""List files for a user from PostgreSQL.

		Args:
			user_id: User ID
			document_type: Optional document type filter

		Returns:
			List of file metadata dictionaries
		"""
		try:
			db_session = next(get_db())
			query = db_session.query(Document).filter_by(user_id=user_id)
			if document_type:
				query = query.filter_by(document_type=document_type)

			documents = query.all()
			return [
				{
					"id": doc.id,
					"original_filename": doc.original_filename,
					"stored_filename": doc.stored_filename,
					"document_type": doc.document_type,
					"file_size": doc.file_size,
					"mime_type": doc.mime_type,
					"usage_count": doc.usage_count,
					"last_used": doc.last_used.isoformat() if doc.last_used else None,
					"created_at": doc.created_at.isoformat(),
					"updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
				}
				for doc in documents
			]

		except Exception as e:
			logger.error(f"Failed to list files for user {user_id}: {e}")
			return []

	async def get_file_metadata(self, stored_filename: str) -> Optional[Dict]:
		"""Get metadata for a file from PostgreSQL.

		Args:
			stored_filename: Stored filename

		Returns:
			File metadata dictionary, or None if not found
		"""
		try:
			db_session = next(get_db())
			document = db_session.query(Document).filter_by(stored_filename=stored_filename).first()
			if document:
				return {
					"id": document.id,
					"user_id": document.user_id,
					"original_filename": document.original_filename,
					"stored_filename": document.stored_filename,
					"document_type": document.document_type,
					"file_size": document.file_size,
					"mime_type": document.mime_type,
					"usage_count": document.usage_count,
					"last_used": document.last_used.isoformat() if document.last_used else None,
					"created_at": document.created_at.isoformat(),
					"updated_at": document.updated_at.isoformat() if document.updated_at else None,
				}
			return None

		except Exception as e:
			logger.error(f"Failed to get metadata for {stored_filename}: {e}")
			return None

	async def search_documents(self, query: str, user_id: Optional[int] = None, limit: int = 10) -> List[Dict]:
		"""Search documents using ChromaDB vector search.

		Args:
			query: Search query
			user_id: Optional user ID filter
			limit: Maximum number of results

		Returns:
			List of search results with metadata
		"""
		try:
			collection = await self._get_collection()

			# Build where clause for filtering
			where_clause = {}
			if user_id:
				where_clause["user_id"] = str(user_id)

			results = await collection.query(
				query_texts=[query], where=where_clause if where_clause else None, n_results=limit, include=["documents", "metadatas", "distances"]
			)

			search_results = []
			if results and results["ids"]:
				for i, doc_id in enumerate(results["ids"][0]):
					metadata = results["metadatas"][0][i]
					distance = results["distances"][0][i] if results["distances"] else None

					search_results.append(
						{
							"stored_filename": doc_id,
							"original_filename": metadata.get("original_filename", ""),
							"document_type": metadata.get("document_type", ""),
							"mime_type": metadata.get("mime_type", ""),
							"file_size": metadata.get("file_size", 0),
							"relevance_score": 1.0 - (distance or 0),  # Convert distance to relevance
							"metadata": metadata,
						}
					)

			return search_results

		except Exception as e:
			logger.error(f"Failed to search documents: {e}")
			return []


import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.exceptions import StorageError
from ..core.logging import get_logger
from ..models.document import Document

logger = get_logger(__name__)


class DatabaseStorageService:
	"""Simple database storage service for files."""

	def __init__(self, db: Optional[Session] = None):
		"""Initialize database storage service.

		Args:
			db: Database session (will get one if None)
		"""
		self.db = db

	async def store_file(self, user_id: int, file_content: bytes, original_filename: str, document_type: str, mime_type: Optional[str] = None) -> str:
		"""Store a file in the database.

		Args:
			user_id: User ID
			file_content: File content as bytes
			original_filename: Original filename
			document_type: Type of document (resume, cover_letter, etc.)
			mime_type: MIME type of the file

		Returns:
			Stored filename (UUID-based)
		"""
		try:
			# Get database session
			if self.db is None:
				db_session = next(get_db())
			else:
				db_session = self.db

			# Generate unique filename
			file_extension = original_filename.split(".")[-1] if "." in original_filename else "bin"
			stored_filename = f"{uuid.uuid4()}.{file_extension}"

			# Create document record
			document = Document(
				user_id=user_id,
				original_filename=original_filename,
				stored_filename=stored_filename,
				document_type=document_type,
				file_size=len(file_content),
				mime_type=mime_type,
				content=file_content,
			)

			db_session.add(document)
			db_session.commit()
			db_session.refresh(document)

			logger.info(f"Stored file {stored_filename} for user {user_id}")
			return stored_filename

		except Exception as e:
			if self.db is None and "db_session" in locals():
				db_session.rollback()
			elif self.db is not None:
				self.db.rollback()
			logger.error(f"Failed to store file: {e}")
			raise StorageError(f"Failed to store file: {e!s}")

	async def get_file(self, stored_filename: str) -> Optional[bytes]:
		"""Retrieve file content from database.

		Args:
			stored_filename: Stored filename

		Returns:
			File content as bytes, or None if not found
		"""
		try:
			# Get database session
			if self.db is None:
				db_session = next(get_db())
			else:
				db_session = self.db

			document = db_session.query(Document).filter_by(stored_filename=stored_filename).first()
			if document:
				# Update usage tracking
				document.usage_count += 1
				document.last_used = datetime.now(timezone.utc)
				db_session.commit()
				return document.content
			return None

		except Exception as e:
			logger.error(f"Failed to retrieve file {stored_filename}: {e}")
			return None

	async def delete_file(self, stored_filename: str) -> bool:
		"""Delete a file from database.

		Args:
			stored_filename: Stored filename

		Returns:
			True if deleted, False if not found
		"""
		try:
			# Get database session
			if self.db is None:
				db_session = next(get_db())
			else:
				db_session = self.db

			document = db_session.query(Document).filter_by(stored_filename=stored_filename).first()
			if document:
				db_session.delete(document)
				db_session.commit()
				logger.info(f"Deleted file {stored_filename}")
				return True
			return False

		except Exception as e:
			if self.db is None and "db_session" in locals():
				db_session.rollback()
			elif self.db is not None:
				self.db.rollback()
			logger.error(f"Failed to delete file {stored_filename}: {e}")
			return False

	async def list_user_files(self, user_id: int, document_type: Optional[str] = None) -> List[Dict]:
		"""List files for a user.

		Args:
			user_id: User ID
			document_type: Optional document type filter

		Returns:
			List of file metadata dictionaries
		"""
		try:
			# Get database session
			if self.db is None:
				db_session = next(get_db())
			else:
				db_session = self.db

			query = db_session.query(Document).filter_by(user_id=user_id)
			if document_type:
				query = query.filter_by(document_type=document_type)

			documents = query.all()
			return [
				{
					"id": doc.id,
					"original_filename": doc.original_filename,
					"stored_filename": doc.stored_filename,
					"document_type": doc.document_type,
					"file_size": doc.file_size,
					"mime_type": doc.mime_type,
					"usage_count": doc.usage_count,
					"last_used": doc.last_used.isoformat() if doc.last_used else None,
					"created_at": doc.created_at.isoformat(),
					"updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
				}
				for doc in documents
			]

		except Exception as e:
			logger.error(f"Failed to list files for user {user_id}: {e}")
			return []

	async def get_file_metadata(self, stored_filename: str) -> Optional[Dict]:
		"""Get metadata for a file.

		Args:
			stored_filename: Stored filename

		Returns:
			File metadata dictionary, or None if not found
		"""
		try:
			# Get database session
			if self.db is None:
				db_session = next(get_db())
			else:
				db_session = self.db

			document = db_session.query(Document).filter_by(stored_filename=stored_filename).first()
			if document:
				return {
					"id": document.id,
					"user_id": document.user_id,
					"original_filename": document.original_filename,
					"stored_filename": document.stored_filename,
					"document_type": document.document_type,
					"file_size": document.file_size,
					"mime_type": document.mime_type,
					"usage_count": document.usage_count,
					"last_used": document.last_used.isoformat() if document.last_used else None,
					"created_at": document.created_at.isoformat(),
					"updated_at": document.updated_at.isoformat() if document.updated_at else None,
				}
			return None

		except Exception as e:
			logger.error(f"Failed to get metadata for {stored_filename}: {e}")
			return None
