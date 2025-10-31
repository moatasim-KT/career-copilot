"""
Vector store service for managing precedent clauses using ChromaDB.

This module provides functionality for storing, retrieving, and searching
precedent clauses using semantic similarity search.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..core.config import get_settings
from ..core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


@dataclass
class PrecedentClause:
	"""Data model for precedent clauses stored in the vector database."""

	id: str
	text: str
	category: str
	risk_level: str  # "Low", "Medium", "High"
	source_document: str
	effectiveness_score: float
	created_at: datetime

	def to_metadata(self) -> Dict[str, Any]:
		"""Convert to metadata dictionary for ChromaDB storage."""
		return {
			"category": self.category,
			"risk_level": self.risk_level,
			"source_document": self.source_document,
			"effectiveness_score": self.effectiveness_score,
			"created_at": self.created_at.isoformat(),
		}

	@classmethod
	def from_metadata(cls, id: str, text: str, metadata: Dict[str, Any]) -> "PrecedentClause":
		"""Create PrecedentClause from ChromaDB metadata."""
		return cls(
			id=id,
			text=text,
			category=metadata.get("category", ""),
			risk_level=metadata.get("risk_level", ""),
			source_document=metadata.get("source_document", ""),
			effectiveness_score=metadata.get("effectiveness_score", 0.0),
			created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
		)


class VectorStoreService:
	"""Service for managing precedent clauses in ChromaDB vector store."""

	def __init__(self):
		self.settings = get_settings()
		self.client = None
		self.collection = None
		self._initialize_client()

	def _initialize_client(self) -> None:
		"""Initialize ChromaDB client with persistent storage."""
		try:
			# Set up persistent directory
			persist_directory = os.path.join(os.getcwd(), self.settings.chroma_persist_directory or "data/chroma")
			os.makedirs(persist_directory, exist_ok=True)

			# Initialize ChromaDB client with persistent storage
			self.client = chromadb.PersistentClient(path=persist_directory, settings=Settings(anonymized_telemetry=False, allow_reset=True))

			# Set up OpenAI embedding function
			openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=self.settings.openai_api_key, model_name="text-embedding-ada-002")

			# Get or create collection
			self.collection = self.client.get_or_create_collection(
				name="precedent_clauses",
				embedding_function=openai_ef,
				metadata={"description": "Legal precedent clauses for job application tracking"},
			)

			logger.info(f"ChromaDB initialized with persistent storage at {persist_directory}")

		except Exception as e:
			logger.error(f"Failed to initialize ChromaDB: {e!s}")
			raise VectorStoreError(f"Vector store initialization failed: {e!s}")

	def add_precedent_clause(self, clause: PrecedentClause) -> None:
		"""Add a single precedent clause to the vector store."""
		try:
			self.collection.add(documents=[clause.text], metadatas=[clause.to_metadata()], ids=[clause.id])
			logger.debug(f"Added precedent clause with ID: {clause.id}")

		except Exception as e:
			logger.error(f"Failed to add precedent clause {clause.id}: {e!s}")
			raise VectorStoreError(f"Failed to add precedent clause: {e!s}")

	def add_precedent_clauses(self, clauses: List[PrecedentClause]) -> None:
		"""Add multiple precedent clauses to the vector store."""
		if not clauses:
			return

		try:
			documents = [clause.text for clause in clauses]
			metadatas = [clause.to_metadata() for clause in clauses]
			ids = [clause.id for clause in clauses]

			self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
			logger.info(f"Added {len(clauses)} precedent clauses to vector store")

		except Exception as e:
			logger.error(f"Failed to add precedent clauses: {e!s}")
			raise VectorStoreError(f"Failed to add precedent clauses: {e!s}")

	def search_similar_clauses(
		self, query_text: str, n_results: int = 5, category_filter: Optional[str] = None, risk_level_filter: Optional[str] = None
	) -> List[PrecedentClause]:
		"""Search for similar precedent clauses using semantic similarity."""
		try:
			# Build where clause for filtering
			where_clause = {}
			if category_filter:
				where_clause["category"] = category_filter
			if risk_level_filter:
				where_clause["risk_level"] = risk_level_filter

			# Perform similarity search
			results = self.collection.query(query_texts=[query_text], n_results=n_results, where=where_clause if where_clause else None)

			# Convert results to PrecedentClause objects
			precedent_clauses = []
			if results["documents"] and results["documents"][0]:
				for i, doc in enumerate(results["documents"][0]):
					clause = PrecedentClause.from_metadata(id=results["ids"][0][i], text=doc, metadata=results["metadatas"][0][i])
					precedent_clauses.append(clause)

			logger.debug(f"Found {len(precedent_clauses)} similar clauses for query")
			return precedent_clauses

		except Exception as e:
			logger.error(f"Failed to search similar clauses: {e!s}")
			raise VectorStoreError(f"Failed to search similar clauses: {e!s}")

	def get_clause_by_id(self, clause_id: str) -> Optional[PrecedentClause]:
		"""Retrieve a specific precedent clause by ID."""
		try:
			results = self.collection.get(ids=[clause_id], include=["documents", "metadatas"])

			if results["documents"] and results["documents"][0]:
				return PrecedentClause.from_metadata(id=clause_id, text=results["documents"][0], metadata=results["metadatas"][0])

			return None

		except Exception as e:
			logger.error(f"Failed to get clause by ID {clause_id}: {e!s}")
			raise VectorStoreError(f"Failed to retrieve clause: {e!s}")

	def get_all_clauses(self) -> List[PrecedentClause]:
		"""Retrieve all precedent clauses from the vector store."""
		try:
			results = self.collection.get(include=["documents", "metadatas"])

			precedent_clauses = []
			if results["documents"]:
				for i, doc in enumerate(results["documents"]):
					clause = PrecedentClause.from_metadata(id=results["ids"][i], text=doc, metadata=results["metadatas"][i])
					precedent_clauses.append(clause)

			logger.info(f"Retrieved {len(precedent_clauses)} total clauses")
			return precedent_clauses

		except Exception as e:
			logger.error(f"Failed to get all clauses: {e!s}")
			raise VectorStoreError(f"Failed to retrieve all clauses: {e!s}")

	def delete_clause(self, clause_id: str) -> bool:
		"""Delete a precedent clause by ID."""
		try:
			self.collection.delete(ids=[clause_id])
			logger.debug(f"Deleted precedent clause with ID: {clause_id}")
			return True

		except Exception as e:
			logger.error(f"Failed to delete clause {clause_id}: {e!s}")
			raise VectorStoreError(f"Failed to delete clause: {e!s}")

	def get_collection_stats(self) -> Dict[str, Any]:
		"""Get statistics about the precedent clause collection."""
		try:
			count = self.collection.count()

			# Get category distribution
			all_clauses = self.get_all_clauses()
			categories = {}
			risk_levels = {}

			for clause in all_clauses:
				categories[clause.category] = categories.get(clause.category, 0) + 1
				risk_levels[clause.risk_level] = risk_levels.get(clause.risk_level, 0) + 1

			return {"total_clauses": count, "categories": categories, "risk_levels": risk_levels}

		except Exception as e:
			logger.error(f"Failed to get collection stats: {e!s}")
			raise VectorStoreError(f"Failed to get collection statistics: {e!s}")

	def reset_collection(self) -> None:
		"""Reset the collection (delete all data). Use with caution."""
		try:
			self.client.delete_collection("precedent_clauses")
			self._initialize_client()  # Recreate the collection
			logger.warning("Vector store collection has been reset")

		except Exception as e:
			logger.error(f"Failed to reset collection: {e!s}")
			raise VectorStoreError(f"Failed to reset collection: {e!s}")


# Global instance
_vector_store_service = None


def get_vector_store_service() -> VectorStoreService:
	"""Get the global vector store service instance."""
	global _vector_store_service
	if _vector_store_service is None:
		_vector_store_service = VectorStoreService()
	return _vector_store_service
