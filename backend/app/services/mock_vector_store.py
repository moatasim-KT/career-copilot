"""
Mock Vector Store Service for testing without OpenAI API key.

This module provides a mock implementation of the vector store service
that can work without requiring OpenAI API keys for testing purposes.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


@dataclass
class MockPrecedentClause:
	"""Data model for precedent clauses in the mock vector store."""

	id: str
	text: str
	category: str
	risk_level: str  # "Low", "Medium", "High"
	source_document: str
	effectiveness_score: float
	created_at: str  # ISO format string

	def to_metadata(self) -> Dict[str, Any]:
		"""Convert to metadata dictionary for storage."""
		return {
			"category": self.category,
			"risk_level": self.risk_level,
			"source_document": self.source_document,
			"effectiveness_score": self.effectiveness_score,
			"created_at": self.created_at,
		}

	@classmethod
	def from_metadata(cls, id: str, text: str, metadata: Dict[str, Any]) -> "MockPrecedentClause":
		"""Create MockPrecedentClause from metadata."""
		return cls(
			id=id,
			text=text,
			category=metadata.get("category", ""),
			risk_level=metadata.get("risk_level", ""),
			source_document=metadata.get("source_document", ""),
			effectiveness_score=metadata.get("effectiveness_score", 0.0),
			created_at=metadata.get("created_at", datetime.now(timezone.utc).isoformat()),
		)


class MockVectorStoreService:
	"""Mock service for managing precedent clauses without external dependencies."""

	def __init__(self):
		self.data_file = Path("data/chroma/precedents.json")
		self.precedents: Dict[str, MockPrecedentClause] = {}
		self._load_precedents()

	def _load_precedents(self) -> None:
		"""Load precedents from JSON file."""
		try:
			if self.data_file.exists():
				with open(self.data_file, "r") as f:
					precedents_data = json.load(f)

				for precedent_data in precedents_data:
					precedent = MockPrecedentClause(
						id=precedent_data["id"],
						text=precedent_data["text"],
						category=precedent_data["category"],
						risk_level=precedent_data["risk_level"],
						source_document=precedent_data["source_document"],
						effectiveness_score=precedent_data["effectiveness_score"],
						created_at=precedent_data["created_at"],
					)
					self.precedents[precedent.id] = precedent

				logger.info(f"Loaded {len(self.precedents)} precedent clauses from {self.data_file}")
			else:
				logger.info("No precedents file found, starting with empty store")

		except Exception as e:
			logger.error(f"Failed to load precedents: {e}")
			self.precedents = {}

	def _save_precedents(self) -> None:
		"""Save precedents to JSON file."""
		try:
			# Ensure directory exists
			self.data_file.parent.mkdir(parents=True, exist_ok=True)

			precedents_data = []
			for precedent in self.precedents.values():
				precedents_data.append(
					{
						"id": precedent.id,
						"text": precedent.text,
						"category": precedent.category,
						"risk_level": precedent.risk_level,
						"source_document": precedent.source_document,
						"effectiveness_score": precedent.effectiveness_score,
						"created_at": precedent.created_at,
					}
				)

			with open(self.data_file, "w") as f:
				json.dump(precedents_data, f, indent=2)

			logger.debug(f"Saved {len(self.precedents)} precedent clauses to {self.data_file}")

		except Exception as e:
			logger.error(f"Failed to save precedents: {e}")

	def add_precedent_clause(self, clause: MockPrecedentClause) -> None:
		"""Add a single precedent clause to the mock store."""
		try:
			self.precedents[clause.id] = clause
			self._save_precedents()
			logger.debug(f"Added precedent clause with ID: {clause.id}")

		except Exception as e:
			logger.error(f"Failed to add precedent clause {clause.id}: {e}")
			raise VectorStoreError(f"Failed to add precedent clause: {e}")

	def add_precedent_clauses(self, clauses: List[MockPrecedentClause]) -> None:
		"""Add multiple precedent clauses to the mock store."""
		if not clauses:
			return

		try:
			for clause in clauses:
				self.precedents[clause.id] = clause

			self._save_precedents()
			logger.info(f"Added {len(clauses)} precedent clauses to mock vector store")

		except Exception as e:
			logger.error(f"Failed to add precedent clauses: {e}")
			raise VectorStoreError(f"Failed to add precedent clauses: {e}")

	def search_similar_clauses(
		self, query_text: str, n_results: int = 5, category_filter: Optional[str] = None, risk_level_filter: Optional[str] = None
	) -> List[MockPrecedentClause]:
		"""Search for similar precedent clauses using simple text matching."""
		try:
			# Simple text-based search (in production, this would use semantic similarity)
			query_words = set(query_text.lower().split())
			scored_clauses = []

			for clause in self.precedents.values():
				# Apply filters
				if category_filter and clause.category != category_filter:
					continue
				if risk_level_filter and clause.risk_level != risk_level_filter:
					continue

				# Simple scoring based on word overlap
				clause_words = set(clause.text.lower().split())
				intersection = len(query_words.intersection(clause_words))
				union = len(query_words.union(clause_words))

				if union > 0:
					similarity_score = intersection / union
					scored_clauses.append((similarity_score, clause))

			# Sort by similarity score and return top results
			scored_clauses.sort(key=lambda x: x[0], reverse=True)
			results = [clause for _, clause in scored_clauses[:n_results]]

			logger.debug(f"Found {len(results)} similar clauses for query")
			return results

		except Exception as e:
			logger.error(f"Failed to search similar clauses: {e}")
			raise VectorStoreError(f"Failed to search similar clauses: {e}")

	def get_clause_by_id(self, clause_id: str) -> Optional[MockPrecedentClause]:
		"""Retrieve a specific precedent clause by ID."""
		try:
			return self.precedents.get(clause_id)

		except Exception as e:
			logger.error(f"Failed to get clause by ID {clause_id}: {e}")
			raise VectorStoreError(f"Failed to retrieve clause: {e}")

	def get_all_clauses(self) -> List[MockPrecedentClause]:
		"""Retrieve all precedent clauses from the mock store."""
		try:
			return list(self.precedents.values())

		except Exception as e:
			logger.error(f"Failed to get all clauses: {e}")
			raise VectorStoreError(f"Failed to retrieve all clauses: {e}")

	def delete_clause(self, clause_id: str) -> bool:
		"""Delete a precedent clause by ID."""
		try:
			if clause_id in self.precedents:
				del self.precedents[clause_id]
				self._save_precedents()
				logger.debug(f"Deleted precedent clause with ID: {clause_id}")
				return True
			return False

		except Exception as e:
			logger.error(f"Failed to delete clause {clause_id}: {e}")
			raise VectorStoreError(f"Failed to delete clause: {e}")

	def get_collection_stats(self) -> Dict[str, Any]:
		"""Get statistics about the precedent clause collection."""
		try:
			count = len(self.precedents)

			# Get category distribution
			categories = {}
			risk_levels = {}

			for clause in self.precedents.values():
				categories[clause.category] = categories.get(clause.category, 0) + 1
				risk_levels[clause.risk_level] = risk_levels.get(clause.risk_level, 0) + 1

			return {"total_clauses": count, "categories": categories, "risk_levels": risk_levels}

		except Exception as e:
			logger.error(f"Failed to get collection stats: {e}")
			raise VectorStoreError(f"Failed to get collection statistics: {e}")

	def reset_collection(self) -> None:
		"""Reset the collection (delete all data). Use with caution."""
		try:
			self.precedents.clear()
			self._save_precedents()
			logger.warning("Mock vector store collection has been reset")

		except Exception as e:
			logger.error(f"Failed to reset collection: {e}")
			raise VectorStoreError(f"Failed to reset collection: {e}")


# Global instance
_mock_vector_store_service = None


def get_mock_vector_store_service() -> MockVectorStoreService:
	"""Get the global mock vector store service instance."""
	global _mock_vector_store_service
	if _mock_vector_store_service is None:
		_mock_vector_store_service = MockVectorStoreService()
	return _mock_vector_store_service
